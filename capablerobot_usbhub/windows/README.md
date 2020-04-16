# libusb Binaries for Windows

## Overview

libusb is a C library that provides generic access to USB devices. It is intended to be used by developers to facilitate the production of applications that communicate with USB hardware.

- It is portable: Using a single cross-platform API, it provides access to USB devices on Linux, macOS, Windows, etc.
- It is user-mode: No special privilege or elevation is required for the application to communicate with a device.
- It is version-agnostic: All versions of the USB protocol, from 1.0 to 3.1 (latest), are supported.

## This Directory

This directory contains Windows binaries (32 and 64 bit) of libusb.  They are packaged with this  driver so that end-users do not need to install them into their Windows installations.  The driver detects when it is running on Windows and specifies these DLLs as the libusb backend for the pyusb library.

DLLs were downloaded from https://libusb.info and are version 1.0.23.