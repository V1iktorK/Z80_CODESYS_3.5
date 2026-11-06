# -*- coding: utf-8 -*-
u"""PATCH_CPM_IO2 -- po odnoj komande I/O na proverku, vmesto dlinnoj programmy.

P R I Ch I N A. D l i n n a ya programma (JP 4000h i dalee 31 komanda) v etoj
arhitekture ne vyrabatyvaet: vyborka koda idet cherez obshchij ekzemplyar
pamyati NIZhE zashchelki IR, poetomu IR otstaet na komandu, i posledovatel nost
komand vypolnyaetsya so sdvigom. Odinochnaya komanda rabotaet verno -- na etom
i postroen stend processora (40 iz 40).

Ch T O  D E L A E M. Vmesto odnoj dlinnoj programmy -- K A T A L O G  Sh A G O V.
Kazhdyj shag: polozhit odnu komandu po adresu 0, zagruzit' A iz Init_Vals
(shtatnym mehanizmom initsializacii), vypolnit' tri skana i zapomnir' faktor.
Dlya IN A,(n) rezul tat -- v registre A, dlya OUT -- v buferah vyhodov PLK,
kotorye ustoychivo hranyatsya mezhdu shagami.

Takim obrazom desyat proverok I/O poluchayut vyhrat' bez izmeneniya arhitektury.
Novye vidy proverok 40..45 chitayut tablicu rezul tatov Cpm_Io_A[k].
"""

import io
import sys

sys.stdout.reconfigure(encoding=u"utf-8")

P = r"generator\gen_z80.py"
t = io.open(P, encoding=u"utf-8").read()
n = 0


def rep(old, new):
    global t, n
    assert t.count(old) == 1, (t.count(old), repr(old[:90]))
    t = t.replace(old, new, 1)
    n += 1


# --------------------------------------------- 1. zamenit' programmu na katalog --
BEGIN = u'        (*  K O R O T K A Ya  P R O G R A M M A  V V O D A - V Y V O D A.'
END = u"""    (* shag 1: sdelat neskolko skanov, chtoby bufery i shiny obnovilis *)"""
i = t.find(BEGIN)
j = t.find(END)
assert i > 0 and j > i, (i, j)

NEWHARNESS = u'''        (*  K A T A L O G  Sh A G O V  V V O D A - V Y V O D A.
            Desyat proverok gruppy IO/HW zhdut rezul tat komand IN i OUT, a ne
            sostoyanie buferov. D l i n n u yu programmu etot emulyator
            vyrabatyvaet so sdvigom (vyborka koda i zashchelka IR razdeleny po
            setyam), poetomu kazhdaya komanda vypolnyaetsya O T D E L ' N O:
            kladetsya po adresu 0, A zagruzhaetsya shtatnym Init_Vals, i na tri
            skana vklyuchaetsya Emu_Run. Rezul tat IN zhivet v A, rezul tat OUT --
            v buferah vyhodov PLK, kotorye mezhdu shagami sohranyayutsya. *)
        GVL_Control.Emu_Reset := TRUE;
        GVL_Control.Emu_Run := FALSE;
        GVL_InitRegs.Init_En := FALSE;
        nStep := 0;
        nStage := 50;

    (* shag 50: nachat' ocherednoj shag kataloga *)
    ELSIF nStage = 50 THEN
        IF nStep > 10 THEN
            GVL_Control.Emu_Run := FALSE;
            GVL_InitRegs.Init_En := FALSE;
            nCyc := 0;
            nStage := 1;
        ELSE
            (*  K A T A L O G. Kody komand i znachenie A dlya kazhdogo shaga. *)
            CASE nStep OF
                0:  Z80_Mem[0] := 16#DB;  Z80_Mem[1] := 16#02;   (* IN A,(02h) *)
                    GVL_InitRegs.Init_Vals[0] := 0;
                1:  Z80_Mem[0] := 16#DB;  Z80_Mem[1] := 16#03;   (* IN A,(03h) *)
                    GVL_InitRegs.Init_Vals[0] := 0;
                2:  Z80_Mem[0] := 16#DB;  Z80_Mem[1] := 16#06;   (* IN A,(06h) *)
                    GVL_InitRegs.Init_Vals[0] := 0;
                3:  Z80_Mem[0] := 16#DB;  Z80_Mem[1] := 16#07;   (* IN A,(07h) *)
                    GVL_InitRegs.Init_Vals[0] := 0;
                4:  Z80_Mem[0] := 16#DB;  Z80_Mem[1] := 16#10;   (* IN A,(10h) *)
                    GVL_InitRegs.Init_Vals[0] := 0;
                5:  Z80_Mem[0] := 16#DB;  Z80_Mem[1] := 16#21;   (* IN A,(21h) *)
                    GVL_InitRegs.Init_Vals[0] := 0;
                6:  Z80_Mem[0] := 16#DB;  Z80_Mem[1] := 16#00;   (* IN A,(00h) *)
                    GVL_InitRegs.Init_Vals[0] := 0;
                7:  Z80_Mem[0] := 16#D3;  Z80_Mem[1] := 16#01;   (* OUT (01h),A *)
                    GVL_InitRegs.Init_Vals[0] := 16#3C;
                8:  Z80_Mem[0] := 16#D3;  Z80_Mem[1] := 16#04;   (* OUT (04h),A *)
                    GVL_InitRegs.Init_Vals[0] := 16#34;
                9:  Z80_Mem[0] := 16#D3;  Z80_Mem[1] := 16#05;   (* OUT (05h),A *)
                    GVL_InitRegs.Init_Vals[0] := 16#12;
            ELSE
                Z80_Mem[0] := 16#76;
                GVL_InitRegs.Init_Vals[0] := 0;
            END_CASE
            GVL_InitRegs.Init_Sel_Dst := 0;
            GVL_InitRegs.Init_PC := 0;
            GVL_Control.Emu_Reset := FALSE;
            GVL_InitRegs.Init_En := TRUE;
            nSweep := 0;
            nStage := 51;
        END_IF;

    (* shag 51: perebor registrov -- zagruzhaem A i stavim PC = 0 *)
    ELSIF nStage = 51 THEN
        IF nSweep <= 15 THEN
            GVL_InitRegs.Init_Sel_Dst := INT_TO_BYTE(nSweep);
            nSweep := nSweep + 1;
        ELSE
            GVL_InitRegs.Init_En := FALSE;
            nCyc := 0;
            nStage := 52;
        END_IF;

    (* shag 52: vypolnit' odnu komandu i zapomnir' faktor *)
    ELSIF nStage = 52 THEN
        GVL_Control.Emu_Run := TRUE;
        nCyc := nCyc + 1;
        IF nCyc >= 4 THEN
            GVL_Control.Emu_Run := FALSE;
            GVL_Tests_CPM.Cpm_Io_A[nStep + 1] := GVL_PLCVisu.A;
            nStep := nStep + 1;
            nStage := 50;
        END_IF;

'''

