#!/usr/bin/env python3
"""Project Severn: Bristol to Boston.

The first deck built from RESEARCH OUTPUT rather than hand-authored content.
Nothing in this file states a fact: it loads research_brs_bos.json and hands it
to spec_from_research.build_spec. Every figure and citation comes from the
research run, which is the point of the test.

Avia Solutions Limited. All rights reserved.
"""

import json
import os

import spec_from_research as C

HERE = os.path.dirname(os.path.abspath(__file__))


def build():
    with open(os.path.join(HERE, "research_brs_bos.json"), encoding="utf-8") as f:
        research = json.load(f)
    return C.build_spec(
        research,
        codename="Project Severn",
        title="A direct link between\nBristol and Boston",
        strap="The largest United Kingdom airport with no transatlantic service",
        prepared_for="Bristol Airport",
        date="6 August 2026",
        confidentiality="Commercial in Confidence")


if __name__ == "__main__":
    spec = build()
    print("%d slides" % len(spec["slides"]))
