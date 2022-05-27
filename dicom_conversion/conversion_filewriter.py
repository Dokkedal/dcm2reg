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
          Represent the two steps in convertorv3_dictwriter and convertorv3_filewriter.
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
#from pandas.io.json import json_normalize

from .conversion_functions import wirte_primary_image_with_ROIs, write_secondary_images, read_dicts_from_excel
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

def parse_args(targetdir,miscdir, modalitylist, ROIs,includered,includeorange,includeyellow):
    """Parsing function that declares relevant variables for later use.
    
    :param targetdir: directory for output nifti files
    :param miscdir: directory for miscellanous output
    :param modalitylist: list of relevant modalities
    :param ROIs: list of relevant regions of interest
    :param includered: boolean variable which includes red flagged patients if True
    :param includeorange: boolean variable which includes orange flagged patients if True
    :param includeyellow: boolean variable which includes yellow flagged patients if True
    
    :returns: parsing arguments
    """
    parser = argparse.ArgumentParser(description='Parse dicom folder and write to nrrd.')

    parser.add_argument(
        '--target_dir',
        default = pathlib.Path(targetdir),
        type=pathlib.Path,
        help='root to target',
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
        '--include_red',
        default = includered,
        type = bool,
        help = 'Whether to include red flagged in conversion',
        #required = False
    )
    
    parser.add_argument(
        '--include_orange',
        default = includeorange,
        type = bool,
        help = 'Whether to include orange flagged in conversion',
        #required = False
    )
    
    parser.add_argument(
        '--include_yellow',
        default = includeyellow,
        type = bool,
        help = 'Whether to include yellow flagged in conversion',
        #required = False
    )
    
    
    # parser.add_argument(
    #     '--keep-structure',
    #     action='store_true',
    #     help='If set, the folder structure will be maintained.',
    # )

    return parser.parse_args()

def main(args):
    """produces converted nifti-files using an excel dictionary.

    :param args: arguement object from parse_args 

    :returns: nifti-files
    """
    args = args
    modality_list = args.modality_list
    ROIs = args.ROIs
    
    logger.debug("Attempting to read dictionary files from (filepath!).")
    selected_patient_dictionary = read_dicts_from_excel(os.path.join(args.misc_dir.__fspath__(), "seriesdict_post_selection.xlsx"),args.include_red,args.include_orange,args.include_yellow)
    logger.debug(f"The read dictionary is {selected_patient_dictionary}. Please verify that this is correct.")
        
    for series_instance_uid in selected_patient_dictionary:

        logger.info(f'Writing NOT REPORTED - ')         #'{series_instance_uid}.')
        series_dictionary = series_instance_uid

        # Read image_filenames from .txt-file.
        image_filenames_txt = series_dictionary["filenames"]
        with open(image_filenames_txt) as f:
            image_filenames = f.read().splitlines()
        
        patient_id = series_dictionary['PatientID']
        modality_name = series_dictionary['Modality']
        series_description = series_dictionary['SeriesDescription']
        root_dir = series_dictionary['source_dir']
        
        
        #print("hej igen", isinstance(image_filenames, str))
        
        # Reinterpreting image_filenames from str to list, i.e. "[..., ..., ...]" to [..., ..., ...]
        #image_filenames = ast.literal_eval(image_filenames)
        
        
        # --- Conversion of escaped backslashes to forward slash is unnecessary, 
        #     since read_dcm_series casts into type pathlib.Path anyway.
        #image_filenames = image_filenames.replace("\\\\", "/")

        
        #for img_index in range(len(image_filenames)):
        #    image_filenames[img_index] = image_filenames[img_index].replace("\\", "/")
        
        #print("image_filenames her", image_filenames)

        write_to_folder = args.target_dir / root_dir
        
        
        
        # series_dictionary["RTSTRUCT"] = list(map(lambda x: x.replace('/', '\\'), l))
        #series_dictionary["RTSTRUCT"] = series_dictionary["RTSTRUCT"](map(lambda x: x.replace('/', '\\'), series_dictionary["RTSTRUCT"]))
        #
        #print("look here")
        #print(series_dictionary)
        #json.dumps(series_dictionary, indent=3)
        
        #['E:\\Jasper\\HNSCC\\Data_new\\HNCDL_461\\1.2.246.352.221.48454786286470590274705135732204667779_0301_000001_1634381764032b.dcm'
        #['E:\\Jasper\\HNSCC\\Data_new\\HNCDL_461\\1.2.246.352.221.48454786286470590274705135732204667779_0301_000001_1634381764032b.dcm'
        
        if series_dictionary["bestrtstruct"]:
            
            rtstruct_filename = series_dictionary["bestrtstruct"]
            # Reinterpreting image_filenames from str to list
            #rtstruct = ast.literal_eval(rtstruct)
            #if len(rtstruct) > 1:
            #    logger.error(f'Can only handle one RTSTRUCT: {root_dir}.')
            #    continue
            #else:
            #rtstruct_filename = rtstruct[0]
            wirte_primary_image_with_ROIs(modality_name, series_description, image_filenames, rtstruct_filename, ROIs, write_to_folder)
            #series_dictionary["RTSTRUCT"] = "There is an RTSTRUCT" 
            #print("Look here again")
            #print(series_dictionary["RTSTRUCT"])
        else:
            write_secondary_images(modality_name, series_description, image_filenames, write_to_folder)
