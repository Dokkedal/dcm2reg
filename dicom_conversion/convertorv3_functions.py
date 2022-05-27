"""
Functions that help with:

Convert dicom image modalities with ROI
The funcitons of this script is to use RTSTRUCT with SeriesInstanceUID to locate the
correponding primary image. And convert all image modalities sharing same StudyInstanceUID
with the primary image within a specific date gap (). 
Jintao Ren
jintaoren@onoclogy.au.dk
2022.01.06

"""

import pydicom
import pathlib
import argparse
import itertools
import sys
import numpy as np
import SimpleITK as sitk
import skimage.draw
import time
import os
import json
import pandas as pd

#---------------
# libs to normalize ROI names, used in remove_accents()
import re
import traceback
import six
import unicodedata
#---------------
from datetime import datetime

# -*- coding: utf-8 -*-
#from pandas import json_normalize

import ast

from .image_readers import read_dcm_series

# Setup logging
# TODO: Move this to a central logger.
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

MODALITY_TAG = (0x8, 0x60)
REFERENCED_FRAME_OF_REFERENCE_SEQUENCE_TAG = (0x3006, 0x10)
FRAME_OF_REFERENCE_UID_TAG = (0x20, 0x52)
ROI_CONTOUR_SEQUENCE_TAG = (0x3006, 0x39)
ROI_DISPLAY_COLOR_TAG = (0x3006, 0x2a)
REFERENCED_ROI_NUMBER_TAG = (0x3006, 0x84)
ROI_NUMBER_TAG = (0x3006, 0x22)
CONTOUR_SEQUENCE_TAG = (0x3006, 0x40)
CONTOUR_DATA_TAG = (0x3006, 0x50)
ROI_NAME_TAG = (0x3006, 0x26)
STRUCTURE_SET_DATE_TAG = (0x3006, 0x8)
STRUCTURE_SET_TIME_TAG = (0x3006, 0x9)
STRUCTURE_SET_RIO_SEQUENCE_TAG = (0x3006, 0x20)

def day_difference(date1,date2): 
    date_format = "%Y%m%d"
    a = datetime.strptime(date1, date_format)
    b = datetime.strptime(date2, date_format)
    delta = b - a
    return abs(int(delta.days))


def grouper(iterable, n):
    """Given a long string it groups in pairs of `n`"""
    args = [iter(iterable)] * n
    return itertools.zip_longest(*args)


def contour_world_to_index(contour_data, image):
    # TODO: This can be a property of a future Image class.
    return [image.TransformPhysicalPointToIndex(point) for point in
            [
                [float(_) for _ in group] for group in grouper(contour_data, 3)
            ]
    ]

def remove_accents(filename):
    """
    Function that will try to remove accents from a unicode string to be used in a filename.
    input filename should be either an ascii or unicode string
    """
    # noinspection PyBroadException
    try:
        filename = filename.replace(" ", "_")
        if isinstance(filename, type(six.u(''))):
            unicode_filename = filename
        else:
            unicode_filename = six.u(filename)
        cleaned_filename = unicodedata.normalize('NFKD', unicode_filename).encode('ASCII', 'ignore').decode('ASCII')

        cleaned_filename = re.sub('[^\w\s-]', '', cleaned_filename.strip().lower())
        cleaned_filename = re.sub('[-\s]+', '-', cleaned_filename)

        return cleaned_filename
    except:
        traceback.print_exc()
        return filename

def get_ROIs(scan):

    structs = '' 
    # first create a map so that we can easily trace referenced_roi_number back to its metadata
    metadata_mappings = {}
    for contour_metadata in scan.StructureSetROISequence:
        
        metadata_mappings[contour_metadata.ROINumber] = contour_metadata

    for contour_sequence in scan.ROIContourSequence:
        contour_data = {}
        metadata = metadata_mappings[contour_sequence.ReferencedROINumber] # retrieve metadata
        if hasattr(metadata, 'ROIName'):
            structs = structs+remove_accents(metadata.ROIName)+','
    
    return structs[:-1]

