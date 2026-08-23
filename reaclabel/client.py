# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>

"""Thin TCP client for the Roland V-Mixer / M-5000 remote protocol (port 8023),
plus the high-level scan that builds the slot->name table.

Line-oriented telnet: send "CMD;\r\n", read until a ';'-terminated reply or
"OK". Read-only (queries only). Pairs the pure proto + join modules with a real
socket.

On an M-5000 the patch queries (PIQ/POQ) answer empty while VRQ and RCQ answer
normally: routing is not exposed on the ASCII LAN protocol, so scan_labels comes
back with every channel unpatched. That is the desk, not a fault here.
"""
import socket
from .proto import frame_query, parse_reply
from .join import LabelJoin

DEFAULT_PORT = 8023


class MixerClient:
    """Read-only TCP client for one Roland mixer's remote-control port.

    Holds a single connection (mixers accept one control client at a time) and
    exposes typed query helpers; it never sends control/set commands.
    """

    def __init__(self, host, port=DEFAULT_PORT, timeout=5.0):
        """Configure the target; call connect() to open the socket."""
        self.host = host
        self.port = port
        self.timeout = timeout
        self._sock = None
        self._buf = b""

    def connect(self):
        """Open the TCP connection to the mixer."""
        self._sock = socket.create_connection((self.host, self.port), self.timeout)
        self._sock.settimeout(self.timeout)

    def close(self):
        """Send QUIT and close the connection (best-effort)."""
        if self._sock:
            try:
                self._sock.sendall(b"QUIT;\r\n")
            except OSError:
                pass
            self._sock.close()
            self._sock = None

    def _read_reply(self):
        """Read until a ';'-terminated reply or a bare 'OK' line."""
        while True:
            # is a complete reply already buffered?
            for term in (b";", b"\n"):
                if term in self._buf:
                    line, _, self._buf = self._buf.partition(term)
                    text = line.decode("ascii", "replace").strip()
                    if not text:
                        continue
                    return parse_reply(text + (";" if term == b";" else ""))
            data = self._sock.recv(1024)
            if not data:
                raise ConnectionError("mixer closed connection")
            self._buf += data

    def query(self, code, target=None):
        """Send a query and return the parsed Reply (skips ack-only lines)."""
        self._sock.sendall(frame_query(code, target) + b"\r\n")
        r = self._read_reply()
        while r.is_ack:        # ignore stray acks
            r = self._read_reply()
        return r

    def version(self):
        """Return the mixer firmware version string (VRQ -> VRS)."""
        r = self.query("VRQ")
        return ",".join(r.args)

    def channel_name(self, channel):
        """Return an input channel's name (CNQ), or '' if unset."""
        r = self.query("CNQ", channel)
        return r.args[0] if r.args else ""

    def input_patch(self, channel):
        """Return the source slot feeding a channel (PIQ), e.g. RAI22; 'OFF' if unpatched."""
        r = self.query("PIQ", channel)
        return r.args[0] if r.args else "OFF"

    def output_patch(self, slot):
        """Return the source feeding a REAC output slot (POQ); 'OFF' if unpatched."""
        r = self.query("POQ", slot)
        return r.args[0] if r.args else "OFF"


def scan_labels(host, port, input_channels, output_slots=None):
    """Connect, scan names + input/output patch, return the slot->name table."""
    c = MixerClient(host, port)
    c.connect()
    try:
        j = LabelJoin()
        for ch in input_channels:
            j.observe_name(ch, c.channel_name(ch))
            j.observe_patch(ch, c.input_patch(ch))
        for slot in (output_slots or []):
            source = c.output_patch(slot)
            if source and source != "OFF":
                j.observe_name(source, c.channel_name(source))
                j.observe_output_patch(slot, source)
        return j.slot_to_name()
    finally:
        c.close()
