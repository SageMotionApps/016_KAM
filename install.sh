#!/bin/bash

# Detect architecture
ARCH=$(dpkg --print-architecture)

# Update package list
sudo apt-get update

# Install required dependencies based on detected architecture
if [ "$ARCH" = "armhf" ]; then
    sudo apt-get install -y libc6:armhf libgfortran5:armhf libgcc-s1:armhf gcc-12-base:armhf libidn2-0:armhf
elif [ "$ARCH" = "arm64" ]; then
    sudo apt-get install -y libc6:arm64 libgfortran5:arm64 libgcc-s1:arm64 gcc-12-base:arm64 libidn2-0:arm64
else
    echo "Unsupported architecture: $ARCH"
    exit 1
fi

# Fix any broken dependencies
sudo apt-get install -f -y

# Install libopenblas-base package
if [ "$ARCH" = "armhf" ]; then
    sudo dpkg -i libopenblas-base_0.3.5+ds-3+rpi1_armhf.deb
elif [ "$ARCH" = "arm64" ]; then
    sudo dpkg -i libopenblas-base_0.3.5+ds-3+rpi1_arm64.deb
fi

# Fix any broken dependencies again
sudo apt-get install -f -y

# Install libopenblas-dev package
if [ "$ARCH" = "armhf" ]; then
    sudo dpkg -i libopenblas-dev_0.3.5+ds-3+rpi1_armhf.deb
elif [ "$ARCH" = "arm64" ]; then
    sudo dpkg -i libopenblas-dev_0.3.5+ds-3+rpi1_arm64.deb
fi

# Fix any broken dependencies again
sudo apt-get install -f -y
