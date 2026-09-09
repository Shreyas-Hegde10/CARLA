#!/bin/bash
set -e

# NVIDIA driver: compute-only, headless install (official NVIDIA method)
# consult https://docs.nvidia.com/datacenter/tesla/driver-installation-guide/ubuntu.html for more info 
if ! command -v nvidia-smi &> /dev/null; then
  apt-get update
  apt-get install -y linux-headers-$(uname -r) wget

  # Enroll NVIDIA's CUDA repo signing key
  wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
  dpkg -i cuda-keyring_1.1-1_all.deb
  apt-get update

  # Compute-only install: no GL/EGL/Vulkan/X desktop packages, just what CARLA's
  # -RenderOffScreen mode needs for CUDA + rendering-to-buffer.
  apt-get install -y libnvidia-compute nvidia-dkms-open

  echo "NVIDIA driver installed. A reboot is required before nvidia-smi will work."
  # Compute Engine will re-run this script on next boot; nvidia-smi check below
  # will simply pass on that next run once the kernel module is loaded.
  reboot
fi

# Docker
if ! command -v docker &> /dev/null; then
  curl -fsSL https://get.docker.com | sh
fi

# NVIDIA Container Toolkit
if ! dpkg -l | grep -q nvidia-container-toolkit; then
  curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
  curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
  apt-get update
  apt-get install -y nvidia-container-toolkit
  nvidia-ctk runtime configure --runtime=docker
  systemctl restart docker
fi

# Pull CARLA image (cached after first run
docker pull carlasim/carla:0.9.15