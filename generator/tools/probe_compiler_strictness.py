# -*- coding: utf-8 -*-
u"""Proverka: lovit li kompilyator ssylku na nesushchestvuyushchuyu peremennuyu?

ZAPUSKAT SISTEMNYM PYTHON 3.

KONTEKST. Odna iz sborkok pokazala "0 oshibok, 0 preduprezhdeniy", hotya v
GVL_Bus ne bylo ob''yavlenij Bus_Addr / Bus_Data, a shema PLC_PRG na nih
ssylalas. Znachit schetchik oshibok kompilyatora nel'zya schitat dokazatelstvom
korrektnosti. Nado ponyat, pochemu.

SHEMA PROVERKI (bez pravki generatora!):
  1. Kopiruem shemu PLC_PRG.
  2. Menyaem v kopii odno iz upominanij GVL_Bus.Bus_Addr na zaglushku
     GVL_Bus.EtoTochnoNet -- takogo imeni v proekte net ni v odnoj GVL.
  3. Sborka podstavlyaet kopiyu v import VME STO originala.
  4. Smotrim, poyavitsya li oshibka kompilyacii.
  5. Kopiyu udalyaem, original ne tronut.

REZULTAT interpretiruem tak:
  * oshibka est  -> kompilyator strogiy, i "0 oshibok" doveren;
  * oshibki net  -> u kompilyatora SP17 est rezhim, kogda on molchit, i togda
    nuzhen sobstvennyy proverNNa imen (on u nas est: sverka GVL + deklaracij).
"""
import io
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, u"src")
ORIG = os.path.join(SRC, u"PLC_PRG.plcopenxml")
BAK = os.path.join(SRC, u"PLC_PRG.plcopenxml.orig")
STUB = u"GVL_Bus.EtoTochnoNet"


def main():
    src = io.open(ORIG, encoding=u"utf-8").read()

    # 1) ubezhdaemsya, chto zaglushki v proekte net
    hit = False
    for f in os.listdir(SRC):
        if f.endswith((u".gvl", u".plcopenxml")):
            t = io.open(os.path.join(SRC, f), encoding=u"utf-8").read()
            if u"EtoTochnoNet" in t:
                print(u"VNIMANIE: zaglushka uzhe est v %s" % f)
                hit = True
    if hit:
        print(u"ubedites, chto zaglushki net, i zapustite snova")
        return

    n = src.count(u"GVL_Bus.Bus_Addr<")
    print(u"ssylok na GVL_Bus.Bus_Addr v PLC_PRG: %d" % n)
    if n == 0:
        print(u"net ssylok -- proverka nevozmozhna")
        return

    # 2) delaem kopiyu s zaglushkoy
    broken = src.replace(u"GVL_Bus.Bus_Addr<", STUB + u"<", 1)
    if broken == src:
        print(u"zamena ne srabotala")
        return

    print(u"podstavlyaem kopiyu s %s" % STUB)
    shutil.copyfile(ORIG, BAK)                    # original v bezopasnosti
    io.open(ORIG, u"w", encoding=u"utf-8").write(broken)
    print(u"gotovo. Teper zapustite sborku i posmotrite build.log.")
    print(u"POSLE PROVERKI obyazatelno: python generator/tools/probe_compiler_strictness.py --restore")


def restore():
    if os.path.exists(BAK):
        shutil.copyfile(BAK, ORIG)
        os.remove(BAK)
        print(u"original PLC_PRG vosstanovlen")
    else:
        print(u"rezervnoj kopii net -- vosstanovite: python generator/gen_z80.py")


if __name__ == u"__main__":
    if u"--restore" in sys.argv:
        restore()
    else:
        main()
