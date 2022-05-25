Coding tutorial - Philip
****************

When using the module the procedure can be split up into three steps: conversion, registration and evaluation.

Conversion
==========
The conversion part of the module takes DICOM-files and converts them into nifty files. In order to run
conversion the user has to supply the code with a path to the location of the DICOM-files and how many
DICOM-files the user wants converted. The user also has to supply the code with a list of modalities to look
for and wich regions of interest we are interested in.

.. literalinclude:: ../../dictwriter_tutorial.py
    :language: python

Registration
============

Skal vi gennemgå noget af jaspers kode her eller?

Evaluation
==========
The evaluation part of the module loads the registered pictures and evaluates by computing a metric. The user 
will need to supply the code with a path to the registered pictures and how many pictures the user wants converted.











