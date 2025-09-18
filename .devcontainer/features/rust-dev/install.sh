#!/usr/bin/env bash
set -e

export DEBIAN_FRONTEND=noninteractive

# Get the Rust version from the feature option, default to stable if not set
RUST_VERSION="${RUST_VERSION:-stable}"
# Get the target triples from the feature option
TARGET_TRIPLES="${TARGET_TRIPLES:-thumbv7em-none-eabihf,thumbv8m.main-none-eabihf}"

# Load system info
. /etc/os-release

# Determine base Linux distribution
if [[ "${ID}" != "debian" && ! "${ID_LIKE}" =~ "debian" ]]; then
    echo "Error: Unsupported Linux distribution '${ID}'."
    exit 1
fi

# Install dependencies for Rust
apt-get update -y
apt-get install -y --no-install-recommends build-essential curl clang libclang-dev ca-certificates
rm -rf /var/lib/apt/lists/*

# Set up system-wide Rust installation directories
RUSTUP_HOME="/usr/local/rustup"
CARGO_HOME="/usr/local/cargo"

# Install Rust system-wide
echo "Installing Rust version: ${RUST_VERSION}"
export RUSTUP_HOME="${RUSTUP_HOME}"
export CARGO_HOME="${CARGO_HOME}"
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain "${RUST_VERSION}" --no-modify-path

# Make Rust available system-wide
echo "export RUSTUP_HOME=\"${RUSTUP_HOME}\"" >> /etc/profile.d/rust.sh
echo "export CARGO_HOME=\"${CARGO_HOME}\"" >> /etc/profile.d/rust.sh
echo "export PATH=\"${CARGO_HOME}/bin:\$PATH\"" >> /etc/profile.d/rust.sh
chmod +x /etc/profile.d/rust.sh

# Source the environment for the current session
export PATH="${CARGO_HOME}/bin:$PATH"

# Create symlinks for system-wide access
ln -sf "${CARGO_HOME}/bin/rustc" /usr/local/bin/rustc
ln -sf "${CARGO_HOME}/bin/cargo" /usr/local/bin/cargo
ln -sf "${CARGO_HOME}/bin/rustup" /usr/local/bin/rustup

# Set proper permissions for all users
chmod -R 777 "${RUSTUP_HOME}" "${CARGO_HOME}"

# Install target triples if specified
if [[ -n "${TARGET_TRIPLES}" ]]; then
    echo "Installing Rust target triples: ${TARGET_TRIPLES}"
    IFS=',' read -ra TARGETS <<< "${TARGET_TRIPLES}"
    for target in "${TARGETS[@]}"; do
        target=$(echo "$target" | xargs)  # trim whitespace
        if [[ -n "$target" ]]; then
            echo "Installing target: $target"
            rustup target add "$target"
        fi
    done
fi

echo "Rust installation completed successfully."
