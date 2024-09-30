#!/bin/bash
# This program is free software: you can redistribute it under the terms
# of the GNU General Public License, v. 3.0. If a copy of the GNU General
# Public License was not distributed with this file, see <https://www.gnu.org/licenses/>.

SCRIPT_ROOT=$(dirname $(readlink -f "${BASH_SOURCE[0]}"))
PARENT_DIR=$(dirname "$SCRIPT_ROOT")
. "${SCRIPT_ROOT}/common.sh" || exit 1

VENV_NAME="$PARENT_DIR/venv"
ENV_FILE="$PARENT_DIR/.env"

if [[ -d "$VENV_NAME" ]]; then
    warn "The virtual environment '${VENV_NAME}' already exists. Activating it now..."
else
    info "Creating virtual environment '${VENV_NAME}'..."
    python3 -m venv "$VENV_NAME"

    if [[ $? -ne 0 ]]; then
        error "Failed to create virtual environment '${VENV_NAME}'."
        exit 1
    fi
fi

source "$VENV_NAME/bin/activate"
success "Virtual environment '${VENV_NAME}' is now activated."
warn "To deactivate, run: deactivate"

if [[ -f "$ENV_FILE" ]]; then
    info "Exporting environment variables from '${ENV_FILE}'..."

    while IFS= read -r line; do
        if [[ ! -z "$line" && "$line" != \#* ]]; then
            export "$line"
            success "Exported: ${line}"
        fi
    done <"$ENV_FILE"
else
    warn "No .env file found. Skipping environment variable export."
fi
