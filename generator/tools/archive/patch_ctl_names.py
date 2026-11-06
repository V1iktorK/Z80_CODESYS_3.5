# -*- coding: utf-8 -*-
u"""Dobavit' tri propushchennyh signala dekodera v spisok ctl_names.

ZAPUSKAT SISTEMNYM PYTHON 3 ODIN RAZ.

P O Ch E M U. Kompilyator soobshchil:
    C4:  'Ctl_Is_Jr' ne yavlyaetsya komponentom 'GVL_Control'
    C46: Identifikator 'vCtl_IO_Rd' ne zadan
    C77: Neizvestnyy tip: 'vCtl_IO_Wr'
Znachit u FB_DecoderZ80 est vyhody, kotorye ne popali v spisok perenosa:
Ctl_Is_Jr, Ctl_Is_IN, Ctl_Is_OUT, Ctl_IO_Rd, Ctl_IO_Wr. Ih nado dobavit,
inache oni nikuda ne peredautsya i o stayutsya bez obyavleniya.
"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEN = os.path.join(ROOT, u"generator", u"gen_z80.py")

OLD = (u'                 u"Ctl_Sel_Src", u"Ctl_ALU_Op", u"Ctl_Cond", u"Ctl_IncDec")\n')
NEW = (u'                 u"Ctl_Sel_Src", u"Ctl_ALU_Op", u"Ctl_Cond", u"Ctl_IncDec",\n'
       u'                 u"Ctl_Is_IN", u"Ctl_Is_OUT", u"Ctl_IO_Rd", u"Ctl_IO_Wr")\n')


def main():
    t = io.open(GEN, encoding=u"utf-8").read()
    if u"Ctl_IO_Rd" in t.split(u"ctl_names = (")[1][:400]:
        sys.stdout.write(u"uzhe dobavleno\n")
        return
    if OLD not in t:
        sys.stdout.write(u"SHABLON NE NAJDEN\n")
        return
    t = t.replace(OLD, NEW, 1)
    io.open(GEN, u"w", encoding=u"utf-8").write(t)
    sys.stdout.write(u"ctl_names: dobavleny Ctl_Is_IN, Ctl_Is_OUT, Ctl_IO_Rd, Ctl_IO_Wr\n")


if __name__ == u"__main__":
    main()
