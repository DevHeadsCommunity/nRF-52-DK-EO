#!/usr/bin/env bash
set -e

# Restart device with BOOT0 pin high to enter DFU mode
dfu-util -d 0483:df11 -a 0 -s 0x08000000:leave -D app/build/zephyr/zephyr.bin