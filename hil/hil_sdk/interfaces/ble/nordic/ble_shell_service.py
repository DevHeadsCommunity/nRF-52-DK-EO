#
# Copyright (C) 2023, Dojo Five
# All rights reserved.
#

import cbor2
from ..ble_client import BLEClient
from .ble_smp_service import *


class BLEShellService(BLESMPService):

    """A service for performing shell operations over SMP."""

    def __init__(self, client: BLEClient):

        """
        Construct a new BLEShellService object.
        """

        super().__init__(client)

    async def execute_command(self, command: list[str]):

        """Performs a shell command over SMP. The format of the response can be found
        `here <https://developer.nordicsemi.com/nRF_Connect_SDK/doc/latest/zephyr/services/device_mgmt/smp_groups/smp_group_9.html#shell-command-line-execute-response>`_

        :param command: Array of command and arguments (eg, ["command", "arg1", "arg2"])

        :return: Shell response object as a dictionary
        """

        header = BLESMPService._get_smp_header(OP_WRITE, 0, GRP_SHELL_MANAGEMENT, 0, IMAGE_STATE_COMMAND)

        print("%s: execute command: %s" % (self.__class__.__name__, command))
        cbor_data = {"argv": command}
        payload = list(cbor2.dumps(cbor_data))

        rsp = await self.write_smp_and_response(bytearray(header + payload))

        return rsp
