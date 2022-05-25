# -*- coding: utf-8 -*-
"""
Created on Wed May 25 14:41:13 2022

@author: student
"""


import os
from evaluation import evaluation

#Directories
cwd = os.getcwd()
sourcedir = os.path.join(os.path.dirname(cwd),"data","nifti_reg")
miscdir = os.path.join(os.path.dirname(cwd),"data","misc_output")

#startpatient,endpatient,sourcedir,miscdir, margin, flaggingthreshold
parsed_args = evaluation.parse_args(1,10,sourcedir,miscdir,3,0.5)
evaluation.main(parsed_args)
