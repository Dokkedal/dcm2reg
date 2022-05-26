# -*- coding: utf-8 -*-
import os
from registration import register_rigid_bspline as registration

#Directories
cwd = os.getcwd()
sourcedir = os.path.join(os.path.dirname(cwd),"data","nifti")
targetdir = os.path.join(os.path.dirname(cwd),"data","nifti_reg")

parsed_args = registration.parse_args(sourcedir,targetdir, 0, 10)
registration.main(parsed_args)