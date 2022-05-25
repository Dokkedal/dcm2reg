import SimpleITK as sitk
import numpy as np
import os
import argparse
import pathlib
from tqdm import tqdm
import time
import shutil
import os
import pandas as pd
from openpyxl.styles import PatternFill
from openpyxl.styles.differential import DifferentialStyle
from openpyxl.formatting.rule import Rule
from openpyxl import Workbook
from openpyxl import load_workbook

#function to resample an image after applying a shift in one or more directions (make sure you apply this to the original before cropping)
def resample(image, tx=0.0, ty=0.0, tz=0.0, def_value=0.0):
    # Output image Origin, Spacing, Size, Direction are taken from the reference
    # image in this call to Resample
    translation = sitk.TranslationTransform(3)
    translation.SetOffset((tx, ty, tz))
    reference_image = image
    interpolator = sitk.sitkLinear
    default_value = def_value
    return sitk.Resample(image, reference_image, translation,
                         interpolator, default_value)
						 
#function to calculate the mutual information between 2 images
def calcMI(fixed, moving):
    registration_method = sitk.ImageRegistrationMethod()
    registration_method.SetMetricAsMattesMutualInformation()
    return registration_method.MetricEvaluate(sitk.Cast(fixed, sitk.sitkFloat32),sitk.Cast(moving, sitk.sitkFloat32))

#function to automatically find the cropbox for an MR image (assuming that the background value is 0). It finds all the voxels
#with a value of 1 or above.
def getCropParameters(moving, marginsize=0):
    label_shape_filter = sitk.LabelShapeStatisticsImageFilter()
    label_shape_filter.Execute(moving)
    #this will give us a bounding box with [indexX, indexY, indexZ, sizeX, sizeY, sizeZ)
    bb = label_shape_filter.GetBoundingBox(1)

    # if you want to remove some additional area to be sure the corrupt parts are out add a crop margin
    margin = marginsize
    crop = np.arange(6)
    crop[0] = bb[0]+margin
    crop[1] = bb[0]+margin+bb[3]-2*margin
    crop[2] = bb[1]+margin
    crop[3] = bb[1]+margin+bb[4]-2*margin
    crop[4] = bb[2]+margin
    crop[5] = bb[2]+margin+bb[5]-2*margin
    #return values are thus [xmin, xmax, ymin, ymax, zmin, zmax]
    return crop

#now first find the region to crop

# Deliberately bad mr image
def badimage(fixedimg,image,direction,pixels):
    
    if direction == "right":
        badmrimage = resample(image,pixels)
    elif direction == "left":
        badmrimage = resample(image,-pixels)
    elif direction == "up":
        badmrimage = resample(image,0,pixels)
    elif direction =="down":
        badmrimage = resample(image,0,-pixels)
    elif direction == "forward":
        badmrimage = resample(image,0,0,pixels)
    elif direction == "backwards":
        badmrimage = resample(image,0,0,-pixels)
    else:
        raise ValueError("Invalid direction. Type one of following: right, left, up, down, forward, backwards")
        
    cropmrbad = getCropParameters(badmrimage, 3)
    croppedmovingmrbad = badmrimage[cropmrbad[0]:cropmrbad[1], cropmrbad[2]:cropmrbad[3], cropmrbad[4]:cropmrbad[5]]
    badmrcalc = calcMI(fixedimg, croppedmovingmrbad)
    return badmrcalc
    

def highlight_rows_eval(row,list_flagged):
    if row.loc["PatientNum"] in list_flagged:
        color = "red"
    else:
        color = "white"
    return ["background-color: {}".format(color) for r in row]

def parse_args(startpatient,endpatient,sourcedir,miscdir, margin, flaggingthreshold):
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
        '--margin',
        default = margin,
        type = int,
        help = 'margin to crop further than zero-columns',
        #required = False
    )
    
    # directory for miscellaneous output
    parser.add_argument(
        '--flagging_threshold',
        default = flaggingthreshold,
        type = float,
        help = 'metric threshold to use in flagging',
        #required = False
    )

    # parser.add_argument(
    #     '--keep-structure',
    #     action='store_true',
    #     help='If set, the folder structure will be maintained.',
    # )

    return parser.parse_args()

