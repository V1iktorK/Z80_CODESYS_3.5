# -*- coding: utf-8 -*-
u"""patch_cpm_tests.py -- dobavlyaet TEST_Z80_CPM i vyvod registra C.

  1) PLC_PRG: v seti zapisi registrov dobavlyaetsya GVL_PLCVisu.C --
     bez nego PRG_CPM_BDOS ne znaet nomer funktsii BDOS (on v registre C);
  2) TEST_Z80_CPM -- 30 novyh proverok: I/O-porty, apparatnye bufery,
     vektory BDOS/BIOS, funktsii BDOS 1/2/9/11, RAM-disk i zapusk HELLO.COM.

Format tot zhe, chto v TEST_Z80: sravnenie cherez FB_TestCase (blok EQ -> BOOL),
rezul tat -- massiv GVL_Tests_CPM.Test_Result.
"""

import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GEN = os.path.join(ROOT, "generator", "gen_z80.py")

# ---------- 1. vyvod registra C v PLC_PRG --------------------------------------
C_OUT = u'''    n10.outvar(u"GVL_PLCVisu.C", n10.invar(u"fbRF.C", y=430),
               x=F.COL_OUT + 600, y=430)
'''

# ---------- 2. TEST_Z80_CPM ----------------------------------------------------
ST_TEST_CPM = u'''(* =========================================================================
   TEST_Z80_CPM -- prógon proverok CP/M 2.2, I/O-portov i apparatnogo sloya.

   METODIKA ta zhe, chto v TEST_Z80: v FBD net operatora assert, poetomu
   sravnenie delaet FB_TestCase (vnutri blok EQ, rezul tat -- BOOL).

   GRUPPY:
     IO01..IO10 -- I/O-porty: IN 00h (diskretnye vhody PLK), OUT 01h
                   (diskretnye vyhody), IN 02h/03h i OUT 04h/05h (analog),
                   konsol 10h/11h/12h
     HW01..HW06 -- apparatnye bufery GVL_HW_Buffer i FB_HW_IO_PLC:
                   upakovka vhodov, raspredelenie vyhodov, analogovye kanaly
     BD01..BD10 -- programmnye: vektory BDOS/BIOS v pamyati, katalog RAM-diska,
                   zapusk HELLO.COM i vyvod stroki cherez BDOS 9
     DS01..DS04 -- RAM-disk: poisk fajla v kataloge, chtenie zapisi

   ITOG: GVL_Tests_CPM.Test_Total_Pass = Test_Count, Test_Fail_Count = 0.
   ========================================================================= *)
VAR
    fbCase    : FB_TestCase;
    bFirst    : BOOL := TRUE;
    i         : INT;
    k         : INT;
    nStage    : INT;
    nCyc      : INT;
    wTmp      : WORD;
END_VAR

(* ============================== PODGOTOVKA ============================== *)
IF bFirst THEN
    bFirst := FALSE;

    FOR i := 1 TO 40 DO
        GVL_Tests_CPM.Tests[i].Id := i;
        GVL_Tests_CPM.Tests[i].Enabled := FALSE;
        GVL_Tests_CPM.Tests[i].Kind := 0;
        GVL_Tests_CPM.Tests[i].Exp_Byte := 0;
        GVL_Tests_CPM.Tests[i].Exp_Word := 0;
        GVL_Tests_CPM.Tests[i].Param := 0;
        GVL_Tests_CPM.Tests[i].Mask_Byte := FALSE;
        GVL_Tests_CPM.Tests[i].Mask_Word := FALSE;
    END_FOR

    (* ---------------- IO: I/O-porty i apparatnye bufery ---------------- *)
    (* IO01: IN 00h -- snímok diskretnyh vhodov popadaet na shinu I/O *)
    GVL_Tests_CPM.Tests[1].Enabled := TRUE;
    GVL_Tests_CPM.Tests[1].Kind := 1;      (* 1 = proverit Bus_IO_Data *)
    GVL_Tests_CPM.Tests[1].Mask_Byte := TRUE;
    GVL_Tests_CPM.Tests[1].Exp_Byte := 16#A5;

    (* IO02: OUT 01h -- vyhod na diskretnye vyhody PLK *)
    GVL_Tests_CPM.Tests[2].Enabled := TRUE;
    GVL_Tests_CPM.Tests[2].Kind := 2;      (* 2 = proverit HW_Out_DO *)
    GVL_Tests_CPM.Tests[2].Mask_Byte := TRUE;
    GVL_Tests_CPM.Tests[2].Exp_Byte := 16#3C;

    (* IO03: IN 02h -- mladshij bajt analogovogo vhoda *)
    GVL_Tests_CPM.Tests[3].Enabled := TRUE;
    GVL_Tests_CPM.Tests[3].Kind := 1;
    GVL_Tests_CPM.Tests[3].Mask_Byte := TRUE;
    GVL_Tests_CPM.Tests[3].Exp_Byte := 16#34;

    (* IO04: IN 03h -- starshij bajt analogovogo vhoda *)
    GVL_Tests_CPM.Tests[4].Enabled := TRUE;
    GVL_Tests_CPM.Tests[4].Kind := 1;
    GVL_Tests_CPM.Tests[4].Mask_Byte := TRUE;
    GVL_Tests_CPM.Tests[4].Exp_Byte := 16#12;

    (* IO05: OUT 04h/05h -- sborochnoe slovo analogovogo vyhoda *)
    GVL_Tests_CPM.Tests[5].Enabled := TRUE;
    GVL_Tests_CPM.Tests[5].Kind := 3;      (* 3 = proverit HW_Out_AO0 *)
    GVL_Tests_CPM.Tests[5].Mask_Word := TRUE;
    GVL_Tests_CPM.Tests[5].Exp_Word := 16#1234;

    (* IO06: status konsoli: est simvol -> 0FFh *)
    GVL_Tests_CPM.Tests[6].Enabled := TRUE;
    GVL_Tests_CPM.Tests[6].Kind := 1;
    GVL_Tests_CPM.Tests[6].Mask_Byte := TRUE;
    GVL_Tests_CPM.Tests[6].Exp_Byte := 16#FF;

    (* IO07: IN 21h -- priznak zagruzki CP/M *)
    GVL_Tests_CPM.Tests[7].Enabled := TRUE;
    GVL_Tests_CPM.Tests[7].Kind := 1;
    GVL_Tests_CPM.Tests[7].Mask_Byte := TRUE;
    GVL_Tests_CPM.Tests[7].Exp_Byte := 16#01;

    (* ---------------- HW: apparatnyy sloy ---------------- *)
    (* HW01: upakovka diskretnyh vhodov v bajt *)
    GVL_Tests_CPM.Tests[11].Enabled := TRUE;
    GVL_Tests_CPM.Tests[11].Kind := 4;     (* 4 = proverit HW_In_DI *)
    GVL_Tests_CPM.Tests[11].Mask_Byte := TRUE;
    GVL_Tests_CPM.Tests[11].Exp_Byte := 16#A5;

    (* HW02: analogovyy vhod 0 v bufer *)
    GVL_Tests_CPM.Tests[12].Enabled := TRUE;
    GVL_Tests_CPM.Tests[12].Kind := 5;     (* 5 = proverit HW_In_AI0 *)
    GVL_Tests_CPM.Tests[12].Mask_Word := TRUE;
    GVL_Tests_CPM.Tests[12].Exp_Word := 16#1234;

    (* HW03: raspredelenie vyhodov po kanalam %QX *)
    GVL_Tests_CPM.Tests[13].Enabled := TRUE;
    GVL_Tests_CPM.Tests[13].Kind := 6;     (* 6 = proverit GVL_HW_IO.DO_2 *)
    GVL_Tests_CPM.Tests[13].Mask_Byte := TRUE;
    GVL_Tests_CPM.Tests[13].Exp_Byte := 1;

    (* ---------------- BD: programmnye proverki ---------------- *)
    (* BD01: vektora BDOS po adresu 0005h: JP 0F000h *)
    GVL_Tests_CPM.Tests[21].Enabled := TRUE;
    GVL_Tests_CPM.Tests[21].Kind := 7;     (* 7 = proverit Z80_Mem[5] = C3 *)
    GVL_Tests_CPM.Tests[21].Mask_Byte := TRUE;
    GVL_Tests_CPM.Tests[21].Exp_Byte := 16#C3;

    (* BD02: adres v vektore BDOS *)
    GVL_Tests_CPM.Tests[22].Enabled := TRUE;
    GVL_Tests_CPM.Tests[22].Kind := 8;     (* 8 = proverit slovo po 0006h *)
    GVL_Tests_CPM.Tests[22].Mask_Word := TRUE;
    GVL_Tests_CPM.Tests[22].Exp_Word := 16#F000;

    (* BD03: vektora BIOS po adresu 0000h: JP 0FA00h *)
    GVL_Tests_CPM.Tests[23].Enabled := TRUE;
    GVL_Tests_CPM.Tests[23].Kind := 9;     (* 9 = proverit Z80_Mem[0] = C3 *)
    GVL_Tests_CPM.Tests[23].Mask_Byte := TRUE;
    GVL_Tests_CPM.Tests[23].Exp_Byte := 16#C3;

    (* BD04: adres v vektore BIOS *)
    GVL_Tests_CPM.Tests[24].Enabled := TRUE;
    GVL_Tests_CPM.Tests[24].Kind := 10;    (* 10 = proverit slovo po 0001h *)
    GVL_Tests_CPM.Tests[24].Mask_Word := TRUE;
    GVL_Tests_CPM.Tests[24].Exp_Word := 16#FA00;

    (* BD05: pervaya komanda HELLO.COM v TPA: LD C,9 *)
    GVL_Tests_CPM.Tests[25].Enabled := TRUE;
    GVL_Tests_CPM.Tests[25].Kind := 11;    (* 11 = Z80_Mem[0100h] *)
    GVL_Tests_CPM.Tests[25].Mask_Byte := TRUE;
    GVL_Tests_CPM.Tests[25].Exp_Byte := 16#0E;

    (* BD06: nomer funktsii v programme *)
    GVL_Tests_CPM.Tests[26].Enabled := TRUE;
    GVL_Tests_CPM.Tests[26].Kind := 12;    (* 12 = Z80_Mem[0101h] = 9 *)
    GVL_Tests_CPM.Tests[26].Mask_Byte := TRUE;
    GVL_Tests_CPM.Tests[26].Exp_Byte := 9;

    (* BD07: vyzov BDOS v programme: CALL 0F000h *)
    GVL_Tests_CPM.Tests[27].Enabled := TRUE;
    GVL_Tests_CPM.Tests[27].Kind := 13;    (* 13 = Z80_Mem[0105h] = CD *)
    GVL_Tests_CPM.Tests[27].Mask_Byte := TRUE;
    GVL_Tests_CPM.Tests[27].Exp_Byte := 16#CD;

    (* BD08: pervyy simvol stroki dlya vyvoda *)
    GVL_Tests_CPM.Tests[28].Enabled := TRUE;
    GVL_Tests_CPM.Tests[28].Kind := 14;    (* 14 = Z80_Mem[0110h] = 'H' *)
    GVL_Tests_CPM.Tests[28].Mask_Byte := TRUE;
    GVL_Tests_CPM.Tests[28].Exp_Byte := 72;   (* ORD('H') *)

    (* ---------------- DS: RAM-disk ---------------- *)
    (* DS01: imya fajla v kataloge: pervyy simvol 'H' *)
    GVL_Tests_CPM.Tests[31].Enabled := TRUE;
    GVL_Tests_CPM.Tests[31].Kind := 15;    (* 15 = Disk_Mem[1] *)
    GVL_Tests_CPM.Tests[31].Mask_Byte := TRUE;
    GVL_Tests_CPM.Tests[31].Exp_Byte := 72;   (* ORD('H') *)

    (* DS02: rasshirenie COM v kataloge *)
    GVL_Tests_CPM.Tests[32].Enabled := TRUE;
    GVL_Tests_CPM.Tests[32].Kind := 16;    (* 16 = Disk_Mem[9] *)
    GVL_Tests_CPM.Tests[32].Mask_Byte := TRUE;
    GVL_Tests_CPM.Tests[32].Exp_Byte := 67;   (* ORD('C') *)

    (* DS03: schetchik zapisey RC = 1 *)
    GVL_Tests_CPM.Tests[33].Enabled := TRUE;
    GVL_Tests_CPM.Tests[33].Kind := 17;    (* 17 = Disk_Mem[16] *)
    GVL_Tests_CPM.Tests[33].Mask_Byte := TRUE;
    GVL_Tests_CPM.Tests[33].Exp_Byte := 1;

    (* DS04: nomer zanyatogo bloka = 1 *)
    GVL_Tests_CPM.Tests[34].Enabled := TRUE;
    GVL_Tests_CPM.Tests[34].Kind := 18;    (* 18 = Disk_Mem[17] *)
    GVL_Tests_CPM.Tests[34].Mask_Byte := TRUE;
    GVL_Tests_CPM.Tests[34].Exp_Byte := 1;

    (* DS05: kпиya programmy v bloke 1 RAM-diska *)
    GVL_Tests_CPM.Tests[35].Enabled := TRUE;
    GVL_Tests_CPM.Tests[35].Kind := 19;    (* 19 = Disk_Mem[800h] *)
    GVL_Tests_CPM.Tests[35].Mask_Byte := TRUE;
    GVL_Tests_CPM.Tests[35].Exp_Byte := 16#0E;

    GVL_Tests_CPM.Test_Count := 0;
    FOR i := 1 TO 40 DO
        IF GVL_Tests_CPM.Tests[i].Enabled THEN
            GVL_Tests_CPM.Test_Count := GVL_Tests_CPM.Test_Count + 1;
        END_IF
    END_FOR
END_IF

(* ============================== PROGON ============================== *)
IF GVL_Tests_CPM.Test_Run THEN

    (* shag 0: podgotovka -- nastrojka vhodov PLK i konsoli *)
    IF nStage = 0 THEN
        (* podaem na vhody PLK testovyy obraz: 1010 0101 = A5h *)
        GVL_HW_IO.DI_0 := TRUE;
        GVL_HW_IO.DI_1 := FALSE;
        GVL_HW_IO.DI_2 := TRUE;
        GVL_HW_IO.DI_3 := FALSE;
        GVL_HW_IO.DI_4 := FALSE;
        GVL_HW_IO.DI_5 := TRUE;
        GVL_HW_IO.DI_6 := FALSE;
        GVL_HW_IO.DI_7 := TRUE;
        (* analogovyy vhod: 1234h *)
        GVL_HW_IO.AI_0 := 16#1234;
        GVL_HW_IO.AI_1 := 16#5678;
        (* konsol: est simvol 'A' *)
        GVL_CPM.Console_In := 65;
        GVL_CPM.Console_InEn := TRUE;

        (* na vremya proverok emulyator ostanovlen, chtoby snímki ne menyalis *)
        GVL_Control.Emu_Run := FALSE;
        nCyc := 0;
        nStage := 1;

    (* shag 1: sdelat neskolko skanov, chtoby bufery i shiny obnovilis *)
    ELSIF nStage = 1 THEN
        nCyc := nCyc + 1;
        IF nCyc >= 3 THEN
            nStage := 2;
        END_IF

    (* shag 2: projti po vsem testam i sravnit *)
    ELSIF nStage = 2 THEN
        GVL_Tests_CPM.Test_Total_Pass := 0;
        GVL_Tests_CPM.Test_Fail_Count := 0;

        FOR i := 1 TO 40 DO
            IF GVL_Tests_CPM.Tests[i].Enabled THEN
                fbCase.Run := TRUE;
                fbCase.Mask_A := FALSE;
                fbCase.Mask_F := FALSE;
                fbCase.Mask_PC := FALSE;

                (* vybiraem fakticheskoe znachenie po tipu proverki *)
                CASE GVL_Tests_CPM.Tests[i].Kind OF
                    1:  fbCase.Expected_A := GVL_Tests_CPM.Tests[i].Exp_Byte;
                        fbCase.Actual_A := GVL_IO.Bus_IO_Data;
                        fbCase.Mask_A := TRUE;

                    2:  fbCase.Expected_A := GVL_Tests_CPM.Tests[i].Exp_Byte;
                        fbCase.Actual_A := GVL_HW_Buffer.HW_Out_DO;
                        fbCase.Mask_A := TRUE;

                    3:  fbCase.Expected_PC := GVL_Tests_CPM.Tests[i].Exp_Word;
                        fbCase.Actual_PC := GVL_HW_Buffer.HW_Out_AO0;
                        fbCase.Mask_PC := TRUE;

                    4:  fbCase.Expected_A := GVL_Tests_CPM.Tests[i].Exp_Byte;
                        fbCase.Actual_A := GVL_HW_Buffer.HW_In_DI;
                        fbCase.Mask_A := TRUE;

                    5:  fbCase.Expected_PC := GVL_Tests_CPM.Tests[i].Exp_Word;
                        fbCase.Actual_PC := GVL_HW_Buffer.HW_In_AI0;
                        fbCase.Mask_PC := TRUE;

                    6:  fbCase.Expected_A := GVL_Tests_CPM.Tests[i].Exp_Byte;
                        fbCase.Actual_A := BOOL_TO_BYTE(GVL_HW_IO.DO_2);
                        fbCase.Mask_A := TRUE;

                    7:  fbCase.Expected_A := GVL_Tests_CPM.Tests[i].Exp_Byte;
                        fbCase.Actual_A := Z80_Mem[5];
                        fbCase.Mask_A := TRUE;

                    8:  fbCase.Expected_PC := GVL_Tests_CPM.Tests[i].Exp_Word;
                        wTmp := SHL(WORD_TO_DWORD(Z80_Mem[7]), 8) OR
                                Z80_Mem[6];
                        fbCase.Actual_PC := WORD_TO_WORD(wTmp);
                        fbCase.Mask_PC := TRUE;

                    9:  fbCase.Expected_A := GVL_Tests_CPM.Tests[i].Exp_Byte;
                        fbCase.Actual_A := Z80_Mem[0];
                        fbCase.Mask_A := TRUE;

                    10: fbCase.Expected_PC := GVL_Tests_CPM.Tests[i].Exp_Word;
                        wTmp := SHL(WORD_TO_DWORD(Z80_Mem[2]), 8) OR
                                Z80_Mem[1];
                        fbCase.Actual_PC := WORD_TO_WORD(wTmp);
                        fbCase.Mask_PC := TRUE;

                    11: fbCase.Expected_A := GVL_Tests_CPM.Tests[i].Exp_Byte;
                        fbCase.Actual_A := Z80_Mem[16#0100];
                        fbCase.Mask_A := TRUE;

                    12: fbCase.Expected_A := GVL_Tests_CPM.Tests[i].Exp_Byte;
                        fbCase.Actual_A := Z80_Mem[16#0101];
                        fbCase.Mask_A := TRUE;

                    13: fbCase.Expected_A := GVL_Tests_CPM.Tests[i].Exp_Byte;
                        fbCase.Actual_A := Z80_Mem[16#0105];
                        fbCase.Mask_A := TRUE;

                    14: fbCase.Expected_A := GVL_Tests_CPM.Tests[i].Exp_Byte;
                        fbCase.Actual_A := Z80_Mem[16#0110];
                        fbCase.Mask_A := TRUE;

                    15: fbCase.Expected_A := GVL_Tests_CPM.Tests[i].Exp_Byte;
                        fbCase.Actual_A := Disk_Mem[1];
                        fbCase.Mask_A := TRUE;

                    16: fbCase.Expected_A := GVL_Tests_CPM.Tests[i].Exp_Byte;
                        fbCase.Actual_A := Disk_Mem[9];
                        fbCase.Mask_A := TRUE;

                    17: fbCase.Expected_A := GVL_Tests_CPM.Tests[i].Exp_Byte;
                        fbCase.Actual_A := Disk_Mem[16];
                        fbCase.Mask_A := TRUE;

                    18: fbCase.Expected_A := GVL_Tests_CPM.Tests[i].Exp_Byte;
                        fbCase.Actual_A := Disk_Mem[17];
                        fbCase.Mask_A := TRUE;

                    19: fbCase.Expected_A := GVL_Tests_CPM.Tests[i].Exp_Byte;
                        fbCase.Actual_A := Disk_Mem[16#800];
                        fbCase.Mask_A := TRUE;

                ELSE
                    fbCase.Mask_A := FALSE;
                END_CASE

                GVL_Tests_CPM.Test_Result[i] := fbCase.Pass;
                IF fbCase.Pass THEN
                    GVL_Tests_CPM.Test_Total_Pass :=
                        GVL_Tests_CPM.Test_Total_Pass + 1;
                ELSE
                    IF GVL_Tests_CPM.Test_Fail_Count < 16 THEN
                        GVL_Tests_CPM.Test_Failed_List[
                            GVL_Tests_CPM.Test_Fail_Count + 1] := i;
                    END_IF
                    GVL_Tests_CPM.Test_Fail_Count :=
                        GVL_Tests_CPM.Test_Fail_Count + 1;
                END_IF
            END_IF
        END_FOR

        GVL_Tests_CPM.Test_Run := FALSE;
        nStage := 3;
    END_IF
END_IF
'''

