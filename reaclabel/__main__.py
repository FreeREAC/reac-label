# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>

"""reac-label CLI: scan a Roland V-Mixer/M-5000 and print/emit a slot->name map.

  python3 -m reaclabel --host <mixer_ip> [--port 8023] [--inputs 48]
                       [--outputs 40] [--json out.json] [--probe]
  python3 -m reaclabel --sim                 # run against the built-in simulator

--probe just connects and prints VRQ (version) + a couple of CNQ/PIQ replies,
for confirming transport/model on real hardware before a full scan.
"""
import argparse
import json
import sys
from .client import MixerClient, scan_labels, DEFAULT_PORT

# per-model input counts (verified from the Companion mixerconfig.json)
MODEL_INPUTS = {"m200": 32, "m200i": 32, "m300": 32, "m380": 48,
                "m400": 48, "m480": 48, "m5000": 128}


def main(argv=None):
    """Parse args, scan the mixer (or simulator), and print/emit the slot->name table."""
    ap = argparse.ArgumentParser(prog="reac-label")
    ap.add_argument("--host", help="mixer IP (omit with --sim)")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--model", choices=sorted(MODEL_INPUTS), help="size the input scan")
    ap.add_argument("--inputs", type=int, help="override input channel count")
    ap.add_argument("--outputs", type=int, default=0, help="scan RAO1..N output slots")
    ap.add_argument("--json", help="write the slot->name table to this file")
    ap.add_argument("--probe", action="store_true", help="connect + print VRQ/CNQ/PIQ samples")
    ap.add_argument("--sim", action="store_true", help="run against the built-in simulator")
    args = ap.parse_args(argv)

    host, port = args.host, args.port
    sim = None
    if args.sim:
        from .simulator import MixerSim
        sim = MixerSim(
            names={"I1": "Kick  ", "I2": "Snare ", "I3": "Vox L ", "I22": "Bass  ", "AX1": "MonMix"},
            in_patch={"I1": "RAI1", "I2": "RAI2", "I3": "RAI3", "I22": "RAI22"},
            out_patch={"RAO1": "AX1"})
        host, port = "127.0.0.1", sim.start()
    elif not host:
        ap.error("--host is required (or use --sim)")

    try:
        if args.probe:
            c = MixerClient(host, port); c.connect()
            print("version:", c.version())
            print("CNQ I1 :", c.channel_name("I1"))
            print("PIQ I1 :", c.input_patch("I1"))
            c.close()
            return 0

        n = args.inputs or (MODEL_INPUTS.get(args.model, 0)) or 32
        inputs = ["I%d" % i for i in range(1, n + 1)]
        outputs = ["RAO%d" % i for i in range(1, args.outputs + 1)]
        table = scan_labels(host, port, inputs, outputs)
        if args.json:
            with open(args.json, "w") as f:
                json.dump(table, f, indent=2, sort_keys=True)
            print("wrote %d labels -> %s" % (len(table), args.json))
        else:
            for slot, name in sorted(table.items()):
                print("%-8s -> %s" % (slot, name))
        return 0
    finally:
        if sim:
            sim.stop()


if __name__ == "__main__":
    sys.exit(main())
