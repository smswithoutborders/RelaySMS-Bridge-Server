#!/bin/bash
# This program is free software: you can redistribute it under the terms
# of the GNU General Public License, v. 3.0. If a copy of the GNU General
# Public License was not distributed with this file, see <https://www.gnu.org/licenses/>.

SCRIPT_ROOT=$(dirname $(readlink -f "${BASH_SOURCE[0]}"))
PARENT_DIR=$(dirname "$SCRIPT_ROOT")
. "${SCRIPT_ROOT}/common.sh" || exit 1

PROTO_BASE_DIR="$PARENT_DIR/protos"
PROTO_FILE="${1:-}"
VERSION="${2:-}"

declare -A PROTO_FILES=(
    ["vault.proto"]="https://raw.githubusercontent.com/smswithoutborders/SMSwithoutborders-BE/refs/heads/main/protos/v1/vault.proto"
)

if [[ -z "$PROTO_FILE" || -z "$VERSION" ]]; then
    error "Both proto file name and version are required."
    exit 1
fi

extract_version_from_url() {
    local url="$1"
    if [[ "$url" =~ /protos/(v[0-9]+)/ ]]; then
        echo "${BASH_REMATCH[1]}"
    else
        error "Failed to extract version from URL."
        exit 1
    fi
}

download_proto_file() {
    local file_name="$1"
    local file_url="$2"

    VERSION_DIR="$PROTO_BASE_DIR/$VERSION"
    mkdir -p "$VERSION_DIR"
    OUTPUT_FILE="$VERSION_DIR/$file_name"

    info "Downloading $file_name from GitHub..."
    curl -s -o "$OUTPUT_FILE" "$file_url"

    if [[ $? -ne 0 ]]; then
        error "Failed to download $file_name."
        exit 1
    else
        success "$file_name downloaded successfully to '$OUTPUT_FILE'."
    fi
}

list_available_versions() {
    info "Available versions:"
    for url in "${PROTO_FILES[@]}"; do
        extracted_version=$(extract_version_from_url "$url")
        info "- $extracted_version"
    done
}

if [[ -v "PROTO_FILES[$PROTO_FILE]" ]]; then
    file_url="${PROTO_FILES[$PROTO_FILE]}"
    url_version=$(extract_version_from_url "$file_url")

    if [[ "$VERSION" == "$url_version" ]]; then
        download_proto_file "$PROTO_FILE" "$file_url"
    else
        warn "No URL found for version '$VERSION'."
        list_available_versions
        exit 1
    fi
else
    error "Proto file '$PROTO_FILE' not found in the list."
    exit 1
fi

success "Download process completed."