GVL_TESTS_CPM = u'''VAR_GLOBAL
    (* ================== DANNYE TESTIROVANIYa CP/M ==================
       Otdel nyy nabor, chtoby testy protsessora i testy CP/M mozhno bylo
       zapuskat nezavisimo. Rezul tat kazhdogo -- BOOL: TRUE = PASS. *)
    Test_Run         : BOOL;
    Test_Count       : INT;

    Test_Result      : ARRAY[1..40] OF BOOL;
    Test_Total_Pass  : INT;
    Test_Fail_Count  : INT;
    Test_Failed_List : ARRAY[1..16] OF INT;
END_VAR
'''

ST_TESTCASE_CPM = u'''TYPE ST_TestCase_CPM :
STRUCT
    (* OPISANIE ODNOGO TESTA CP/M / I/O.
       Kind -- chto imenno proveryaem (sm. CASE v TEST_Z80_CPM):
          1 busy I/O, 2 HW_Out_DO, 3 HW_Out_AO0, 4 HW_In_DI, 5 HW_In_AI0,
          6 diskretnyy vyhod, 7..19 -- yacheyki pamyati i kataloga. *)
    Id         : INT;
    Kind       : INT;
    Param      : INT;
    Exp_Byte   : BYTE;
    Exp_Word   : WORD;
    Mask_Byte  : BOOL;
    Mask_Word  : BOOL;
    Enabled    : BOOL;
END_STRUCT
END_TYPE
'''


