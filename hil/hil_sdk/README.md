# EmbedOps HIL SDK

Welcome to the EmbedOps HIL SDK.
This package contains all of the code needed to develop fully-functioning HIL (hardware-in-the-loop) tests for any platform.

This repository contains the source of the SDK; the final deliverable is created using the build_release.py script in the related [hil-sdk-test](https://gitlab.com/dojofive/embedops/hil/hil-sdk-test) repository.
This repository is NOT designed to be simply zipped and sent to the customer, the script must be used to create the release.

## Repository Structure

- `examples`: Fully-functioning example projects
- `interfaces`: Interface classes to common HW and SW modules used by HIL testing

## Create Virtual Python Environment

The creation of a virtual Python environment is recommended.
The following steps will create a virtual Python environment in the root of the repository:

```python
# Navigate to the hil-sdk root
cd <path to hil-sdk>

# Create virtual Python environment
python3 -m venv .venv
```