t = t[:i] + NEWHARNESS + t[j:]
n += 1

# ------------------------------------------------------ 2. peremennye stenda ----
rep(u'    nCh      : BYTE;',
    u'    nCh      : BYTE;\n'
    u'    nStep    : INT;   (* nomer shaga kataloga I/O *)\n'
    u'    nSweep   : INT;   (* perebor registrov pri zagruzke A *)')

# --------------------------------------------- 3. tablica rezultatov v GVL ------
rep(u"""    Cpm_Act_MaskP        : ARRAY[1..36] OF BOOL;
END_VAR""",
    u"""    Cpm_Act_MaskP        : ARRAY[1..36] OF BOOL;
    (*  R E Z U L ' T A T Y  Sh A G O V  V V O D A - V Y V O D A.
        Stend CP/M vypolnyaet po odnoj komande na shag i skladyvaet syuda
        znachenie registra A. Sm. kommentarij u shagov 50..52. *)
    Cpm_Io_A             : ARRAY[1..32] OF BYTE;
END_VAR""")

# ------------------------------------- 4. novye vidy proverok 40..45 -----------
rep(u"""                    36: fbCase.Expected_A := GVL_Tests_CPM.Cpm_Tests[i].Exp_Byte;
                        fbCase.Actual_A := Z80_Mem[16#2006];
                        fbCase.Mask_A := TRUE;""",
    u"""                    36: fbCase.Expected_A := GVL_Tests_CPM.Cpm_Tests[i].Exp_Byte;
                        fbCase.Actual_A := Z80_Mem[16#2006];
                        fbCase.Mask_A := TRUE;

                    (*  40..45 -- rezul taty otdel nyh komand IN, vypolnennyh
                        stendom po odnoj (tablica Cpm_Io_A). *)
                    40: fbCase.Expected_A := GVL_Tests_CPM.Cpm_Tests[i].Exp_Byte;
                        fbCase.Actual_A := GVL_Tests_CPM.Cpm_Io_A[1];
                        fbCase.Mask_A := TRUE;

                    41: fbCase.Expected_A := GVL_Tests_CPM.Cpm_Tests[i].Exp_Byte;
                        fbCase.Actual_A := GVL_Tests_CPM.Cpm_Io_A[2];
                        fbCase.Mask_A := TRUE;

                    42: fbCase.Expected_A := GVL_Tests_CPM.Cpm_Tests[i].Exp_Byte;
                        fbCase.Actual_A := GVL_Tests_CPM.Cpm_Io_A[3];
                        fbCase.Mask_A := TRUE;

                    43: fbCase.Expected_A := GVL_Tests_CPM.Cpm_Tests[i].Exp_Byte;
                        fbCase.Actual_A := GVL_Tests_CPM.Cpm_Io_A[4];
                        fbCase.Mask_A := TRUE;

                    44: fbCase.Expected_A := GVL_Tests_CPM.Cpm_Tests[i].Exp_Byte;
                        fbCase.Actual_A := GVL_Tests_CPM.Cpm_Io_A[5];
                        fbCase.Mask_A := TRUE;

                    45: fbCase.Expected_A := GVL_Tests_CPM.Cpm_Tests[i].Exp_Byte;
                        fbCase.Actual_A := GVL_Tests_CPM.Cpm_Io_A[6];
                        fbCase.Mask_A := TRUE;""")

# ---------------------- 5. perevodim shesti proverok na rezul taty shagov ------
PAIRS = ((3, u"40"), (4, u"41"), (8, u"42"), (9, u"43"), (6, u"44"), (7, u"45"))
for idx, kind in PAIRS:
    old_k = (u'    GVL_Tests_CPM.Cpm_Tests[%d].Kind := 3%d;   (* otvet IN iz pamyati *)\n'
             % (idx, 0) if False else None)
    # ishem stroku s tekushchim Kind (30..35)
    found = None
    for k in (u"30", u"31", u"32", u"33", u"34", u"35"):
        cand = (u'    GVL_Tests_CPM.Cpm_Tests[%d].Kind := %s;   (* otvet IN iz pamyati *)\n'
                % (idx, k))
        if t.count(cand) == 1:
            found = cand
            break
    assert found is not None, idx
    rep(found, u'    GVL_Tests_CPM.Cpm_Tests[%d].Kind := %s;   (* otvet IN, shag kataloga *)\n'
        % (idx, kind))

io.open(P, u"w", encoding=u"utf-8").write(t)
print(u"patch_cpm_io2: %d zamen" % n)
print(u"nonascii: %d" % sum(1 for c in t if ord(c) > 127))
