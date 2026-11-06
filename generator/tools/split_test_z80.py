# -*- coding: utf-8 -*-
u"""R A Z B I T I E  TEST_Z80: vynesenie tablitsy testov v TEST_Z80_PREP.

P O Ch E M U. Segodnya v TEST_Z80 lezhit i tablitsa 62 proverok (bolee
300 strok odnih prisvoenij), i obrabotchik prohoda (chetyre shaga).
Vmeste -- POU na 500 s lishnim strok ST. Imenno v etoj masse dolgo
ne mogli najti nezakrytyj IF, kotoryy daval buket oshibok C9 bez
nomera stroki.

Ch T O  D E L A E M (p o sh a g o v o, inache uzhe dva raza portil fajl
regulyarkami po vsemu tekstu):

  1) vyrezaem iz ST_TEST_Z80 blok ot stroki "PODGOTOVKA" do stroki pered
     "PROGON" -- eto i est tablitsa;
  2) iz nego delaem otdelnyj ST_TEST_Z80_PREP: shapka, VAR, telo, END_VAR;
  3) v tele zamenyaem uslovie "IF bFirstScan THEN" na rabotu cherez flag
     iz GVL -- bFirstScan byl lokalnoj peremennoj TEST_Z80 i v novom POU
     ego net;
  4) na meste vyrezannogo bloka v ST_TEST_Z80 stavim odnu stroku-kommentariy;
  5) iz obyavleniya TEST_Z80 ubiraem bFirstScan (on teper ne nuzhen),
     no ostavlyaem ego znachenie v GVL.

ZAPUSK: python generator\tools\split_test_z80.py
Otkat:  kopiya fajla lezhit v generator\gen_z80.bak_split1
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GEN = os.path.join(ROOT, u"generator", u"gen_z80.py")


def find(lines, sub, start=0):
    for n in range(start, len(lines)):
        if sub in lines[n]:
            return n
    return -1


def main():
    try:
        sys.stdout.reconfigure(encoding=u"utf-8", errors=u"replace")
    except Exception:                                          # noqa: BLE001
        pass
    src = io.open(GEN, encoding=u"utf-8").read()
    lines = src.split(u"\n")

    base = find(lines, u"ST_TEST_Z80 = ")
    if base < 0:
        sys.stdout.write(u"NE NAJDEN ST_TEST_Z80\n")
        return 1
    i_podg = find(lines, u"PODGOTOVKA", base)
    i_prog = find(lines, u"PROGON", i_podg)
    i_end = find(lines, u"END_VAR", base)
    if min(i_podg, i_prog, i_end) < 0:
        sys.stdout.write(u"NE NAJDENY granicy: podg=%d prog=%d endvar=%d\n"
                         % (i_podg, i_prog, i_end))
        return 1
    sys.stdout.write(u"ST_TEST_Z80: baza=%d, PODGOTOVKA=%d, PROGON=%d, END_VAR=%d\n"
                     % (base + 1, i_podg + 1, i_prog + 1, i_end + 1))

    # 1. vyrezat tablitsu
    table = lines[i_podg:i_prog]
    while table and not table[-1].strip():
        table.pop()
    sys.stdout.write(u"vyrezaem strok: %d\n" % len(table))
    if u"IF bFirstScan THEN" not in u"\n".join(table):
        sys.stdout.write(u"V N I M A N I E: v bloke net 'IF bFirstScan THEN'\n")
        return 1

    # 2. sobrat telo novogo POU
    body = []
    for l in table:
        if l.strip() == u"IF bFirstScan THEN":
            body.append(u"IF NOT GVL_InitState.TestTableDone THEN")
        elif l.strip() == u"bFirstScan := FALSE;":
            body.append(u"    GVL_InitState.TestTableDone := TRUE;")
        else:
            body.append(l)

    prep = []
    prep.append(u"ST_TEST_Z80_PREP = u'''(* ========================================="
                u"================================")
    prep.append(u"   TEST_Z80_PREP -- TABLITsA PROVEROK emulyatora (62 testa).")
    prep.append(u"")
    prep.append(u"   Z D E S  T O L K O  D A N N Y E: chto podat na vhod, chto")
    prep.append(u"   zhdem na vyhode i chto iz etogo proveryat. Nikakih operatorov")
    prep.append(u"   obrabotki tut net -- oni v TEST_Z80.")
    prep.append(u"")
    prep.append(u"   P O Ch E M U  O T D E L N O. Ranshe tablitsa i obrabotchik byli")
    prep.append(u"   odnim POU na 500 s lishnim strok ST. Imenno v etoj masse dolgo")
    prep.append(u"   ne mogli najti nezakrytyj IF, kotoryy daval buket oshibok C9 bez")
    prep.append(u"   nomera stroki i bez imeni POU.")
    prep.append(u"")
    prep.append(u"   Zapolnyaetsya ODIN RAZ za progno, priznak -- GVL_InitState.")
    prep.append(u"   TestTableDone. Poryadok zapuska POU v zadache ne vazhen:")
    prep.append(u"   sostoyanie lezhit v GVL, a ne v lokalnyh peremennyh.")
    prep.append(u"   ================================================================ *)")
    prep.append(u"VAR")
    prep.append(u"    i : INT;")
    prep.append(u"END_VAR")
    prep.append(u"")
    prep.extend(body)
    prep.append(u"'''")
    prep.append(u"")

    # 3. vstavit novyj POU pered ST_TEST_Z80
    lines = lines[:base] + prep + lines[base:]
    # 4. na meste tablitsy v TEST_Z80 -- kommentariy
    shift = len(prep)
    note = [u"(* ============================== TABLITsA TESTov =====================",
            u"   Sami dannye proverok pereneseny v TEST_Z80_PREP: tak chitaemee",
            u"   i tak ih mozhno pravit, ne trogaya obrabotchik.",
            u"   Zdes ostalsya tolko progon.",
            u"   ==================================================================== *)"]
    lines = lines[:i_podg + shift] + note + lines[i_prog + shift:]
    # 5. bFirstScan v obyavlenii TEST_Z80 bolshe ne nuzhen
    out = []
    removed = 0
    for n, l in enumerate(lines):
        if u"bFirstScan" in l and u":" in l and u"BOOL" in l:
            out.append(u"    (* bFirstScan perenesen v GVL_InitState.TestTableDone:")
            out.append(u"       ego vystavlyaet POU TEST_Z80_PREP. *)")
            removed += 1
            continue
        out.append(l)
    lines = out
    sys.stdout.write(u"ubrano obyavlenij bFirstScan: %d\n" % removed)
    if removed != 1:
        sys.stdout.write(u"O Zh I D A L O S  R O V N O  1 -- ostanavlivayus\n")
        return 1

    io.open(GEN, u"w", encoding=u"utf-8").write(u"\n".join(lines))
    sys.stdout.write(u"gotovo\n")
    return 0


if __name__ == u"__main__":
    sys.exit(main())
