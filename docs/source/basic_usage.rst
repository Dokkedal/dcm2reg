Coding tutorial - Philip
****************

When using the module the procedure can be split up into three steps: conversion, registration and evaluation.

Conversion
==========
The conversion part of the module takes DICOM-files and converts them into nifty files. This is again split
up into two parts: writing a dictionary and writing nifti files. The dictionary is written using the function
``convertorv3_dictwriter_tutorial`` and is outputted as an excel file. The excel file is accessible by the user
and also contains the flagged patients. It is important that the folder structure matches the paths given in the 
function. A structure as follows is thus required for all of the functions to work:
::
    project directory
    |-- data
    |   |-- dicom
    |   |   |-- dicom_file1.dcm
    |   |   |-- ...
    |   |-- misc_output
    |   |-- nifti
    |-- dcm2reg

The dicom files thus has to be located in the folder named ``dicom``.In order to run 
``convertorv3_dictwriter_tutorial`` the user has to has to supply the code with a startpatient and an endpatient
i.e. how many patients the function should convert. A list of modalities to look for and which regions of 
interest that are of importance is also required. Furthermore the function requires the amount of days allowed
between the patient being scanned and the delineations being drawn: ``maxdelineationdelay``. Lastly the function
requires the maximum allowed days between a primary study and secondary study: ``maxstudydelay``.

.. literalinclude:: ../../dictwriter_tutorial.py
    :language: python
    :linenos:

The next part of the conversion is handled by the function ``convertorv3_filewriter_tutorial``. This function
takes the excel file written by the previous function as input and from this converts to nifti files.
The function requires a modalitylist and a list of regions of interest supplyed from the user. Furthermore the 
user can specify which flagged patients the function should include when writing to nifti files. This is
specified using the boolean variables: ``includered, includeorange, includeyellow``. The nifti files will be
outputted to the directory ``targetdir``.

.. literalinclude:: ../../filewriter_tutorial.py
    :language: python
    :linenos:

Registration
============

Skal vi gennemgå noget af jaspers kode her eller?

Evaluation
==========
The evaluation part of the module loads the registered pictures and evaluates by computing a metric. The user 
will need to supply the function with the amount of patients that it needs to evaluate. This is done via the
variables ``startpatient`` and ``endpatient`` which is the first two arguements. The user is also able to select
the margin of the croppoing box and the flagging_threshold using the variables ``margin`` and ``flagging``. These
are the last two arguements.

.. literalinclude:: ../../evaluation_tutorial.py
    :language: python
    :linenos:










