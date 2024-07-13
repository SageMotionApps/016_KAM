#!/bin/bash

# Update package list
sudo apt-get update

# Install dependencies with the correct architecture
sudo apt-get install -y libc6:armhf libgfortran5:armhf

# Fix any broken dependencies
sudo apt-get install -f -y

# Install libopenblas-base package
sudo dpkg -i libopenblas-base_0.3.5+ds-3+rpi1_armhf.deb

# Fix any broken dependencies again
sudo apt-get install -f -y

# Install libopenblas-dev package
sudo dpkg -i libopenblas-dev_0.3.5+ds-3+rpi1_armhf.deb

# Fix any broken dependencies again
sudo apt-get install -f -y
