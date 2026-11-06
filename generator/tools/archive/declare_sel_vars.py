# -*- coding: utf-8 -*-
u"""O B Ya V L E N I E  vremennyh peremennyh dlya tsepochek SEL.

Z A Ch E M. Cepochka SEL v FBD ne mozhet byt obobshchennoj: kogda v nej
ryadom okazyvayutsya vetki i usloviya raznogo tipa, CODESYS beret USINT
dlya vseh i syplet parami
    C32: Nevozmozhno konvertirovat tip 'BOOL' v tip 'USINT'
    C32: Nevmozmozhno konvertirovat tip 'USINT' v tip 'BOOL'.
Lechenie -- promezhutochnye peremennye s yavnym tipom. No oni dolzhny byt
obyavleny V O B Ya V L E N I I P O U, a ne v tele seti: esli obyavit ih
v seti, CODESYS schitaet ih "lazy" i otkazyvaetsya vyvodit tip
("Tip lazy peremennoj '__FB_IO_Ports__ImpVarN' ne mozhet byt razreshen").

Ch T O  D E L A E M. Dobavlyaem v obyavleniya treh POU nabor
    vBYTE_0 .. vBYTE_N   (vetki cepochki, tip BYTE)
    vBYTECond_0 .. vBYTECond_K   (usloviya, tip BOOL)
Kolichestvo schitaem po chislu vyzovov sel_chain v generatore.

ZAPUSK: python generator\tools\declare_sel_vars.py
Otkat:  generator\gen_z80.bak_selvars
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GEN = os.path.join(ROOT, u"generator", u"gen_z80.py")

#  POU -> (skolko vetok, skolko uslovij)
#  Vetok vsegda na odnu bolshe, chem uslovij: poslednyaya -- rezervnaya IN0.
TARGETS = [
    (u"FB_RegFileZ80", 13, 12),
    (u"FB_IO_Ports", 10, 9),
]


def main():
    try:
        sys.stdout.reconfigure(encoding=u"utf-8", errors=u"replace")
    except Exception:                                          # noqa: BLE001
        pass
    src = io.open(GEN, encoding=u"utf-8").read()

    for pou, nbranch, ncond in TARGETS:
        lines = src.split(u"\n")
        #  ishchem IMENNO prisvoenie vida "nX = p.network(", a ne upominanie
        #  p.network v kommentarii: pervaya versiya etogo skripta vstavila
        #  obyavleniya v seredinu stroki "nw =" i slomala fajl.
        start = None
        for n, l in enumerate(lines):
            if u'p = F.Pou(u"%s"' % pou in l:
                start = n
                break
        if start is None:
            sys.stdout.write(u"NE NAJDEN POU %s\n" % pou)
            return 1
        at = None
        for n in range(start, min(start + 120, len(lines))):
            if re.match(u"^\\s*\\w+\\s*=\\s*p\\.network\\(", lines[n]):
                at = n
                break
        if at is None:
            sys.stdout.write(u"NE NAJDEN pervyj p.network u %s\n" % pou)
            return 1

        block = []
        block.append(u"    #  --- P R O M E Zh U T O Ch N Y E  P E R E M E N N Y E")
        block.append(u"    #  dlya tsepochek SEL -- sm. kommentarij u sel_chain().")
        block.append(u"    #  Vetki cepochki (tip uzhe zadan) i usloviya (BOOL): bez nih")
        block.append(u"    #  CODESYS ne mozhet soglasovat tipy i daet pary C32 'BOOL'")
        block.append(u"    #  <-> 'USINT' bez imeni POU i bez nomera stroki.")
        for n in range(nbranch):
            block.append(u'    p.var(u"vBYTE_%d", u"BYTE")' % n)
        for n in range(ncond):
            block.append(u'    p.var(u"vBYTECond_%d", u"BOOL")' % n)
        block.append(u"")
        lines[at:at] = block
        src = u"\n".join(lines)
        sys.stdout.write(u"%s: vetok %d, uslovij %d (stroka %d)\n"
                         % (pou, nbranch, ncond, at + 1))

    io.open(GEN, u"w", encoding=u"utf-8").write(src)
    sys.stdout.write(u"gotovo\n")
    return 0


if __name__ == u"__main__":
    sys.exit(main())
