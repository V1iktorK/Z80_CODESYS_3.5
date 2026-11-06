# -*- coding: utf-8 -*-
u"""Ispravit' tipy peremennyh v*_* v PLC_PRG po faktam iz sgenerirovannyh shem.

ZAPUSKAT SISTEMNYM PYTHON 3 ODIN RAZ.

ChTO NE TAK. Avtomaticheskij patч perenes vyhody FB v peremennye, no vsem
prisvoil tip BYTE. Na samom dele tipy raznye: PC_New i SP -- WORD, Halted i
PC_Load -- BOOL. Iz-za etogo dobavilos' 26 novyh oshibok C32.

Zdes berem tip kazhdogo vyhoda pryamo iz strukturnogo <interface>
sootvetstvuyushchego FB i podstavlyaem v obyavlenie.
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEN = os.path.join(ROOT, u"generator", u"gen_z80.py")
SRC = os.path.join(ROOT, u"src")

# kakoy peremennoy sootvetstvuet kakoy FB i vyvod
MAP = {
    u"vRFRd_Addr_HL": (u"FB_RegFileZ80", u"Addr_HL"),
    u"vMem_D_Out": (u"FB_Memory64K", u"D_Out"),
    u"vMem_Bus_Drv": (u"FB_Memory64K", u"Bus_Drv"),
    u"vMem_Rd_Data": (u"FB_Memory64K", u"Rd_Data"),
    u"vMem_SP_Out": (u"FB_Memory64K", u"SP_Out"),
    u"vALU_Y": (u"FB_ALU_Z80", u"Y"),
    u"vFlags_F": (u"FB_FlagsRegZ80", u"F"),
    u"vSP_SP": (u"FB_SP_StackZ80", u"SP"),
    u"vCtl_PC_New": (u"FB_ControlUnit", u"PC_New"),
    u"vCtl_PC_Load": (u"FB_ControlUnit", u"PC_Load"),
    u"vCtl_Inc_By": (u"FB_ControlUnit", u"Inc_By"),
    u"vCtl_Halted": (u"FB_ControlUnit", u"Halted"),
    u"vPC_PC_Next": (u"FB_PC_Z80", u"PC_Next"),
    u"vR_Q": (u"FB_Reg8", u"Q"),
}


def out_type(fb, pin):
    path = os.path.join(SRC, fb + u".plcopenxml")
    if not os.path.exists(path):
        return None
    t = io.open(path, encoding=u"utf-8").read()
    m = re.search(u"<outputVars>(.*?)</outputVars>", t, re.S)
    if not m:
        return None
    for v in re.finditer(u'<variable name="(\\w+)"><type>(?:<(\\w+)\\s*/>'
                         u'|<derived name="(\\w+)")', m.group(1)):
        if v.group(1) != pin:
            continue
        return v.group(2) or v.group(3)
    return None


def main():
    t = io.open(GEN, encoding=u"utf-8").read()
    n = 0
    for var, (fb, pin) in sorted(MAP.items()):
        tp = out_type(fb, pin)
        if not tp:
            sys.stdout.write(u"  %-18s tip NE NAJDEN v %s\n" % (var, fb))
            continue
        old = u'p.var(u"%s", u"BYTE", u"vyhod FB cherez peremennuyu")' % var
        new = u'p.var(u"%s", u"%s", u"vyhod %s.%s")' % (var, tp, fb, pin)
        if old in t:
            t = t.replace(old, new, 1)
            n += 1
            sys.stdout.write(u"  %-18s -> %s\n" % (var, tp))
        elif new in t:
            sys.stdout.write(u"  %-18s uzhe %s\n" % (var, tp))
        else:
            sys.stdout.write(u"  %-18s STROKA NE NAJDENA\n" % var)
    io.open(GEN, u"w", encoding=u"utf-8").write(t)
    sys.stdout.write(u"\nispravleno tipov: %d\n" % n)


if __name__ == u"__main__":
    main()
