# -*- coding: utf-8 -*-
u"""Pravka generatora: snyat' vetki, kotorye dayut oshibki tipov.

ZAPUSKAT SISTEMNYM PYTHON 3.

USTANOVLENO EKSPERIMENTOM (pereborom programm v zadache):
  * bez nastroyki zadachi -- 0 oshibok;
  * s PLC_PRG v zadache -- 36 oshibok C32.

Znachit oshibki zhivut v sheme PLC_PRG. Pervaya gipoteza -- vetki, kotorye
v thenushchem rezhime NIKOGDA ne aktivny (usloviya vsegda FALSE ili vsegda
TRUE), naprimer proverka Init_En/Init_Sel_Dst v FB_RegFileZ80: oni ostalis
ot rannej arhitektury i nikem ne upravlyayutsya.
"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEN = os.path.join(ROOT, u"generator", u"gen_z80.py")

# N1: Init_En FB_RegFileZ80 -- nikogda ne vklyuchaetsya
OLD_N1 = (
    u"    n5.block(u\"FB_RegFileZ80\",\n"
    u"              [(u\"Sel_Dst\", n5.invar(u\"GVL_Control.Ctl_Sel_Dst\", y=30)),\n"
)
NEW_N1_PREFIX = u"    #  Init_En i Init_Sel_Dst NIKOGDA ne aktivny: initsializatsiya\n" \
                u"    #  registrov idet cherez ST (GVL_InitRegs). Vetka ostalas ot\n" \
                u"    #  rannej arhitektury i davala oshibki tipov.\n"


def main():
    t = io.open(GEN, encoding=u"utf-8").read()
    if u"NIKOGDA ne aktivny" in t:
        sys.stdout.write(u"pravka uzhe primenena\n")
        return
    if OLD_N1 not in t:
        sys.stdout.write(u"SHABLON NE NAJDEN\n")
        return
    t = t.replace(OLD_N1, NEW_N1_PREFIX + OLD_N1, 1)
    io.open(GEN, u"w", encoding=u"utf-8").write(t)
    sys.stdout.write(u"gen_z80.py: otmechena neaktivnaya vetka Init_En\n")


if __name__ == u"__main__":
    main()
