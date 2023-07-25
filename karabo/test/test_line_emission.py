import tempfile
from pathlib import Path

import h5py
import numpy as np
import pytest
from astropy.io import fits

from karabo.data.external_data import DilutedBATTYESurveyDownloadObject, DownloadObject
from karabo.simulation.line_emission import (
    gaussian_fwhm_meerkat,
    line_emission_pointing,
    plot_scatter_recon,
    simple_gaussian_beam_correction,
)
from karabo.simulation.sky_model import SkyModel
from karabo.util.dask import DaskHandler


# DownloadObject instances used to download different golden files:
# - FITS file before beam correction
# - H5 file with channels stored separately, before beam correction
# - FITS file after beam correction
@pytest.fixture
def uncorrected_fits_filename():
    return "test_line_emission.fits"


@pytest.fixture
def uncorrected_h5_filename():
    return "test_line_emission.h5"


@pytest.fixture
def corrected_fits_filename():
    return "test_line_emission_GaussianBeam_Corrected.fits"


@pytest.fixture
def uncorrected_fits_downloader(uncorrected_fits_filename):
    return DownloadObject(
        f"karabo_public/{uncorrected_fits_filename}",
    )


@pytest.fixture
def uncorrected_h5_downloader(uncorrected_h5_filename):
    return DownloadObject(
        f"karabo_public/{uncorrected_h5_filename}",
    )


@pytest.fixture
def corrected_fits_downloader(corrected_fits_filename):
    return DownloadObject(
        f"karabo_public/{corrected_fits_filename}",
    )


def test_line_emission_run(
    uncorrected_fits_filename,
    uncorrected_h5_filename,
    corrected_fits_filename,
    uncorrected_fits_downloader,
    uncorrected_h5_downloader,
    corrected_fits_downloader,
):
    """Executes the line emission pipeline and validates the output files.

    The line emission pipeline consists of the following steps:
       Load sky model with input sources.
       Prepare sky pointing, which keeps only sources within
       a given field of view.
       Simulate the line emission observation.
       Prepare a Gaussian beam, and apply beam correction to pointing result.

    Args:
      uncorrected_fits_filename:
        Name of FITS file containing added images before beam correction.
      uncorrected_h5_filename:
        Name of HDF5 file containing individual images from each channel,
        before beam correction.
      corrected_fits_filename:
        Name of FITS file containing added images after beam correction.
    """
    DaskHandler.n_threads_per_worker = 1

    # Download golden files for comparison
    golden_uncorrected_fits_path = uncorrected_fits_downloader.get()
    golden_uncorrected_h5_path = uncorrected_h5_downloader.get()
    golden_corrected_fits_path = corrected_fits_downloader.get()

    # Load sky model data
    survey = DilutedBATTYESurveyDownloadObject()
    catalog_path = survey.get()

    # Directory containing output files for validation
    with tempfile.TemporaryDirectory() as tmpdir:
        outpath = Path(tmpdir)
        uncorrected_fits_path = outpath / uncorrected_fits_filename
        uncorrected_h5_path = outpath / uncorrected_h5_filename
        corrected_fits_path = outpath / corrected_fits_filename

        # Set sky position for pointing
        ra = 20
        dec = -30
        cut = 1.0  # degrees

        sky_pointing = SkyModel.sky_from_h5_with_redshift_filtered(
            path=catalog_path, ra_deg=ra, dec_deg=dec, outer_rad=3
        )

        # Simulation of line emission observation
        dirty_im, _, header_dirty, freq_mid_dirty = line_emission_pointing(
            outpath_base=outpath, sky=sky_pointing, cut=cut, img_size=1024
        )

        # Validate uncorrected H5 file,
        # which results from the line emission simulation
        golden_uncorrected_h5_file = h5py.File(golden_uncorrected_h5_path, "r")
        uncorrected_h5_file = h5py.File(uncorrected_h5_path, "r")

        # Check each H5 dataset individually
        assert (
            golden_uncorrected_h5_file["Dirty Images"].shape
            == uncorrected_h5_file["Dirty Images"].shape
        )
        assert (
            golden_uncorrected_h5_file["Dirty Images"].attrs["Units"]
            == uncorrected_h5_file["Dirty Images"].attrs["Units"]
        )

        for golden_dirty_image, dirty_image in zip(
            golden_uncorrected_h5_file["Dirty Images"],
            uncorrected_h5_file["Dirty Images"],
        ):
            assert np.allclose(
                golden_dirty_image,
                dirty_image,
                equal_nan=True,
            )

        assert (
            golden_uncorrected_h5_file["Observed Redshift Bin Size"][()]
            == uncorrected_h5_file["Observed Redshift Bin Size"][()]
        )

        assert np.array_equal(
            golden_uncorrected_h5_file["Observed Redshift Channel Center"],
            uncorrected_h5_file["Observed Redshift Channel Center"],
        )

        # Verify uncorrected FITS file,
        # which results from the line emission simulation
        uncorrected_fits_data, uncorrected_fits_header = fits.getdata(
            uncorrected_fits_path, header=True
        )
        golden_uncorrected_fits_data, golden_uncorrected_fits_header = fits.getdata(
            golden_uncorrected_fits_path, header=True
        )

        # Check FITS data is close to goldenfile
        assert np.allclose(
            golden_uncorrected_fits_data,
            uncorrected_fits_data,
            equal_nan=True,
        )

        # Check that headers contain the same keys
        assert set(golden_uncorrected_fits_header.keys()) == set(
            uncorrected_fits_header.keys()
        )

        # Check that header fields have the same values
        for k in golden_uncorrected_fits_header.keys():
            assert golden_uncorrected_fits_header[k] == uncorrected_fits_header[k]

        # Generate scatter plot, to validate that plotting can run
        plot_scatter_recon(
            sky_pointing,
            dirty_im,
            outpath / "test_line_emission.pdf",
            header_dirty,
            cut=cut,
        )

        # Generate Gaussian primary beam for correction,
        # and apply correction to dirty images
        gauss_fwhm = gaussian_fwhm_meerkat(freq_mid_dirty)

        beam_corrected, _ = simple_gaussian_beam_correction(
            outpath,
            dirty_im,
            gauss_fwhm,
            cut=cut,
            img_size=1024,  # Small image size for testing purposes
        )

        # Validate output FITS file after beam correction
        corrected_fits_data, corrected_fits_header = fits.getdata(
            corrected_fits_path, header=True
        )
        golden_corrected_fits_data, golden_corrected_fits_header = fits.getdata(
            golden_corrected_fits_path, header=True
        )

        # Check FITS data is close to goldenfile
        assert np.allclose(
            golden_corrected_fits_data,
            corrected_fits_data,
            equal_nan=True,
        )

        # Check that headers contain the same keys
        assert set(golden_corrected_fits_header.keys()) == set(
            corrected_fits_header.keys()
        )

        # Check that header fields have the same values
        for k in golden_corrected_fits_header.keys():
            assert golden_corrected_fits_header[k] == corrected_fits_header[k]

        # Generate plot using the corrected FITS data
        plot_scatter_recon(
            sky_pointing,
            beam_corrected,
            outpath / "test_line_emission_GaussianBeam_Corrected.pdf",
            header_dirty,
            cut=cut,
        )

        print("Finished")
