#
# Copyright (C) 2025, Dojo Five
# All rights reserved.
#
# OpenVPN HIL Test focused on testing OpenVPN connection from DUT

import logging
from pathlib import Path


def test_generate_dut_client_config(request, openvpn_server_fixture, client_config_dir):
    """Generate OpenVPN client configuration for DUT using auto-detected IP"""
    
    dut_client_name = "dut_device"
    
    # Save configuration file for DUT deployment
    config_file_path = openvpn_server_fixture.save_client_config(
        dut_client_name, 
        client_config_dir
    )
    
    # Verify the configuration is suitable for DUT
    config_file = Path(config_file_path)
    assert config_file.exists()
    
    with open(config_file, 'r') as f:
        content = f.read()
        # Verify that remote directive exists (IP will be auto-detected)
        assert "remote " in content
        assert "client" in content
        # Extract the auto-detected IP for logging
        for line in content.split('\n'):
            if line.startswith('remote '):
                detected_ip = line.split()[1]
                logging.info(f"Auto-detected HIL server IP: {detected_ip}")
                break
    
    logging.info(f"DUT client config generated: {config_file_path}")
    
    # Store the config file path in the test session for other tests to use
    request.config.cache.set("dut_config_file_path", config_file_path)
    
    return config_file_path