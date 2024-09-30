#!/bin/bash
# This program is free software: you can redistribute it under the terms
# of the GNU General Public License, v. 3.0. If a copy of the GNU General
# Public License was not distributed with this file, see <https://www.gnu.org/licenses/>.

SCRIPT_ROOT=$(dirname $(readlink -f "${BASH_SOURCE[0]}"))
. "${SCRIPT_ROOT}/common.sh" || exit 1

install_package() {
	package_name=$1

	info "Installing package '${package_name}'..."
	pip install "$package_name"

	if [[ $? -eq 0 ]]; then
		package_info=$(pip freeze | grep "$package_name==")
		success "Installed package '${package_info}' successfully."

		if [[ ! -f requirements.txt ]]; then
			warn "requirements.txt not found. Creating a new one."
			touch requirements.txt
		fi

		if ! grep -q "$package_info" requirements.txt; then
			echo "$package_info" >>requirements.txt
			success "Added '${package_info}' to requirements.txt."
		else
			warn "'${package_info}' is already listed in requirements.txt."
		fi
	else
		error "Failed to install package '${package_name}'."
	fi
}

if [[ $# -eq 0 ]]; then
	error "Please provide package names to install."
	exit 1
fi

for package in "$@"; do
	install_package "$package"
done

sort -o requirements.txt requirements.txt
success "Sorted requirements.txt in alphabetical order."
