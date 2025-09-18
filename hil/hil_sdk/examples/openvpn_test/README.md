# OpenVPN HIL Test Example

This example demonstrates how to use the OpenVPN interface for HIL testing.

## Prerequisites

On Debian/Ubuntu systems, install OpenVPN:
```bash
sudo apt-get install openvpn
```

## What This Example Does

1. **Sets up an OpenVPN server** - Creates CA certificate, server certificate, and configuration
2. **Starts the OpenVPN server** - Launches the server process
3. **Generates client configuration** - Creates a .ovpn file that clients can use to connect

## Use Cases

This OpenVPN interface can be used for:
- Testing network connectivity in isolated environments
- Simulating VPN connections for IoT devices
- Creating secure tunnels for HIL test communication
- Testing VPN client behavior on embedded devices

## Security Note

The certificates generated in this example are for testing purposes only and use default test values. Do not use in production environments.
