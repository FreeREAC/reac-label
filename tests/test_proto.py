# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>

"""Tests for the Roland V-Mixer remote protocol framing/parsing.

Grounded in real VMXProxy simrc.txt pairs:
  CNQ:I1;  -> CNS:I1,"NoName";
  PIC:I22,RAI22;  (channel 22 fed from REAC A input slot 22)
  VRQ;     -> VRS:1.010,1.010,1.010;
  set commands -> <ack> (telnet: text "OK")
Framing: [STX] + 3 letters + ':' + CSV args + ';'  (telnet drops STX).
"""
import unittest
from reaclabel.proto import frame_query, parse_reply, Reply


class TestFrame(unittest.TestCase):
    def test_query_no_args(self):
        # telnet form (no STX): "VRQ;"
        self.assertEqual(frame_query("VRQ"), b"VRQ;")

    def test_query_with_target(self):
        self.assertEqual(frame_query("CNQ", "I1"), b"CNQ:I1;")
        self.assertEqual(frame_query("PIQ", "I22"), b"PIQ:I22;")


class TestParse(unittest.TestCase):
    def test_channel_name(self):
        r = parse_reply('CNS:I1,"NoName";')
        self.assertEqual(r.action, "S")
        self.assertEqual(r.code, "CN")
        self.assertEqual(r.target, "I1")
        self.assertEqual(r.args, ["NoName"])  # quotes stripped

    def test_name_with_trailing_spaces_preserved(self):
        # names are fixed 6 chars; blank = spaces — don't strip inside quotes
        r = parse_reply('CNS:MAL,"MAINL ";')
        self.assertEqual(r.target, "MAL")
        self.assertEqual(r.args, ["MAINL "])

    def test_input_patch(self):
        r = parse_reply("PIS:I22,RAI22;")
        self.assertEqual(r.code, "PI")
        self.assertEqual(r.action, "S")
        self.assertEqual(r.target, "I22")
        self.assertEqual(r.args, ["RAI22"])

    def test_version(self):
        r = parse_reply("VRS:1.010,1.010,1.010;")
        self.assertEqual(r.code, "VR")
        self.assertEqual(r.args, ["1.010", "1.010", "1.010"])

    def test_ack_ok(self):
        # telnet ack renders as text OK
        r = parse_reply("OK")
        self.assertTrue(r.is_ack)

    def test_error(self):
        r = parse_reply("ERR:5;")
        self.assertTrue(r.is_error)
        self.assertEqual(r.args, ["5"])

    def test_stx_prefix_tolerated(self):
        # serial form may include STX (0x02) — parser strips it
        r = parse_reply("\x02CNS:I3,\"BASS  \";")
        self.assertEqual(r.code, "CN")
        self.assertEqual(r.target, "I3")
        self.assertEqual(r.args, ["BASS  "])


if __name__ == "__main__":
    unittest.main()
