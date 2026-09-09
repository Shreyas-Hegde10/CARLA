# CARLA

## Purpose
This repository contains code for running the CARLA autonomous driving simulator on a Google Cloud Compute Engine GPU instance, controlled remotely from a laptop that has no NVIDIA GPU of its own. The CARLA server runs headless(which means no 3D display) in Docker on a cloud VM. The lightweight Python client runs locally and connects over an SSH tunnel to the VM.  


