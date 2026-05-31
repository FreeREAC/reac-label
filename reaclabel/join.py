# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>

"""Slot -> name join — the core value of reac-label.

The mixer exposes channel->slot (PIS: I22 -> RAI22) and channel->name
(CNS: I1 -> "Kick"). We invert and join into slot->name, keyed on the
RAI<n>/RAO<n> token, which is exactly the REAC slot index reac-aes67's passive
tap keys on. Pure: feed it observed values, read the table.
"""


class LabelJoin:
    def __init__(self):
        self._name = {}          # channel id -> name (raw, may be padded/blank)
        self._patch = {}         # channel id -> input slot token (RAIn/RBIn/OFF)
        self._out_patch = {}     # output slot token (RAOn) -> source channel id

    def observe_name(self, channel, name):
        self._name[channel] = name

    def observe_patch(self, channel, slot):
        """Input patch: channel <- input slot (e.g. I22 <- RAI22)."""
        self._patch[channel] = slot

    def observe_output_patch(self, slot, source):
        """Output patch: REAC output slot <- source channel (e.g. RAO1 <- AX1)."""
        self._out_patch[slot] = source

    @staticmethod
    def _label_for(channel, name):
        """Trim the fixed-width mixer name; fall back to the channel id if the
        name is blank/absent."""
        if name is not None:
            trimmed = name.rstrip()
            if trimmed:
                return trimmed
        return channel

    def slot_to_name(self):
        """Build {slot_token: label}. Input slots from the input patch;
        output slots from the output patch joined via their source channel."""
        out = {}
        # input slots: channel -> slot, label from the channel's name
        for channel, slot in self._patch.items():
            if not slot or slot == "OFF":
                continue
            out[slot] = self._label_for(channel, self._name.get(channel))
        # output slots: slot -> source channel, label from the source's name
        for slot, source in self._out_patch.items():
            if not source or source == "OFF":
                continue
            out[slot] = self._label_for(source, self._name.get(source))
        return out
