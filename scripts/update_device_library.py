#!/usr/bin/env python3
"""Load latest Netbox devicetype-library."""

from os import walk, path
import yaml
from yaml.loader import SafeLoader

SRC_DIR = "../devicetype-library/device-types"
DST_DIR = "netdoc/library/"

if not path.isdir(SRC_DIR):
    print("Clone git repository with the following command:")
    print("git clone https://github.com/netbox-community/devicetype-library/ ..")

for dirpath, dirnames, filenames in walk(SRC_DIR):  # pylint: disable=unused-variable
    if not (dirpath and not dirnames and filenames):
        # Not in a vendor directory
        continue

    keywords = []
    models = []
    manufacturer = None

    for model_file in filenames:
        # Reading all models
        print(f"Reading {model_file}...")
        model_filepath = f"{dirpath}/{model_file}"
        with open(model_filepath) as fh:
            data = yaml.load(fh, Loader=SafeLoader)
        if data.get("model"):
            keywords.append(data.get("model"))
        if data.get("part_number"):
            keywords.append(data.get("part_number"))
        models.append(data)
        if not manufacturer:
            manufacturer = data.get("manufacturer")

    # Save
    with open(f"{DST_DIR}/{manufacturer}.yml", "w", encoding="utf-8") as fh:
        fh.write(
            yaml.dump(
                {
                    "keywords": keywords,
                    "models": models,
                }
            )
        )
