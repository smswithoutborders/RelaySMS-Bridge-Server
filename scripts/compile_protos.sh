#!/bin/bash
# This program is free software: you can redistribute it under the terms
# of the GNU General Public License, v. 3.0. If a copy of the GNU General
# Public License was not distributed with this file, see <https://www.gnu.org/licenses/>.

SCRIPT_ROOT=$(dirname $(readlink -f "${BASH_SOURCE[0]}"))
PARENT_DIR=$(dirname "$SCRIPT_ROOT")
. "${SCRIPT_ROOT}/common.sh" || exit 1

PROTO_BASE_DIR="$PARENT_DIR/protos"
OUTPUT_DIR="$PARENT_DIR/."

VERSION="${1:-latest}"

if [[ ! -d "$PROTO_BASE_DIR" ]]; then
    error "Directory '$PROTO_BASE_DIR' does not exist."
    exit 1
fi

get_latest_version() {
    local latest_version=""
    for dir in "$PROTO_BASE_DIR"/*; do
        if [[ -d "$dir" ]]; then
            version=$(basename "$dir")
            if [[ "$version" =~ ^v[0-9]+$ ]]; then
                if [[ -z "$latest_version" || "$(printf '%s\n' "$version" "$latest_version" | sort -V | tail -n1)" == "$version" ]]; then
                    latest_version="$version"
                fi
            fi
        fi
    done
    echo "$latest_version"
}

if [[ "$VERSION" == "latest" ]]; then
    VERSION=$(get_latest_version)
    if [[ -z "$VERSION" ]]; then
        error "No valid versions found in '$PROTO_BASE_DIR'."
        exit 1
    fi
    info "Using the latest version: '$VERSION'"
fi

VERSION_DIR="$PROTO_BASE_DIR/$VERSION"

if [[ ! -d "$VERSION_DIR" ]]; then
    error "Version directory '$VERSION_DIR' does not exist."
    exit 1
fi

info "Compiling Protocol Buffers in '$VERSION_DIR'..."

python3 -m grpc_tools.protoc \
    -I"$VERSION_DIR" \
    --python_out="$OUTPUT_DIR" \
    --pyi_out="$OUTPUT_DIR" \
    --grpc_python_out="$OUTPUT_DIR" \
    "$VERSION_DIR"/*.proto

if [[ $? -ne 0 ]]; then
    error "Failed to compile Protocol Buffers in '$VERSION_DIR'."
    exit 1
fi

success "All Protocol Buffers compiled successfully."
