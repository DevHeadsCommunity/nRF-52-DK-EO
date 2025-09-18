import os
import pytest
import logging
import tempfile
import time
import shutil

from hil_sdk.version import __version__
from hil_sdk.interfaces.openvpn import OpenVPNInterface, OpenVPNInterfaceException

@pytest.fixture(autouse=True, scope="session")
def hil_version_fixture():
    logging.info(f"HIL SDK version {__version__}")

@pytest.fixture(scope="session")
def openvpn_work_dir():
    """Create a temporary directory for OpenVPN test files"""
    temp_dir = tempfile.mkdtemp(prefix="hil_openvpn_test_")
    logging.info(f"Using OpenVPN work directory: {temp_dir}")
    yield temp_dir
    # Cleanup is handled by the OpenVPN interface

@pytest.fixture(scope="session")
def openvpn_server_fixture(hil_version_fixture, openvpn_work_dir):
    """
    Set up and start OpenVPN server for testing.
    This fixture runs once per test session.
    """
    logging.info("Setting up OpenVPN server...")
    
    # Create OpenVPN interface with test configuration
    openvpn = OpenVPNInterface(
        server_ip="127.0.0.1",
        server_port=11194,  # Use non-standard port to avoid conflicts
        network="10.9.0.0",
        netmask="255.255.255.0",
        work_dir=openvpn_work_dir
    )
    
    try:
        # Setup server certificates and configuration
        openvpn.setup_server()
        
        # Start the server
        openvpn.start_server()
        
        # Give server time to fully initialize
        # Poll server status until ready or timeout
        max_attempts = 10
        for _ in range(max_attempts):
            if openvpn.is_running:
                break
            time.sleep(1)
        else:
            raise OpenVPNInterfaceException("Server failed to start within timeout")

        
        logging.info("OpenVPN server started successfully")
        
        yield openvpn
        
    except Exception as e:
        logging.error(f"Failed to setup OpenVPN server: {e}")
        raise
    finally:
        # Cleanup HIL gateway
        logging.info("Cleaning up HIL gateway...")
        try:
            openvpn.cleanup()
        except Exception as e:
            logging.warning(f"HIL gateway cleanup failed: {e}")

@pytest.fixture(scope="session")
def client_config_dir():
    """Create a temporary directory for client configuration files"""
    temp_dir = tempfile.mkdtemp(prefix="hil_openvpn_client_")
    logging.info(f"Using client config directory: {temp_dir}")
    yield temp_dir
    # Cleanup client config directory after all tests
    try:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
            logging.info(f"Removed client config directory: {temp_dir}")
    except Exception as e:
        logging.warning(f"Client config directory cleanup failed: {e}")