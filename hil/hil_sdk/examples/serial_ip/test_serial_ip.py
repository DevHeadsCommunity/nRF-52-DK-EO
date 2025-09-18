#
# Copyright (C) 2025, Dojo Five
# All rights reserved.
#

import logging
import time

logging.basicConfig(level=logging.INFO)

def test_serial_ip(serial_interface_fixture, tcp_server_fixture):

    #
    # Note: This is where you would configure your DUT, if needed.
    #

    logging.info(f"Connecting to a TCP client...")
    tcp_server_fixture.connect()

    try:
        message_to_send_via_serial = b'ping'
        logging.info(f"Sending {message_to_send_via_serial.decode('utf-8')} via serial...")
        serial_interface_fixture.write(message_to_send_via_serial)
        time.sleep(1)

        message_received_via_tcp = tcp_server_fixture.receive()
        assert message_received_via_tcp == message_to_send_via_serial
        logging.info(f"Received {message_received_via_tcp.decode('utf-8')} via TCP")
        time.sleep(1)

        message_to_send_via_tcp = b'pong'
        MSG_TO_RECEIVE_STR_LEN = len(message_to_send_via_tcp)
        logging.info(f"Sending {message_to_send_via_tcp.decode('utf-8')} via TCP...")
        tcp_server_fixture.send(message_to_send_via_tcp)
        time.sleep(1)

        message_received_via_serial = serial_interface_fixture.read(MSG_TO_RECEIVE_STR_LEN)
        assert len(message_received_via_serial) == MSG_TO_RECEIVE_STR_LEN
        assert message_received_via_serial == message_to_send_via_tcp
        logging.info(f"Received {bytes.decode(message_received_via_serial).strip()} via serial")
    finally:
        serial_interface_fixture.flush_output()