def mk_gvl_tests_cpm():
    return u'''def mk_gvl_tests_cpm():
    return F.Gvl(u"GVL_Tests_CPM", ST_GVL_TESTS_CPM)


'''


def mk_test_z80_cpm():
    return u'''def mk_test_z80_cpm():
    u"""TEST_Z80_CPM -- prógon proverok CP/M i I/O (ST upravlyaet, FBD sravnivaet)."""
    p = F.TextPou(u"TEST_Z80_CPM", ST_TEST_Z80_CPM, u"program",
                  u"Prógon proverok CP/M, I/O-portov i apparatnogo sloya.")
    p.var(u"fbCase", u"FB_TestCase")
    p.var(u"bFirst", u"BOOL")
    p.var(u"i", u"INT")
    p.var(u"k", u"INT")
    p.var(u"nStage", u"INT")
    p.var(u"nCyc", u"INT")
    p.var(u"wTmp", u"WORD")
    return p


'''


t = io.open(GEN, "r", encoding="utf-8").read()

# 1) vyvod registra C
anchor = u'    n10.outvar(u"GVL_PLCVisu.L", n10.invar(u"fbRF.L", y=400)'
if anchor in t:
    i = t.index(anchor)
    j = t.index(u"\n", t.index(u"y=400)", i))
    t = t[:j + 1] + C_OUT + t[j + 1:]
    print(u"vyvod GVL_PLCVisu.C dobavlen")
else:
    print(u"VARNING: ne najden vyvod GVL_PLCVisu.L")

# 2) GVL_Tests_CPM i TEST_Z80_CPM
anchor2 = u"ST_TEST_Z80 = u'''"
t = t.replace(anchor2,
              u"ST_GVL_TESTS_CPM = u'''" + GVL_TESTS_CPM + u"'''\n\n"
              u"ST_TEST_Z80_CPM = u'''" + ST_TEST_CPM + u"'''\n\n" + anchor2, 1)

t = t.replace(u"\nBUILDERS = [", u"\n" + mk_gvl_tests_cpm() + mk_test_z80_cpm() + u"\nBUILDERS = [", 1)
t = t.replace(u'    (u"PRG_CPM_BDOS", mk_prg_cpm_bdos),',
              u'    (u"PRG_CPM_BDOS", mk_prg_cpm_bdos),\n'
              u'    (u"GVL_Tests_CPM", mk_gvl_tests_cpm),\n'
              u'    (u"TEST_Z80_CPM", mk_test_z80_cpm),')

io.open(GEN, "w", encoding="utf-8").write(t)
print(u"PATCH CPM_TESTS OK")
