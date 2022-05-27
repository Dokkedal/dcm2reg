# -*- coding: utf-8 -*-
import os
from dicom_conversion import conversion_filewriter as filewriter

#Directories
cwd = os.getcwd()
targetdir = os.path.join(os.path.dirname(cwd),"data","nifti")
miscdir = os.path.join(os.path.dirname(cwd),"data","misc_output")

modalitylist = ["CT","PT","MR"]
ROIs = ["mandible", "paro", "gtv", "brain", "chiasm", "cochlea", "esopha", "larynx", "lens", "lips", "optic", "oral", "spinal", "submand", "thyroid"]

#targetdir, miscdir, modalitylist, ROIs, includered, includeorange, includeyellow
parsed_args = filewriter.parse_args(targetdir, miscdir, modalitylist, ROIs, False, False, False)
filewriter.main(parsed_args)