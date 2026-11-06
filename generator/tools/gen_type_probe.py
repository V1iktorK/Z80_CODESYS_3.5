# -*- coding: utf-8 -*-
u"""Eksperiment: kakie konstrukcii FBD kompilyator prinimaet po tipam.

ZAPUSKAT SISTEMNYM PYTHON 3 (generaciya XML), zatem sborka cherez CODESYS.

ZADAChA. Kompilyator daet 40 oshibok C32 "Nevozmozhno konvertirovat tip
'BOOL' v tip 'USINT'" i obratno. Chtoby ne ugadyvat, soberaem otdelnyj
proekt iz KROSSOV, kazhdaya -- odna konstrukciya:
    A) BOOL_TO_BYTE -> SHL(BYTE, 7)               -- kak v FB_FlagsRegZ80
    B) SHL(BYTE, USINT-konstanta)
    C) ADD(BYTE, BYTE)
    D) SEL(BOOL, BYTE, BYTE)
    E) BYTE_TO_WORD -> ADD(WORD, WORD) -> WORD_TO_BYTE
    F) SHR(WORD, 8)                                -- kak v FB_IO_Ports
Posle sborki v log popadut tolko problemnye krossy, i budet vidno, kakuyu
konstrukciyu nado peredelat.
"""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import fbd_xml as F                                              # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.dirname(HERE)), u"tests")
PIN1, PIN2, PINU, POUT = u"IN1", u"IN2", u"IN", u"OUT"


def mk(name, doc, decl, build):
    p = F.Pou(name, u"functionBlock", doc)
    for kind, nm, tp in decl:
        getattr(p, kind)(nm, tp)
    n = p.network(u"proba")
    build(p, n)
    return p


def t_a(p, n):
    u"""BOOL_TO_BYTE -> SHL s konstantoj."""
    b = n.block(u"BOOL_TO_BYTE", [(PINU, n.invar(u"B_In", y=30))], [POUT],
                x=F.COL_BLK, y=30)
    s = n.block(u"SHL", [(PIN1, b), (PIN2, n.const(u"7", y=44))], [POUT],
                x=F.COL_BLK2, y=30)
    n.outvar(u"B_Out", s, x=F.COL_OUT, y=30)


def t_b(p, n):
    u"""SHL(BYTE, konstantoj) -- bez konversii BOOL."""
    s = n.block(u"SHL", [(PIN1, n.invar(u"B_In", y=30)),
                         (PIN2, n.const(u"3", y=44))], [POUT],
                x=F.COL_BLK, y=30)
    n.outvar(u"B_Out", s, x=F.COL_OUT, y=30)


def t_c(p, n):
    u"""ADD(BYTE, BYTE)."""
    a = n.block(u"ADD", [(PIN1, n.invar(u"B_In", y=30)),
                         (PIN2, n.invar(u"B_In2", y=60))], [POUT],
                x=F.COL_BLK, y=30)
    n.outvar(u"B_Out", a, x=F.COL_OUT, y=30)


def t_d(p, n):
    u"""SEL(BOOL, BYTE, BYTE)."""
    s = n.block(u"SEL", [(u"G", n.invar(u"En", y=30)),
                         (u"IN0", n.invar(u"B_In", y=60)),
                         (u"IN1", n.invar(u"B_In2", y=90))], [POUT],
                x=F.COL_BLK, y=30)
    n.outvar(u"B_Out", s, x=F.COL_OUT, y=30)


def t_e(p, n):
    u"""BYTE -> WORD -> ADD -> WORD_TO_BYTE."""
    w = n.block(u"BYTE_TO_WORD", [(PINU, n.invar(u"B_In", y=30))], [POUT],
                x=F.COL_BLK, y=30)
    a = n.block(u"ADD", [(PIN1, w), (PIN2, n.const(u"1", y=44))], [POUT],
                x=F.COL_BLK2, y=30)
    r = n.block(u"WORD_TO_BYTE", [(PINU, a)], [POUT], x=F.COL_BLK2 + 160, y=30)
    n.outvar(u"B_Out", r, x=F.COL_OUT, y=30)


def t_f(p, n):
    u"""SHR(WORD, 8) -- kak v FB_IO_Ports."""
    s = n.block(u"SHR", [(PIN1, n.invar(u"W_In", y=30)),
                         (PIN2, n.const(u"8", y=44))], [POUT],
                x=F.COL_BLK, y=30)
    n.outvar(u"B_Out", s, x=F.COL_OUT, y=30)


CASES = [
    (u"T_A_BoolShift", u"BOOL_TO_BYTE -> SHL",
     [(u"var_in", u"B_In", u"BOOL"), (u"var_out", u"B_Out", u"BYTE")], t_a),
    (u"T_B_ShlByte", u"SHL(BYTE, konst)",
     [(u"var_in", u"B_In", u"BYTE"), (u"var_out", u"B_Out", u"BYTE")], t_b),
    (u"T_C_AddByte", u"ADD(BYTE, BYTE)",
     [(u"var_in", u"B_In", u"BYTE"), (u"var_in", u"B_In2", u"BYTE"),
      (u"var_out", u"B_Out", u"BYTE")], t_c),
    (u"T_D_SelByte", u"SEL(BOOL, BYTE, BYTE)",
     [(u"var_in", u"En", u"BOOL"), (u"var_in", u"B_In", u"BYTE"),
      (u"var_in", u"B_In2", u"BYTE"), (u"var_out", u"B_Out", u"BYTE")], t_d),
    (u"T_E_WordChain", u"BYTE->WORD->ADD->BYTE",
     [(u"var_in", u"B_In", u"BYTE"), (u"var_out", u"B_Out", u"BYTE")], t_e),
    (u"T_F_ShrWord", u"SHR(WORD, 8)",
     [(u"var_in", u"W_In", u"WORD"), (u"var_out", u"B_Out", u"BYTE")], t_f),
]


def main():
    pous = []
    for name, doc, decl, build in CASES:
        pous.append(mk(name, doc, decl, build))
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    path = os.path.join(OUT, u"type_probe.plcopenxml")
    F.write_project(path, pous, u"TYPE_PROBE")
    sys.stdout.write(u"zapisano: %s (%d POU)\n" % (path, len(pous)))


if __name__ == u"__main__":
    main()
