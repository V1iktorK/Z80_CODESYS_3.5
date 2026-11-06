# -*- coding: utf-8 -*-
u"""Tochnaya pochinka strok outvar s poteryannymi skobkami.

ZAPUSKAT SISTEMNYM PYTHON 3 ODIN RAZ.

ChTO NADO IS PRAVIT'. Posle dvuh neakkuratnyh avtomaticheskih zamen poluchilos'
    n7.outvar(u"vImm", n7.invar(u"vMem_Rd_Data", y=60, x=F.COL_OUT, y=480)
Vmesto
    n7.outvar(u"vImm", n7.invar(u"vMem_Rd_Data", y=60), x=F.COL_OUT, y=480)

Algoritm: dlya kazhdoj stroki s ".outvar(" nahodim poziciyu ", x=F.COL_OUT" i
perestavlyaem skobki tak, chtoby argument vnutrennego invar zakryvalsya pered
etoj zapyatoj, a vneshnij outvar -- v konce stroki.
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEN = os.path.join(ROOT, u"generator", u"gen_z80.py")

TARGET = u", x=F.COL_OUT, y="


def fix_line(ln):
    u"""Perepostroit' stroku vida ...outvar(u"D", nX.invar(u"S", y=A, x=F.COL_OUT, y=B)"""
    i = ln.find(u".outvar(")
    if i < 0:
        return ln, False
    k = ln.find(TARGET, i)
    if k < 0:
        return ln, False
    head = ln[:k]                       # ...outvar(u"D", nX.invar(u"S", y=A
    tail = ln[k:]                       # , x=F.COL_OUT, y=B)
    # v head nado zakryt' invar: dobavlyaem ")" esli ego net pered zapyatoj
    if not head.rstrip().endswith(u")"):
        head = head.rstrip() + u")"
    # v hvoste nado zakryt' outvar
    if tail.count(u"(") < tail.count(u")"):
        pass
    elif tail.rstrip().endswith(u")"):
        tail = tail.rstrip() + u")"
    else:
        tail = tail.rstrip() + u")"
    return head + u", x=F.COL_OUT" + tail[tail.find(u", y="):], True


def main():
    lines = io.open(GEN, encoding=u"utf-8").read().split(u"\n")
    n = 0
    for i, ln in enumerate(lines):
        if u".outvar(" not in ln:
            continue
        # uzhe pravilnaya stroka?
        new, ch = fix_line(ln)
        if ch and new != ln:
            lines[i] = new
            sys.stdout.write(u"%5d: %s\n" % (i + 1, new.strip()))
            n += 1
    io.open(GEN, u"w", encoding=u"utf-8").write(u"\n".join(lines))
    sys.stdout.write(u"\nispravleno: %d\n" % n)


if __name__ == u"__main__":
    main()
