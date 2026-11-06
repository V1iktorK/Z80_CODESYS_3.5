# -*- coding: utf-8 -*-
u"""Dobavit' v GVL_Control chetyre propushchennyh signala dekodera.

ZAPUSKAT SISTEMNYM PYTHON 3 ODIN RAZ.

SHEMA PLC_PRG peredaet v GVL_Control vyhody dekodera Ctl_Is_Jr, Ctl_Is_IN,
Ctl_Is_OUT, Ctl_IO_Rd, Ctl_IO_Wr. V obyavleniyah GVL ih ne bylo, i
kompilyator soobshchal "C4: 'Ctl_Is_Jr' ne yavlyaetsya komponentom
'GVL_Control'". Spisok perenosa (ctl_names) uzhe rasshiren, ostaetsya
dobavit imena v sam GVL.
"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEN = os.path.join(ROOT, u"generator", u"gen_z80.py")

ANCHOR = u"    Ctl_IncDec    : BOOL;   (* INC/DEC: operand = 1 *)\n"
ADD = (u"    Ctl_Is_Jr     : BOOL;   (* JR -- perehod otnositelnyy *)\n"
       u"    Ctl_IO_Rd     : BOOL;   (* strob chteniya porta I/O *)\n"
       u"    Ctl_IO_Wr     : BOOL;   (* strob zapisi v port I/O *)\n")


def main():
    t = io.open(GEN, encoding=u"utf-8").read()
    if u"Ctl_Is_Jr     : BOOL" in t:
        sys.stdout.write(u"uzhe dobavleno\n")
        return
    if ANCHOR not in t:
        sys.stdout.write(u"ANKER NE NAJDEN\n")
        return
    t = t.replace(ANCHOR, ANCHOR + ADD, 1)
    io.open(GEN, u"w", encoding=u"utf-8").write(t)
    sys.stdout.write(u"GVL_Control: dobavleny Ctl_Is_Jr, Ctl_IO_Rd, Ctl_IO_Wr\n"
                     u"(Ctl_Is_IN i Ctl_Is_OUT uzhe byli v obyavleniyah)\n")


if __name__ == u"__main__":
    main()
