# -*- coding: utf-8 -*-
u"""Poisk v ST-telah programm: gde USINT/BYTE upotreblyaetsya kak uslovie.

ZAPUSKAT SISTEMNYM PYTHON 3.

ZADAChA. 12 oshibok C32 vida "USINT v BOOL" i "BOOL v USINT". Staticheskij
analiz FBD-shem ih ne nahodit -- znachit oni v ST. Tipichnaya prichina:
v uslovii (IF/WHILE/ELSIF) stoit peremennaya tipa BYTE, libo BYTE-poluchayut
znachenie BOOL-bes vozvrashchaemogo vyrazheniya.
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GEN = os.path.join(ROOT, u"generator", u"gen_z80.py")

# tipy peremennyh iz GVL i obyavlenij ST
def collect_types():
    types = {}
    for f in sorted(os.listdir(os.path.join(ROOT, u"src"))):
        if not f.endswith(u".gvl"):
            continue
        t = re.sub(u"\\(\\*.*?\\*\\)", u" ", io.open(os.path.join(ROOT, u"src", f),
                                                    encoding=u"utf-8").read(), flags=re.S)
        for m in re.finditer(u"(?m)^\\s*(\\w+)\\s*:\\s*([A-Za-z0-9_\\[\\]\\. ]+?)\\s*;", t):
            types[m.group(1)] = m.group(2).strip().upper()
    return types


BYTELIKE = (u"BYTE", u"USINT", u"WORD", u"UINT", u"DWORD", u"UDINT", u"INT", u"DINT")


def main():
    types = collect_types()
    t = io.open(GEN, encoding=u"utf-8").read()
    lines = t.split(u"\n")
    n_if = 0
    n_asg = 0

    for i, ln in enumerate(lines, 1):
        s = ln.strip()
        # 1) usloviya IF/WHILE/ELSIF/UNTIL s BYTE-peremennoj
        m = re.match(u"^(IF|WHILE|ELSIF|UNTIL|REPEAT)\\s*\\(?\\s*([A-Za-z_][A-Za-z0-9_.]*)", s)
        if m:
            var = m.group(2).split(u".")[-1]
            tp = types.get(var)
            if tp and any(tp.startswith(b) for b in BYTELIKE):
                sys.stdout.write(u"%5d: USLOVIE s %-16s (%s):  %s\n" % (i, var, tp, s[:80]))
                n_if += 1
        # 2) prisvaivanie BYTE-peremennoj buleva vyrazheniya
        m2 = re.match(u"^([A-Za-z_][A-Za-z0-9_]*)\\s*:=\\s*(.+);$", s)
        if m2:
            dst, expr = m2.group(1), m2.group(2)
            tp = types.get(dst)
            if tp and any(tp.startswith(b) for b in BYTELIKE):
                if re.search(u"(NOT\\s|AND|OR|XOR|\\bTRUE\\b|\\bFALSE\\b|<>|>=|<=)", expr) \
                        and u"_TO_" not in expr:
                    sys.stdout.write(u"%5d: %-16s (%s) := %s\n" % (i, dst, tp, expr[:70]))
                    n_asg += 1

    sys.stdout.write(u"\nuslovij s BYTE: %d, prisvaivanij BOOL v BYTE: %d\n" % (n_if, n_asg))


if __name__ == u"__main__":
    main()
