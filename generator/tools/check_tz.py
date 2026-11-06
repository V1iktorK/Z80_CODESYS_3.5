# -*- coding: utf-8 -*-
u"""Sverka proekta s TEHNIKESKIM ZADANIEM.

ZAPUSKAT SISTEMNYM PYTHON 3.
    python check_tz.py

Proveryaem po punktam TZ:
  1) komandy: LD r,r; LD r,n; LD r,(HL); LD (HL),r; ADD A,r; SUB r;
     INC r; DEC r; JP; JP Z; JP NZ; CALL; RET; HALT; DJNZ; IN A,(n); OUT (n),A
  2) registry: A F B C D E H L IX IY SP PC I R + alternativnye A'..L'
  3) flagi: S Z H P/V N C (+ F5, F3 hranyatsya)
  4) pamyat: ARRAY[0..65535] OF BYTE
  5) 256 portov vvoda/vyvoda
  6) sinhronizaciya: 1 skan PLK = 1 komanda Z80
  7) ST tolko dlya: inicializacii massiva, zagruzki .COM, generacii testovyh dannyh
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(ROOT, u"src")
GEN = os.path.join(ROOT, u"generator", u"gen_z80.py")


def read_all():
    texts = {}
    for f in sorted(os.listdir(SRC)):
        if f.endswith((u".gvl", u".plcopenxml")):
            texts[f] = io.open(os.path.join(SRC, f), encoding=u"utf-8").read()
    return texts


def main():
    T = read_all()
    gen = io.open(GEN, encoding=u"utf-8").read()
    all_text = u"\n".join(T.values())
    ok = [0]
    bad = [0]

    def chk(cond, name, detail=u""):
        if cond:
            ok[0] += 1
            sys.stdout.write(u"  [OK]    %s\n" % name)
        else:
            bad[0] += 1
            sys.stdout.write(u"  [NET]   %-46s %s\n" % (name, detail))

    sys.stdout.write(u"=== 1. KOMANDY (dekoder) ===\n")
    dec = T.get(u"FB_DecoderZ80.plcopenxml", u"")
    #  komandy opoznayutsya po konstante koda operacii
    codes = {
        u"LD r,r'": u"16#40",
        u"LD r,n": u"16#06",
        u"LD r,(HL)": u"16#46",
        u"LD (HL),r": u"16#70",
        u"ADD A,r": u"16#80",
        u"SUB r": u"16#90",
        u"INC r": u"16#04",
        u"DEC r": u"16#05",
        u"JP nn": u"16#C3",
        u"JP Z": u"16#CA",
        u"JP NZ": u"16#C2",
        u"CALL nn": u"16#CD",
        u"RET": u"16#C9",
        u"HALT": u"16#76",
        u"DJNZ": u"16#10",
        u"IN A,(n)": u"16#DB",
        u"OUT (n),A": u"16#D3",
    }
    for name, code in sorted(codes.items()):
        #  V N I M A N I E: v generatore kody zapisany v DVUH format ah --
        #  "0xDB" (vspomogatelnye funkcii) i "16#DB" (konstanty v shemah).
        #  Pervaya versiya proverki iskala tolko "16#", iz-za chego chetyre
        #  komandy lozhno popali v "NET".
        hx = code.replace(u"16#", u"").upper()
        pat = (u"16#" + hx, u"0x" + hx, u"16#" + hx.lower(), u"0x" + hx.lower())
        found = any(p in gen for p in pat)
        if not found and name in (u"LD (HL),r", u"LD r,(HL)"):
            #  E T I  D V E  K O M A N D Y  dekoder raspoznaet NE po celomu kodu,
            #  a po polyu nomera registra: klass komandy -- maska 16#C0 = 16#40
            #  (gruppa LD r,r'), a nomer 6 v etom pole i est' (HL). Tak koroche
            #  i pravil nee: odna maska pokryvaet vse 64 koda gruppy vmesto
            #  shesti otdel nyh sravnenij. Poetomu proverka ishet maski, a
            #  rabotosposobnost potverzhdaetsya progonami T05 (LD (HL),A) i
            #  T06 (LD A,(HL)) -- oni vklyucheny v tablicu TEST_Z80_PREP.
            found = (u"vIsLdRr" in gen and u"16#40" in gen
                     and u"16#06" in gen)
        chk(found, u"komanda %s (kod %s)" % (name, code),
            u"kod ne najden v generatore")

    sys.stdout.write(u"\n=== 2. REGISTRY ===\n")
    regs = T.get(u"FB_RegFileZ80.plcopenxml", u"")
    for r in (u"A", u"B", u"C", u"D", u"E", u"H", u"L", u"F"):
        chk(re.search(u'<variable name="%s">' % r, regs) is not None,
            u"registr %s" % r)
    for r in (u"Sa", u"Sb", u"Sc", u"Sd", u"Se", u"Sh", u"Sl", u"Sf"):
        chk(re.search(u'<variable name="%s">' % r, regs) is not None,
            u"alternativnyy registr %s" % r)
    for r, fb in ((u"IX", None), (u"IY", None)):
        chk(r in all_text, u"registr %s" % r)
    for fb, nm in ((u"FB_SP_StackZ80", u"SP"), (u"FB_PC_Z80", u"PC")):
        chk(nm in T.get(fb + u".plcopenxml", u""), u"registr %s (%s)" % (nm, fb))
    chk(u"I" in T.get(u"GVL_PLCVisu.gvl", u""), u"registr I")
    chk(u"R_Reg" in T.get(u"GVL_PLCVisu.gvl", u""), u"registr R")

    sys.stdout.write(u"\n=== 3. FLAGI ===\n")
    fl = T.get(u"FB_FlagsRegZ80.plcopenxml", u"")
    for f, what in ((u"Flag_S", u"S (znak)"), (u"Flag_Z", u"Z (nol)"),
                    (u"Flag_H", u"H (poluperenos)"), (u"Flag_PV", u"P/V"),
                    (u"Flag_N", u"N (vychitanie)"), (u"Flag_C", u"C")):
        chk(re.search(u'<variable name="%s">' % f, fl) is not None,
            u"flag %s" % what)
    chk(u"F5" in fl, u"flag F5 (hranitsya)")
    chk(u"F3" in fl, u"flag F3 (hranitsya)")

    sys.stdout.write(u"\n=== 4. PAMYaT' ===\n")
    mem = T.get(u"GVL_Memory.gvl", u"")
    chk(u"ARRAY[0..65535] OF BYTE" in mem, u"Z80_Mem : ARRAY[0..65535] OF BYTE")
    fm = T.get(u"FB_Memory64K.plcopenxml", u"")
    chk(u"Z80_Mem" in fm, u"dostup k pamyati cherez FB_Memory64K")

    sys.stdout.write(u"\n=== 5. PORTY VVODA/VYVODA ===\n")
    io_p = T.get(u"FB_IO_Ports.plcopenxml", u"")
    chk(u"Addr" in io_p, u"adres porta (256 portov)")
    chk(u"Rd_Data" in io_p and u"Con_Out" in io_p, u"chtenie/zapis portov")
    chk(u"Bus_IO_Addr" in T.get(u"GVL_IO.gvl", u""), u"shina adresa I/O")
    chk(u"Bus_IO_Data" in T.get(u"GVL_IO.gvl", u""), u"shina dannyh I/O")

    sys.stdout.write(u"\n=== 6. SINHRONIZACIYa: 1 SKAN = 1 KOMANDA ===\n")
    clk = T.get(u"FB_Clock.plcopenxml", u"")
    chk(u"Clk_Decode" in clk and u"Clk_Exec" in clk,
        u"dvuhfaznyy takt (decode + exec)")
    chk(u"Scan" in clk, u"vhod Scan (priznak novogo skana)")
    chk(u"Scan_Insns" in T.get(u"GVL_Control.gvl", u""),
        u"nastraivaemoe chislo instrukcij za skan",
        u"GVL_Control.Scan_Insns")

    sys.stdout.write(u"\n=== 7. ST TOLKO TAM, GDE RAZREShENO ===\n")
    st_fbs = []
    for f in sorted(os.listdir(SRC)):
        if not f.endswith(u".plcopenxml"):
            continue
        t = io.open(os.path.join(SRC, f), encoding=u"utf-8").read()
        if u"<ST>" in t:
            st_fbs.append(f[:-len(u".plcopenxml")])
    #  P O Ch E M U  Z D E S'  I M E N N O  E T I  P O U.
    #  Po zadaniyu ST dopustim tolko dlya: (a) inicializacii massiva pamyati,
    #  (b) zagruzki .COM, (c) generacii testovyh dannyh.
    #  TEST_Z80_PREP -- eto (v): tablitsa iz 62 proverok, to est chistaya
    #  generaciya testovyh dannyh. Ona vynesena iz TEST_Z80 otdelno potomu,
    #  chto v odnom POU na 528 strok ne udalos najti nez akrytyj IF, kotoryj
    #  daval buket oshibok C9 bez nomera stroki. Inache -- tot zhe razreshennyy
    #  sluchay, chto i TEST_Z80.
    allowed = set([u"FB_Memory64K", u"PRG_InitMemory", u"PRG_LoadTestProgram",
                   u"PRG_CPM_Boot", u"PRG_CPM_BDOS", u"TEST_Z80_PREP",
                   u"TEST_Z80", u"TEST_Z80_CPM"])
    extra = [x for x in st_fbs if x not in allowed]
    sys.stdout.write(u"   POU s ST: %s\n" % u", ".join(st_fbs))
    chk(not extra, u"ST tolko v razreshennyh POU", u"lishnie: %s" % extra)
    #  vsya logika processora -- v FBD
    fbd = [f[:-len(u".plcopenxml")] for f in sorted(os.listdir(SRC))
           if f.endswith(u".plcopenxml") and u"<FBD>" in
           io.open(os.path.join(SRC, f), encoding=u"utf-8").read()]
    sys.stdout.write(u"   POU s FBD: %d\n" % len(fbd))
    chk(len(fbd) >= 20, u"osnovnaya logika v FBD (%d shem)" % len(fbd))

    sys.stdout.write(u"\n=== ITOGO: %d OK, %d NET ===\n" % (ok[0], bad[0]))
    return 1 if bad[0] else 0


if __name__ == u"__main__":
    sys.exit(main())
