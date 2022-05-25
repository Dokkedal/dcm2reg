# encoding: utf-8
import os
import pathlib

import SimpleITK as sitk
import numpy as np
import tempfile

#from fexp.readers import read_image

_DICOM_MODALITY_TAG = '0008|0060'
_DICOM_VOI_LUT_FUNCTION = '0028|1056'
_DICOM_WINDOW_CENTER_TAG = '0028|1050'
_DICOM_WINDOW_WIDTH_TAG = '0028|1051'
_DICOM_WINDOW_CENTER_WIDTH_EXPLANATION_TAG = '0028|1055'


def read_dcm_series(directory_or_files, series_id=None, return_sitk=False):
    """Read dicom series from a folder. If multiple dicom series are availabe in the folder,
    no image is returned. The metadata dictionary then contains the SeriesIDs which can be selected.
    Parameters
    ----------
    directory_or_files : str
        path to folder containing the series
    series_id : str
        SeriesID to load
    directory_or_files : str
        If filenames is given then series_id is ignored, and assume that there is one series and these files are loaded.
    return_sitk : bool
        If true, the original SimpleITK image will also be returned
    Returns
    -------
    np.ndarray and dictionary.
    TODO
    ----
    Catch errors such as
    WARNING: In /tmp/SimpleITK-build/ITK/Modules/IO/GDCM/src/itkGDCMSeriesFileNames.cxx, line 109
    GDCMSeriesFileNames (0x4a6e830): No Series were found
    """
    if isinstance(directory_or_files, str):
        directory_or_files = pathlib.Path(directory_or_files)

    if not isinstance(directory_or_files, list):
        if not directory_or_files.is_dir():
            raise ValueError(f'{directory_or_files} is not a directory or list of files.')

    metadata = {'filenames': []}

    if directory_or_files:
        file_reader = sitk.ImageFileReader()
        file_reader.SetFileName(str(directory_or_files[0]))
        file_reader.ReadImageInformation()
        series_ids = [file_reader.GetMetaData('0020|000e')]
        with tempfile.TemporaryDirectory() as tmpdir_name:
            for f in directory_or_files:
                os.symlink(os.path.abspath(f), os.path.join(tmpdir_name, os.path.basename(f)))
            sorted_filenames = sitk.ImageSeriesReader.GetGDCMSeriesFileNames(tmpdir_name, series_ids[0])
            sitk_image = sitk.ReadImage(sorted_filenames)
        metadata['filenames'] = directory_or_files
    else:
        reader = sitk.ImageSeriesReader()
        series_ids = list(reader.GetGDCMSeriesIDs(str(directory_or_files)))

        for series_id in series_ids:
            sorted_filenames = sitk.ImageSeriesReader.GetGDCMSeriesFileNames(directory_or_files, series_id)
            metadata['filenames'].append(sorted_filenames)
            sitk_image = sitk.ReadImage(sorted_filenames)
        if len(series_ids) > 1 and not series_id:
            image = None
            metadata['series_ids'] = series_ids

            return image, metadata

    metadata['series_ids'] = series_ids

    metadata['filenames'] = [sorted_filenames]
    metadata['depth'] = sitk_image.GetDepth()
    metadata['spacing'] = tuple(sitk_image.GetSpacing())
    metadata['origin'] = tuple(sitk_image.GetOrigin())
    metadata['direction'] = tuple(sitk_image.GetDirection())
    data = sitk.GetArrayFromImage(sitk_image)

    if return_sitk:
        return data, sitk_image, metadata

    return data, metadata