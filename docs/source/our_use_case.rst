Original use case
******************

Our data 
========

* Visual examples - different scans - Philip
* Levels - color code - Philip

..
    * Additional information - Jonathan
    * Delineation in RTSTRUCT - Jonathan

In addition to the images themselves, the data contains various header information, such as 
the *modality* of the image (i.e. whether it is a CT-, PET- or MR-scan), the date of the scan,
a medical description of the scan etc. This information is crucial in identifying the scans,
referring to them and making decisions about them.

For some of the scans (typically a CT-scan), a doctor has delineated various organs and/or tumors.
These delineations are saved as a set of lines in one or more so-called *RTSTRUCT*-file(s). The
RTSTRUCT-file also contains the name of each delineation, e.g. "brain" or "parotid_L" for the left
parotid gland. Occasionally, a single organ may have been delineated more than once, e.g. if a 
patient's tumor changed in shape or size due to treatment performed between two delineations. 
In this case, the two delineations will be saved in different RTSTRUCT-files from different dates.
The delineations must be kept track of alongside the rest of the data, as they are essentially what
an ultimate model must learn from. However, since not all scans have delineations, since not all
scans *with* delinations include the same organs and since not all scans with the same delineations
have identical naming schemes for those delineations, identifying the correct delineations is a
challenge that must be met.

* Noise e.g. table - Philip
* Limitations - very heterogenous data - Busch

Our pipeline and the big picture
================================

* Preprocessing - conversion, registration, Evaluation - Philip
* Model development - neural network, comparison (CT vs CT+MR) - Busch 
* Model usage - implementation, user acceptance - Busch
* Flowchart - Jonathan 


Challenges and solutions
========================

This sections describes a variety of challenges faced during the project along with
the solutions that were developed.

..
    * Missing header information in conversion - code example - Jonathan

One such challenge concerns the header information in the DICOM-files. When selecting
the scans for format conversion, it may at first glance be desirable to select based
on the medical description of the scans, e.g. to get an overview of what the scan
was used for. However, this is difficult due to the lack of standardisation of those
descriptions - in fact, there are occasionally scans which completely lack a description.
To overcome this challenge, we have avoided making decisions based on the description,
and wrapped the attribute reading in an exception catcher as follows.

.. literalinclude:: ../../dicom_conversion/convertorv3_functions.py
    :linenos:
    :lineno-start: 439
    :language: python
    :lines: 439-446
    :emphasize-lines: 441-446

..
    * Many edge cases e.g. missing secondary study - Jonathan

The general hetereogeneity of the data also poses a challenge, since there are so
many edge cases to consider. Some patients do not have a CT-scan with RTSTRUCT-files at
all, which consequently means none of the scans for that patient will be selected for 
conversion. This essentially causes any PET- and MR-scans to be dropped due to a lack of
CT-scans with delineations. The opposite is also an issue. If there are several CT-scans
with delineations, but no PET- or MR-scans, the selection program cannot be sure which
of the CT-scans to choose, since this is usually done by comparing how many PET- or MR-scans
relate to the individual CT-scans.



* A lot of data and therefore slow running - solved in conversion by splitting process. - Jonathan
* Noise limiting use of thresholding - Philip
* Thresholding based on change in pixel value turned out to be not possible - Philip
* Different MR's have different colors - Philip
* Field difficulty and lack of documentation - Busch
* Excel cell character limit - Jonathan
* 
 






