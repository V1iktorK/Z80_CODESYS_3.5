# -*- coding: utf-8 -*-
u"""Poisk v generatore: gde BYTE-poluchayut BOOL i naoborot.

ZAPUSKAT SISTEMNYM PYTHON 3.

ZADAChA. Kompilyator daet 12 oshibok C32 vida "BOOL v USINT", "USINT v BOOL",
"WORD v BYTE", "UDINT v WORD". Staticheskij analiz shem ih ne nahodit (znachit
delo v ST-tekstah), a soobshcheniya ne soderzhat nomerov strok.

Zdes ishem v ST-tekstah generatora prisvaivaniya vida
    <peremennaya_tipa_X> := <vyrazhenie>;
gde vyrazhenie po vidu yavno drugogo tipa.
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEN = os.path.join(ROOT, u"generator", u"gen_z80.py")

BOOLFUN = re.compile(u"^(NOT|AND|OR|XOR)|=(\\s|$)|<>|>=|<=")
WORDFUN = re.compile(u"^SHL\\(|^SHR\\(|^WORD_TO_|\\*\\s*256")


def main():
    t = io.open(GEN, encoding=u"utf-8").read()
    lines = t.split(u"\n")
    hits = 0
    for i, ln in enumerate(lines, 1):
        s = ln.strip()
        m = re.match(u"^([A-Za-z_][A-Za-z0-9_]*)\\s*:=\\s*(.+);$", s)
        if not m:
            continue
        dst, expr = m.group(1), m.group(2)
        # interessuyut tolko imena, kotorye yavno pohozhii na BYTE/WORD-flagi
        if not re.search(u"(?i)(_out|byte|word|dma|addr|count|cnt|len|num|val|code|reg|sp_|pc_|ch|char)", dst):
            continue
        if BOOLFUN.search(expr) and u"BOOL_TO" not in expr:
            sys.stdout.write(u"%5d: %s := %s\n" % (i, dst, expr[:90]))
            hits += 1
    sys.stdout.write(u"\nkandidatov: %d\n" % hits)


if __name__ == u"__main__":
    main()
