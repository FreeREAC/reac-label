# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>

"""reac-label — label reac-aes67's AES67 channels with Roland mixer names.

Query a Roland V-Mixer over its remote-control protocol (TCP 8023) and build a
REAC-slot -> channel-name table, supplying the slot<->channel<->name patch
mapping that the passive REAC tap does not decode.

Scope: a desk-mastered REAC segment. The M-5000 answers the protocol but returns
an empty input/output patch, so no table can be built for it over this port; and
where reac-pw masters the segment the console session already owns the patch and
the names.
"""

