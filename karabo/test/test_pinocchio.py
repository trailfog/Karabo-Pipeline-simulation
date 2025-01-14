import datetime
import os
import unittest

from karabo.imaging.imager import Imager
from karabo.simulation.interferometer import InterferometerSimulation
from karabo.simulation.observation import Observation
from karabo.simulation.pinocchio import Pinocchio
from karabo.simulation.telescope import Telescope


class TestPinocchio(unittest.TestCase):
    RESULT_FOLDER = "./result"

    @classmethod
    def setUpClass(cls) -> None:
        # make dir for result files
        if not os.path.exists(TestPinocchio.RESULT_FOLDER):
            os.makedirs(TestPinocchio.RESULT_FOLDER)

    def testSimpleInstance(self) -> None:
        p = Pinocchio()
        p.setRunName("unittest")
        p.printConfig()
        p.printRedShiftRequest()
        p.runPlanner(16, 1)
        p.run(mpiThreads=2)

        p.save(TestPinocchio.RESULT_FOLDER)
        sky = p.getSkyModel()
        sky = sky.filter_by_radius(0, 1, 32, 45)

        telescope = Telescope.get_SKA1_MID_Telescope()

        simulation = InterferometerSimulation(
            channel_bandwidth_hz=1e3, time_average_sec=10
        )

        observation = Observation(
            start_frequency_hz=1e9,
            phase_centre_ra_deg=31.9875,
            phase_centre_dec_deg=45.1333,
            length=datetime.timedelta(minutes=10),
            number_of_time_steps=1,
            frequency_increment_hz=1,
            number_of_channels=1,
            start_date_and_time="2022-03-01T11:00:00",
        )

        visibility = simulation.run_simulation(telescope, sky, observation)

        cellsize = 0.003
        boxsize = 2048
        imager = Imager(visibility, imaging_npixel=boxsize, imaging_cellsize=cellsize)

        dirty = imager.get_dirty_image()
        dirty.write_to_file(f"{TestPinocchio.RESULT_FOLDER}/dirty.fits", overwrite=True)
        dirty.plot("pinocchio sim dirty plot")
