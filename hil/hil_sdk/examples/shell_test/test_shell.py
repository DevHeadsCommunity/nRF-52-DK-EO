#
# Copyright (C) 2023, Dojo Five
# All rights reserved.
#

import os
import asyncio
import pytest
import pytest_asyncio

@pytest.mark.asyncio
async def test_ble_shell(ble_shell_fixture):

    cmd_response = await ble_shell_fixture.execute_command(["hil", "ping"])

    print(f"Shell response: {cmd_response}")

    await asyncio.sleep(5)

    # "ping" command is expected to return "pong"
    assert str(cmd_response["o"]).strip() == "pong"


