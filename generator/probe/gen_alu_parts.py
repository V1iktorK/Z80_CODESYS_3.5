# -*- coding: utf-8 -*-
"""Bisekciya: kakaya imenno chast ALU teryaetsya pri importe."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))          # generator/probe
ROOT = os.path.dirname(os.path.dirname(HERE))              # Z80_EMU
sys.path.insert(0, os.path.join(ROOT, "generator"))
sys.path.insert(0, os.path.join(ROOT, "generator", "tools"))
import fbd_xml as F
import gen_z80 as gz

SRC = os.path.join(ROOT, "src")
base = gz.mk_alu()
n = len(base.networks)
print("setey v polnom ALU:", n)

for k in range(1, n + 1):
    part = gz.mk_alu()
    part.name = "ALU_PART%d" % k
    part.networks = part.networks[:k]
    path = os.path.join(SRC, "ALU_PART%d.plcopenxml" % k)
    F.write_project(path, [part], part.name)
    print("  ALU_PART%d sozdan (setey %d)" % (k, k))
