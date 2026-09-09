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
# consult https://docs.docker.com/engine/install/ubuntu/ for more info
if ! command -v docker &> /dev/null; then
  apt-get update 
  apt-get install ca-certificates curl
  install -m 0755 -d /etc/apt/keyrings 
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc 

  tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

fi

# NVIDIA Container Toolkit 
# consult https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html for more info 
if ! dpkg -l | grep -q nvidia-container-toolkit; then
  apt-get update && apt-get install -y --no-install-recommends ca-certificates curl gnupg2 
  curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
  curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
  
  apt-get update 
  export NVIDIA_CONTAINER_TOOLKIT_VERSION=1.20.0-1
  apt-get install -y \
    nvidia-container-toolkit=${NVIDIA_CONTAINER_TOOLKIT_VERSION} \
    nvidia-container-toolkit-base=${NVIDIA_CONTAINER_TOOLKIT_VERSION} \
    libnvidia-container-tools=${NVIDIA_CONTAINER_TOOLKIT_VERSION} \
    libnvidia-container1=${NVIDIA_CONTAINER_TOOLKIT_VERSION}
  
  nvidia-ctk runtime configure --runtime=docker
  systemctl restart docker
fi

# Pull CARLA image (cached after first run 
# consult https://carla.readthedocs.io/en/latest/build_docker/ for more info 
docker pull carlasim/carla:0.9.16