# -*- coding: utf-8 -*-
u"""Svodnaya diagnostika po otchyotu iz IDE.

ZAPUSKAT SISTEMNYM PYTHON 3.
    python diag_ide_report.py

Proveryaet tri gruppy problem iz otchyota polzovatelya:
  1) otsutstvuyushchie chleny GVL (naprimer Tests) -- sverka vseh
     GVL_x.chlen v ST-tekstah s deklaraciyami GVL;
  2) neveroyatnye konvertory BYTE_TO_BYTE / WORD_TO_WORD i t. p.;
  3) C0383 "Obyavlenie POU ne zaversheno bez imeni" -- provrit, chto
     zagolovok POU i bloki VAR v poryadke.
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEN = os.path.join(ROOT, u"generator", u"gen_z80.py")
SRC = os.path.join(ROOT, u"src")


def gvl_members():
    out = {}
    for f in sorted(os.listdir(SRC)):
        if not f.endswith(u".gvl"):
            continue
        t = re.sub(u"\\(\\*.*?\\*\\)", u" ", io.open(os.path.join(SRC, f),
                                                    encoding=u"utf-8").read(), flags=re.S)
        out[f[:-4]] = set(re.findall(u"(?m)^\\s*(\\w+)\\s*:", t))
    return out


def main():
    g = gvl_members()
    gen = io.open(GEN, encoding=u"utf-8").read()

    sys.stdout.write(u"=== 1. SSYLKI GVL_x.chlen V GENERATORE ===\n")
    ref = re.compile(u"(GVL_\\w+)\\.(\\w+)")
    bad = {}
    for m in ref.finditer(gen):
        gl, mem = m.group(1), m.group(2)
        if gl not in g:
            bad.setdefault(u"%s.%s" % (gl, mem), u"net takogo GVL")
            continue
        if mem not in g[gl]:
            bad.setdefault(u"%s.%s" % (gl, mem), u"net chlena")
    if bad:
        for k in sorted(bad):
            sys.stdout.write(u"   NET: %-42s (%s)\n" % (k, bad[k]))
    else:
        sys.stdout.write(u"   vse ssylki korrektny\n")

    sys.stdout.write(u"\n=== 2. NEVEROYaTNYE KONVERTORY ===\n")
    weird = 0
    for f in sorted(os.listdir(SRC)):
        if not f.endswith(u".plcopenxml"):
            continue
        t = io.open(os.path.join(SRC, f), encoding=u"utf-8").read()
        for m in re.finditer(u'typeName="(\\w+)_TO_(\\w+)"', t):
            if m.group(1) == m.group(2):
                sys.stdout.write(u"   %s: %s\n" % (f[:-12], m.group(0)))
                weird += 1
    if not weird:
        sys.stdout.write(u"   net\n")

    sys.stdout.write(u"\n=== 3. STRUKTURA OB''YaVLENIY ST-PROGRAMM ===\n")
    for name in (u"TEST_Z80", u"TEST_Z80_CPM", u"PRG_CPM_BDOS",
                 u"PRG_InitMemory", u"PRG_LoadTestProgram", u"PRG_CPM_Boot"):
        path = os.path.join(SRC, name + u".plcopenxml")
        if not os.path.exists(path):
            continue
        t = io.open(path, encoding=u"utf-8").read()
        m = re.search(u"<InterfaceAsPlainText>.*?<xhtml[^>]*>(.*?)</xhtml>", t, re.S)
        if not m:
            sys.stdout.write(u"   %-22s NET obyavleniya\n" % name)
            continue
        decl = m.group(1)
        lines = decl.split(u"\n")
        head = lines[0] if lines else u""
        ends = [i for i, l in enumerate(lines) if l.strip().startswith(u"END_VAR")]
        nvars = len([l for l in lines if re.match(u"^\\s*\\w+\\s*:", l)])
        sys.stdout.write(u"   %-22s zagolovok=%r  END_VAR=%d  peremennyh=%d\n"
                         % (name, head[:44], len(ends), nvars))

    sys.stdout.write(u"\n=== 4. GVL: est li massiv testov ===\n")
    for gl in (u"GVL_Tests", u"GVL_Tests_CPM"):
        mem = sorted(g.get(gl, []))
        sys.stdout.write(u"   %-16s chlenov=%d\n" % (gl, len(mem)))
        if u"Tests" not in mem:
            sys.stdout.write(u"      !!! NET massiva Tests\n")


if __name__ == u"__main__":
    main()
