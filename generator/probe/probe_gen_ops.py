# -*- coding: utf-8 -*-
u"""probe_gen_ops.py -- sozdaet odnu shemu so VSEMI nuzhnymi nam blokami.

Zapuskaetsya OBYChNYM Python. Dalee CODESYS importiruet eyo i vygruzhaet
obratno, otkuda my chitaem KANONIChESKIE imena pinov dlya kazhdogo operatora.

Tak my uznaem imena pinov odin raz i navernyaka, vmesto ugadyvaniya.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))          # .../generator/probe
ROOT = os.path.dirname(os.path.dirname(HERE))              # .../Z80_EMU
sys.path.insert(0, os.path.join(ROOT, "generator", "tools"))

import fbd_xml as F

SRC = os.path.join(ROOT, "src")

# (imya bloka, vhodnye piny, vyhodnye piny)
OPS = [
    (u"AND",  [u"IN1", u"IN2"], [u"OUT"]),
    (u"OR",   [u"IN1", u"IN2"], [u"OUT"]),
    (u"XOR",  [u"IN1", u"IN2"], [u"OUT"]),
    (u"NOT",  [u"IN"],          [u"OUT"]),
    (u"SEL",  [u"G", u"IN0", u"IN1"], [u"OUT"]),
    (u"ADD",  [u"IN1", u"IN2"], [u"OUT"]),
    (u"SUB",  [u"IN1", u"IN2"], [u"OUT"]),
    (u"EQ",   [u"IN1", u"IN2"], [u"OUT"]),
    (u"MUX",  [u"K", u"IN0", u"IN1"], [u"OUT"]),
]


def mk():
    p = F.Pou(u"FB_OPS_PROBE", u"functionBlock",
              u"probnyj blok: imena pinov vseh operatorov")
    p.var_in(u"A", u"BOOL")
    p.var_in(u"B", u"BOOL")
    p.var_in(u"G", u"BOOL")
    p.var_out(u"R1", u"BOOL")
    p.var_out(u"R2", u"BOOL")
    p.var_out(u"R3", u"BOOL")
    p.var_out(u"R4", u"BOOL")
    p.var_out(u"R5", u"BOOL")

    n = p.network(u"vse operatory")
    y = 40
    res = []
    for tname, pins, outs in OPS:
        a = n.invar(u"A", x=F.COL_IN, y=y)
        b = n.invar(u"B", x=F.COL_IN, y=y + 14)
        g = n.invar(u"G", x=F.COL_IN, y=y + 28)
        srcs = []
        for k, pin in enumerate(pins):
            if k == 0:
                srcs.append((pin, a))
            elif k == 1:
                srcs.append((pin, b))
            else:
                srcs.append((pin, g))
        blk = n.block(tname, srcs, outs, x=F.COL_BLK, y=y)
        res.append(blk)
        y += 60

    # vyhody -- cherez promezhutochnye peremennye R1..R5
    y = 40
    for k, blk in enumerate(res[:5]):
        n.outvar(u"R%d" % (k + 1), blk, x=F.COL_OUT, y=y)
        y += 60
    return p


try:
    F.write_project(os.path.join(SRC, u"FB_OPS_PROBE.plcopenxml"), [mk()],
                    u"FB_OPS_PROBE")
    print(u"OK: FB_OPS_PROBE.plcopenxml written")
except Exception:
    import traceback
    print(u"FAIL: %s" % traceback.format_exc())
