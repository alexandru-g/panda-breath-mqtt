#!/bin/bash
# Copies the source code into the add-on directory for building.
# Run this before adding the add-on repo to HA.

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

rm -rf "$SCRIPT_DIR/panda_breath_mqtt"
cp -r "$REPO_DIR/src/panda_breath_mqtt" "$SCRIPT_DIR/panda_breath_mqtt"

echo "Add-on prepared. Source copied to ha-addon/panda_breath_mqtt/"