def read_rtstruct(image_filenames, rtstruct_filename):
    """Reads directory of DICOM files and rstruct file"""
    output_dict = {'image_filenames': image_filenames}

    if rtstruct_filename:
        rtstruct = pydicom.read_file(str(rtstruct_filename), stop_before_pixels=True)
        if not rtstruct[MODALITY_TAG].value == 'RTSTRUCT':
            raise ValueError(f'{rtstruct_filename} is not an RTSTRUCT.')

        output_dict['rtstruct_filename'] = rtstruct_filename
    data, sitk_image, image_metadata = read_dcm_series(directory_or_files=image_filenames, series_id=None,
                                                       return_sitk=True)

    output_dict['num_slices'] = len(image_metadata['filenames'])
    output_dict['sitk_image'] = sitk_image

    if rtstruct_filename:
        # We start by constructing an empty dictionary with all available ROIs.
        structures = {
            structure[ROI_NUMBER_TAG].value: {
                'roi_name': structure[ROI_NAME_TAG].value,
                'points': [],
            } for structure in rtstruct[STRUCTURE_SET_RIO_SEQUENCE_TAG].value
        }
        if not structures:
            raise ValueError(f'{rtstruct_filename} does not contain any ROIs.')

        # Next, we fill the points
        for contour in rtstruct[ROI_CONTOUR_SEQUENCE_TAG].value:
            # Each ROI has a number.
            roi_no = contour[REFERENCED_ROI_NUMBER_TAG].value
            try:
                for contour_string in contour[CONTOUR_SEQUENCE_TAG].value:
                    # We can extract the string containing the contour information
                    contour_data = contour_string[CONTOUR_DATA_TAG].value
                    # Convert the contour data to points and store in the structure.
                    structures[roi_no]['points'] += contour_world_to_index(contour_data, sitk_image)
            except KeyError:
                # Ignore missing contours
                pass

        # The structures dictionary is slightly inconvenient, but this is
        # unfortunately how it is stored in the RTSTRUCT. We rewrite it here
        new_structures = {}
        output_dict['roi_names'] = []
        for roi_no, roi in structures.items():
            roi_name = roi['roi_name']
            roi_points = roi['points']

            if len(roi_points) < 3:  # Contour needs at least three points.
                continue
            output_dict['roi_names'].append(roi_name)
            new_structures[roi_name] = {
                'roi_number': roi_no,
                'points': roi_points,
            }
        output_dict['structures'] = new_structures

    return output_dict


def split_curves(curve, eps=3):
    """
    Traverse a Dicom world-curve and split up into closed contours. It is assumed that the
    individual contours can be detected in an unambiguous manner by traversing the world-curve in
    the order it is stored and locating the first point at which the world-curve comes back, i.e.,
    is close, to an initial starting point.
    Parameters
    ----------
    curve: float-valued numpy array of size [num_pts 2]
        the curve which traverses possibly multiple closed contours (coordinates are integers)
    eps: float
        threshold used to establish that two points are sufficiently close to each other. This
        threshold is used to mark the start and end of a curve.
    Returns
    -------
    contours: list of numpy arrays each of size [num_pts_contour 2]
        the extracted contours
    """

    # Initialization
    num_pts = curve.shape[1]
    current_start_pt = 0
    current_end_pt = 0

    # Find contours
    contours = []
    num_contours = 0
    while current_end_pt <= num_pts - 1:

        # Get out of epsilon neighborhood of starting point
        while current_end_pt <= num_pts - 1 and \
                np.linalg.norm(curve[:, current_start_pt] - curve[:, current_end_pt]) < eps:
            current_end_pt += 1

        # Locate endpoint contour and add to set of contours
        while current_end_pt <= num_pts - 1 and \
                np.linalg.norm(curve[:, current_start_pt] - curve[:, current_end_pt]) >= eps:
            current_end_pt += 1

        # Find start new contour
        while current_end_pt <= num_pts - 1 and \
                np.linalg.norm(curve[:, current_start_pt] - curve[:, current_end_pt]) < eps:
            current_end_pt += 1
        contours.append(curve[:, current_start_pt:current_end_pt])
        num_contours += 1
        current_start_pt = current_end_pt

    return contours


