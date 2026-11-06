# -*- coding: utf-8 -*-
u"""probe_gen_pins.py -- sozdaet tri probnyh shemy s raznymi imenami pinov.

Zapuskaetsya OBYChNYM Python (vne CODESYS). Chtoby vyyasnit', kakie imena
pinov prinimaet import XML v CODESYS 3.5 SP17.

  FB_PIN_A: IN1 / IN2 / OUT   (kak u semejstva AND/OR/XOR)
  FB_PIN_B: IN / OUT          (kak ozhidayut dlya NOT)
  FB_PIN_C: piny voobshche ne ukazany
"""

import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))          # .../generator/probe
ROOT = os.path.dirname(os.path.dirname(HERE))              # .../Z80_EMU
sys.path.insert(0, os.path.join(ROOT, "generator", "tools"))

import fbd_xml as F

SRC = os.path.join(ROOT, "src")


def mk(name, pin1, pin2, pout, use_sel=True):
    u"""Prostaya shema: (A AND B) -> Y   ili   A -> Y."""
    p = F.Pou(name, u"functionBlock", u"probnyj blok dlya vybora imen pinov")
    p.var_in(u"A", u"BOOL")
    p.var_in(u"B", u"BOOL")
    p.var_out(u"Y", u"BOOL")

    n = p.network(u"probe")
    a = n.invar(u"A", y=40)
    b = n.invar(u"B", y=80)
    blk = n.block(u"AND", [(pin1, a), (pin2, b)], [pout], x=F.COL_BLK, y=50)
    n.outvar(u"Y", blk, x=F.COL_OUT, y=50)
    return p


CASES = [
    (u"FB_PIN_A", u"IN1", u"IN2", u"OUT"),
    (u"FB_PIN_B", u"IN", u"IN", u"OUT"),
    (u"FB_PIN_C", u"", u"", u""),
]

for name, p1, p2, po in CASES:
    try:
        F.write_project(os.path.join(SRC, u"%s.plcopenxml" % name),
                        [mk(name, p1, p2, po)], name)
        print(u"OK  %s  pins=%r/%r out=%r" % (name, p1, p2, po))
    except Exception:
        import traceback
        print(u"FAIL %s: %s" % (name, traceback.format_exc()))
