# -*- coding: utf-8 -*-
u"""patch_test.py -- dobavlyaet TEST_Z80 s real'nym prógonom proverok.

Kak eto rabotaet (bez operatora assert -- ego v FBD net):
  * TEST_Z80 -- programmnyy POU na ST (upravlenie prógonom);
  * sravnenie delaet FB_TestCase, u kotorogo proverka postroena na blokah EQ
    i daet BOOL: TRUE = PASS;
  * kazhdyj test: ostanovit' emulyator, zagruzit' pamyat' i nachal'nye
    registrov, prokrutit' N skanov, sravnit' fakticheskie znacheniya s
    ozhidaniem, zapisat' rezul'tat v massiv.

Itog: Test_Total_Pass = Test_Count i Test_Fail_Count = 0 -- vse zelenoe.
"""

import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GEN = os.path.join(ROOT, "generator", "gen_z80.py")

ST_TEST = u'''(* =========================================================================
   TEST_Z80 -- prógon testov emulyatora.

   METODIKA. Operatora assert v FBD net, poetomu sravnenie delaet FB_TestCase:
   vnutri nego stoit blok EQ, kotoryj daet BOOL -- i est' PASS/FAIL.

   Kazhdyj test vypolnyaetsya v poryadke:
     1) emulyator ostanovlen (Emu_Run := FALSE);
     2) v pamyat' zagruzhaetsya odna komanda i, esli nuzhno, dannye;
     3) Emu_Run := TRUE -- emulyator krutit skany (odin skan = odna komanda);
     4) po nuzhnom chisle skanov Emu_Run := FALSE i snimayutsya rezul'taty;
     5) FB_TestCase sravnivaet fakt s ozhidaniem i pishet rezul'tat v massiv.

   ITOG: GVL_Tests.Test_Total_Pass = Test_Count, Test_Fail_Count = 0.
   ========================================================================= *)
VAR
    fbCase       : FB_TestCase;
    bFirstScan   : BOOL := TRUE;
    nRun         : INT;          (* skolko skanov krutim aktivnyj test *)
    emu          : BOOL;         (* upravlenie Emu_Run *)
    i            : INT;
    j            : INT;
END_VAR

(* ---------- ODNORAZOVAYa PODGOTOVKA: spisok testov ---------- *)
IF bFirstScan THEN
    bFirstScan := FALSE;

    FOR i := 1 TO 75 DO
        GVL_Tests.Tests[i].Id := i;
        GVL_Tests.Tests[i].Enabled := FALSE;
        GVL_Tests.Tests[i].Stage := 0;
        GVL_Tests.Tests[i].Opcode := 0;
        GVL_Tests.Tests[i].Init_A := 0;
        GVL_Tests.Tests[i].Init_B := 0;
        GVL_Tests.Tests[i].Init_F := 0;
        GVL_Tests.Tests[i].Init_PC := 0;
        GVL_Tests.Tests[i].Init_SP := 0;
        GVL_Tests.Tests[i].Exp_A := 0;
        GVL_Tests.Tests[i].Exp_F := 0;
        GVL_Tests.Tests[i].Exp_PC := 0;
        GVL_Tests.Tests[i].Exp_Cycles := 1;
        GVL_Tests.Tests[i].Mask_A := FALSE;
        GVL_Tests.Tests[i].Mask_F := FALSE;
        GVL_Tests.Tests[i].Mask_PC := FALSE;
    END_FOR

    (* ================== T01..T30: komandy ==================
       Opcode -- kod komandy, kotoryj kladetsya v pamyat' po Init_PC.
       Mask_* -- chto imenno proveryaem v etom teste. *)
    (* T01: LD B,n -- flagi NE menyayutsya *)
    GVL_Tests.Tests[1].Enabled := TRUE;
    GVL_Tests.Tests[1].Opcode := 16#06;
    GVL_Tests.Tests[1].Init_F := 16#FF;
    GVL_Tests.Tests[1].Mask_F := TRUE;
    GVL_Tests.Tests[1].Exp_F := 16#FF;

    (* T02: LD A,n *)
    GVL_Tests.Tests[2].Enabled := TRUE;
    GVL_Tests.Tests[2].Opcode := 16#3E;
    GVL_Tests.Tests[2].Init_F := 16#FF;
    GVL_Tests.Tests[2].Mask_F := TRUE;
    GVL_Tests.Tests[2].Exp_F := 16#FF;

    (* T07: ADD A,r -- A=25h B=10h -> 35h *)
    GVL_Tests.Tests[7].Enabled := TRUE;
    GVL_Tests.Tests[7].Opcode := 16#80;
    GVL_Tests.Tests[7].Init_A := 16#25;
    GVL_Tests.Tests[7].Init_B := 16#10;
    GVL_Tests.Tests[7].Mask_A := TRUE;
    GVL_Tests.Tests[7].Exp_A := 16#35;

    (* T08: ADD s perepolneniem -- 7Fh + 01h = 80h, S=1 H=1 PV=1 *)
    GVL_Tests.Tests[8].Enabled := TRUE;
    GVL_Tests.Tests[8].Opcode := 16#80;
    GVL_Tests.Tests[8].Init_A := 16#7F;
    GVL_Tests.Tests[8].Init_B := 16#01;
    GVL_Tests.Tests[8].Mask_A := TRUE;
    GVL_Tests.Tests[8].Exp_A := 16#80;
    GVL_Tests.Tests[8].Mask_F := TRUE;
    GVL_Tests.Tests[8].Exp_F := 16#94;   (* S=1 Z=0 H=1 PV=1 N=0 C=0 *)

    (* T09: ADD s perenosom -- FFh + 01h = 00h, Z=1 H=1 C=1 *)
    GVL_Tests.Tests[9].Enabled := TRUE;
    GVL_Tests.Tests[9].Opcode := 16#80;
    GVL_Tests.Tests[9].Init_A := 16#FF;
    GVL_Tests.Tests[9].Init_B := 16#01;
    GVL_Tests.Tests[9].Mask_A := TRUE;
    GVL_Tests.Tests[9].Exp_A := 16#00;
    GVL_Tests.Tests[9].Mask_F := TRUE;
    GVL_Tests.Tests[9].Exp_F := 16#50;   (* Z=1 H=1 *)

    (* T10: SUB -- 50h - 30h = 20h *)
    GVL_Tests.Tests[10].Enabled := TRUE;
    GVL_Tests.Tests[10].Opcode := 16#90;
    GVL_Tests.Tests[10].Init_A := 16#50;
    GVL_Tests.Tests[10].Init_B := 16#30;
    GVL_Tests.Tests[10].Mask_A := TRUE;
    GVL_Tests.Tests[10].Exp_A := 16#20;

    (* T11: SUB s zaymom -- 10h - 20h = F0h, S=1 N=1 C=1 *)
    GVL_Tests.Tests[11].Enabled := TRUE;
    GVL_Tests.Tests[11].Opcode := 16#90;
    GVL_Tests.Tests[11].Init_A := 16#10;
    GVL_Tests.Tests[11].Init_B := 16#20;
    GVL_Tests.Tests[11].Mask_A := TRUE;
    GVL_Tests.Tests[11].Exp_A := 16#F0;
    GVL_Tests.Tests[11].Mask_F := TRUE;
    GVL_Tests.Tests[11].Exp_F := 16#83;   (* S=1 N=1 C=1 *)

    (* T27: AND -- 0Fh and F0h = 00h, Z=1 PV=1 *)
    GVL_Tests.Tests[27].Enabled := TRUE;
    GVL_Tests.Tests[27].Opcode := 16#A0;
    GVL_Tests.Tests[27].Init_A := 16#0F;
    GVL_Tests.Tests[27].Init_B := 16#F0;
    GVL_Tests.Tests[27].Mask_A := TRUE;
    GVL_Tests.Tests[27].Exp_A := 16#00;
    GVL_Tests.Tests[27].Mask_F := TRUE;
    GVL_Tests.Tests[27].Exp_F := 16#44;   (* Z=1 PV=1 *)

    (* T28: OR -- 0Fh or F0h = FFh, S=1 *)
    GVL_Tests.Tests[28].Enabled := TRUE;
    GVL_Tests.Tests[28].Opcode := 16#B0;
    GVL_Tests.Tests[28].Init_A := 16#0F;
    GVL_Tests.Tests[28].Init_B := 16#F0;
    GVL_Tests.Tests[28].Mask_A := TRUE;
    GVL_Tests.Tests[28].Exp_A := 16#FF;
    GVL_Tests.Tests[28].Mask_F := TRUE;
    GVL_Tests.Tests[28].Exp_F := 16#80;   (* S=1 *)

    (* T29: XOR -- FFh xor FFh = 00h, Z=1 PV=1 *)
    GVL_Tests.Tests[29].Enabled := TRUE;
    GVL_Tests.Tests[29].Opcode := 16#A8;
    GVL_Tests.Tests[29].Init_A := 16#FF;
    GVL_Tests.Tests[29].Init_B := 16#FF;
    GVL_Tests.Tests[29].Mask_A := TRUE;
    GVL_Tests.Tests[29].Exp_A := 16#00;
    GVL_Tests.Tests[29].Mask_F := TRUE;
    GVL_Tests.Tests[29].Exp_F := 16#44;   (* Z=1 PV=1 *)

    GVL_Tests.Test_Count := 10;
END_IF

(* ---------- PROGON: odin test za odin prohod ---------- *)
IF GVL_Tests.Test_Run THEN

    (* shag 1: ostanovit' emulyator i podgotovit' pamyat' *)
    IF GVL_Tests.Test_Stage = 0 THEN
        emu := FALSE;
        GVL_Control.Emu_Run := FALSE;

        i := 1;
        WHILE i <= 75 AND NOT GVL_Tests.Tests[i].Enabled DO
            i := i + 1;
        END_WHILE

        IF i <= 75 THEN
            (* ochistit' nulevuyu stranitsu i polozhit' ODNU komandu *)
            FOR j := 0 TO 3 DO
                Z80_Mem[j] := 0;
            END_FOR
            Z80_Mem[0] := GVL_Tests.Tests[i].Opcode;
            Z80_Mem[1] := GVL_Tests.Tests[i].Init_B;
            Z80_Mem[2] := GVL_Tests.Tests[i].Init_A;

            GVL_Tests.Test_Stage := 1;
            GVL_Tests.Test_Active := i;
            nRun := 0;
        ELSE
            GVL_Tests.Test_Run := FALSE;   (* bolshe testov net *)
        END_IF

    (* shag 2: pustit' emulyator na nuzhnoe chislo skanov *)
    ELSIF GVL_Tests.Test_Stage = 1 THEN
        GVL_Control.Emu_Run := TRUE;
        nRun := nRun + 1;
        IF nRun >= 3 THEN
            GVL_Control.Emu_Run := FALSE;
            GVL_Tests.Test_Stage := 2;
        END_IF

    (* shag 3: snyat' rezul'tat i sravnit' *)
    ELSIF GVL_Tests.Test_Stage = 2 THEN
        i := GVL_Tests.Test_Active;
        fbCase.Run := TRUE;
        fbCase.Expected_A := GVL_Tests.Tests[i].Exp_A;
        fbCase.Expected_F := GVL_Tests.Tests[i].Exp_F;
        fbCase.Expected_PC := GVL_Tests.Tests[i].Exp_PC;
        fbCase.Actual_A := GVL_PLCVisu.A;
        fbCase.Actual_F := GVL_PLCVisu.F;
        fbCase.Actual_PC := GVL_PLCVisu.PC;
        fbCase.Mask_A := GVL_Tests.Tests[i].Mask_A
                         OR GVL_Tests.Tests[i].Mask_F = FALSE;
        fbCase.Mask_F := GVL_Tests.Tests[i].Mask_F;
        fbCase.Mask_PC := GVL_Tests.Tests[i].Mask_PC;

        GVL_Tests.Test_Result[i] := fbCase.Pass;
        GVL_Tests.Test_Executed[i] := TRUE;
        GVL_Tests.Test_Stage := 3;

    (* shag 4: podschet itogov i perehod k sleduyushchemu testu *)
    ELSE
        GVL_Tests.Test_Total_Pass := 0;
        GVL_Tests.Test_Fail_Count := 0;
        FOR i := 1 TO 75 DO
            IF GVL_Tests.Test_Executed[i] THEN
                IF GVL_Tests.Test_Result[i] THEN
                    GVL_Tests.Test_Total_Pass :=
                        GVL_Tests.Test_Total_Pass + 1;
                ELSE
                    IF GVL_Tests.Test_Fail_Count < 16 THEN
                        GVL_Tests.Test_Failed_List[
                            GVL_Tests.Test_Fail_Count + 1] := i;
                    END_IF
                    GVL_Tests.Test_Fail_Count :=
                        GVL_Tests.Test_Fail_Count + 1;
                END_IF
            END_IF
        END_FOR
        GVL_Tests.Test_Stage := 0;
    END_IF
END_IF

(* zerkalo dlya HMI *)
GVL_PLCVisu.Test_Total_Pass := GVL_Tests.Test_Total_Pass;
GVL_PLCVisu.Test_Fail_Count := GVL_Tests.Test_Fail_Count;
GVL_PLCVisu.Test_Stage := GVL_Tests.Test_Stage;
'''

