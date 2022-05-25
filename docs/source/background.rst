
Background
**********

3D-images - Busch
==========

* Dicom format 
DICOM is an acronym for Digital Imaging and Commutations in Medicine. 
It is first of all used to store digital images in 2-d format. 
Because a body part cannot be represented in 2-d format, you often 
need more than hundreds of DICOM files to represent a body part. 
In addition to that DICOM files can also stole medical information. 
Thus DICOM-files insures that all the data for each patient stays with
each patient.

* nifti format - input neural network 
Instead of having a lot of 2-d slices to represent a body part, 
we want to represented it as a 3-d slice. This makes it even easier
 to keep all the data together, since we do not have hundreds of files 
 we should manage. In addition to that the nifti-file does also contain 
 all of the medical information. This nifti-format is also the input type 
 for the neural network. 

* Voxels
In a 2-d image you have a grid that exists of pixels. A pixel center is 
defined by the (x,y) coordinates. Likewise, the size of a pickle is 
defined by the length of the pixel multiplied by the height of the pixel. 
On the other hand, a voxel is defined by the (x,y,z) coordinates, and exist
in 3-d images. Likewise, the size of pixel here the pixels length, height 
and width multiplied together. 


Registration 
============

* Rigid
* Deformable

Evaluation - Busch 
============
* Metrics 
When you have done a lot of preprocessing with the data, you want to make sure
that the data is as you expect. One possible way is to manually check all of
the data that has been processed. Often this is time consuming, and sometimes the human eye
is not as good at spotting irregularities as computers might be. Therefore, 
a 'metric' is often used. Metrics often gives one or two values as describes
how good or how accurate the data has been preprocessed. In our case the 
'accuracy' is how similar our CT and MR 3D-image is. We have chosen the
'MutualInformation' as our validation metric. This metric focuses on the
structure similarities and uses among other things voxel color values 
for this.

* Cropping - relevant in proportion to Metrics
Because 'mutual information' uses structural similarities and
voxel color values, we need to crop the image to all the air gets erased,
because air has the same picture color value and thus were result
in a lot of false accuracy. In addition to that we also require
the images to have the same size, since we can't compare 'something' with
'nothing'. Lastly, we also need all the slices in the 3D-image to be 
comparable, which means that the drawing architecture should be clean and without noise








