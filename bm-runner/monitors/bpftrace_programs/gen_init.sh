#!/bin/bash

mods=""

for file in *.py; do
    # skip __init__.py created by this script
    if [[ $file == *"__init__"* ]]; then
        continue
    fi
    name=$(basename "${file}" .py)
    mods="${mods}, \"${name}\""
done

# remove leading comma
mods="${mods:1}"

echo "__all__ = [${mods}]" > __init__.py