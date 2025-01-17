# set shared library if WSL to detect GPU drivers
import os
import platform
import sys

from karabo.version import __version__

__version__ = __version__

if "WSL" in platform.release() and (
    os.environ.get("LD_LIBRARY_PATH") is None
    or "wsl" not in os.environ["LD_LIBRARY_PATH"]
):
    wsl_ld_path = "/usr/lib/wsl/lib"
    if os.environ.get("LD_LIBRARY_PATH") is None:
        os.environ["LD_LIBRARY_PATH"] = wsl_ld_path
    else:
        os.environ["LD_LIBRARY_PATH"] = (
            os.environ["LD_LIBRARY_PATH"] + ":" + wsl_ld_path
        )
    # Restart Python Interpreter
    # https://stackoverflow.com/questions/6543847/setting-ld-library-path-from-inside-python
    os.execv(sys.executable, ["python"] + sys.argv)

# Setup dask for slurm
from karabo.util.dask import prepare_slurm_nodes_for_dask

prepare_slurm_nodes_for_dask()

# set rascil data directory environment variable
# see https://ska-telescope.gitlab.io/external/rascil/RASCIL_install.html
from karabo.util.jupyter import set_rascil_data_directory_env  # noqa: E402

set_rascil_data_directory_env()
