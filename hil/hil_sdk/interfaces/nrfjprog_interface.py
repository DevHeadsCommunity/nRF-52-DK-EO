#
# Copyright (C) 2023, Dojo Five
# All rights reserved.
#

import subprocess

def nrfjprog_flash(binary: str, family: str) -> int:

    """
    Load a file onto the target device via the nrfjprog tool.

    :param binary: Path of the file to be loaded. For nRF53 devices,
        this should be a merged hex file

    :param family: Device family (eg, "NRF53")

    :return: Status of operation (0 for success, other for error. See nrfprog documentation for further details).
    :rtype: int
    """

    return subprocess.Popen(f"nrfjprog -f {family} --program {binary} --recover --verify", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).wait()


def nrfjprog_eraseall(family: str) -> int:

    """
    Load a file onto the target device via the nrfjprog tool.

    :param family: Device family (eg, "NRF53")

    :return: Status of operation (0 for success, other for error. See nrfprog documentation for further details).
    :rtype: int
    """

    return subprocess.Popen(f"nrfjprog -f {family} --eraseall", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).wait()
