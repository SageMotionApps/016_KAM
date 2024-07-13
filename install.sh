#!/bin/bash

# Update package list
sudo apt-get update

# Ensure multi-architecture support
sudo dpkg --add-architecture armhf
sudo apt-get update

# Install required dependencies for armhf architecture
sudo apt-get install -y libc6:armhf libgfortran5:armhf libgcc-s1:armhf gcc-12-base:armhf libidn2-0:armhf

# Fix any broken dependencies
sudo apt-get install -f -y

# Install libopenblas-base package for armhf
sudo dpkg -i libopenblas-base_0.3.5+ds-3+rpi1_armhf.deb

# Fix any broken dependencies again
sudo apt-get install -f -y

# Install libopenblas-dev package for armhf
sudo dpkg -i libopenblas-dev_0.3.5+ds-3+rpi1_armhf.deb

# Fix any broken dependencies again
sudo apt-get install -f -y
