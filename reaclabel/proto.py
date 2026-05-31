# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>

"""Roland V-Mixer / M-5000 remote-control protocol — framing & parsing (pure).

Wire format (telnet over TCP 8023): a command is 3 uppercase letters, an
optional ':' + comma-separated args, terminated by ';'. The serial form
prefixes STX (0x02); the telnet form omits it and renders the 0x06 ack as the
literal text "OK". The 3rd letter is the action: C=set(Control), Q=query, S=
status reply. Replies we consume are the 'S' forms; errors come as "ERR:<n>;".

This module is pure (no I/O) so it is unit-testable against the documented
VMXProxy simrc.txt command/response pairs.
"""
from dataclasses import dataclass, field

STX = "\x02"


def frame_query(code, target=None):
    """Build a query command as bytes (telnet form, no STX).
    frame_query("VRQ") -> b"VRQ;"; frame_query("CNQ","I1") -> b"CNQ:I1;"."""
    s = code if target is None else "%s:%s" % (code, target)
    return (s + ";").encode("ascii")


@dataclass
class Reply:
    raw: str
    code: str = ""        # 2-letter category, e.g. "CN", "PI", "VR"
    action: str = ""      # 3rd letter: "S" (status), "C", "Q"
    target: str = ""      # e.g. "I22", "MAL", "RAO2" (empty if none)
    args: list = field(default_factory=list)
    is_ack: bool = False
    is_error: bool = False


def _split_args(s):
    """Split CSV args, stripping surrounding double-quotes but preserving
    content (channel names are fixed-width, trailing spaces are significant)."""
    out = []
    for a in s.split(","):
        if len(a) >= 2 and a[0] == '"' and a[-1] == '"':
            a = a[1:-1]
        out.append(a)
    return out


def parse_reply(line):
    """Parse one reply line into a Reply. Tolerates a leading STX and a
    trailing ';'. Recognises the telnet ack ("OK") and "ERR:<n>;"."""
    s = line.strip()
    if s.startswith(STX):
        s = s[1:]
    if s == "OK" or s == "\x06":
        return Reply(raw=line, is_ack=True)
    if s.endswith(";"):
        s = s[:-1]

    # "CODE" or "CODE:args"
    if ":" in s:
        head, _, argstr = s.partition(":")
    else:
        head, argstr = s, ""

    if head == "ERR":
        return Reply(raw=line, code="ER", action="R",
                     args=_split_args(argstr), is_error=True)

    code = head[:2]
    action = head[2:3]
    args = _split_args(argstr) if argstr != "" else []
    # First arg is the target (e.g. I22), the rest are values — EXCEPT for
    # replies whose first field IS a value (VR, SC handled by callers).
    target = ""
    if action == "S" and args and code in ("CN", "PI", "PO", "FD", "MU",
                                            "PT", "PS", "PG", "EQ", "FL",
                                            "AX", "MX", "PN"):
        target = args[0]
        args = args[1:]
    return Reply(raw=line, code=code, action=action, target=target, args=args)
