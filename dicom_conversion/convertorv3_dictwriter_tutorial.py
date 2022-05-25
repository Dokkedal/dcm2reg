"""
Convert dicom image modalities with ROI
The funcitons of this script is to use RTSTRUCT with SeriesInstanceUID to locate the
correponding primary image. And convert all image modalities sharing same StudyInstanceUID
with the primary image within a specific date gap (). 
Jintao Ren
jintaoren@onoclogy.au.dk
2022.01.06

"""

"""
Changes by datascience students spring 2022.
020522 -> split the processes into two steps: creating the dictionaries and writing the NIfTI-files.
          Represent the two steps in convertorv3_dictwriter and convertorv3_filewriter. Also, place
          helper functions in convertorv3_functions..
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

from convertorv3_functions import day_difference, construct_dict_patient, optimal_series, DFConverter, highlight_rows, get_ROIs

from image_readers import read_dcm_series

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


def parse_args(startpatient,endpatient,sourcedir, miscdir,modalitylist,ROIs,maxdelineationdelay,maxstudydelay):
    """Parse input arguments"""
    parser = argparse.ArgumentParser(description='Parse dicom folder and write to nrrd.')

    parser.add_argument( 
        '--source_dir',
        default = pathlib.Path(sourcedir),
        type=pathlib.Path,
        help='root to source',
        #required=False
    )

    # index of patient to start
    parser.add_argument( 
        '--startfile',
        default = startpatient,
        type=int,
        help='index of patient to start',
        #required=False
    )

    # index of patient to end
    parser.add_argument( 
        '--endfile',
        default = endpatient,
        type=int,
        help='index of patient to end',
        #required=False
    )
    
    # directory for miscellaneous output
    parser.add_argument(
        '--misc_dir',
        default = pathlib.Path(miscdir),
        type = pathlib.Path,
        help = 'directory for miscellaneous output',
        #required = False
    )
    
    # directory for miscellaneous output
    parser.add_argument(
        '--modality_list',
        default = modalitylist,
        type = list,
        help = 'list of modalities to consider',
        #required = False
    )
    
    # directory for miscellaneous output
    parser.add_argument(
        '--ROIs',
        default = ROIs,
        type = list,
        help = 'list of ROIs to consider',
        #required = False
    )
    
    parser.add_argument(
        '--max_delineation_delay',
        default = maxdelineationdelay,
        type = int,
        help = 'maximum difference in days from scanning to delineation',
        #required = False
    )
    
    parser.add_argument(
        '--max_study_delay',
        default = maxstudydelay,
        type = int,
        help = 'maximum difference in days between primary and secondary study',
        #required = False
    )

    # parser.add_argument(
    #     '--keep-structure',
    #     action='store_true',
    #     help='If set, the folder structure will be maintained.',
    # )

    return parser.parse_args()

def main(args):
    modality_list = args.modality_list
    ROIs = args.ROIs
    
    seriesdictprint_pre = []
    seriesdictprint_post = []
    #data_dictionary = construct_dict_study_instance(args.source_dir)
    list_flagged = []
    
    data_dictionary,list_flagged = construct_dict_patient(args.source_dir,args.startfile,args.endfile,list_flagged)
    
    
    for patient_id in data_dictionary:
        logger.info(f'New study instance: {patient_id} .')
        
        patient_dictionary = data_dictionary[patient_id]
        selected_patient_dictionary = {}

        primary_studies = []
        secondary_studies = []
        
        
        #print("Here is the patriendic",patient_dictionary["1.2.246.352.221.49907815476431648337560379478021877418"])
        
        for series_instance_uid in patient_dictionary:
            # search for the optimal series based on rules:
            # 1. The primary series should have RTSTRUCT + IMAGE(i.e. CT)
            # 2. RTSTRUCT should have the wanted ROI
            # 3. If multiple series comlpy rule 1&2, pick the one with the most sub-image modalites
            # 4. Sub-image should only be picked if the StudyDate is within a week from the primary image.
            ## create a output dictionary for all dcm filenames.
            
            
            
            logger.info(f'Processing {patient_id} - {series_instance_uid}.')
            series_dictionary = patient_dictionary[series_instance_uid]
            try:
                root_dir = series_dictionary['source_dir']
            except KeyError:
                logger.warning(f"No source directory found {series_instance_uid}")
                continue
            copypatientdict = series_dictionary.copy()
            #print("Here it is",copypatientdict)
            
            # pathlib.Path objects have been removed from the Excel-file for now. Can add later if desired.
            #copypatientdict.pop("filenames")
            #copypatientdict.pop("source_dir")
            # Reformat filepaths to a format which is JSON-serialisable, so that
            # they can be saved to Excel.
            for filename in copypatientdict["filenames"]:
                filename = filename.replace("/", "\\")
        
            copypatientdict["source_dir"] = copypatientdict["source_dir"].__fspath__()
            
            # Save the series instance UID to the series dictionary.
            copypatientdict["series_instance_uid"] = series_instance_uid
            
            # Initialise the name of the .txt-file which will save the filenames for this series.
            filenames_txt_file = f"{series_instance_uid}-filenames.txt"
            
            # Write filenames string to specified .txt-file.
            with open(os.path.join(args.misc_dir.__fspath__(), "filenames", filenames_txt_file), "w") as f:
                f.write('\n'.join(copypatientdict["filenames"]))
            
            # Overwrite filenames column entry to contain path to the .txt-file.
            copypatientdict["filenames"] = os.path.join(args.misc_dir.__fspath__(), "filenames", filenames_txt_file)
            
            seriesdictprint_pre.append(copypatientdict)
            
            if 'RTSTRUCT' in series_dictionary:
                if len(series_dictionary['ROIs']) > 1:
                    smallestdaydiff = -1
                    for rtstruct in series_dictionary['RTSTRUCT']:    
                        dcm_object = pydicom.read_file(str(rtstruct), stop_before_pixels=True)
                        structuredate = dcm_object.StructureSetDate
                       
                        diff = day_difference(series_dictionary["StudyDate"] , structuredate)
                        if diff < args.max_delineation_delay:    
                            if diff > smallestdaydiff:
                                smallestdaydiff = diff
                                structuretime = float(dcm_object.StructureSetTime)
                                bestrtstruct = rtstruct
                                bestROI = get_ROIs(dcm_object)
                            elif diff == smallestdaydiff:
                                if float(dcm_object.StructureSetTime) > structuretime:
                                    smallestdaydiff = diff
                                    structuretime = float(dcm_object.StructureSetTime)
                                    bestrtstruct = rtstruct 
                                    bestROI = get_ROIs(dcm_object)
                    if smallestdaydiff > -1:    
                       # primary_studies.append((series_instance_uid,series_dictionary['StudyDate'],bestrtstruct))
                        for ROI in ROIs:
                            if ROI.lower() in bestROI.lower():
                                primary_studies.append((series_instance_uid,series_dictionary['StudyDate'],bestrtstruct))
                    #logger.error(f'Can only handle one ROIs: {root_dir} - {series_instance_uid}.')
                    # ! TODO choose the best series from multiple series which have RTSTRUCT
                else:
                    for ROI in ROIs:
                        for roi_name in series_dictionary['ROIs']:
                            if ROI.lower() in roi_name.lower():
                                primary_studies.append((series_instance_uid,series_dictionary['StudyDate'],series_dictionary['RTSTRUCT'][0]))
            else: 
                if series_dictionary['Modality'] in modality_list:
                    secondary_studies.append((series_instance_uid,series_dictionary['StudyDate']))

        primary_studies = list(set(primary_studies))
        hasfoundsecondary = False
        if len(primary_studies) == 1:
            selected_patient_dictionary[primary_studies[0][0]] = patient_dictionary[primary_studies[0][0]]
            selected_patient_dictionary[primary_studies[0][0]]["bestrtstruct"] = primary_studies[0][2]
            for secondary_study in secondary_studies:
                # if the StudyDate is within a week between primary_studies[1] and secondary_study[1]
                # then select as part of selected_patient_dictionary.
                if day_difference(primary_studies[0][1], secondary_study[1]) < args.max_study_delay:
                    selected_patient_dictionary[secondary_study[0]] = patient_dictionary[secondary_study[0]]
                    hasfoundsecondary = True
                
        else:
            logger.error(f'Multiple primary study found, selecting the optimal one - {patient_id}.')

            selected_primary_study_series_uid,selected_best_rtstruct = optimal_series(primary_studies, secondary_studies, args.max_study_delay)
            if not selected_primary_study_series_uid:
                logger.error(f"No primary study found for patient: {patient_id}, skipping to next patient instead.")
                list_flagged.append((patient_id,"No series selected",3))
                continue
            selected_patient_dictionary[selected_primary_study_series_uid] = patient_dictionary[selected_primary_study_series_uid]
            selected_patient_dictionary[selected_primary_study_series_uid]["bestrtstruct"] = selected_best_rtstruct
            for secondary_study in secondary_studies:
                # if the StudyDate is within a week between primary_studies[1] and secondary_study[1]
                # then select as part of selected_patient_dictionary.
                if day_difference(selected_patient_dictionary[selected_primary_study_series_uid]["StudyDate"], secondary_study[1]) < args.max_study_delay:
                    selected_patient_dictionary[secondary_study[0]] = patient_dictionary[secondary_study[0]]
                    hasfoundsecondary = True
        
        # No secondary within 7 days
        if not hasfoundsecondary:
            list_flagged.append((patient_id,"Missing secondary study. Check whether primary study is optimal",2))
        # REMOVED FILE WRITER FROM HERE -----------------------------
        for series_instance_uid in selected_patient_dictionary:

            series_dictionary = selected_patient_dictionary[series_instance_uid]

            # Reformat filepaths to a format which is JSON-serialisable, so that
            # they can be saved to Excel (filenames will be saved to separate .txt-file.
            for filename in series_dictionary["filenames"]:
                filename = filename.replace("/", "\\")
        
            series_dictionary["source_dir"] = series_dictionary["source_dir"].__fspath__()
            if "RTSTRUCT" in series_dictionary:
                for rtstruct_filename in series_dictionary["RTSTRUCT"]:
                    rtstruct_filename = rtstruct_filename.replace("/", "\\")
                    
            # Save the series instance UID to the series dictionary.
            series_dictionary["series_instance_uid"] = series_instance_uid
            
            # Initialise the name of the .txt-file which contains the filenames for this series.
            filenames_txt_file = f"{series_instance_uid}-filenames.txt"
            
            # Overwrite filenames column entry to contain path to the .txt-file.
            series_dictionary["filenames"] = os.path.join(args.misc_dir.__fspath__(), "filenames", filenames_txt_file)
            
            #print("seriesdict here")
            #print(series_dictionary)
            seriesdictprint_post.append(series_dictionary)
    
    
    print("Here starts dictexport")
    #print(seriesdictprint)
    formatted_seriesdict_pre = json.dumps(seriesdictprint_pre, indent=3)
    formatted_seriesdict_post = json.dumps(seriesdictprint_post, indent=3)
    print(formatted_seriesdict_post)
    #with open('seriesdict.json', 'w') as f:
        #json.dump(formatted, f)
    
    # OLD JSON CONVERSION METHOD:
    #df_json = pd.read_json(formatted)
    
    # NEW JSON CONVERSION METHOD:
    dfConverterObject = DFConverter()
    df_flagged = pd.DataFrame(list_flagged, columns=["PatientID","Flag","Importance"])
    df_flagged = df_flagged.groupby("PatientID", group_keys = False ).apply(lambda x: x.loc[x.Importance.idxmax()])
    df_flagged.to_excel(os.path.join(args.misc_dir.__fspath__(), 'flagged_patients.xlsx'))
    
    df_json_pre = dfConverterObject.convertToDF(formatted_seriesdict_pre)
    df_json_pre = df_json_pre.join(df_flagged.set_index("PatientID"), on="PatientID")
    df_json_pre = df_json_pre.reset_index(drop = True)
    if list_flagged:     
        df_json_pre = df_json_pre.style.apply(highlight_rows,axis=1,list_flagged=list_flagged)
    df_json_pre.to_excel(os.path.join(args.misc_dir.__fspath__(), 'seriesdict_pre_selection.xlsx'))
    
    
    df_json_post = dfConverterObject.convertToDF(formatted_seriesdict_post)
    df_json_post = df_json_post.join(df_flagged.set_index("PatientID"), on="PatientID")
    df_json_post = df_json_post.reset_index(drop = True)
    if list_flagged:
        df_json_post = df_json_post.style.apply(highlight_rows,axis=1,list_flagged=list_flagged)
    df_json_post.to_excel(os.path.join(args.misc_dir.__fspath__(), 'seriesdict_post_selection.xlsx'))
    

    logger.debug(f"Series dictionaries pre- and post-selection have been written. Please check the files (at {args.misc_dir}) before running the filewriter script.")
