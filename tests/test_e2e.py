# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>

"""End-to-end: client queries the mixer simulator over a real TCP socket and
produces a slot->name table. Proves query -> parse -> join with no hardware."""
import unittest
from reaclabel.simulator import MixerSim
from reaclabel.client import scan_labels


class TestEndToEnd(unittest.TestCase):
    def setUp(self):
        # a small 4-channel desk: names + REAC-A input patch, one output patch.
        self.sim = MixerSim(
            names={"I1": "Kick  ", "I2": "Snare ", "I3": "Vocal1", "I4": "      ",
                   "AX1": "SingFB"},
            in_patch={"I1": "RAI1", "I2": "RAI2", "I3": "RAI22", "I4": "OFF"},
            out_patch={"RAO1": "AX1"},
        )
        self.port = self.sim.start()

    def tearDown(self):
        self.sim.stop()

    def test_scan_builds_slot_to_name(self):
        # scan inputs I1..I4 and output slots RAO1..RAO1
        table = scan_labels("127.0.0.1", self.port,
                            input_channels=["I1", "I2", "I3", "I4"],
                            output_slots=["RAO1"])
        self.assertEqual(table["RAI1"], "Kick")
        self.assertEqual(table["RAI2"], "Snare")
        self.assertEqual(table["RAI22"], "Vocal1")
        # I4 is patched OFF -> no slot label
        self.assertNotIn("OFF", table)
        # output slot RAO1 sourced from AX1 "SingFB"
        self.assertEqual(table["RAO1"], "SingFB")

    def test_version_handshake(self):
        from reaclabel.client import MixerClient
        c = MixerClient("127.0.0.1", self.port)
        c.connect()
        self.assertTrue(c.version().startswith("1.010"))
        c.close()


if __name__ == "__main__":
    unittest.main()
