#!/usr/bin/env python3
r"""Print the engine and demand blocks of a saved Meridian payload, wherever they sit. W10, Sep 2026.

    py -3.12 probe_payload_keys.py E:\Avia\probe\BLQ-JFK-25Sep\opt_BLQ-JFK.json

Read-only. Walks the JSON and prints forecast_engine, demand, annual_capacity, aircraft and
frequency at every level, so the basis check (model range against the seats it was anchored on)
can be made from the payload already on disk without a new run.
"""
import json
import sys
from collections import deque

KEYS = ("forecast_engine", "demand", "annual_capacity", "aircraft", "frequency", "seats", "carrier")


def main(path):
    d = json.load(open(path))
    q = deque([("", d)])
    while q:
        pre, x = q.popleft()
        if isinstance(x, dict):
            for k, v in x.items():
                if k in KEYS:
                    print("%s%s: %s" % (pre, k, json.dumps(v, indent=1)))
                q.append((pre + k + ".", v))
        elif isinstance(x, list):
            for i, v in enumerate(x[:40]):
                q.append((pre + "[%d]." % i, v))


if __name__ == "__main__":
    main(sys.argv[1])
