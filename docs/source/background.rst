
.. _background:
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
    * DICOM format 

All three types of medical scans along with medical information are 
stored in the so-called DICOM-format from the beginning. 
DICOM is an acronym for Digital Imaging and Communications in Medicine. 
It is a file format that stores digital 2D-images. Since medical scans are 3D-images,
you often need hundreds of DICOM files to represent a single scan. Additionally, 
DICOM-files can also store medical information, e.g. descriptions of the scans.
Finally, DICOM-files are even able to store *delineations*, which are essentially
medical hand-drawn outlines of where organs and tumors are located. These delineations
are crucial to the planning of the medical treatment, and it is thus the main goal
of an ultimate deep learning model to learn to construct these delineations.

Thus, DICOM-files ensure that all the data for each patient stays with the 
respective patient. However, in order to make them easier to handle for both doctors
and an eventual deep learning model, they need to be converted into a niftier format.

..
    * NIfTI format - input neural network 

Instead of having a lot of 2D-slices to represent a body part, 
we want to represent it as a 3D-volume. This is exactly what the Neuroimaging
Informatics Technology Initiative (NIfTI) file format accomplishes. This makes
it easier to keep all the data together, since there are no longer
hundreds of files to manage. In addition to that the NIfTI-file also contains 
all of the medical information. These NIfTI-files can also be used as input
for a deep learning model. In fact, the deep learning framework known as nnU-Net,
which is commonly used to automatically tune hyperparameters and train the network
in medical image tasks, only accepts NIfTI-formatted 3D-scans, making the format
significantly more advantageous than the DICOM-format.

Registration 
============

..
    * Rigid

When only one type of scan is used for a deep learning model, simply converting e.g. 
the CT-scan to NIfTI is sufficient preprocessing. However, when introducing several
types of scans simultaneously, one must ensure the scans all contain the exact same
organs in the exact same areas. E.g. when using both CT-scans and MR-scans as input
to the neural network, the MR-scan must be manipulated so that e.g. the mandible is
located across the exact same voxels as in the CT-scan. It is typically easier to
manipulate the MR-scan, since any delineations are typically created based on the
CT-scan and would thus also need to be manipulated.

To ensure the above equivalence, a procedure known as *registration* must be performed,
along with cropping the images in case one scan covers more of the body than the other.
Registration is done in two types, whereof the first is called *rigid registration*.
This essentially amounts to rotating and translating the entire MR-scan to fit the CT-scan
as well as possible. It can occasionally be difficult to perform sufficient registration
using only the rigid method, e.g. if the patient's jaw was opened a bit more during the
MR-scan than in the CT-scan.

..
    * Deformable

The other type of registration, *deformable registration*, solves exactly this problem. 
In deformable registration, individual voxel values may be displaced within constraints with
respect to the rest of the image, i.e. in the previous example the lower jaw may be 
"moved up" to better fit the closed jaw of the CT-scan. This procedure requires a certain 
level of constraint, since otherwise voxels would be moved erratically. In turn, this
means deformable registration should be preceded by rigid registration, so that only small
voxel adjustments are necessary.

Evaluation 
============

..
    * Metrics 

After having performed registration, it remains to check that the registrations
were performed well. One possible way is to manually check all of
the data that has been processed, i.e. visualise the images and look for poor 
registrations. Often this is time consuming, and sometimes the human eye
is not as good at spotting irregularities as computers might be. Therefore, 
a *metric* is often used. Metrics measure how well a process was performed, i.e. 
they often give one or two values that describe how accurately the data was 
preprocessed. In the case of registration the "accuracy" is how similar the CT- 
and MR-images are. Several metrics that measure this kind of 3D-image similarity exist,
including:

* Correlation coefficient, measuring the correlation between voxel values at identical 
  positions of the two images. 
* Dice coefficient (also known as the Sørensen-Dice coefficient), measuring the quotient
  between overlapping volume and total volume.
* Mutual Information, measuring how well a voxel value from one image can be predicted from
  the same voxel's value in another image.

..
    * Cropping - relevant in proportion to Metrics

Many 3D-image similarity metrics, including the above, suffer from an issue wherein
"background" (in this case, air) voxels contribute to false accuracy. This issue can
be partially remedied by cropping the image to include as little air as possible.
In addition to that they also require the images to have the same size, since "something" 
cannot be compared with "nothing". 
.. 
    Lastly, we also need all the slices in the 3D-image to be 
    comparable, which means that the drawing architecture should be clean and without noise