def world_curve_to_mask(curves, size):
    """
    Construct binary mask determined by a set of closed curves. A region enclosed by one curve
    contained in a region enclosed by another curve is interpreted as a hole. It is assumed that
    if two enclosed regions have a non-empty intersection, then one region is a proper subset of
    the other.
    Parameters
    ----------
    curve: float-valued numpy array of size [num_pts 2]
        the curve which traverses possibly multiple closed curves (coordinates are integers)
    size: 2-tuple of ints
        spatial dimensions of mask
    Returns
    -------
    mask: numpy array of prescribed size
        binary mask associated to region(s) enclosed by curves (should be stored as a binary array)
    """
    mask = np.zeros(size)

    for curve in split_curves(curves):
    #for curve in curves:
        rows, cols = skimage.draw.polygon(curve[0, :], curve[1, :])
        mask_curve = np.zeros(size)
        mask_curve[rows, cols] = 1
        intersect = np.where(mask * mask_curve == 1)
        new_pts = np.where((mask == 0) & (mask_curve == 1))
        if intersect:
            mask[intersect] = 0
        if new_pts:
            mask[new_pts] = 1

    return mask


class DicomRtstructReader(object):
    def __init__(self, image_filenames, rtstruct_filename):
        raw_dict = read_rtstruct(image_filenames, rtstruct_filename)
        self.roi_names = raw_dict.get('roi_names', None)
        self.num_slices = raw_dict['num_slices']

        self.image = raw_dict['sitk_image']
        self.structures = raw_dict.get('structures', [])

    def get_roi(self, roi_name):
        if roi_name not in self.roi_names:
            raise ValueError(f'ROI {roi_name} does not exist.')
        roi_dict = self.structures[roi_name]

        # Placeholder for ROI
        # TODO: Improve
        roi = np.zeros(
            (self.image.GetDepth(), self.image.GetHeight(), self.image.GetWidth()), dtype=np.uint8)

        for z, points in itertools.groupby(roi_dict['points'], key=lambda point: point[2]):
            points_list = list(points)
            y = [point[1] for point in points_list]
            x = [point[0] for point in points_list]
            roi[z, :, :] = world_curve_to_mask(np. array([y, x]), roi.shape[1::])

        sitk_roi = sitk.GetImageFromArray(roi)
        sitk_roi.SetSpacing(list(self.image.GetSpacing()))
        sitk_roi.SetDirection(self.image.GetDirection())
        sitk_roi.SetOrigin(self.image.GetOrigin())

        return sitk_roi

