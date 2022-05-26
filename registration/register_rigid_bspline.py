
#%%
import matplotlib.pyplot as plt
import SimpleITK as sitk
import numpy as np
import os
import math
from scipy import signal
import shutil
import tqdm
import argparse
import pathlib

def parse_args(sourcedir, startpatient, endpatient):
    """Parse input arguments"""
    parser = argparse.ArgumentParser(description='Parse dicom folder and write to nrrd.')

    parser.add_argument( 
        '--source_dir',
        default = pathlib.Path(sourcedir),
        type=pathlib.Path,
        help='root to nifti-files',
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
    
    return parser.parse_args()

def rigidParameterMap():
    parameterMapRigid = sitk.GetDefaultParameterMap('rigid')
    
    parameterMapRigid['CheckNumberOfSamples']= ['false']
    parameterMapRigid['FixedImageDimension'] = ['3']
    parameterMapRigid['MovingImageDimension'] = ['3']
    parameterMapRigid['FixedInternalImagePixelType'] = ['float']
    parameterMapRigid['MovingInternalImagePixelType'] = ['float']
    
    parameterMapRigid['AutomaticScalesEstimation']= ['false']
    parameterMapRigid['AutomaticTransformInitialization']= ['true']
    parameterMapRigid['AutomaticTransformInitializationMethod']= ['GeometricalCenter']
    parameterMapRigid['DefaultPixelValue']= ['0.0']
    parameterMapRigid['FinalGridSpacingInVoxels']= ['10']
    parameterMapRigid['FixedImagePyramid']= ['FixedSmoothingImagePyramid']
    parameterMapRigid['HowToCombineTransforms']= ['Compose']
    parameterMapRigid['ImageSampler']= ['Random']
    parameterMapRigid['Interpolator']= ['BSplineInterpolator']
    parameterMapRigid['MaximumNumberOfIterations']= ['1024']
    parameterMapRigid['Metric']= ['AdvancedMattesMutualInformation']
    parameterMapRigid['MovingImagePyramid']= ['MovingSmoothingImagePyramid']
    parameterMapRigid['NumberOfResolutions']= ['3']
    parameterMapRigid['ImagePyramidSchedule']= ['4','4','2','2','1','1']
    parameterMapRigid['NumberOfSpatialSamples']=['1024']
    parameterMapRigid['Optimizer']= ['AdaptiveStochasticGradientDescent']
    parameterMapRigid['Registration']= ['MultiResolutionRegistration']
    parameterMapRigid['ResampleInterpolator']= ['FinalBSplineInterpolator']
    parameterMapRigid['Resampler']= ['DefaultResampler']
    parameterMapRigid['ResultImageFormat']= ['nii']
    parameterMapRigid['ResultImagePixelType']= ['unsigned short']
    # parameterMapRigid['Transform']= ['AffineTransform']
    parameterMapRigid['UseDirectionCosines']= ['true']
    parameterMapRigid['WriteResultImage']= ['true']    
    return parameterMapRigid

def BsplineParameterMap():
    parametermapBspline = sitk.GetDefaultParameterMap('bspline')
    parametermapBspline['CheckNumberOfSamples']= ['false']
    parametermapBspline['FixedImageDimension'] = ['3']
    parametermapBspline['MovingImageDimension'] = ['3']
    parametermapBspline['FixedInternalImagePixelType'] = ['float']
    parametermapBspline['MovingInternalImagePixelType'] = ['float']
    parametermapBspline['AutomaticScalesEstimation']= ['false']
    parametermapBspline['DefaultPixelValue']= ['0.0']
    parametermapBspline['FinalGridSpacingInPhysicalUnits']= ['12']
    parametermapBspline['FixedImagePyramid']= ['FixedSmoothingImagePyramid']
    parametermapBspline['HowToCombineTransforms']= ['Compose']
    parametermapBspline['ImageSampler']= ['Random']
    parametermapBspline['Interpolator']= ['BSplineInterpolator']
    parametermapBspline['MaximumNumberOfIterations']= ['512']
    parametermapBspline['Metric']= ["AdvancedMattesMutualInformation", "TransformRigidityPenalty"]
    parametermapBspline['Metric0Weight']=['2']
    parametermapBspline['Metric0Use']=['true']
    parametermapBspline['Metric1Weight']=['3']
    parametermapBspline['Metric1Use']=['true']
    parametermapBspline['MovingImagePyramid']= ['MovingSmoothingImagePyramid']
    # parametermapBspline['NumberOfResolutions']= ['3']
    # parametermapBspline['ImagePyramidSchedule']= ['4','4','4','2','2','2','1','1','1']
    # parametermapBspline['GridSpacingSchedule']=['4.0', '4.0', '4.0', '2.0', '2.0', '2.0', '1.0', '1.0', '1.0']
    parametermapBspline['NumberOfResolutions']= ['1']
    parametermapBspline['ImagePyramidSchedule']= ['1','1','1']
    parametermapBspline['GridSpacingSchedule']=['1.0', '1.0', '1.0']
    parametermapBspline['Optimizer']= ['AdaptiveStochasticGradientDescent']
    parametermapBspline['Registration']= ['MultiMetricMultiResolutionRegistration']
    parametermapBspline['ResampleInterpolator']= ['FinalBSplineInterpolator']
    parametermapBspline['Resampler']= ['DefaultResampler']
    parametermapBspline['ResultImageFormat']= ['nii']
    parametermapBspline['ResultImagePixelType']= ['unsigned short']
    parametermapBspline['Transform']= ['BSplineTransform']
    parametermapBspline['UseDirectionCosines']= ['true']
    parametermapBspline['WriteResultImage']= ['true']
    return parametermapBspline

def BsplineCombineParameterMap():
    parametermapBspline = sitk.GetDefaultParameterMap('bspline')
    parametermapBspline['CheckNumberOfSamples']= ['false']
    parametermapBspline['FixedImageDimension'] = ['3']
    parametermapBspline['MovingImageDimension'] = ['3']
    parametermapBspline['FixedInternalImagePixelType'] = ['float']
    parametermapBspline['MovingInternalImagePixelType'] = ['float']
    parametermapBspline['AutomaticScalesEstimation']= ['false']
    parametermapBspline['DefaultPixelValue']= ['0.0']
    parametermapBspline['FinalGridSpacingInPhysicalUnits']= ['12']
    parametermapBspline['FixedImagePyramid']= ['FixedRecursiveImagePyramid']
    parametermapBspline['HowToCombineTransforms']= ['Compose']
    parametermapBspline['ImageSampler']= ['Random']
    parametermapBspline['Interpolator']= ['BSplineInterpolator', 'BSplineInterpolator', 'BSplineInterpolator']
    parametermapBspline['MaximumNumberOfIterations']= ['600']
    parametermapBspline['Metric']= ["AdvancedMattesMutualInformation", "AdvancedMattesMutualInformation", "TransformRigidityPenalty"]
    parametermapBspline['Metric0Weight']=['2']
    parametermapBspline['Metric0Use']=['true']
    parametermapBspline['Metric1Weight']=['2']
    parametermapBspline['Metric1Use']=['true']
    parametermapBspline['Metric2Weight']=['1']
    parametermapBspline['Metric2Use']=['true']
    parametermapBspline['MovingImagePyramid']= ['MovingRecursiveImagePyramid', 'MovingRecursiveImagePyramid', 'MovingRecursiveImagePyramid']
    parametermapBspline['NewSamplesEveryIteration']=['true']
    parametermapBspline['NumberOfHistogramBins']=['64']
    parametermapBspline['NumberOfResolutions']= ['1']
    parametermapBspline['NumberOfSpatialSamples']= ['5000']
    parametermapBspline['ImagePyramidSchedule']= ['1','1','1']
    parametermapBspline['GridSpacingSchedule']=['4.0', '2.0', '1.0']
    parametermapBspline['Optimizer']= ['AdaptiveStochasticGradientDescent']
    parametermapBspline['Registration']= ['MultiMetricMultiResolutionRegistration']
    parametermapBspline['ResampleInterpolator']= ['FinalBSplineInterpolator']
    parametermapBspline['Resampler']= ['DefaultResampler']
    parametermapBspline['ResultImageFormat']= ['nii']
    parametermapBspline['ResultImagePixelType']= ['unsigned short']
    parametermapBspline['Transform']= ['BSplineTransform']
    parametermapBspline['UseDirectionCosines']= ['false']
    parametermapBspline['WriteResultImage']= ['true']
    return parametermapBspline

def main(args):
    erode_filter = sitk.BinaryErodeImageFilter()
    erode_filter.SetKernelType(sitk.sitkBall)
    erode_filter.SetKernelRadius( 10 )
    erode_filter.SetForegroundValue(1)
    dilate_filter = sitk.BinaryDilateImageFilter()
    dilate_filter.SetKernelType(sitk.sitkBall)
    dilate_filter.SetKernelRadius( 5 )
    dilate_filter.SetForegroundValue(1)

    holefill_filter  = sitk.BinaryFillholeImageFilter()
    holefill_filter.SetForegroundValue(1)

    basepath = args.source_dir

    parameterMapRigid= rigidParameterMap()
    parameterMapBSpline = BsplineParameterMap()
    parameterMapBSplineCombine = BsplineCombineParameterMap()

    for patient_num in tqdm(range(args.startfile, args.endfile)):
        basefolder = os.path.join(basepath, "HNCDL_{:03d}".format(patient_num))
        try:
            fixedfilename = os.path.join(basefolder, 'ct.nii.gz')
            fixed = sitk.ReadImage(fixedfilename)
            movingfilename = os.path.join(basefolder, 'mr_t1w_mdixona.nii.gz')
            moving = sitk.ReadImage(movingfilename)
            movingfilename2 = os.path.join(basefolder, 'mr_t2w.nii.gz')
            moving2 = sitk.ReadImage(movingfilename2)
        except:
            print("Missing file",patient_num)
            continue

        
        
        
        for i in range(1,99):
            outfolder = os.path.join(basefolder,'Registration_'+str(i).zfill(2))
            if not os.path.isdir(outfolder):
                os.makedirs(outfolder) 
                break
                
        regfolder = outfolder  
        
        sitk.WriteParameterFile(parameterMapRigid, os.path.join(regfolder, 'rigid_params.txt'))
        
        shutil.copy(__file__, os.path.join(regfolder, os.path.basename(__file__)))  # dst can be a folder; use shutil.copy2() to preserve timestamp
        sitk.WriteImage(fixed, os.path.join(outfolder, 'fixed.nii'))
        sitk.WriteImage(moving, os.path.join(outfolder, 'moving.nii'))
        sitk.WriteImage(moving2, os.path.join(outfolder, 'moving2.nii'))
        
        
        elastix = sitk.ElastixImageFilter()
        elastix.SetFixedImage(fixed)
        
        elastix.SetMovingImage(moving)
        elastix.LogToFileOn()
        elastix.SetOutputDirectory(regfolder)
        
        
        elastix.SetParameterMap(parameterMapRigid)
        
        resultImage = elastix.Execute()
        mask = resultImage>0
        resultImage = resultImage*sitk.Cast(mask, resultImage.GetPixelID()) 
        resultImage = sitk.Cast(resultImage,sitk.sitkUInt16)
        sitk.WriteImage(resultImage, os.path.join(outfolder, 'T1_rigid_reg.nii'))
        
        Transform = os.path.join(outfolder, 'TransformParameters.0.txt')
        rigidTransform = os.path.join(outfolder, 'TransformRigid.txt')
        if os.path.exists(rigidTransform):
            os.remove(rigidTransform)
        if os.path.exists(Transform):
            os.rename(Transform, rigidTransform)#rename
        
        fixed_mask = sitk.Cast(fixed>-200,sitk.sitkUInt8)
        fixed_mask = holefill_filter.Execute(fixed_mask)
        array = sitk.GetArrayFromImage(moving)
        threshold = np.average(array[array > 0])/2
        moving_mask = sitk.Cast(resultImage>threshold,sitk.sitkUInt8)
        moving_mask = holefill_filter.Execute(moving_mask)
        # sitk.WriteImage(fixed_mask, os.path.join(outfolder, 'fixed_mask.nii'))
        fixed_mask = fixed_mask + moving_mask
        fixed_mask = sitk.Cast(fixed_mask>1,sitk.sitkUInt8)
        dilate_filter.SetKernelRadius( 15 )
        fixed_mask = dilate_filter.Execute(fixed_mask)
        erode_filter.SetKernelRadius(12)
        fixed_mask = erode_filter.Execute(fixed_mask)
        sitk.WriteImage(fixed_mask, os.path.join(outfolder, 'fixed_mask.nii'))
        
        del elastix
        
        elastix = sitk.ElastixImageFilter()
        elastix.SetFixedImage(fixed)
        elastix.SetMovingImage(moving)
        elastix.AddMovingImage(moving2)
        elastix.AddMovingImage(moving)
        elastix.SetInitialTransformParameterFileName(rigidTransform)
        elastix.SetFixedMask(fixed_mask)
        elastix.LogToFileOn()
        elastix.SetOutputDirectory(regfolder)
        elastix.SetParameterMap(parameterMapRigid)
        elastix.AddParameterMap(parameterMapBSplineCombine)
        sitk.WriteParameterFile(parameterMapBSplineCombine, os.path.join(regfolder, 'bspline_params.txt'))
        resultImage = elastix.Execute()
        mask = resultImage>0
        resultImage = resultImage*sitk.Cast(mask, resultImage.GetPixelID()) 
        resultImage = sitk.Cast(resultImage,sitk.sitkUInt16)
        sitk.WriteImage(resultImage, os.path.join(outfolder, 'T1_bspline_reg.nii'))
        
        del elastix
        
        Transform = os.path.join(outfolder, 'TransformParameters.0.txt')
        rigidTransform2 = os.path.join(outfolder, 'TransformRigid2.txt')
        
        if os.path.exists(Transform):
            if os.path.exists(rigidTransform2):
                os.remove(rigidTransform2)
            os.rename(Transform, rigidTransform2)#rename
            
        Transform = os.path.join(outfolder, 'TransformParameters.1.txt')
        BsplineTransform = os.path.join(outfolder, 'TransformBspline.txt')
        
        if os.path.exists(Transform):
            if os.path.exists(BsplineTransform):
                os.remove(BsplineTransform)
            os.rename(Transform, BsplineTransform)#rename
            
            
        transformix=sitk.TransformixImageFilter()
        transformix.SetMovingImage(moving2)
        parameter0=sitk.ReadParameterFile(rigidTransform)
        parameter1=sitk.ReadParameterFile(rigidTransform2)
        parameter2=sitk.ReadParameterFile(BsplineTransform)
        
        transformix.SetTransformParameterMap(parameter0)
        transformix.Execute()
        resultImage = transformix.GetResultImage()
        mask = resultImage>0
        resultImage = resultImage*sitk.Cast(mask, resultImage.GetPixelID()) 
        resultImage = sitk.Cast(resultImage,sitk.sitkUInt16)
        sitk.WriteImage(resultImage, os.path.join(outfolder, 'T2_rigid_reg.nii'))
        transformix.AddTransformParameterMap(parameter1)
        transformix.Execute()
        resultImage = transformix.GetResultImage()
        mask = resultImage>0
        resultImage = resultImage*sitk.Cast(mask, resultImage.GetPixelID()) 
        resultImage = sitk.Cast(resultImage,sitk.sitkUInt16)
        sitk.WriteImage(resultImage, os.path.join(outfolder, 'T2_rigid_reg2.nii'))
        transformix.AddTransformParameterMap(parameter2)
        transformix.Execute()
        resultImage = transformix.GetResultImage()
        mask = resultImage>0
        resultImage = resultImage*sitk.Cast(mask, resultImage.GetPixelID()) 
        resultImage = sitk.Cast(resultImage,sitk.sitkUInt16)
        sitk.WriteImage(resultImage, os.path.join(outfolder, 'T2_bspline_reg.nii'))
        
        del transformix
        
        transformix2=sitk.TransformixImageFilter()
        transformix2.SetMovingImage(moving)
        transformix2.SetTransformParameterMap(parameter0)
        transformix2.AddTransformParameterMap(parameter1)
        transformix2.Execute()
        resultImage = transformix2.GetResultImage()
        mask = resultImage>0
        resultImage = resultImage*sitk.Cast(mask, resultImage.GetPixelID()) 
        resultImage = sitk.Cast(resultImage,sitk.sitkUInt16)
        sitk.WriteImage(resultImage, os.path.join(outfolder, 'T1_rigid_reg2.nii'))
        del transformix2
        
        



        
    


