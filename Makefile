# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>

test:
	python3 -m unittest discover tests -v
demo:
	python3 -m reaclabel --sim
.PHONY: test demo
