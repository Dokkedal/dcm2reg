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
the registration of our images. A cropbox is a cropped version of the image where the cropped part comprises 
more comparable parts of the image. The cropbox thus removes parts of the image that consists of air
by cropping voxels with a color value of less than 1. Noisy tissue or images containing very little tissue
can also be a problem but this is taken into account by providing the cropbox with a margin. The margin is the
number of addtional images to be cropped besides the images with color values of less than 1.

For evaluating the registration a metric is computed, in this case AdvancedMattesMutualInformation. One of 
the advantages of using this metric is that the modalities of the images doesn't have to be the same. So even
though the signal is of different intencity for the same tissue AdvancedMattesMutualInformation can still give
us a decent measure of how well the registration went.

Link about MutualInformation: https://matthew-brett.github.io/teaching/mutual_information.html 

During evaluation of the registration images that get a low metric score is flagged. This allows the user
to do a manual evaluation of low performing registrations. Flagged registrations is colored red in the output
file. A metric score of 0.5 has been chosen as the threshold for flagging registrations. The score is based
partly on manual evaluation of several registrations but also by plotting a histogram of the scores.

.. figure:: Histogram_of_metric_score.png
    :align: center
    :alt: alternate text
    :figclass: align-center

    Histogram of metric score



There is a clear drop between values 

When evalution of the registrations is done an overview of the 
metric scores is produced as an excel sheet. The flagged values have been colored red.


* Crop zero-columns
* Crop threshold (manual)
* Compute MutualInformation
* Flag values below threshold
* Logging











