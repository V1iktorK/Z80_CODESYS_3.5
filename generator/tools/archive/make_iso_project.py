# -*- coding: utf-8 -*-
u"""Sobrat' proverochnyj proekt iz UZHE sgenerirovannyh POU -- chtoby ponyat,
v shemah ili v ST-programmah zhivut oshibki C32.

ZAPUSKAT SISTEMNYM PYTHON 3. Rezultat -- tests/iso/ *.plcopenxml.

Rezhim (pervyj argument):
    fbd   -- tolko FBD-shemy (FB_*)
    st    -- tolko ST-programmy (PRG_*, TEST_*)
    one <imya> -- odin POU
"""
import io
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(ROOT, u"src")
OUT = os.path.join(ROOT, u"tests", u"iso")


def copy_pou(name, dst_dir):
    src = os.path.join(SRC, name + u".plcopenxml")
    shutil.copyfile(src, os.path.join(dst_dir, name + u".plcopenxml"))
    return src


def copy_gvls(dst_dir):
    for f in sorted(os.listdir(SRC)):
        if f.endswith(u".gvl"):
            shutil.copyfile(os.path.join(SRC, f), os.path.join(dst_dir, f))


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else u"all"
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    copy_gvls(OUT)

    fbd = [u"FB_Reg8", u"FB_Reg16", u"FB_RTrig", u"FB_FTrig", u"FB_RS",
           u"FB_Reg8Latch", u"FB_BitUnpack8", u"FB_ADDER8", u"FB_RegFileZ80",
           u"FB_ALU_Z80", u"FB_FlagsRegZ80", u"FB_DecoderZ80", u"FB_Memory64K",
           u"FB_PC_Z80", u"FB_SP_StackZ80", u"FB_ControlUnit", u"FB_Clock",
           u"FB_TestCase", u"FB_AlwaysTrue", u"FB_HW_IO_PLC", u"FB_IO_Ports",
           u"FB_CPM_Disk", u"FB_CPM_BDOS", u"FB_CPM_BIOS"]
    st = [u"PRG_InitMemory", u"PRG_LoadTestProgram", u"PRG_CPM_Boot",
          u"PRG_CPM_BDOS", u"TEST_Z80", u"TEST_Z80_CPM"]

    if mode == u"fbd":
        names = fbd
    elif mode == u"st":
        names = st
    elif mode == u"one":
        names = [sys.argv[2]]
    else:
        names = fbd + st

    for n in names:
        copy_pou(n, OUT)
    sys.stdout.write(u"skopirovano v %s: %d POU\n" % (OUT, len(names)))


if __name__ == u"__main__":
    main()