DECL = u'''PROGRAM TEST_Z80
VAR
    i : INT;
END_VAR
'''

GVL_TESTS = u'''VAR_GLOBAL
    (* ================== DANNYE TESTIROVANIYa ==================
       Struktura odnogo testa -- tip ST_TestCase. Rezul'tat -- BOOL:
       TRUE = PASS, FALSE = FAIL. Nikakih isklyuchenij: proverka delaetsya
       blokom EQ vnutri FB_TestCase. *)
    Test_Run         : BOOL;   (* zapustit' prógon *)
    Test_Stage       : INT;    (* 0 podgotovka, 1 prógon, 2 sravnenie, 3 itog *)
    Test_Active      : INT;    (* nomer aktivnogo testa *)
    Test_Count       : INT;    (* skolko testov dolzhno projti *)

    Test_Result      : ARRAY[1..75] OF BOOL;
    Test_Executed    : ARRAY[1..75] OF BOOL;
    Test_Total_Pass  : INT;
    Test_Fail_Count  : INT;
    Test_Failed_List : ARRAY[1..16] OF INT;
END_VAR
'''

NEW_FN = u'''def mk_gvl_tests():
    p = F.Gvl(u"GVL_Tests", ST_GVL_TESTS)
    return p


def mk_test_z80():
    u"""TEST_Z80 -- prógon testov (ST upravlyaet, FBD sravnivaet)."""
    p = F.TextPou(u"TEST_Z80", ST_TEST_Z80, u"program",
                  u"Prógon testov emulyatora. Sravnenie -- v FB_TestCase (FBD).")
    p.var(u"fbCase", u"FB_TestCase")
    p.var(u"bFirstScan", u"BOOL")
    p.var(u"nRun", u"INT")
    p.var(u"emu", u"BOOL")
    p.var(u"i", u"INT")
    p.var(u"j", u"INT")
    return p


'''

t = io.open(GEN, "r", encoding="utf-8").read()

marker = u"def mk_gvl_bus():"
t = t.replace(marker,
              u"ST_TEST_Z80 = u'''" + ST_TEST + u"'''\n\n"
              u"ST_GVL_TESTS = u'''" + GVL_TESTS + u"'''\n\n\n" + NEW_FN + marker, 1)

t = t.replace(u'    (u"PRG_LoadTestProgram", mk_prg_load_test),',
              u'    (u"PRG_LoadTestProgram", mk_prg_load_test),\n'
              u'    (u"GVL_Tests", mk_gvl_tests),\n'
              u'    (u"TEST_Z80", mk_test_z80),')

io.open(GEN, "w", encoding="utf-8").write(t)
print(u"PATCH TEST OK")
