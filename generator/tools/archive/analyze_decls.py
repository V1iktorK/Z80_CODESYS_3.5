# -*- coding: utf-8 -*-
u"""Analiz: kakie peremennye ob''yavlyayut funkcii-generatory i kakie signaly oni ispolzuyut.

ZAPUSKAT SISTEMNYM PYTHON 3.

Nuzhno, chtoby ponyat tipy nedoopredelennyh signalov (BOOL/BYTE/WORD) i
resit, kak ih ob''yavit: p.var(...) v generatore.
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEN = os.path.join(ROOT, u"generator", u"gen_z80.py")

FUNCS = (u"mk_regfile", u"mk_alu", u"mk_bdos", u"mk_cpm_bios")
DECL = re.compile(u"p\\.var(_in|_out)?\\(u\"([A-Za-z0-9_]+)\",\\s*u\"([^\"]+)\"")
NET = re.compile(u"\\bn\\d*\\.(invar|outvar)\\(u\"([^\"]+)\"")


def body_of(text, fn):
    i = text.find(u"def %s():" % fn)
    if i < 0:
        return None
    j = text.find(u"\ndef ", i + 10)
    return text[i:j if j > 0 else len(text)]


def main():
    text = io.open(GEN, encoding=u"utf-8").read()
    for fn in FUNCS:
        body = body_of(text, fn)
        sys.stdout.write(u"=========== %s ===========\n" % fn)
        if body is None:
            sys.stdout.write(u"  funkciya ne najdena\n")
            continue
        sys.stdout.write(u"  --- OB''YaVLYAET ---\n")
        for m in DECL.finditer(body):
            kind = {None: u"var", u"_in": u"var_in", u"_out": u"var_out"}[m.group(1)]
            sys.stdout.write(u"    %-9s %-16s %s\n" % (kind, m.group(2), m.group(3)))
        sys.stdout.write(u"  --- ISPOLZUET kak signal ---\n")
        seen = []
        for m in NET.finditer(body):
            name = m.group(2)
            if name not in seen:
                seen.append(name)
        sys.stdout.write(u"    %s\n" % u", ".join(seen))
        sys.stdout.write(u"\n")


if __name__ == u"__main__":
    main()
