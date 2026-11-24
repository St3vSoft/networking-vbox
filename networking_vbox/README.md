# Building the Debian Package

This document describes how to build the `networking-virtualbox` Debian package for OpenStack Neutron on Ubuntu 26.10 LTS.

The package installs the VirtualBox ML2 mechanism driver into the system Python environment without requiring modifications to Ubuntu-managed Python packages through pip.

## 1\. Requirements

Install the required tools:

```bash
sudo apt update
sudo apt install -y dpkg-dev python3
```

Verify the Debian package builder:

```bash
dpkg-deb --version
```

## 2\. Package structure

The Debian package uses the following directory structure:

```text
networking-vbox/
├── DEBIAN/
│   └── control
└── usr/
    └── lib/
        └── python3/
            └── dist-packages/
                ├── networking_vbox/
                │   ├── __init__.py
                │   ├── mechanism_driver.py
                │   ├── config.py
                │   └── common/
                │       ├── __init__.py
                │       ├── network_mapping.py
                │       └── vmrest_client.py
                └── networking_virtualbox-1.0.x.dist-info/
                    ├── METADATA
                    ├── WHEEL
                    ├── RECORD
                    ├── top_level.txt
                    └── entry_points.txt
```

The `DEBIAN/control` file contains the package metadata and dependency declarations.

The `networking_vbox` directory contains the Python implementation of the mechanism driver.

The `.dist-info` directory contains the Python distribution metadata, including the plugin entry points used for driver discovery.

## 3\. Package control file

Example `DEBIAN/control`:


```text
Package: networking-virtualbox
Version: 1.0.x
Section: net
Priority: optional
Architecture: all
Maintainer: St3vSoft
Depends: python3, python3-neutron, python3-neutron-lib
Description: VirtualBox ML2 mechanism driver for OpenStack Neutron
 Integrates VirtualBox-based networking with OpenStack Neutron.
```

Adjust dependencies according to the actual runtime requirements of the driver.

## 4\. Build the Debian package

From the repository root directory, run:

```bash
dpkg-deb --build \
    networking_vbox/deb \
    networking-virtualbox_1.0.x_all.deb
```

The resulting Debian package will be:

```text
networking-virtualbox_1.0.x_all.deb
```

## 5\. Validate the package

Inspect package metadata:

bash

```bash
dpkg-deb --info networking-virtualbox_1.0.x_all.deb
```

Inspect installed files:

```bash
dpkg-deb --contents networking-virtualbox_1.0.x_all.deb
```

Check the package architecture:

```bash
dpkg-deb -f networking-virtualbox_1.0.x_all.deb Architecture
```

Expected output:

```text
all
```

## 6\. Install the package

Install using APT:

```bash
sudo apt install ./networking-virtualbox_1.0.x_all.deb
```

Alternatively, use dpkg:

```bash
sudo dpkg -i networking-virtualbox_1.0.x_all.deb
```

APT is recommended because it can resolve dependencies from configured repositories.

## 7\. Verify installation

Check that the Python module is available:

```bash
python3 -c "import networking_vbox; print(networking_vbox.__file__)"
```

Verify the mechanism driver module:

```bash
python3 -c "import networking_vbox.mechanism_driver"
```

Check that the Python distribution metadata is recognized:

```bash
python3 -c "from importlib.metadata import distribution; print(distribution('networking-virtualbox').entry_points)"
```

## 8\. Uninstall

Remove the package:

```bash
sudo apt remove networking-virtualbox
```

## 9\. Important notes

- The package is architecture-independent (`Architecture: all`).
- The package targets Ubuntu 26.10 LTS and its system Python environment.
- Do not install or upgrade the driver using pip into the system Python environment.
- Preserve the `.dist-info` directory and its `entry_points.txt` file.
- Test the package against the target OpenStack and Neutron versions before production deployment.
- Ensure the mechanism driver is correctly configured in the Neutron ML2 configuration.

## Project

Source code and releases:

https://github.com/St3vSoft/networking-vbox

Maintainer: St3vSoft
