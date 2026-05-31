"""Tests for the slot->name join (the core value).

PIS gives channel->slot (I22 -> RAI22); CNS gives channel->name. We invert+join
to slot->name so reac-aes67 can label the AES67 channel for REAC slot N.
"""
import unittest
from reaclabel.join import LabelJoin


class TestJoin(unittest.TestCase):
    def test_basic_join(self):
        j = LabelJoin()
        j.observe_name("I1", "Kick")
        j.observe_patch("I1", "RAI1")
        j.observe_name("I22", "Vocal1")
        j.observe_patch("I22", "RAI22")
        m = j.slot_to_name()
        self.assertEqual(m["RAI1"], "Kick")
        self.assertEqual(m["RAI22"], "Vocal1")

    def test_unpatched_channel_excluded(self):
        # a channel patched to OFF contributes no slot label
        j = LabelJoin()
        j.observe_name("I3", "Spare")
        j.observe_patch("I3", "OFF")
        self.assertNotIn("OFF", j.slot_to_name())
        self.assertEqual(j.slot_to_name(), {})

    def test_reac_b_slots(self):
        j = LabelJoin()
        j.observe_name("I5", "Gtr")
        j.observe_patch("I5", "RBI5")  # REAC B input
        self.assertEqual(j.slot_to_name()["RBI5"], "Gtr")

    def test_output_patch_join(self):
        # POS gives output-slot -> source; we can label REAC OUT slots too
        j = LabelJoin()
        j.observe_name("AX1", "SingFB")
        j.observe_output_patch("RAO1", "AX1")
        self.assertEqual(j.slot_to_name()["RAO1"], "SingFB")

    def test_name_trailing_space_trimmed_for_label(self):
        # mixer names are fixed 6 chars; trim trailing pad for a clean label
        j = LabelJoin()
        j.observe_name("I1", "BASS  ")
        j.observe_patch("I1", "RAI1")
        self.assertEqual(j.slot_to_name()["RAI1"], "BASS")

    def test_patch_without_name_uses_channel(self):
        # if we have a patch but no (non-blank) name, fall back to the channel id
        j = LabelJoin()
        j.observe_patch("I7", "RAI7")
        self.assertEqual(j.slot_to_name()["RAI7"], "I7")

    def test_blank_name_falls_back(self):
        j = LabelJoin()
        j.observe_name("I8", "      ")  # all spaces
        j.observe_patch("I8", "RAI8")
        self.assertEqual(j.slot_to_name()["RAI8"], "I8")


if __name__ == "__main__":
    unittest.main()
