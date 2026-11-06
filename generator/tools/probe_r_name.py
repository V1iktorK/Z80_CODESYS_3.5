# -*- coding: utf-8 -*-
u"""Probe: konfliktuet li imya peremennoj 'R' so vstroennym identifikatorom.

ZAPUSKAT TOLKO cherez CODESYS. Rezultat -- log/probe_r.log.

SITUACIYA. Kompilyator uporno soobshchaet "C4: 'R' ne yavlyaetsya komponentom
'GVL_PLCVisu'", hotya v GVL_PLCVisu peremennaya R est (vidna i v fajle .gvl,
i v textual_declaration sobrannogo proekta, i nichego drugogo s etim imenem
v proekte net).

GIPOTEZA. V CODESYS identifikatory NE chuvstvitelny k registru, i odnosimvolnoe
imya R mozhet stolknut'sya s vstroennym imenem (v yazyke SFC/CFC est
"R" -- sbros triggera). Proverim: pereimenum peremennuyu v R_Reg i posmotrim,
ischeznet li oshibka.
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, u"src")
GEN = os.path.join(ROOT, u"generator", u"gen_z80.py")

OLD = u"GVL_PLCVisu.R"
NEW = u"GVL_PLCVisu.R_Reg"


def main():
    n = 0
    # 1) GVL
    g = os.path.join(SRC, u"GVL_PLCVisu.gvl")
    t = io.open(g, encoding=u"utf-8").read()
    t2, k = re.subn(u"(?m)^(\\s*)R(\\s*:)", u"\\g<1>R_Reg\\g<2>", t)
    io.open(g, u"w", encoding=u"utf-8").write(t2)
    n += k
    print(u"GVL_PLCVisu.gvl: %d zamen" % k)

    # 2) shema
    p = os.path.join(SRC, u"PLC_PRG.plcopenxml")
    t = io.open(p, encoding=u"utf-8").read()
    t2, k = re.subn(re.escape(u"<expression>GVL_PLCVisu.R</expression>"),
                    u"<expression>GVL_PLCVisu.R_Reg</expression>", t)
    io.open(p, u"w", encoding=u"utf-8").write(t2)
    n += k
    print(u"PLC_PRG.plcopenxml: %d zamen" % k)

    print(u"vsego: %d" % n)
    print(u"teper zapustite sborku i posmotrite, est li oshibka C4")


if __name__ == u"__main__":
    main()
