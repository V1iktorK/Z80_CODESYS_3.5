# -*- coding: utf-8 -*-
u"""Proverka: voobshche li app.build() kompiliruet kod?

ZAPUSKAT SISTEMNYM PYTHON 3.

ZADAChA. Dva opyta podryad dali "0 oshibok, 0 preduprezhdeniy":
  * kogda v GVL_Bus ne bylo ob''yavlenij Bus_Addr / Bus_Data;
  * kogda v shemu podstavili ssylku na GVL_Bus.EtoTochnoNet.
Oba raza ozhidalas oshibka. Znachit pod voprosom sam kriteriy "0 oshibok".

CHTO DELAEM: vstraivaem v PRG_InitMemory ZAVEDOMO nedopustimuyu stroku
(`ETO @@@ sindaksicheskaya oshibka;`) i smotrim, poyavit li kompilyator
hot chto-nibud. Chtoby proverka ne zavisela ot togo, chto kompilyator
propuskaet neopredelennye imena, oshibka imenno LEKSIChESKAYa.

POSLE PROVERKI: python generator/tools/probe_build_compiles.py --restore
"""
import io
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, u"src")
ORIG = os.path.join(SRC, u"PRG_InitMemory.plcopenxml")
BAK = os.path.join(SRC, u"PRG_InitMemory.plcopenxml.orig")

BAD = u"ETO @@@ sindaksicheskaya oshibka;\n"


def main():
    src = io.open(ORIG, encoding=u"utf-8").read()
    # vstraivaem oshibku v SAMOE nachalo tela ST
    i = src.find(u"<ST>")
    if i < 0:
        print(u"net tela ST v PRG_InitMemory")
        return
    j = src.find(u">", src.find(u"xhtml", i)) + 1
    broken = src[:j] + BAD + src[j:]
    shutil.copyfile(ORIG, BAK)
    io.open(ORIG, u"w", encoding=u"utf-8").write(broken)
    print(u"v PRG_InitMemory vstavlena zavedomaya oshibka:")
    print(u"   %s" % BAD.strip())
    print(u"teper zapustite sborku i posmotrite build.log")


def restore():
    if os.path.exists(BAK):
        shutil.copyfile(BAK, ORIG)
        os.remove(BAK)
        print(u"original PRG_InitMemory vosstanovlen")
    else:
        print(u"rezervnoj kopii net -- vosstanovite: python generator/gen_z80.py")


if __name__ == u"__main__":
    if u"--restore" in sys.argv:
        restore()
    else:
        main()
