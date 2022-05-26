
Background
**********

3D-images
==========
..
    * Medical scans

In radiation therapy, medical body scans are an important tool which
doctors can use for planning dosage delivery. Several different kinds
of scans are used, including:

* *Computed Tomography* (CT) scans. These essentially take cross-sectional
slices (tomograms) and that can be used in computing a reconstruction of
the full 3D-image. CT-scans typically indicate air with a value of -1000,
water with 0, and bone with 400 or greater (measured in Hounsfield units).
* *Positron emission tomography* (PET/PT) scans. These utilise gamma rays to 
visualise injected radiotracers, which are essentially compounds that are 
radioactively decaying in such a way that the PT-scan can show the spatial 
journey of the compounds during a scan. Many different radiotracers exist, 
e.g. for metabolism and blood flow tracing, and the way in which a PT-scan 
visualises compounds depends on the choice of radiotracer and the chosen task.
* *Magnetic Resonance* (MR) scans. These use magnetic resonance to visualise
body tissue and other substances and come in two types: T1-MR and T2-MR,
which measure different kinds of magnetic resonance. They typically indicate
bone and air with values close to 0 and fat with higher values, while the
visualisation values of water, protein-rich fluids etc. depend on the type used.

.. 
    * Voxels

In general, medical scans consist of 3D-images, which differentiates them from 
regular 2D-images. 2D-images have grids that consist of pixels. A pixel is 
defined by the (x,y) coordinates of its centre along with a colour value. 
The size of a pixel is defined by the length of the pixel multiplied by the
height of the pixel. In the case of 3D-images, a voxel is defined by the (x,y,z)
coordinates of its centre along with a colour value. Likewise, the size 
of a voxel is defined by the voxel's length, height and depth multiplied together. 
The colour values of medical scans typically lie on a greyscale range based on
the type of scan, i.e. voxels that show air will have a value of -1000 in CT-scans
and a value of around 0 in MR-scans, as described above.

..
    * Dicom format 

DICOM is an acronym for Digital Imaging and Communications in Medicine. 
It is a file format that stores digital 2D-images. Since medical scans are 3D-images,
you often need hundreds of DICOM files to represent a single scan. Additionally, 
DICOM files can also store medical information. Thus DICOM-files insures that all 
the data for each patient stays with the respective patient.

* nifti format - input neural network 
Instead of having a lot of 2D-slices to represent a body part, 
we want to represented it as a 3D-slice. This makes it even easier
 to keep all the data together, since we do not have hundreds of files 
 we should manage. In addition to that the nifti-file does also contain 
 all of the medical information. This nifti-format is also the input type 
 for the neural network. 




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








