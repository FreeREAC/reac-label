# reac-label

Read-only **labeller** for [`reac-aes67`](https://github.com/FreeREAC/reac-aes67):
queries a Roland **V-Mixer** over its remote-control protocol (TCP 8023) and
builds a **REAC-slot → channel-name** table, so the AES67 channels reac-aes67
emits show the desk's names ("Bass") instead of bare slot numbers.

It supplies what the passive REAC tap does not decode — the slot↔channel↔name
mapping, which lives in the mixer's patch, not in the audio frame.

Part of [FreeREAC](https://github.com/FreeREAC) — *REAC Exposed Audio
Communications*. Python, **stdlib only**, no dependencies.

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

## Where this fits

**Still needed, narrowly.** reac-label has a job on exactly one path: a **Roland
desk is the REAC master** and something listens to that segment passively. There
the desk owns the patch and the names, nothing on the audio wire carries them,
and the control port is the only source.

It has **no job on the openmixer / reac-pw path**. When reac-pw masters a segment
it drives the stageboxes directly, and the console session already holds the
channel roster, the patch and the names; labels come from the session. Pointing
reac-label at that path would add a second, staler declaration of the same thing.

Per desk:

- **V-Mixer — M-200i / M-300 / M-380 / M-400 / M-480.** The target. `PIQ` / `POQ`
  return the `RAI<n>` / `RAO<n>` patch tokens the join is keyed on.
- **M-5000 — the patch is not on this port.** `PIQ` / `POQ` come back **empty**:
  routing is not exposed over the ASCII LAN protocol. Measured on a live M-5000
  on 2026-06-07, on a connection where the banner, `VRQ` and `RCQ` (REAC link
  status) all answered normally, so it is the routing plane that is absent, not
  the session. With no patch side the join has nothing to invert, so reac-label
  cannot build a slot→name table for an M-5000 over TCP 8023 — its routing plane
  is reachable only over RS-232C or DIN MIDI. `--model m5000` sizes a name scan
  and nothing more.

**A label means the desk patched that slot, not that the slot carries audio.** A
stagebox channel stays digitally silent until a head-amp commit promotes its
staged record into the box's active table; a patched slot whose channel was never
committed is patched and silent. Do not read this table as an active-channel map.

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
# confirm transport/model first (M-200i telnet must be enabled in its LAN menu;
# older V-Mixers need a serial<->TCP bridge / VMXProxy):
python3 -m reaclabel --host <mixer_ip> --probe

# full scan -> JSON for reac-aes67 to read:
python3 -m reaclabel --host <mixer_ip> --model m480 --outputs 40 --json slots.json
```

Per-model input counts are built in (`--model`): M-200/M-300 = 32, M-380/M-400/
M-480 = 48, M-5000 = 128. Override with `--inputs N`.

A scan that returns names but no slots is the M-5000 case above: `PIQ` answered
empty, so every channel looks unpatched.

## Constraints & notes

- **Read-only.** reac-label never sets/controls the mixer.
- **Single connection:** the mixer accepts one control client at a time — don't
  run this alongside an iPad Remote / RCS session (or front it with VMXProxy).
- **No auth** on the mixer's control port — keep it on a trusted segment.
- **Poll, no push:** names are fetched per scan; re-run to pick up renames.
- **UNVERIFIED — whether the REAC wire carries the names anyway.** The REAC
  control plane has a scene-transfer channel: an op-0101 header declaring 0x22c8
  (8904) bytes, then 341 op-0100 chunks of 26 bytes, then an op-0102 final of 14;
  the body validates on three 4-byte compares, `1234` at +0x000, `SYSP` at +0x368
  and `SCEN` at +0x37c. Nothing in this repo shows whether that body carries the
  channel-name fields. Settle it by decoding a captured scene body and looking for
  the fixed-width name strings `CNQ` returns. If they are in there, a passive tap
  can recover names without the control port and this tool narrows to the patch
  join alone.
- **UNVERIFIED — the key contract with reac-aes67.** The join emits the desk's own
  token verbatim (`RAI1`, `RAO1`, one-based). Whether reac-aes67 keys its AES67
  channels by the same token and the same base cannot be tested from this repo.
  Settle it with a joint run: a known patch in, a labelled stream out, names
  landing on the expected channels.

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

## API reference

The public API carries docstrings; generate browsable HTML with `make docs`
(needs [pdoc](https://pdoc.dev), output in `site/`). CI publishes it to GitHub
Pages on each `v*` tag.

## License

GPL-3.0-or-later. Copyright (C) 2026 Pau Aliagas. See [LICENSE](LICENSE) and
[NOTICE](NOTICE).