def main(args):   
    #folder_path = "E:/Jasper/nnUNet/nnUNet_raw_data/Task700_HNCDL"
    #folder_pathrig = "E:/Jasper/HNSCC/nifti_reg"
    folder_pathrig = args.source_dir
    
    registration_method = sitk.ImageRegistrationMethod()
    registration_method.SetMetricAsMattesMutualInformation()
    
    datalist = []
    flagged = []
    #rownm = 1
    highlighted = []
    for patient_num in tqdm(range(args.startfile, args.endfile)):
        #label = "HNCDL_{:04d}.nii.gz".format(patient_num)
        try:
            ct = "HNCDL_{:03d}_fixed.nii.gz".format(patient_num)
            mr1 = "HNCDL_{:03d}_T1_bspline_reg.nii.gz".format(patient_num)
            mr2 = "HNCDL_{:03d}_T2_bspline_reg.nii.gz".format(patient_num)
            mr1rig = "HNCDL_{:03d}_T1_rigid_reg.nii.gz".format(patient_num)
            mr2rig = "HNCDL_{:03d}_T2_rigid_reg.nii.gz".format(patient_num)
            #print("Here it is2",mr1rig)
        #try:
            if True:
                ctimage = sitk.ReadImage(folder_pathrig + "/" + ct)
                mr1image = sitk.ReadImage(folder_pathrig + "/" + mr1)
                mr2image = sitk.ReadImage(folder_pathrig + "/" + mr2)
                mr1imagerig = sitk.ReadImage(folder_pathrig + "/" + mr1rig)  
                mr2imagerig = sitk.ReadImage(folder_pathrig + "/" + mr2rig)
        except:
            print("Missing file",patient_num)
            continue
    
        #ctimage = sitk.Clamp(ctimage, lowerbound=2, upperbound=3)
        
        cropmr1 = getCropParameters(mr1image, args.margin)
        croppedmovingmr1 = mr1image[cropmr1[0]:cropmr1[1], cropmr1[2]:cropmr1[3], cropmr1[4]:cropmr1[5]]
        croppedfixedct = ctimage[cropmr1[0]:cropmr1[1], cropmr1[2]:cropmr1[3], cropmr1[4]:cropmr1[5]]
        
        cropmr2 = getCropParameters(mr2image, args.margin)
        croppedmovingmr2 = mr2image[cropmr2[0]:cropmr2[1], cropmr2[2]:cropmr2[3], cropmr2[4]:cropmr2[5]]
        
        cropmr1rig = getCropParameters(mr1imagerig, args.margin)
        croppedmovingmr1rig = mr1imagerig[cropmr1rig[0]:cropmr1rig[1], cropmr1rig[2]:cropmr1rig[3], cropmr1rig[4]:cropmr1rig[5]]
        
        cropmr2rig = getCropParameters(mr2imagerig, args.margin)
        croppedmovingmr2rig = mr2imagerig[cropmr2rig[0]:cropmr2rig[1], cropmr2rig[2]:cropmr2rig[3], cropmr2rig[4]:cropmr2rig[5]]
        
        #mr1array_new = mr1array[3:-3, 225:-222, 175:-175]
        #mr2array_new = mr2array[3:-3, 225:-222, 175:-175]
        #ctarray_new = ctarray[3:-3, 225:-222, 175:-175]
        #mr1array_newrig = mr1arrayrig[3:-3, 225:-222, 175:-175]
        #mr2array_newrig = mr2arrayrig[3:-3, 225:-222, 175:-175]
        
        #print(mr1array_new.dtype,ctarray_new.dtype)
        #finalmr1 = sitk.GetImageFromArray(mr1array_new.astype(np.float32))
        #finalmr2 = sitk.GetImageFromArray(mr2array_new.astype(np.float32))
        #finalct = sitk.GetImageFromArray(ctarray_new.astype(np.float32))
        #finalmr1rig = sitk.GetImageFromArray(mr1array_newrig.astype(np.float32))
        #finalmr2rig = sitk.GetImageFromArray(mr2array_newrig.astype(np.float32))
        
        mr1calc = calcMI(croppedfixedct, croppedmovingmr1)
        mr2calc = calcMI(croppedfixedct, croppedmovingmr2)
        
        mr1calcrig = calcMI(croppedfixedct, croppedmovingmr1rig)
        mr2calcrig = calcMI(croppedfixedct, croppedmovingmr2rig)
        
        
        
        #evalmr1 = registration_method.MetricEvaluate(finalct,finalmr1)
        #evalmr2 = registration_method.MetricEvaluate(finalct,finalmr2)
        #evalmr1rig = registration_method.MetricEvaluate(finalct,finalmr1rig)
        #evalmr2rig = registration_method.MetricEvaluate(finalct,finalmr2rig)
        #print(patient_num,evalmr1,evalmr2)
        #badmr1calcright = badimage(croppedfixedct,croppedmovingmr1,"right",2)
        #badmr1calcleft = badimage(croppedfixedct,croppedmovingmr1,"left",2)
        #badmr1calcup = badimage(croppedfixedct,croppedmovingmr1,"up",2)
        #badmr1calcdown = badimage(croppedfixedct,croppedmovingmr1,"down",2)
        #badmr1calcforward = badimage(croppedfixedct,croppedmovingmr1,"forward",2)
        #badmr1calcbackwards = badimage(croppedfixedct,croppedmovingmr1,"backwards",2)
        #if mr1calc > badmr1calcforward:
        #    diff = 0
        #else:
        #    diff = 1
        
        
        #patientrow = [patient_num,mr1calc,mr2calc,mr1calcrig,mr2calcrig, badmr1calcright,badmr1calcleft, badmr1calcup, badmr1calcdown, badmr1calcforward, badmr1calcbackwards ]
        best = min(mr1calc,mr2calc, mr1calcrig, mr2calcrig)
        patientrow = [patient_num,mr1calc,mr2calc, mr1calcrig, mr2calcrig, best,None]
       
        if abs(best) < args.flagging_threshold:
            flagged.append(patient_num)
       #     highlighted.append("background-color: {red}")
       # else:
       #     highlighted.append("background-color: {white}")
    
        datalist.append(patientrow)
    
    datalist[0][6] = len(flagged)
    #print(flagged)
    df = pd.DataFrame(datalist)
    #df.columns=["PatientNum","DeMR1","DeMR2","RiMR1","RiMR2", "BadDeMR1right","BadDeMR1left","BadDeMR1up","BadDeMR1down","BadDeMR1forward","BadDeMR1backwards"]#,"DeMR2","RiMR1","RiMR2"]
    df.columns=["PatientNum","DeMR1","DeMR2", "RiMR1", "RiMR2", "Best", "Flagged"]#,"DeMR2","RiMR1","RiMR2"]
    writer = pd.ExcelWriter(os.path.join(args.misc_dir, 'evaluations.xlsx'))
    # write dataframe to excel
    df.to_excel(writer)
    writer.save()
    df = df.style.apply(highlight_rows_eval,axis=1,list_flagged=flagged)
    df.to_excel(os.path.join(args.misc_dir, 'flagged_evaluations.xlsx'))


    #sitk.WriteImage(finalmr1,r"E:\Jasper\nnUNet\nnUNet_raw_data\Task700_HNCDL\crop_img\crop_output\HNCDL_{:04d}_0001_Crop.nii.gz".format(patient_num))
    #sitk.WriteImage(finalmr2,r"E:\Jasper\nnUNet\nnUNet_raw_data\Task700_HNCDL\crop_img\crop_output\HNCDL_{:04d}_0002_Crop.nii.gz".format(patient_num))
    #sitk.WriteImage(finalct,r"E:\Jasper\nnUNet\nnUNet_raw_data\Task700_HNCDL\crop_img\crop_output\HNCDL_{:04d}_0000_Crop.nii.gz".format(patient_num))
    #shutil.copy(folder_path + "/" + label,r"E:\Jasper\nnUNet\nnUNet_raw_data\Task700_HNCDL\crop_img\crop_output")
    #os.rename(r"E:\Jasper\nnUNet\nnUNet_raw_data\Task700_HNCDL\crop_img\crop_output" + "/" + label, r"E:\Jasper\nnUNet\nnUNet_raw_data\Task700_HNCDL\crop_img\crop_output" + "/" + "HNCDL_{:04d}_Crop.nii.gz".format(patient_num))
    
    
    # Testing for where to crop
    #concat_img = np.concatenate((np.rollaxis(mr1array_new[:, :, -175:-176:-1],1)), axis=1)
    #imgaug.imshow(concat_img)
    #if patient_num == 364:
     #   break
    
    #Use to see before and after a slice.
    #time.sleep(0.25)
    #if patient_num == 211:
     #   concat_img = np.concatenate((np.rollaxis(mr1array_new[:, -220:-235:-2, :],1)), axis=0)
      #  imgaug.imshow(concat_img)
       # break
        









   # ctarray = ctarray[3:-2, :, :]
   # mr1array = mr1array[3:-2, :, :]
   # mr2array = mr2array[3:-2, :, :]

   # ctarray = sitk.GetImageFromArray(ctarray)
    
    
    
    
    
    
    
    
    # sitk.Clamp(ctarray)
    
    # print("ct shape", ctarray.shape)
    # print("mr1 shape", mr1array.shape)
    # print("mr2 shape", mr2array.shape)

    # continue

    # croplow = -1

    # crophigh = -1

    # found = False

    # for j in range(0, ctarray.shape[0]):

    #     # ct_sum = np.sum(ctarray[j, :, :])
    #     # mr1_sum = np.sum(mr1array[j, :, :])
    #     # mr2_sum = np.sum(mr2array[j, :, :])

    #     # if j == 3:  # ctarray.shape[0]:
    #     #     concat_img = np.concatenate((mr1array[j, :, :], mr2array[j, :, :]), axis=1)
    #     #     imgaug.imshow(concat_img)

    #     # print(ct_sum, mr1_sum, mr2_sum)

    #     if (ct_sum == 0) or (mr1_sum == 0) or (mr2_sum == 0):
    #         print("found empty slice")
    #         if not (found):
    #             croplow = j
    #         else:
    #             crophigh = j
    #             break

    #     else:
    #         found = True

    #     # print(patient_num, croplow, crophigh)

    # if (croplow != -1) or (crophigh != -1):

    #     print(patient_num, ctarray.shape, mr1array.shape, mr2array.shape)
    #     ctarray = ctarray[croplow + 1 : crophigh, :, :]
    #     mr1array = mr1array[croplow + 1 : crophigh, :, :]
    #     mr2array = mr2array[croplow + 1 : crophigh, :, :]
    #     print(patient_num, ctarray.shape, mr1array.shape, mr2array.shape)
