# -*- coding: utf-8 -*-
u"""gen_prg_parts.py -- narezaet glavnuyu shemu na posledovatel'nye chasti.

Zapuskaetsya OBYChNYM Python. Nuzhno ponyat', posle kakoy seti import
PLCPRG perestaet prinimat'sya (fan-out vnutri seti).
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))          # generator/probe
ROOT = os.path.dirname(os.path.dirname(HERE))              # Z80_EMU
sys.path.insert(0, os.path.join(ROOT, "generator"))
sys.path.insert(0, os.path.join(ROOT, "generator", "tools"))
import fbd_xml as F
import gen_z80 as gz

SRC = os.path.join(ROOT, "src")
base = gz.mk_plc_prg()
n = len(base.networks)
print(u"setey v PLC_PRG: %d" % n)

for k in range(1, n + 1):
    part = gz.mk_plc_prg()
    part.name = u"PRG_PART%d" % k
    part.networks = part.networks[:k]
    path = os.path.join(SRC, u"PRG_PART%d.plcopenxml" % k)
    try:
        F.write_project(path, [part], part.name)
        print(u"  PRG_PART%d sozdan (setey %d)" % (k, k))
    except Exception:
        import traceback
        print(u"  PRG_PART%d OSHIBKA GENERATSII:\n%s" % (k, traceback.format_exc()))
