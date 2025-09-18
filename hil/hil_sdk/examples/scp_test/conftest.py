#
# Copyright (C) 2025, Dojo Five
# All rights reserved.
#

import pytest

from hil_sdk.interfaces.remote_interface import RemoteInterface


@pytest.fixture
def remote_interface_fixture():
    # Replace HOSTNAME and USERNAME with the remote server that you want to connect to.
    # If password is required, pass a password string to the RemoteInterface()
    # e.g. RemoteInterface("HOSTNAME", "USERNAME", "PASSWORD")
    return RemoteInterface("HOSTNAME", "USERNAME")
