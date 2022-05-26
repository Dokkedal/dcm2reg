Documentation for dcm2reg
*************************
..
    * Introduction

``dcm2reg`` is a module which is useful for preprocessing medical image data,
whenever the end goal is to prepare the data for development of e.g. deep
learning models which can automatically delineate organs and/or tumors.
The module is available in ``python`` and is known to work on Windows, however
other common operating systems (OS X, Linus) likely work as well, as long as
dependencies can be properly installed.

Developing deep learning models for delineation is of high interest in e.g.
the planning phase of radiation therapy for patients with cancer. Delineations
are crucial in this application because doctors want to deliver an appropriate
radiation dosage to cancer tumors while affecting organs at risk with as small
dosages as possible. While deep learning models will hardly replace doctors 
entirely in delineation tasks at first, simply developing tools that can give
suggestions which the doctors can validate upon will cut down manual labour
on an otherwise time-consuming task. Furthermore, data-based models will
hopefully be able to reduce some of the individual error-prone biases that 
doctors inevitably harbour and thus improve standardisation of treatments.

``dcm2reg`` was created by three data science students at Aarhus University
during a semester-long data project: Andreas Busch, Philip Leth and Jonathan
Nielsen. However, it is also built upon the ``dcm2nii`` module with scripts
modified by several other contributors, including Jintao Ren, Zixiang-Wei
(Alan) and Jasper Nijkamp, the latter two of which also supervised the project
as a whole.

The contributions of the data science students can be generally summarised as 
follows:

* Splitting the conversion script written by Jintao into several restructured 
ones and exporting scan selections to an Excel-file to allow for manual checking
and control.
* Flagging issues with scans for conversion.
* Handling errors and changing decisions for scan selection. 
* Writing functions to evaluate registration of images based on a metric score.
* Exporting metric scores and flagging ones below appropriate threshold.
* Easing the overall usage of the different scripts by restructuring them, 
e.g. with function arguments.
* Writing documentation both in and out of code.

.. toctree::
    :maxdepth: 2
    :numbered:
    :titlesonly:
    :glob:
    :hidden:

    background.rst
    basic_usage.rst
    implementation.rst
    installation.rst
    our_use_case.rst
