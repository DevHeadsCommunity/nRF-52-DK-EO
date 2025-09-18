#
# Copyright (C) 2025, Dojo Five
# All rights reserved.
#
# Pure Python OpenVPN Interface for HIL SDK

import os
import shutil
import socket
import socketserver
import subprocess
import tempfile
import threading
import time
from datetime import datetime, timedelta, timezone
from http.server import SimpleHTTPRequestHandler
from pathlib import Path
from typing import Optional, Dict, Any

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption


class OpenVPNInterfaceException(Exception):
    pass


class OpenVPNInterface:
    """Provides a pure Python OpenVPN server interface for HIL testing"""

    DNS_SERVER = "1.1.1.1" # using cloudflare DNS by default
    
    # Pre-generated DH parameters (2048-bit) for faster setup
    # Generated with: openssl dhparam 2048
    DEFAULT_DH_PARAMS = """-----BEGIN DH PARAMETERS-----
MIIBDAKCAQEAquC6usXXCWfqTtOauNkA57JMj9eHqMSf04OM18qhnmwvKn0MClIX
7+ACVyW2xDnmWk+ySJGsZ/yP99O8zkt8g/OjxtX1eAMs3P41EryYBjP1hfdN3210
ysKYLVHTcwB1LY9nyjhWv/jhucWeDzu2YvdtpuIbiWwi9lKupn6ByulI2ZN+Hf70
g39bOeMimT/mv3VyS4atZltXuoHba1MGp7FoVM1FIRLEjn2UL0kPemQEQY1vWujB
Im/rhyFLRBdbyIWIye4KJN5YheYy998ww5rWgXIuWfNOriVGw2BKtBCM1+0WGcsR
+khmx4fda9nCK2QbkAxKLZhLX71spYxjnwIBAgICAOE=
-----END DH PARAMETERS-----"""

    def __init__(self, 
                 server_ip: str = "127.0.0.1",
                 server_port: int = 1194,
                 network: str = "10.8.0.0",
                 netmask: str = "255.255.255.0",
                 work_dir: Optional[str] = None,
                 auto_detect_location: bool = True,
                 country: Optional[str] = None,
                 state: Optional[str] = None,
                 locality: Optional[str] = None):
        """
        Initialize OpenVPN server interface.

        :param server_ip: IP address the server will bind to (use "127.0.0.1" for auto-detection)
        :param server_port: Port the server will listen on
        :param network: VPN network address
        :param netmask: VPN network mask
        :param work_dir: Working directory for certificates and configs
        :param auto_detect_location: Auto-detect location for certificate attributes (default: True)
        :param country: Country code for certificate attributes (overrides auto-detection)
        :param state: State/province for certificate attributes (overrides auto-detection)
        :param locality: City/locality for certificate attributes (overrides auto-detection)
        """
        # Auto-detect local IP if localhost is provided
        if server_ip == "127.0.0.1":
            self.server_ip = self._get_local_ip()
            print(f"Auto-detected server IP: {self.server_ip} (use explicit IP to override)")
        else:
            self.server_ip = server_ip
        self.server_port = server_port
        self.network = network
        self.netmask = netmask
        self.work_dir = Path(work_dir) if work_dir else Path(tempfile.mkdtemp(prefix="openvpn_hil_"))
        
        # Set location information for certificates
        if auto_detect_location and (country is None or state is None or locality is None):
            detected_location = self._detect_location()
            self.country = country or detected_location.get('country', 'XX')
            self.state = state or detected_location.get('state', 'Unknown')
            self.locality = locality or detected_location.get('city', 'Unknown')
        else:
            # Use provided values or fallbacks
            self.country = country or 'XX'
            self.state = state or 'Unknown'
            self.locality = locality or 'Unknown'
        
        print(f"Using certificate location: {self.locality}, {self.state}, {self.country}")
        
        # Ensure work directory exists
        self.work_dir.mkdir(parents=True, exist_ok=True)
        
        # Server process and state
        self.server_process: Optional[subprocess.Popen] = None
        self.is_running = False
        self.http_server: Optional[socketserver.TCPServer] = None
        self.http_thread: Optional[threading.Thread] = None
        self.http_port: int = 8000  # Default port, will be dynamically assigned
        
        # Certificate paths
        self.ca_cert_path = self.work_dir / "ca.crt"
        self.ca_key_path = self.work_dir / "ca.key" 
        self.server_cert_path = self.work_dir / "server.crt"
        self.server_key_path = self.work_dir / "server.key"
        self.dh_path = self.work_dir / "dh.pem"
        self.server_config_path = self.work_dir / "server.conf"
        
        # Generated certificates storage
        self.ca_private_key = None
        self.ca_certificate = None

    def _get_local_ip(self) -> str:
        """Automatically detect the local IP address of the HIL device"""
        try:
            # Create a socket connection to determine the local IP
            # This doesn't actually connect, just determines which interface would be used
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                # Connect to a public DNS server (doesn't send any data)
                s.connect((self.DNS_SERVER, 80))
                local_ip = s.getsockname()[0]
                print(f"Auto-detected local IP address: {local_ip}")
                return local_ip
        except Exception as e:
            print(f"Warning: Could not auto-detect local IP, using fallback method: {e}")
            
            # Fallback method: get hostname IP
            try:
                hostname = socket.gethostname()
                local_ip = socket.gethostbyname(hostname)
                print(f"Using hostname-based IP address: {local_ip}")
                return local_ip
            except Exception as e2:
                print(f"Warning: Hostname method also failed: {e2}")
                
                # Last resort: try to get from network interfaces
                try:
                    # Try to get IP from common network interfaces
                    result = subprocess.run(
                        ["ip", "route", "get", self.DNS_SERVER], 
                        capture_output=True, text=True, timeout=5
                    )
                    if result.returncode == 0:
                        # Parse the output to extract the source IP
                        for line in result.stdout.split('\n'):
                            if 'src' in line:
                                parts = line.split()
                                if 'src' in parts:
                                    src_idx = parts.index('src')
                                    if src_idx + 1 < len(parts):
                                        local_ip = parts[src_idx + 1]
                                        print(f"Using route-based IP address: {local_ip}")
                                        return local_ip
                except Exception as e3:
                    print(f"Route-based detection also failed: {e3}")
                
                # Final fallback
                print("Using localhost as final fallback")
                return "127.0.0.1"

    def _detect_location(self) -> Dict[str, str]:
        """Attempt to detect current geographic location for certificate attributes"""
        location = {'country': 'XX', 'state': 'Unknown', 'city': 'Unknown'}
        
        # Method 1: Try to get location from IP geolocation API
        try:
            import urllib.request
            import json
            
            # Use a simple, free geolocation API (no API key required)
            with urllib.request.urlopen('http://ip-api.com/json', timeout=5) as response:
                data = json.loads(response.read().decode())
                if data.get('status') == 'success':
                    location['country'] = data.get('countryCode', 'XX')
                    location['state'] = data.get('regionName', 'Unknown')
                    location['city'] = data.get('city', 'Unknown')
                    print(f"Detected location via IP geolocation: {location['city']}, {location['state']}, {location['country']}")
                    return location
        except Exception as e:
            print(f"IP geolocation failed: {e}")
        
        # Method 2: Try to detect from system timezone
        try:
            # Read timezone from /etc/timezone (common on Debian/Ubuntu)
            if os.path.exists('/etc/timezone'):
                with open('/etc/timezone', 'r') as f:
                    timezone = f.read().strip()
                    # Parse timezone like "Europe/Oslo" or "America/New_York"
                    if '/' in timezone:
                        parts = timezone.split('/')
                        if len(parts) >= 2:
                            region = parts[0]
                            city = parts[1].replace('_', ' ')
                            
                            # Map common regions to country codes
                            region_to_country = {
                                'Europe': {
                                    'Oslo': 'NO', 'Stockholm': 'SE', 'Copenhagen': 'DK',
                                    'London': 'GB', 'Paris': 'FR', 'Berlin': 'DE',
                                    'Rome': 'IT', 'Madrid': 'ES', 'Amsterdam': 'NL'
                                },
                                'America': {
                                    'New York': 'US', 'Chicago': 'US', 'Denver': 'US',
                                    'Los Angeles': 'US', 'Toronto': 'CA', 'Mexico City': 'MX'
                                },
                                'Asia': {
                                    'Tokyo': 'JP', 'Shanghai': 'CN', 'Seoul': 'KR',
                                    'Singapore': 'SG', 'Bangkok': 'TH', 'Mumbai': 'IN'
                                },
                                'Australia': {
                                    'Sydney': 'AU', 'Melbourne': 'AU', 'Perth': 'AU'
                                }
                            }
                            
                            if region in region_to_country and city in region_to_country[region]:
                                location['country'] = region_to_country[region][city]
                                location['state'] = city  # Use city as state/region
                                location['city'] = city
                                print(f"Detected location from timezone: {city}, {location['country']}")
                                return location
                            
        except Exception as e:
            print(f"Timezone detection failed: {e}")
        
        # Method 3: Try to get from locale/system settings
        try:
            result = subprocess.run(['locale'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                # Look for country info in locale output
                for line in result.stdout.split('\n'):
                    if 'LC_ADDRESS' in line or 'LANG' in line:
                        # Parse locale like "en_US.UTF-8" or "nb_NO.UTF-8"
                        if '=' in line:
                            locale_value = line.split('=')[1].strip('"')
                            if '_' in locale_value:
                                parts = locale_value.split('_')
                                if len(parts) >= 2:
                                    country_code = parts[1].split('.')[0].upper()
                                    if len(country_code) == 2:
                                        location['country'] = country_code
                                        print(f"Detected country from locale: {country_code}")
                                        break
        except Exception as e:
            print(f"Locale detection failed: {e}")
        
        print(f"Using fallback location: {location['city']}, {location['state']}, {location['country']}")
        return location

    def _generate_private_key(self) -> rsa.RSAPrivateKey:
        """Generate RSA private key"""
        return rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

    def _generate_ca_certificate(self) -> None:
        """Generate CA certificate and private key"""
        # Generate CA private key
        self.ca_private_key = self._generate_private_key()
        
        # Create CA certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, self.country),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, self.state),
            x509.NameAttribute(NameOID.LOCALITY_NAME, self.locality),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "HIL Test CA"),
            x509.NameAttribute(NameOID.COMMON_NAME, "HIL Test CA"),
        ])
        
        self.ca_certificate = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            self.ca_private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.now(timezone.utc)
        ).not_valid_after(
            datetime.now(timezone.utc) + timedelta(days=365)
        ).add_extension(
            x509.BasicConstraints(ca=True, path_length=None),
            critical=True,
        ).add_extension(
            x509.KeyUsage(
                key_cert_sign=True,
                crl_sign=True,
                digital_signature=False,
                key_encipherment=False,
                key_agreement=False,
                content_commitment=False,
                data_encipherment=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        ).sign(self.ca_private_key, hashes.SHA256())
        
        # Write CA certificate and key to files
        with open(self.ca_cert_path, "wb") as f:
            f.write(self.ca_certificate.public_bytes(Encoding.PEM))
            
        with open(self.ca_key_path, "wb") as f:
            f.write(self.ca_private_key.private_bytes(
                encoding=Encoding.PEM,
                format=PrivateFormat.PKCS8,
                encryption_algorithm=NoEncryption()
            ))

    def _generate_server_certificate(self) -> None:
        """Generate server certificate"""
        server_private_key = self._generate_private_key()
        
        subject = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, self.country),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, self.state),
            x509.NameAttribute(NameOID.LOCALITY_NAME, self.locality),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "HIL Test Server"),
            x509.NameAttribute(NameOID.COMMON_NAME, "server"),
        ])
        
        server_cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            self.ca_certificate.subject
        ).public_key(
            server_private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.now(timezone.utc)
        ).not_valid_after(
            datetime.now(timezone.utc) + timedelta(days=365)
        ).add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_encipherment=True,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                content_commitment=False,
                data_encipherment=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        ).add_extension(
            x509.ExtendedKeyUsage([
                x509.oid.ExtendedKeyUsageOID.SERVER_AUTH,
            ]),
            critical=True,
        ).sign(self.ca_private_key, hashes.SHA256())
        
        # Write server certificate and key
        with open(self.server_cert_path, "wb") as f:
            f.write(server_cert.public_bytes(Encoding.PEM))
            
        with open(self.server_key_path, "wb") as f:
            f.write(server_private_key.private_bytes(
                encoding=Encoding.PEM,
                format=PrivateFormat.PKCS8,
                encryption_algorithm=NoEncryption()
            ))

    def _generate_dh_params(self, use_default: bool = True) -> None:
        """Generate or use pre-generated Diffie-Hellman parameters
        
        :param use_default: If True, use pre-generated DH params for speed. If False, generate fresh ones.
        """
        if use_default:
            # Use pre-generated DH parameters for faster setup
            with open(self.dh_path, "w") as f:
                f.write(self.DEFAULT_DH_PARAMS)
            print(f"Using pre-generated DH parameters at {self.dh_path}")
        else:
            # Generate fresh DH parameters using OpenSSL (slow but more secure)
            try:
                print("Generating fresh DH parameters (this may take 1-2 minutes)...")
                subprocess.run([
                    "openssl", "dhparam",
                    "-out", str(self.dh_path),
                    "2048"
                ], check=True)
                print(f"Generated fresh DH parameters at {self.dh_path}")
            except subprocess.CalledProcessError as e:
                raise OpenVPNInterfaceException(f"Failed to generate DH parameters: {e}")

    def _create_server_config(self) -> None:
        """Create OpenVPN server configuration file"""
        config = f"""# OpenVPN Server Configuration for HIL Testing
port {self.server_port}
proto udp
dev tun

ca {self.ca_cert_path}
cert {self.server_cert_path}
key {self.server_key_path}
dh {self.dh_path}

server {self.network} {self.netmask}
ifconfig-pool-persist ipp.txt

keepalive 10 120
# Disable compression entirely:
compress stub-v2
persist-key
persist-tun

# Security improvements
data-ciphers AES-256-GCM
tls-version-min 1.2

status openvpn-status.log
log-append openvpn.log
verb 3

# Allow duplicate certificates for testing
duplicate-cn
"""
        
        with open(self.server_config_path, "w") as f:
            f.write(config)

    def get_vpn_ip(self) -> str:
        """Get the server's IP address on the VPN network."""
        # The server is always the first IP in the VPN subnet
        return f"{self.network.rsplit('.', 1)[0]}.1"

    def _start_http_server(self) -> None:
        """Start a simple HTTP server on the VPN network."""
        try:
            # Wait a moment for VPN to stabilize
            time.sleep(2)
            
            # Create a closure to capture the work_dir
            work_dir = self.work_dir
            
            class QuietHTTPRequestHandler(SimpleHTTPRequestHandler):
                def __init__(self, *args, **kwargs):
                    # Serve files from the OpenVPN working directory
                    super().__init__(*args, directory=str(work_dir), **kwargs)
                def log_message(self, format, *args):
                    # Suppress log messages to keep test output clean
                    pass

            vpn_ip = self.get_vpn_ip()
            # Try to bind to port 8000 first, then try random ports if it fails
            for port in [8000, 0]:  # 0 means "find any available port"
                try:
                    self.http_server = socketserver.TCPServer((vpn_ip, port), QuietHTTPRequestHandler)
                    self.http_port = self.http_server.server_address[1]  # Get actual assigned port
                    break
                except OSError as e:
                    if "Address already in use" in str(e) and port == 8000:
                        print(f"Port 8000 in use, trying random port...")
                        continue
                    else:
                        raise

            # Create a test file for the DUT to fetch
            (self.work_dir / "index.html").write_text("Hello from OpenVPN HIL!")

            self.http_thread = threading.Thread(target=self.http_server.serve_forever)
            self.http_thread.daemon = True
            self.http_thread.start()
            print(f"✓ HTTP server started at http://{vpn_ip}:{self.http_port}")

        except Exception as e:
            if "Address already in use" in str(e):
                raise OpenVPNInterfaceException("Failed to start HTTP server: port 8000 is already in use.")
            elif "Cannot assign requested address" in str(e):
                raise OpenVPNInterfaceException(f"Failed to start HTTP server: could not bind to VPN IP {self.get_vpn_ip()}. Is the VPN running?")
            else:
                raise OpenVPNInterfaceException(f"Failed to start HTTP server: {e}")

    def _stop_http_server(self) -> None:
        """Stop the HTTP server."""
        if self.http_server:
            try:
                self.http_server.shutdown()
                self.http_server.server_close()
                if self.http_thread:
                    self.http_thread.join(timeout=5)
            except Exception as e:
                print(f"Warning during HTTP server shutdown: {e}")
            finally:
                self.http_server = None
                self.http_thread = None
                print("HTTP server stopped")
        
        # Additional cleanup: kill any lingering Python HTTP server processes
        try:
            subprocess.run(["pkill", "-f", "HTTPServer"], check=False, capture_output=True)
            # Kill processes using the actual port number (could be 8000 or dynamically assigned)
            subprocess.run(["pkill", "-f", str(self.http_port)], check=False, capture_output=True)
            # Force kill any process using the HTTP port
            subprocess.run(["fuser", "-k", f"{self.http_port}/tcp"], check=False, capture_output=True)
        except:
            pass

    def setup_server(self, generate_fresh_dh: bool = False) -> None:
        """Generate all certificates and configuration files for OpenVPN server
        
        :param generate_fresh_dh: If True, generate fresh DH parameters (slow). If False, use pre-generated ones (fast).
        """
        try:
            print("Generating CA certificate...")
            self._generate_ca_certificate()
            
            print("Generating server certificate...")
            self._generate_server_certificate()
            
            print("Setting up DH parameters...")
            self._generate_dh_params(use_default=not generate_fresh_dh)
            
            print("Creating server configuration...")
            self._create_server_config()
            
            print(f"OpenVPN server setup complete in {self.work_dir}")
            
        except Exception as e:
            raise OpenVPNInterfaceException(f"Failed to setup server: {e}")


    def start_server(self) -> None:
        """Start the OpenVPN server"""
        if self.is_running:
            raise OpenVPNInterfaceException("Server is already running")
            
        if not self.server_config_path.exists():
            raise OpenVPNInterfaceException("Server not set up. Call setup_server() first.")
            
        try:
            print(f"Starting OpenVPN server with config: {self.server_config_path}")
            
            # Start OpenVPN server process
            cmd = ["openvpn", "--config", str(self.server_config_path)]
            
            self.server_process = subprocess.Popen(
                cmd,
                cwd=self.work_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Redirect stderr to stdout
                text=True,
                bufsize=0,  # Unbuffered
                universal_newlines=True
            )
            
            print(f"OpenVPN process started with PID: {self.server_process.pid}")
            
            # Read output in real-time for a few seconds
            import select
            output_lines = []
            start_time = time.time()
            while time.time() - start_time < 5:  # Wait up to 5 seconds
                if self.server_process.poll() is not None:
                    # Process has exited
                    break
                    
                # Try to read any available output
                try:
                    if self.server_process.stdout and select.select([self.server_process.stdout], [], [], 0.1)[0]:
                        line = self.server_process.stdout.readline()
                        if line:
                            print(f"OpenVPN output: {line.strip()}")
                            output_lines.append(line)
                except:
                    pass
                    
                time.sleep(0.1)
            
            # Check if process is still running
            exit_code = self.server_process.poll()
            if exit_code is not None:
                # Process has exited - get remaining output
                remaining_output, _ = self.server_process.communicate()
                if remaining_output:
                    output_lines.append(remaining_output)
                
                all_output = ''.join(output_lines)
                error_msg = f"OpenVPN server exited with code {exit_code}\n"
                error_msg += f"Output: {all_output}\n"
                error_msg += f"Config file: {self.server_config_path}\n"
                
                # Show config file contents for debugging
                try:
                    with open(self.server_config_path, 'r') as f:
                        config_content = f.read()
                        error_msg += f"Config file contents:\n{config_content}\n"
                except:
                    error_msg += "Could not read config file\n"
                
                error_msg += "Common issues:\n"
                error_msg += "- Run with sudo/administrator privileges\n"
                error_msg += "- Check if port is already in use\n"
                error_msg += "- Verify TUN/TAP driver is available\n"
                raise OpenVPNInterfaceException(error_msg)
            
            self.is_running = True
            self._start_http_server()
            print(f"✓ OpenVPN server started successfully on {self.server_ip}:{self.server_port}")
            print(f"✓ VPN network: {self.network}/{self.netmask}")
            print(f"✓ Server PID: {self.server_process.pid}")
            
        except FileNotFoundError:
            raise OpenVPNInterfaceException("OpenVPN binary not found. Install with: sudo apt-get install openvpn")
        except Exception as e:
            if self.server_process:
                self.server_process.terminate()
            raise OpenVPNInterfaceException(f"Failed to start server: {e}")

    def stop_server(self) -> None:
        """Stop the OpenVPN server"""
        if not self.is_running or not self.server_process:
            return
            
        try:
            self.server_process.terminate()
            self.server_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.server_process.kill()
            self.server_process.wait()
        finally:
            self.server_process = None
            self.is_running = False
            self._stop_http_server()
            print("OpenVPN server stopped")

    def generate_client_config(self, client_name: str, server_address: Optional[str] = None) -> str:
        """
        Generate client configuration that can connect to the OpenVPN server.
        
        :param client_name: Name for the client certificate
        :param server_address: Server address for client config (auto-detected if not provided)
        :return: Client configuration as string
        """
        if not self.ca_certificate or not self.ca_private_key:
            raise OpenVPNInterfaceException("CA not initialized. Call setup_server() first.")
        
        # Use provided server address, or use the server IP (already auto-detected in __init__)
        if server_address:
            server_addr = server_address
        else:
            # Use the server IP that was set during initialization
            server_addr = self.server_ip
            print(f"Using server IP {server_addr} for client configuration")
        
        # Generate client private key
        client_private_key = self._generate_private_key()
        
        # Generate client certificate
        subject = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, self.country),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, self.state),
            x509.NameAttribute(NameOID.LOCALITY_NAME, self.locality),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "HIL Test Client"),
            x509.NameAttribute(NameOID.COMMON_NAME, client_name),
        ])
        
        client_cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            self.ca_certificate.subject
        ).public_key(
            client_private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.now(timezone.utc)
        ).not_valid_after(
            datetime.now(timezone.utc) + timedelta(days=365)
        ).add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_encipherment=True,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                content_commitment=False,
                data_encipherment=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        ).add_extension(
            x509.ExtendedKeyUsage([
                x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH,
            ]),
            critical=True,
        ).sign(self.ca_private_key, hashes.SHA256())
        
        # Create client configuration
        ca_cert_pem = self.ca_certificate.public_bytes(Encoding.PEM).decode('utf-8')
        client_cert_pem = client_cert.public_bytes(Encoding.PEM).decode('utf-8')
        client_key_pem = client_private_key.private_bytes(
            encoding=Encoding.PEM,
            format=PrivateFormat.PKCS8,
            encryption_algorithm=NoEncryption()
        ).decode('utf-8')
        
        client_config = f"""# OpenVPN Client Configuration for HIL Testing
client
dev tun
proto udp
remote {server_addr} {self.server_port}
resolv-retry infinite
nobind
persist-key
persist-tun

# Security settings to match server
data-ciphers AES-256-GCM
tls-version-min 1.2

# Modern compression (matches server)
compress stub-v2

verb 3

<ca>
{ca_cert_pem}</ca>

<cert>
{client_cert_pem}</cert>

<key>
{client_key_pem}</key>
"""
        
        return client_config

    def save_client_config(self, client_name: str, output_path: str, server_address: Optional[str] = None) -> str:
        """
        Generate and save client configuration to file.
        
        :param client_name: Name for the client certificate
        :param output_path: Path to save the client configuration
        :param server_address: Server address for client config
        :return: Path to saved configuration file
        """
        config = self.generate_client_config(client_name, server_address)
        
        config_file = Path(output_path) / f"{client_name}.ovpn"
        with open(config_file, "w") as f:
            f.write(config)
            
        print(f"Client configuration saved to {config_file}")
        return str(config_file)

    def get_http_url(self) -> str:
        """Get the HTTP server URL."""
        return f"http://{self.get_vpn_ip()}:{self.http_port}"

    def get_server_info(self) -> Dict[str, Any]:
        """Get server information"""
        return {
            "server_ip": self.server_ip,
            "server_port": self.server_port,
            "network": self.network,
            "netmask": self.netmask,
            "is_running": self.is_running,
            "work_dir": str(self.work_dir),
            "config_path": str(self.server_config_path),
            "http_port": self.http_port,
            "http_url": self.get_http_url() if self.is_running else None
        }

    def cleanup(self) -> None:
        """Clean up server resources"""
        try:
            self.stop_server()
            
            # Remove work directory and all contents
            if self.work_dir and self.work_dir.exists():
                shutil.rmtree(self.work_dir, ignore_errors=True)
                print(f"Removed OpenVPN work directory: {self.work_dir}")
                
        except Exception as e:
            print(f"Warning: Cleanup failed: {e}")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()
