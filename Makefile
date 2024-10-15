# This program is free software: you can redistribute it under the terms
# of the GNU General Public License, v. 3.0. If a copy of the GNU General
# Public License was not distributed with this file, see <https://www.gnu.org/licenses/>.

PYTHON := python3
VERSION ?= v1

.PHONY: all setup install_packages download_bridges download_protos compile_protos clean

all: setup

setup: download_bridges download_protos compile_protos

install_packages:
	@./scripts/install_packages.sh $(filter-out $@,$(MAKECMDGOALS))

download_bridges:
	@$(PYTHON) -m scripts.download_bridges

download_protos:
	@./scripts/download_protos.sh vault.proto $(VERSION)

compile_protos:
	@./scripts/compile_protos.sh $(VERSION)

clean:
	rm -f *_pb2_grpc.py
	rm -f *_pb2.py
	rm -f *_pb2.pyi

%:
	@: