#!/bin/bash
# This program is free software: you can redistribute it under the terms
# of the GNU General Public License, v. 3.0. If a copy of the GNU General
# Public License was not distributed with this file, see <https://www.gnu.org/licenses/>.

SCRIPT_ROOT=$(dirname $(readlink -f "${BASH_SOURCE[0]}"))
PARENT_DIR=$(dirname "$SCRIPT_ROOT")
. "${SCRIPT_ROOT}/common.sh" || exit 1

BRIDGES=(
    "email_bridge=https://github.com/smswithoutborders/email-bridge.git"
)
DEST_DIR="$PARENT_DIR/bridges"

mkdir -p "$DEST_DIR"

for bridge in ${BRIDGES[@]}; do
    IFS='=' read -r bridge_name bridge_url <<<$bridge
    BRIDGE_DIR="${DEST_DIR}/${bridge_name}"

    if [ -d "$BRIDGE_DIR" ]; then
        info "Updating '$bridge_name' ..."
        if ! git -C "$BRIDGE_DIR" pull; then
            error "Failed to update '$bridge_name'."
            continue
        fi
    else
        info "Downloading '$bridge_name' ..."
        if ! git clone "$bridge_url" "$BRIDGE_DIR"; then
            error "Failed to download '$bridge_name'."
            continue
        fi
    fi
done

success "All bridges downloaded successfully."
