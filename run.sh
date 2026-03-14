#!/usr/bin/env bash
# RawriisSTT — source launcher for Linux
# Run: bash run.sh
python3 launcher.py
if [ $? -ne 0 ]; then
    echo
    echo "Failed to start. Make sure Python 3.10+ is installed and on your PATH."
    exit 1
fi
