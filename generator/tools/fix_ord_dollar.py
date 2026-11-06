# -*- coding: utf-8 -*-
u"""Shagi 2-3 plana: ubrat' '$' i zamenit' ORD('X') na hex-kody.

ZAPUSKAT SISTEMNYM PYTHON 3 ODIN RAZ.

P O Ch E M U.

1) '$' v CODESYS -- ESCAPE-simvol vnutri strokovyh literalov. Stroka
   ORD('$') obrazyvaet parser: vydayutsya C0008 (nedopustimyj End-of-file),
   C0189 i C0007 so obryvkom teksta, i ves ostavshijsya fajl uezzhaet
   v musor. Poetomu simvol '$' zamenyаem ego kodom 16#24, a sam simvol
   ostavlyaem v kommentarii -- tak i chitaemo, i kompilyator dovolen.

2) Funkcii ORD(...) v etoy sborke CODESYS net: 27 oshibok
   "C0046: Identifikator 'ORD' ne zadаn". Zamенyaem na chislovye kody
   s sohraneniem simvola v kommentarii.

Bylo:                                       Stalo:
    Z80_Mem[16#0100] := ORD('H');               Z80_Mem[16#0100] := 16#48;   (* 'H' *)
    Z80_Mem[16#0121] := ORD('$');               Z80_Mem[16#0121] := 16#24;   (* '$' *)
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEN = os.path.join(ROOT, u"generator", u"gen_z80.py")

#  ORD('X') ili ORD(' ') -- odin simvol v odinarnyh kavychkah
PAT = re.compile(u"ORD\\('(.)'\\)")
PAT_ESC = re.compile(u"ORD\\('\\$\\$'\\)")     # ORD('$$') -- ekranirovannyj $


def main():
    t = io.open(GEN, encoding=u"utf-8").read()
    before = len(PAT.findall(t)) + len(PAT_ESC.findall(t))

    #  snachala ekranirovannye varianty
    t, n_esc = PAT_ESC.subn(u"16#24;   (* '$' *)", t)

    def repl(m):
        ch = m.group(1)
        return u"16#%02X;   (* '%s' *)" % (ord(ch), ch)

    t, n = PAT.subn(repl, t)
    #  ubrat' lishnyuyu tochku s zapyatoj, esli ona uzhe byla posle ORD(...)
    t = re.sub(u"16#([0-9A-F]{2});   \\(\\* '(.)' \\*\\);", u"16#\\1;   (* '\\2' *)", t)

    io.open(GEN, u"w", encoding=u"utf-8").write(t)
    sys.stdout.write(u"najdeno ORD(: %d, zamенено: %d (v tom chisle '$': %d)\n"
                     % (before, n + n_esc, n_esc))
    left = len(re.findall(u"\\bORD\\s*\\(", t))
    dollar = len(re.findall(u"\\$", t))
    sys.stdout.write(u"ostalos ORD(: %d, simvolov '$': %d\n" % (left, dollar))
    if left or dollar:
        for m in re.finditer(u"\\bORD\\s*\\(|\\$", t):
            ln = t[:m.start()].count(u"\n") + 1
            sys.stdout.write(u"   stroka %d: %s\n"
                             % (ln, t.split(u"\n")[ln - 1].strip()[:90]))
    else:
        sys.stdout.write(u"chisto\n")


if __name__ == u"__main__":
    main()
