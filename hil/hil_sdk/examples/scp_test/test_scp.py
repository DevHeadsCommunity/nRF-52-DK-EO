#
# Copyright (C) 2025, Dojo Five
# All rights reserved.
#

import os

def test_scp(remote_interface_fixture):

    # Replace REMOTE_PATH with the location on the remote server where you want the file to be sent to.
    remote_path = "REMOTE_PATH"
    file_to_send = "test_scp.txt"
    expected_file_location = os.path.join(remote_path, file_to_send)

    print(f"Verifying that {file_to_send} was not on the remote device...")
    assert remote_interface_fixture.ssh_exec(f"cat {expected_file_location}") == f"cat: {expected_file_location}: No such file or directory\r\n"
    print(f"{file_to_send} does not exist")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_to_send_path = os.path.join(script_dir, file_to_send)
    remote_interface_fixture.scp_send(file_to_send_path, remote_path)

    print(f"Verifying that {file_to_send} was transferred successfully...")
    assert remote_interface_fixture.ssh_exec(f"cat {expected_file_location}") == "It works!!\r\n"
    print(f"{file_to_send} was transferred successfully")

    print(f"Removing {file_to_send} for the next test...")
    remote_interface_fixture.ssh_exec(f"rm {expected_file_location}")
