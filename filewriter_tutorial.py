# -*- coding: utf-8 -*-
"""
Created on Wed May 25 14:18:46 2022

@author: student
"""

import os
from dicom_conversion import convertorv3_filewriter_tutorial as filewriter

#Directories
cwd = os.getcwd()
sourcedir = os.path.join(os.path.dirname(cwd),"data","dicom")
targetdir = os.path.join(os.path.dirname(cwd),"data","nifti")
miscdir = os.path.join(os.path.dirname(cwd),"data","misc_output")


modalitylist = ["CT","PT","MR"]
ROIs = ["mandible", "paro", "gtv", "brain", "chiasm", "cochlea", "esopha", "larynx", "lens", "lips", "optic", "oral", "spinal", "submand", "thyroid"]

parsed_args = filewriter.parse_args(sourcedir,targetdir, miscdir, modalitylist, ROIs, False, False, False)
filewriter.main(parsed_args)