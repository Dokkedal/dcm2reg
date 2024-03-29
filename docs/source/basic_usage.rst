Coding tutorial
****************

When using the module the procedure can be split up into three steps: conversion, registration and evaluation.

Conversion
==========

The conversion part of the module takes DICOM-files and converts them into nifty files. This is again split
up into two parts: writing a dictionary and writing nifti files. The dictionary is written using the script
``conversion_dictwriter.py`` and is outputted as an excel file. The excel file is accessible by the user
and also contains the flagged patients. It is important that the folder structure matches the paths given in the 
function. A structure as follows is thus required for all of the functions to work::

    project directory
    |-- data
    |   |-- dicom
    |   |   |-- dicom_file1.dcm
    |   |   |-- ...
    |   |-- misc_output
    |   |   |-- filenames
    |   |-- nifti
    |-- dcm2reg

The dicom files thus has to be located in the folder named ``dicom``.In order to run 
``conversion_dictwriter.py`` the user has to has to supply the code with a startpatient and an endpatient
i.e. how many patients the function should convert. A list of modalities to look for and which regions of 
interest that are of importance is also required. Furthermore, the function requires the amount of days allowed
between the patient being scanned and the delineations being drawn: ``maxdelineationdelay``. Lastly, the function
requires the maximum allowed days between a primary study and secondary study: ``maxstudydelay``.

.. literalinclude:: ../../dictwriter_tutorial.py
    :language: python
    :linenos:

The next part of the conversion is handled by the script ``conversion_filewriter.py``. This function
takes the excel file written by the previous function as input and from this converts to nifti files.
The function requires a modalitylist and a list of regions of interest supplyed from the user. Furthermore, the 
user can specify which flagged patients the function should include when writing to nifti files. This is
specified using the boolean variables: ``includered, includeorange, includeyellow``. The nifti files will be
outputted to the directory ``targetdir``.

.. literalinclude:: ../../filewriter_tutorial.py
    :language: python
    :linenos:

Registration
============
The registration part of the module takes the converted nifti files as input and runs two different registrations.
First, a rigid registration is run on all images and afterwards a deformable registration is run. The user needs 
to input how many images the registration function should run through. If the folder structure is set up 
correctly, the function will be able to find the needed directories. The registered images are outputted to the
folder ``nifti_reg``.

.. literalinclude:: ../../registration_tutorial.py
    :language: python
    :linenos:

Evaluation
==========
The evaluation part of the module loads the registered pictures and evaluates by computing a metric. The user 
will need to supply the function with the amount of patients that it needs to evaluate. This is done via the
variables ``startpatient`` and ``endpatient`` which is the first two arguements. The user is also able to select
the margin of the croppoing box and the flagging_threshold using the variables ``margin`` and ``flagging``. These
are the last two arguments.

.. literalinclude:: ../../evaluation_tutorial.py
    :language: python
    :linenos:










