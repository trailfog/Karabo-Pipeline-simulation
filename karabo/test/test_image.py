import os
import unittest

import numpy as np

from karabo.imaging.image import Image
from karabo.imaging.imager import Imager
from karabo.simulation.sky_model import SkyModel
from karabo.simulation.visibility import Visibility
from karabo.test import data_path


class TestImage(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # make dir for result files
        if not os.path.exists("result/"):
            os.makedirs("result/")

    def test_dirty_image(self):
        vis = Visibility.read_from_file(f"{data_path}/visibilities_gleam.ms")
        imager = Imager(
            vis, imaging_npixel=2048, imaging_cellsize=3.878509448876288e-05
        )

        dirty = imager.get_dirty_image()
        dirty.write_to_file("result/dirty.fits", overwrite=True)
        dirty.plot(title="Dirty Image")

    def test_dirty_image_resample(self):
        vis = Visibility.read_from_file(f"{data_path}/visibilities_gleam.ms")
        SHAPE = 2048
        imager = Imager(
            vis, imaging_npixel=SHAPE, imaging_cellsize=3.878509448876288e-05
        )

        dirty = imager.get_dirty_image()
        shape_before = dirty.data.shape

        NEW_SHAPE = 512
        dirty.resample((NEW_SHAPE, NEW_SHAPE))
        dirty.write_to_file("result/dirty_resample.fits", overwrite=True)
        dirty.plot(title="Dirty Image")

        assert dirty.data.shape[2] == NEW_SHAPE
        assert dirty.data.shape[3] == NEW_SHAPE
        assert dirty.data.shape[0] == shape_before[0]
        assert dirty.data.shape[1] == shape_before[1]
        assert np.sum(np.isnan(dirty.data)) == 0

        dirty.resample((SHAPE, SHAPE))

        assert dirty.data.shape[2] == SHAPE
        assert dirty.data.shape[3] == SHAPE
        assert dirty.data.shape[0] == shape_before[0]
        assert dirty.data.shape[1] == shape_before[1]
        assert np.sum(np.isnan(dirty.data)) == 0

    def test_cellsize_overwrite(self):
        vis = Visibility.read_from_file(f"{data_path}/visibilities_gleam.ms")
        imager = Imager(
            vis,
            imaging_npixel=2048,
            imaging_cellsize=10,
            override_cellsize=True,
        )

        dirty = imager.get_dirty_image()
        header = dirty.header
        cdelt_overwrite_cellsize_false = header["CDELT1"]

        imager = Imager(
            vis,
            imaging_npixel=2048,
            imaging_cellsize=1,
            override_cellsize=True,
        )
        dirty = imager.get_dirty_image()
        header = dirty.header
        cdelt_overwrite_cellsize_true = header["CDELT1"]

        assert cdelt_overwrite_cellsize_false == cdelt_overwrite_cellsize_true

    def test_cellsize_overwrite_false(self):
        vis = Visibility.read_from_file(f"{data_path}/visibilities_gleam.ms")
        imager = Imager(
            vis,
            imaging_npixel=2048,
            imaging_cellsize=10,
            override_cellsize=False,
        )
        dirty = imager.get_dirty_image()
        cdelt_overwrite_cellsize_false = dirty.header["CDELT1"]

        imager = Imager(
            vis,
            imaging_npixel=2048,
            imaging_cellsize=1,
            override_cellsize=False,
        )
        dirty = imager.get_dirty_image()
        cdelt_overwrite_cellsize_true = dirty.header["CDELT1"]

        assert cdelt_overwrite_cellsize_false != cdelt_overwrite_cellsize_true

    def test_explore_sky(self):
        sky = SkyModel.get_GLEAM_Sky([76])
        sky.explore_sky([250, -80], s=0.1)

    # # TODO: move these on to CSCS Test Infrastructure once we have it.
    # def test_clean(self):
    #     sky = get_GLEAM_Sky()
    #     phase_center = [250, -80]
    #     sky = sky.filter_by_radius(0, .55, phase_center[0], phase_center[1])
    #     sky.setup_default_wcs(phase_center=phase_center)
    #     tel = Telescope.get_ASKAP_Telescope()
    #     observation_settings = Observation(100e6,
    #                                        phase_centre_ra_deg=phase_center[0],
    #                                        phase_centre_dec_deg=phase_center[1],
    #                                        number_of_channels=64,
    #                                        number_of_time_steps=24)
    #
    #     interferometer_sim = InterferometerSimulation(channel_bandwidth_hz=1e6)
    #     visibility = interferometer_sim.run_simulation(tel, sky, observation_settings)
    #
    #     # visibility = Visibility()
    #     # visibility.load_ms_file(f"./{data_path}/visibilities_gleam.ms")
    #     imager = Imager(visibility,
    #                     ingest_vis_nchan=16,
    #                     ingest_chan_per_blockvis=1,
    #                     ingest_average_blockvis=True,
    #                     imaging_npixel=512,
    #                     imaging_cellsize=3.878509448876288e-05*4,
    #                     imaging_weighting='robust',
    #                     imaging_robustness=-.5)
    #     deconvoled_image, restored_image, residual_image = imager.imaging_rascil()
    #     restored_image.save_to_file("result/restored.fits")
    #     residual_image.save_to_file("result/residual.fits")
    #     sky.save_to_file("result/imaging_sky.txt")

    def test_power_spectrum(self):
        restored_image = Image(path=f"{data_path}/restored.fits")
        # restored_image.plot_power_spectrum(save_png=True)
        restored_image.get_cellsize()
        # restored_image.plot_histogram()

    # def test_source_detection(self):
    #     restored = open_fits_image("karabo/test/data/restored.fits")
    #     detection_result = detect_sources_in_image(restored)
    #     residual = detection_result.get_gaussian_residual_image()
    #     residual.save_as_fits("result/gaus_residual.fits")
    #     residual.plot()
    #     detection_result.detection.show_fit()

    # def test_source_detection_on_residual(self):
    #     residual = open_fits_image("./data/residual.fits")
    #     sources = detect_sources_in_image(residual, beam=(0.06, 0.02, 13.3))
    #     print(sources.sources)

    # def test_source_detection_on_dirty_image(self):
    #     dirty = open_fits_image("./data/dirty.fits")
    #     dirty.plot()
    #     detection = detect_sources_in_image(dirty, beam=(0.06, 0.02, 13.3))
    #     detection.get_island_mask().plot()

    # def test_show_deconvolved(self):
    #     deconv = open_fits_image("./data/deconvolved.fits")
    #     deconv.plot()

    # def test_try_star_finder(self):
    #     deconvolved = open_fits_image("./data/deconvolved.fits")
    #     use_dao_star_finder(deconvolved)
    #
    # def test_source_detection_on_deconvolved(self):
    #     deconvolved = open_fits_image("./data/deconvolved.fits")
    # sources = detect_sources_in_image(
    #     deconvolved,
    #     # beam=(0.05425680530067645, 0.05047422298502832, -205.3215315790252))
    #     beam=(0.06, 0.02, 13.3),
    # )
    #     print(sources.sources)
