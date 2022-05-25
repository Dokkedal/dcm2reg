# -*- coding: utf-8 -*-
import os
from dicom_conversion import convertorv3_dictwriter_tutorial as dictwriter

#Directories
cwd = os.getcwd()
sourcedir = os.path.join(os.path.dirname(cwd),"data","dicom")
miscdir = os.path.join(os.path.dirname(cwd),"data","misc_output")

modalitylist = ["CT","PT","MR"]
ROIs = ["mandible", "paro", "gtv", "brain", "chiasm", "cochlea", "esopha", "larynx", "lens", "lips", "optic", "oral", "spinal", "submand", "thyroid"]

# startpatient, endpatient, sourcedir, targetdir, miscdir, modalitylist, ROIs, maxdelineationdelay, maxstudydelay
parsed_args = dictwriter.parse_args(0,10,sourcedir, miscdir, modalitylist, ROIs, 21, 7)
dictwriter.main(parsed_args)
