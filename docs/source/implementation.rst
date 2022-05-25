Implementation
***************

Dicom to nifti conversion - Jonathan
=========================

* Write a dictionary from dicom files 
* Perform selection of series
* Flagging issues for manual control
* Write nifti-files (optional including of different flags)

Registrations
=============

* 

Evaluation of registrations - Philip
===========================

Evaluation of registration can be done via several methods. We are using a cropbox in order to evaluate
the registration of our images. The cropbox thus represents a section of the images. Before evaluating
using the cropbox it is neccessary to comb through the images beforehand where you remove the images that 
is not interesting to look at with our cropbox.

For example images only containing air or images that contain very little tissue. These images have to be
removed manually by the user via slicing the image array. Afterwards a metric is computed, in this case 
AdvancedMattesMutualInformation, in order to evaluate how well the registration went. One of the advantages
of using this metric is that the modalities of the images doesn't have to be the same. So even though the
signal is of different intencity for the same tissue AdvancedMattesMutualInformation can still give us a 
decent measure of how well the registration went.

Link about MutualInformation: https://matthew-brett.github.io/teaching/mutual_information.html 

During evaluation of the registration images that get a low metric score is flagged. This allows the user
to do a manual evaluation of low performing registrations. A metric score of 0.5 has been chosen as the
threshold for flagging registrations. The score is based on manual evaluation of several registrations.


* Crop zero-columns
* Crop threshold (manual)
* Compute MutualInformation
* Flag values below threshold
* Logging











