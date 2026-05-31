# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>

"""A minimal Roland V-Mixer telnet simulator (stdlib only).

Answers the query subset reac-label uses (VRQ, CNQ, PIQ, POQ), framed exactly
like a real mixer per VMXProxy's simrc.txt. Lets the client + join be tested
end-to-end over a real TCP socket with no hardware and no external dependency.
Seed it with channel names + input/output patch; it replies to queries.
"""
import socket
import threading


class MixerSim:
    """In-process TCP stand-in for a Roland mixer's control port.

    Answers the VRQ/CNQ/PIQ/POQ query subset framed like a real desk, so the
    client and join logic can be exercised end-to-end without hardware.
    """

    def __init__(self, names=None, in_patch=None, out_patch=None, version="1.010"):
        """Seed the simulated state: channel names, input patch, output patch."""
        self.names = dict(names or {})        # channel id -> name (caller pads)
        self.in_patch = dict(in_patch or {})  # channel id -> RAIn/RBIn/OFF
        self.out_patch = dict(out_patch or {})# RAOn -> source channel
        self.version = version
        self._sock = None
        self._thread = None
        self.port = None

    def _reply(self, cmd):
        cmd = cmd.strip()
        if cmd.endswith(";"):
            cmd = cmd[:-1]
        head, _, arg = cmd.partition(":")
        if head == "VRQ":
            return 'VRS:%s,%s,%s;' % (self.version, self.version, self.version)
        if head == "CNQ":
            name = self.names.get(arg, "      ")
            return 'CNS:%s,"%s";' % (arg, name)
        if head == "PIQ":
            return 'PIS:%s,%s;' % (arg, self.in_patch.get(arg, "OFF"))
        if head == "POQ":
            return 'POS:%s,%s;' % (arg, self.out_patch.get(arg, "OFF"))
        return "ERR:0;"

    def _serve(self):
        conn, _ = self._sock.accept()
        buf = b""
        with conn:
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                buf += data
                # commands terminated by ';'
                while b";" in buf:
                    line, _, buf = buf.partition(b";")
                    cmd = line.decode("ascii", "replace").lstrip("\x02").strip()
                    if not cmd:
                        continue
                    if cmd.upper() == "QUIT":
                        return
                    conn.sendall((self._reply(cmd + ";") + "\r\n").encode())

    def start(self):
        """Bind an ephemeral localhost port, serve in a daemon thread, return the port."""
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(("127.0.0.1", 0))
        self._sock.listen(1)
        self.port = self._sock.getsockname()[1]
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()
        return self.port

    def stop(self):
        """Close the listening socket and stop serving."""
        try:
            if self._sock:
                self._sock.close()
        except OSError:
            pass
