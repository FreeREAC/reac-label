# reac-label

Read-only **labeller** for [`reac-aes67`](https://github.com/linuxnow/reac-aes67):
queries a Roland **V-Mixer / M-5000** over its remote-control protocol (TCP
8023) and builds a **REAC-slot → channel-name** table, so the AES67 channels
reac-aes67 emits show the desk's names ("Bass") instead of bare slot numbers.

It supplies the one thing the passive REAC tap **cannot** see — the
slot↔channel↔name mapping, which lives in the mixer's patch, not on the wire.

Personal audio project (lives under the `linuxnow` org alongside `reac-aes67`,
`reac-tools`). Python, **stdlib only**, no dependencies.

## How it works

The Roland protocol exposes read ("Q") queries that return ("S") replies:

- `CNQ:I1;` → `CNS:I1,"Kick  ";` — channel **name**
- `PIQ:I22;` → `PIS:I22,RAI22;` — **input patch**: channel 22 is fed from REAC A
  input slot 22. That `RAI`/`RAO` token **is** the REAC slot index the reac-aes67
  tap keys on.

reac-label joins `channel→slot` (PIQ) with `channel→name` (CNQ), inverted, into
**slot→name** — landing the label on the correct AES67 channel.

```
mixer (TCP 8023)
  → proto    pure: frame a query, parse a reply (STX/telnet, ERR, OK)
  → client   thin socket: connect, line I/O, queries
  → join     pure: CNS + PIS  ->  slot_to_name (keyed RAIn/RAOn)
  → CLI/JSON slot->name table for reac-aes67 to stamp on the AES67 labels
```

## Try it (no hardware)

A built-in mixer **simulator** answers the query subset exactly like a real desk
(framing per Roland's spec / VMXProxy `simrc.txt`), so the whole flow runs with
nothing plugged in:

```sh
python3 -m unittest discover tests   # 18 tests incl. end-to-end over a socket
python3 -m reaclabel --sim           # scan the simulator, print slot->name
python3 -m reaclabel --sim --probe   # VRQ/CNQ/PIQ sample replies
```

## Against a real mixer

```sh
# confirm transport/model first (M-5000 native TCP; M-200i telnet must be
# enabled in its LAN menu; older V-Mixers need a serial<->TCP bridge / VMXProxy):
python3 -m reaclabel --host <mixer_ip> --probe

# full scan -> JSON for reac-aes67 to read:
python3 -m reaclabel --host <mixer_ip> --model m480 --outputs 40 --json slots.json
```

Per-model input counts are built in (`--model`): M-200/M-300 = 32, M-380/M-400/
M-480 = 48, M-5000 = 128. Override with `--inputs N`.

## Constraints & notes

- **Read-only.** reac-label never sets/controls the mixer.
- **Single connection:** the mixer accepts one control client at a time — don't
  run this alongside an iPad Remote / RCS session (or front it with VMXProxy).
- **No auth** on the mixer's control port — keep it on a trusted segment.
- **Poll, no push:** names are fetched per scan; re-run to pick up renames.
- **M-5000 (OHRCA)** may use different patch tokens than the V-Mixer `RAI/RAO`;
  confirm with `--probe` on the real unit (open item).

## References

- Roland V-Mixer RS-232C / Telnet reference (the protocol).
- `bitfocus/companion-module-roland-m5000`, `JamesCC/VMXProxyPy` (open impls;
  the latter ships the protocol PDF + a simulator).

## Acknowledgements

reac-label is original, stdlib-only Python and includes no third-party code. It
does, however, stand on prior reverse-engineering and documentation of the
Roland V-Mixer / M-5000 remote-control protocol: the Roland RS-232C / Telnet
remote-control reference documents the command/reply wire format, while two open
projects supplied data (not code) that grounded the parser, tests, and the
built-in simulator. Per-model channel counts come from a third project as plain
facts. The protocol and specification facts themselves carry no copyright claim
here.

- [JamesCC/VMXProxyPy](https://github.com/JamesCC/VMXProxyPy) (LGPL-3.0 /
  GPL-3.0) — its `simrc.txt` sample command/response pairs grounded the
  protocol-parsing tests and simulator reply framing (used as data).
- [bitfocus/companion-module-roland-m5000](https://github.com/bitfocus/companion-module-roland-m5000)
  (MIT) — per-model channel counts (factual data) for the `--model` defaults.
- Roland V-Mixer / M-5000 RS-232C / Telnet remote-control reference — the
  documented protocol implemented here.

## License

GPL-3.0-or-later. Copyright (C) 2026 Pau Aliagas. See [LICENSE](LICENSE) and
[NOTICE](NOTICE).