def construct_dict_study_instance(folder_in):
    """
    Construct dictionary StudyInstanceUID -> SeriesInstanceUID
    Parameters
    ----------
    folder_in : Path
        Path to folder containing dicom files.
    Returns
    -------
    dict
    """

    # Initialization
    dcm_files = list(folder_in.rglob('*.dcm'))
    num_dcm_files = len(dcm_files)
    logger.info(f'Located {num_dcm_files} dicom files.')
    study_dictionary = {}

    # Construct dictionary
    for idx, dicom_filename in enumerate(dcm_files):
        if (idx + 1) % (num_dcm_files // 10) == 0:
            logger.info(f'Working on {idx} / {num_dcm_files}.')

        dcm_object = pydicom.read_file(str(dicom_filename), stop_before_pixels=True)
        study_instance_uid = dcm_object.StudyInstanceUID
        if study_instance_uid not in study_dictionary:
            study_dictionary[study_instance_uid] = {}

        # If file is a RTSTRUCT append reference to associated series.
        if dcm_object.Modality in ['RTSTRUCT']:
            series_instance_uid = dcm_object.ReferencedFrameOfReferenceSequence[0] \
                                  .RTReferencedStudySequence[0] \
                                  .RTReferencedSeriesSequence[0] \
                                  .SeriesInstanceUID
            if series_instance_uid not in study_dictionary[study_instance_uid]:
                study_dictionary[study_instance_uid][series_instance_uid] = {}
            if 'RTSTRUCT' in study_dictionary[study_instance_uid][series_instance_uid]:
                study_dictionary[study_instance_uid][series_instance_uid]['RTSTRUCT'].append(str(dicom_filename))
            else:
                study_dictionary[study_instance_uid][series_instance_uid]['RTSTRUCT'] = [str(dicom_filename)]
            continue

        series_instance_uid = dcm_object.SeriesInstanceUID
        if series_instance_uid not in study_dictionary[study_instance_uid]:
            study_dictionary[study_instance_uid][series_instance_uid] = {}

        series_dictionary = study_dictionary[study_instance_uid][series_instance_uid]

        # Can be the case that only one file in the series has one of the following attributes,
        # however these always have to be set or are empty.
        for dicom_attribute in ['Modality', 'PatientID', 'PatientName', 'StudyDate']:
            if not series_dictionary.get(dicom_attribute, ''):
                series_dictionary[dicom_attribute] = str(getattr(dcm_object, dicom_attribute))

        if not series_dictionary.get('source_dir', None):
            series_dictionary['source_dir'] = dicom_filename.relative_to(folder_in).parent

        if 'filenames' in series_dictionary:
            series_dictionary['filenames'].append(str(dicom_filename))
        else:
            series_dictionary['filenames'] = [str(dicom_filename)]

    return study_dictionary


def construct_dict_patient(folder_in,startfile,endfile,list_flagged):
    """
    Construct dictionary PatientID -> SeriesInstanceUID
    Parameters
    ----------
    folder_in : Path
        Path to folder containing dicom files.
    Returns
    -------
    dict
    """

    # Initialization
    
    # Only chose dicom files from the first numberoffiles folders.
    dcm_files = []
    #print(list(os.walk(folder_in)))
    patient_folders = list(os.walk(folder_in))[0][1][startfile:endfile]
    #print(patient_folders)
    for patient_folder_name in patient_folders:
        patient_folder = os.path.join(folder_in, patient_folder_name)
        #print(patient_folder)
        patient_dcm = list(pathlib.Path(patient_folder).rglob('*.dcm'))
        dcm_files = dcm_files + patient_dcm 

    num_dcm_files = len(dcm_files)
    logger.info(f'Located {num_dcm_files} dicom files.')
    patient_dictionary = {}
    #patient_dictionary = {}

    # Construct dictionary
    for idx, dicom_filename in enumerate(dcm_files):
        if (idx + 1) % (num_dcm_files // 10) == 0:
            logger.info(f'Working on {idx} / {num_dcm_files}.')

        dcm_object = pydicom.read_file(str(dicom_filename), stop_before_pixels=True)
        patient_id = dcm_object.PatientID # change from StudyInstanceUID to PatientID
        if patient_id not in patient_dictionary:
            patient_dictionary[patient_id] = {}

        # If file is a RTSTRUCT append reference to associated series.
        if dcm_object.Modality in ['RTSTRUCT']:
            series_instance_uid = dcm_object.ReferencedFrameOfReferenceSequence[0] \
                                  .RTReferencedStudySequence[0] \
                                  .RTReferencedSeriesSequence[0] \
                                  .SeriesInstanceUID
            ROIs = get_ROIs(dcm_object)
            if series_instance_uid not in patient_dictionary[patient_id]:
                patient_dictionary[patient_id][series_instance_uid] = {}
           
            if 'RTSTRUCT' in patient_dictionary[patient_id][series_instance_uid]:
                patient_dictionary[patient_id][series_instance_uid]['RTSTRUCT'].append(str(dicom_filename))
                patient_dictionary[patient_id][series_instance_uid]['ROIs'].append(str(ROIs))
            else:
                patient_dictionary[patient_id][series_instance_uid]['RTSTRUCT'] = [str(dicom_filename)]
                patient_dictionary[patient_id][series_instance_uid]['ROIs'] = [str(ROIs)]
            continue

        series_instance_uid = dcm_object.SeriesInstanceUID
        if series_instance_uid not in patient_dictionary[patient_id]:
            #print("Her er patient_id",patient_dictionary[patient_id])
            patient_dictionary[patient_id][series_instance_uid] = {}

        series_dictionary = patient_dictionary[patient_id][series_instance_uid]

        # Can be the case that only one file in the series has one of the following attributes,
        # however these always have to be set or are empty.
        for dicom_attribute in ['Modality', 'PatientID', 'PatientName', 'StudyDate', 'SeriesDescription']:
            if not series_dictionary.get(dicom_attribute, ''):
                try:
                    series_dictionary[dicom_attribute] = str(getattr(dcm_object, dicom_attribute))
                except AttributeError:
                    logger.warning("There exists no attribute " + dicom_attribute + " for file " + str(dicom_filename))
                    series_dictionary[dicom_attribute] = "Default"
                    list_flagged.append((patient_id,"Missing attribute",1))

        if not series_dictionary.get('source_dir', None):
            dicomchild  = dicom_filename.relative_to(folder_in)
            #print("Here is child",dicomchild)
            #print("Here is parent",dicomchild.parent)
#            assert len(dicomchild.__fspath__()) > 0, f"length is {len(dicomchild.__fspath__())}"
            series_dictionary['source_dir'] = dicom_filename.relative_to(folder_in).parent
        if 'filenames' in series_dictionary:
            series_dictionary['filenames'].append(str(dicom_filename))
        else:
            series_dictionary['filenames'] = [str(dicom_filename)]
    #print("Here starts dictexport")
    #formatted = json.dumps(patient_dictionary, indent=2)
    #print(formatted)
    return patient_dictionary,list_flagged





def optimal_series(primary_studies, secondary_studies, max_study_delay):
    # select the primary study by finding the most related(studydate gap within 7 days) secondary studies. 
    related_study_count = []
    for primary_study in primary_studies:
        current_num = 0 
        for secondary_study in secondary_studies:
            if day_difference(primary_study[1] , secondary_study[1]) < max_study_delay:
                current_num += 1 
        related_study_count.append(current_num)
    if not related_study_count:
        if not primary_studies:
            return None, None
        else:    
            #print("Her er primary studies",primary_studies)
            return primary_studies[0][0],primary_studies[0][2]
    else:    
        return primary_studies[np.argmax(related_study_count)][0], primary_studies[np.argmax(related_study_count)][2] 

class DFConverter:

    #Converts the input JSON to a DataFrame
    def convertToDF(self,dfJSON):
        return(pd.read_json(dfJSON, orient = "records"))

    #Converts the input DataFrame to JSON 
    def convertToJSON(self, df):
        resultJSON = df.to_json(orient='records')
        return(resultJSON)

def read_dicts_from_excel(filepath,include_red,include_orange,include_yellow):
    """Read dictionaries from Excel-file via JSON.
    
    :param filepath: directory for excel-file
    :param include_red: boolean variable which includes red flagged patients if True
    :param include_orange: boolean variable which includes orange flagged patients if True
    :param include_yellow: boolean variable which includes yellow flagged patients if True
    
    :returns: series dictionary
    """
    df = pd.read_excel(filepath)
    
    #print("RED-ORANGE-YELLOW", include_red, include_orange, include_yellow)
    
    if not include_red:
        df = df.loc[df["Importance"]!=3]
    if not include_orange:
        df = df.loc[df["Importance"]!=2]
    if not include_yellow:
        df = df.loc[df["Importance"]!=1]
    dfConverterObject = DFConverter()
    json_dict = dfConverterObject.convertToJSON(df)
    selected_dict = json.loads(json_dict)
    return selected_dict

def write_with_sitk(sitk_image, image_fn):
    if not image_fn.exists():
        sitk.WriteImage(sitk_image, str(image_fn), True)
    else:
        logger.info(f'{image_fn} exists. Skipping.')

def wirte_primary_image_with_ROIs(modality_name, series_description, image_filenames, rtstruct_filename, ROIs, target_dir):

    logger.info(f'Writing {modality_name} to {target_dir}.')
    target_dir.mkdir(parents=True, exist_ok=True)
    if modality_name == 'CT':
        image_fn = target_dir / f'{modality_name.lower()}.nii.gz'
    else:
        image_fn = target_dir / f'{modality_name.lower()}_{series_description.lower()}.nii.gz'

    data = DicomRtstructReader(image_filenames, rtstruct_filename)
    logger.info(f'Processing {modality_name} - {series_description}data of with'
                f' {len(data.roi_names)} structures.')

    structures = {}
    for ROI in ROIs:
        for roi_name in data.roi_names:
            if ROI.lower() in roi_name.lower():
                structures[roi_name] = data.get_roi(roi_name)

    write_with_sitk(data.image,  image_fn)

    for roi_name in structures:
        write_with_sitk(
            structures[roi_name], target_dir / f'{remove_accents(roi_name).lower()}.nii.gz')

def write_secondary_images(modality_name, series_description, image_filenames, target_dir):

    logger.info(f'Writing {modality_name} to {target_dir}.')
    target_dir.mkdir(parents=True, exist_ok=True)

    ## rename PT and MR based on rules
    if modality_name == 'PT':
        image_fn = target_dir / f'{modality_name.lower()}.nii.gz'
        ## convert PET value to SUV

    elif modality_name == 'MR':
        if series_description.lower().startswith('mdixona'):
            series_description = 't1w_mdixona'
        elif series_description.lower().startswith('t2w'):
            series_description = 't2w'
                
        image_fn = target_dir / f'{modality_name.lower()}_{series_description.lower()}.nii.gz'

    # Some patients have several CT-scans. Can be secondary.
    elif modality_name == 'CT':
        image_fn = target_dir / f'{modality_name.lower()}.nii.gz'
        logger.warning(f'A CT-scan was found as secondary study, possibly because there were several CT-scans. Imagefilename:{image_filenames}')
        

    _, sitk_image, _ = read_dcm_series(directory_or_files=image_filenames, series_id=None,
                                                       return_sitk=True)

    logger.info(f'Processing {modality_name} - {series_description} data.')
    write_with_sitk(sitk_image,  image_fn)
    
directory = r'E:\Jasper\HNSCC\Data_new\HNCDL_461\1.2.246.352.221.48454786286470590274705135732204667779_0301_000180_1634381772038e.dcm'
print(pathlib.Path(directory))
directoryforward = "E:/Jasper/HNSCC/Data_new/HNCDL_461/1.2.246.352.221.48454786286470590274705135732204667779_0301_000180_1634381772038e.dcm"
print(pathlib.Path(directoryforward))
directorydoubleback = "E:\\Jasper\\HNSCC\\Data_new\\HNCDL_461\\1.2.246.352.221.48454786286470590274705135732204667779_0301_000180_1634381772038e.dcm"
print(pathlib.Path(directorydoubleback))
print(pathlib.Path(directorydoubleback).is_file())

print(ast.literal_eval(f"{[directory, directoryforward, directorydoubleback]}"))


def highlight_rows(row,list_flagged):
    """ flags patients with error codes.

    :param row: row of the flagged patient
    :param list_flagged: list of flagged patients. 

    :returns: formatting options
    """
    if row.loc["PatientID"] in list(zip(*list_flagged))[0]:
        if row.loc["Flag"] == "No series selected":
            color = "red"
        elif row.loc["Flag"] == "Missing secondary study. Check whether primary study is optimal":
            color = "orange"
        elif row.loc["Flag"] == "Missing attribute":
            color = "yellow"
        else:
            color = "white"
    else:
        color = "white"
    return ["background-color: {}".format(color) for r in row]





