# -*- coding: utf-8 -*-
u"""Eksperiment: rabotayut li ORD() i literaly s '$' v CODESYS 3.5.

ZAPUSKAT SISTEMNYM PYTHON 3 -- generiruet tests/lang_probe.plcopenxml.
Zatem sborka cherez CODESYS (run_lang_probe.cmd).

ChTO PROVERYaEM (4 otdelnyh POU, chtoby videt#, kakoy imenno kroshitsya):
    P1: b := ORD('A');            -- est li ORD v CODESYS
    P2: b := ORD('$');            -- simvol $ v kavy chkah
    P3: b := 16#24;               -- to zhe chislo bez literala
    P4: s := 'HELLO$';            -- stroka s $ vnutri
"""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import fbd_xml as F                                              # noqa: E402

OUT = os.path.join(ROOT, u"tests")
NAMES = (u"P1_ORD_A", u"P2_ORD_DOLLAR", u"P3_HEX", u"P4_STRING")


def mk(name, body, doc):
    return F.TextPou(name, u"""PROGRAM %s
(* %s *)
VAR
    b : BYTE;
    s : STRING(16);
END_VAR

%s
""" % (name, doc, body), u"program", doc)


CASES = (
    (u"P1_ORD_A", u"b := ORD('A');", u"proverka: est li funkciya ORD"),
    (u"P2_ORD_DOLLAR", u"b := ORD('$');", u"proverka: simvol $ v kavychkah"),
    (u"P3_HEX", u"b := 16#24;", u"proverka: to zhe chislo bez literala"),
    (u"P4_STRING", u"s := 'HELLO$';", u"proverka: stroka s $ vnutri"),
)


def main():
    pous = [mk(n, b, d) for n, b, d in CASES]
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    path = os.path.join(OUT, u"lang_probe.plcopenxml")
    F.write_project(path, pous, u"LANG_PROBE")
    sys.stdout.write(u"zapisano: %s (%d POU)\n" % (path, len(pous)))
    for n, b, _ in CASES:
        sys.stdout.write(u"   %-16s %s\n" % (n, b))


if __name__ == u"__main__":
    main()
