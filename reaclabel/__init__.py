# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>

"""reac-label — label reac-aes67's AES67 channels with Roland mixer names.

Query a Roland V-Mixer / M-5000 over its remote-control protocol (TCP 8023) and
build a REAC-slot -> channel-name table, supplying the slot<->channel<->name
patch mapping that a passive REAC tap cannot see.
"""

