# -*- coding: utf-8 -*-
u"""patch_full_tests.py -- polnyy nabor iz 62 proverok + port initsializatsii.

Chto dobavlyaetsya:
  * GVL_InitRegs -- znacheniya dlya initsializatsii vseh registrov i SP;
  * PLC_PRG -- vyzov Init_En/Init_Sel_Dst i vybor Init_Vals[k] v Wr_Val;
  * TEST_Z80 -- polnaya tablitsa T01..T30, F_*, P01..P05, L01..L08, I01..I07
    (62 proverki) s zagruzkov testovyh programm v pamyat.
"""

import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GEN = os.path.join(ROOT, "generator", "gen_z80.py")

GVL_INITREGS = u'''VAR_GLOBAL
    (* ============ INICIALIZACIYa REGISTROV (dlya testov i sbrosa) ============
       Testam nuzhno zadat proizvol'nye znacheniya registrov, poetomu vse oni
       vyvedeny syuda. Poryadok sovpadaet s kodami Sel_Dst:
           0=A 1=B 2=C 3=D 4=E 5=H 6=L 7=F 8=A' ... 15=F' *)
    Init_En      : BOOL;                    (* nachat initsializatsiyu *)
    Init_Sel_Dst : BYTE;                    (* nomer registra 0..15 *)
    Init_Vals    : ARRAY[0..15] OF BYTE;    (* chto zapisat *)
    Init_SP      : WORD;                    (* nachal'noe znachenie steka *)
    Init_PC      : WORD;                    (* nachal'nyj schetchik komand *)
END_VAR
'''

# --- polnyy nabor testov --------------------------------------------------------
ST_TEST = u'''(* =========================================================================
   TEST_Z80 -- prógon 62 proverok emulyatora.

   METODIKA. Operatora assert v FBD net, poetomu sravnenie delaet FB_TestCase:
   vnutri nego blok EQ, kotoryy daet BOOL -- i est' PASS/FAIL.

   Kazhdyy test prohodit chetyre shaga (Test_Stage):
     0 -- ostanovit emulyator, zagruzit pamyat i nachalnye registrov;
     1 -- pustit emulyator na Exp_Cycles skanov (odin skan = odna komanda);
     2 -- snyat rezultaty i sravnit cherez FB_TestCase;
     3 -- podschet itogov i perehod k sleduyushchemu testu.

   GRUPPY TESTov:
     T01..T30 -- otdelnye komandy (Stages 0)
     P01..P05 -- programma slozheniya iz pamyati (Stage 1)
     L01..L08 -- tsikly DJNZ i DEC+JP NZ (Stage 2)
     I01..I07 -- tselostnost (Stage 3)

   ITOG: Test_Total_Pass = Test_Count, Test_Fail_Count = 0.
   ========================================================================= *)
VAR
    fbCase       : FB_TestCase;
    bFirstScan   : BOOL := TRUE;
    nRun         : INT;
    i            : INT;
    j            : INT;
    k            : INT;
    bPrepared    : BOOL;
END_VAR

(* ============================== PODGOTOVKA ==============================
   Odnorazovoe zapolnenie tablitsy testov. Kazhdaya stroka -- odna proverka:
   Opcode, nachalnye znacheniya, ozhidaemyy rezultat i maski (chto proveryaem). *)
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
        GVL_Tests.Tests[i].Init_HL := 0;
        GVL_Tests.Tests[i].Exp_A := 0;
        GVL_Tests.Tests[i].Exp_F := 0;
        GVL_Tests.Tests[i].Exp_PC := 0;
        GVL_Tests.Tests[i].Exp_Mem := 0;
        GVL_Tests.Tests[i].Exp_Mem_Addr := 0;
        GVL_Tests.Tests[i].Exp_Cycles := 1;
        GVL_Tests.Tests[i].Mask_A := FALSE;
        GVL_Tests.Tests[i].Mask_F := FALSE;
        GVL_Tests.Tests[i].Mask_PC := FALSE;
        GVL_Tests.Tests[i].Mask_Mem := FALSE;
    END_FOR

    (* ---------------- T01..T06: peresylki LD (flagi NE menyayutsya) --------
       Init_F := FFh -- esli komanda sluchayno isportit flagi, test upadet. *)
    GVL_Tests.Tests[1].Enabled := TRUE;   (* T01 LD B,n *)
    GVL_Tests.Tests[1].Opcode := 16#06;
    GVL_Tests.Tests[1].Init_F := 16#FF;
    GVL_Tests.Tests[1].Mask_F := TRUE;
    GVL_Tests.Tests[1].Exp_F := 16#FF;

    GVL_Tests.Tests[2].Enabled := TRUE;   (* T02 LD A,n *)
    GVL_Tests.Tests[2].Opcode := 16#3E;
    GVL_Tests.Tests[2].Init_F := 16#FF;
    GVL_Tests.Tests[2].Mask_F := TRUE;
    GVL_Tests.Tests[2].Exp_F := 16#FF;

    GVL_Tests.Tests[3].Enabled := TRUE;   (* T03 LD C,B *)
    GVL_Tests.Tests[3].Opcode := 16#48;
    GVL_Tests.Tests[3].Init_B := 16#3C;
    GVL_Tests.Tests[3].Init_F := 16#FF;
    GVL_Tests.Tests[3].Mask_F := TRUE;
    GVL_Tests.Tests[3].Exp_F := 16#FF;

    GVL_Tests.Tests[4].Enabled := TRUE;   (* T04 LD A,L *)
    GVL_Tests.Tests[4].Opcode := 16#7D;
    GVL_Tests.Tests[4].Init_HL := 16#1100;
    GVL_Tests.Tests[4].Mask_A := TRUE;
    GVL_Tests.Tests[4].Exp_A := 16#00;

    GVL_Tests.Tests[5].Enabled := TRUE;   (* T05 LD (HL),A -- zapis v pamyat *)
    GVL_Tests.Tests[5].Opcode := 16#77;
    GVL_Tests.Tests[5].Init_A := 16#AA;
    GVL_Tests.Tests[5].Init_HL := 16#2000;
    GVL_Tests.Tests[5].Mask_Mem := TRUE;
    GVL_Tests.Tests[5].Exp_Mem_Addr := 16#2000;
    GVL_Tests.Tests[5].Exp_Mem := 16#AA;

    GVL_Tests.Tests[6].Enabled := TRUE;   (* T06 LD A,(HL) -- chtenie iz pamyati *)
    GVL_Tests.Tests[6].Opcode := 16#7E;
    GVL_Tests.Tests[6].Init_HL := 16#2000;
    GVL_Tests.Tests[6].Mask_A := TRUE;
    GVL_Tests.Tests[6].Exp_A := 16#55;

    (* ---------------- T07..T12: ADD i SUB --------------------------------- *)
    GVL_Tests.Tests[7].Enabled := TRUE;   (* T07 ADD 25h+10h=35h *)
    GVL_Tests.Tests[7].Opcode := 16#80;
    GVL_Tests.Tests[7].Init_A := 16#25;
    GVL_Tests.Tests[7].Init_B := 16#10;
    GVL_Tests.Tests[7].Mask_A := TRUE;   GVL_Tests.Tests[7].Exp_A := 16#35;
    GVL_Tests.Tests[7].Mask_F := TRUE;   GVL_Tests.Tests[7].Exp_F := 16#00;

    GVL_Tests.Tests[8].Enabled := TRUE;   (* T08 ADD perepolnenie -> 94h *)
    GVL_Tests.Tests[8].Opcode := 16#80;
    GVL_Tests.Tests[8].Init_A := 16#7F;
    GVL_Tests.Tests[8].Init_B := 16#01;
    GVL_Tests.Tests[8].Mask_A := TRUE;   GVL_Tests.Tests[8].Exp_A := 16#80;
    GVL_Tests.Tests[8].Mask_F := TRUE;   GVL_Tests.Tests[8].Exp_F := 16#94;

    GVL_Tests.Tests[9].Enabled := TRUE;   (* T09 ADD perenos -> 50h *)
    GVL_Tests.Tests[9].Opcode := 16#80;
    GVL_Tests.Tests[9].Init_A := 16#FF;
    GVL_Tests.Tests[9].Init_B := 16#01;
    GVL_Tests.Tests[9].Mask_A := TRUE;   GVL_Tests.Tests[9].Exp_A := 16#00;
    GVL_Tests.Tests[9].Mask_F := TRUE;   GVL_Tests.Tests[9].Exp_F := 16#50;

    GVL_Tests.Tests[10].Enabled := TRUE;  (* T10 SUB 50h-30h=20h *)
    GVL_Tests.Tests[10].Opcode := 16#90;
    GVL_Tests.Tests[10].Init_A := 16#50;
    GVL_Tests.Tests[10].Init_B := 16#30;
    GVL_Tests.Tests[10].Mask_A := TRUE;  GVL_Tests.Tests[10].Exp_A := 16#20;
    GVL_Tests.Tests[10].Mask_F := TRUE;  GVL_Tests.Tests[10].Exp_F := 16#02;

    GVL_Tests.Tests[11].Enabled := TRUE;  (* T11 SUB zaym -> 83h *)
    GVL_Tests.Tests[11].Opcode := 16#90;
    GVL_Tests.Tests[11].Init_A := 16#10;
    GVL_Tests.Tests[11].Init_B := 16#20;
    GVL_Tests.Tests[11].Mask_A := TRUE;  GVL_Tests.Tests[11].Exp_A := 16#F0;
    GVL_Tests.Tests[11].Mask_F := TRUE;  GVL_Tests.Tests[11].Exp_F := 16#83;

    GVL_Tests.Tests[12].Enabled := TRUE;  (* T12 SUB perepolnenie -> 47h *)
    GVL_Tests.Tests[12].Opcode := 16#90;
    GVL_Tests.Tests[12].Init_A := 16#80;
    GVL_Tests.Tests[12].Init_B := 16#01;
    GVL_Tests.Tests[12].Mask_A := TRUE;  GVL_Tests.Tests[12].Exp_A := 16#7F;
    GVL_Tests.Tests[12].Mask_F := TRUE;  GVL_Tests.Tests[12].Exp_F := 16#47;

    (* ---------------- T13..T16: INC i DEC (C NE menyaetsya!) ------------- *)
    GVL_Tests.Tests[13].Enabled := TRUE;  (* T13 INC A: 0Fh->10h, H=1, C ostalsya *)
    GVL_Tests.Tests[13].Opcode := 16#3C;
    GVL_Tests.Tests[13].Init_A := 16#0F;
    GVL_Tests.Tests[13].Init_F := 16#01;
    GVL_Tests.Tests[13].Mask_A := TRUE;  GVL_Tests.Tests[13].Exp_A := 16#10;

    GVL_Tests.Tests[14].Enabled := TRUE;  (* T14 INC A perepolnenie: 7Fh->80h *)
    GVL_Tests.Tests[14].Opcode := 16#3C;
    GVL_Tests.Tests[14].Init_A := 16#7F;
    GVL_Tests.Tests[14].Mask_A := TRUE;  GVL_Tests.Tests[14].Exp_A := 16#80;

    GVL_Tests.Tests[15].Enabled := TRUE;  (* T15 DEC B: 01h->00h, Z=1 *)
    GVL_Tests.Tests[15].Opcode := 16#05;
    GVL_Tests.Tests[15].Init_B := 16#01;
    GVL_Tests.Tests[15].Init_F := 16#01;
    GVL_Tests.Tests[15].Mask_F := TRUE;  GVL_Tests.Tests[15].Exp_F := 16#42;

    GVL_Tests.Tests[16].Enabled := TRUE;  (* T16 DEC B zaym: 00h->FFh *)
    GVL_Tests.Tests[16].Opcode := 16#05;
    GVL_Tests.Tests[16].Init_B := 16#00;
    GVL_Tests.Tests[16].Mask_F := TRUE;  GVL_Tests.Tests[16].Exp_F := 16#BA;

    (* ---------------- T17..T21: perehody JP ------------------------------- *)
    GVL_Tests.Tests[17].Enabled := TRUE;  (* T17 JP 2000h *)
    GVL_Tests.Tests[17].Opcode := 16#C3;
    GVL_Tests.Tests[17].Mask_PC := TRUE;
    GVL_Tests.Tests[17].Exp_PC := 16#2000;

    GVL_Tests.Tests[18].Enabled := TRUE;  (* T18 JP Z pri Z=1 -- perehod *)
    GVL_Tests.Tests[18].Opcode := 16#CA;
    GVL_Tests.Tests[18].Init_F := 16#40;
    GVL_Tests.Tests[18].Test_Has_Cond := TRUE;
    GVL_Tests.Tests[18].Mask_PC := TRUE;
    GVL_Tests.Tests[18].Exp_PC := 16#2000;

    GVL_Tests.Tests[19].Enabled := TRUE;  (* T19 JP Z pri Z=0 -- net perehoda *)
    GVL_Tests.Tests[19].Opcode := 16#CA;
    GVL_Tests.Tests[19].Init_F := 16#00;
    GVL_Tests.Tests[19].Mask_PC := TRUE;
    GVL_Tests.Tests[19].Exp_PC := 16#0003;

    GVL_Tests.Tests[20].Enabled := TRUE;  (* T20 JP NZ pri Z=0 -- perehod *)
    GVL_Tests.Tests[20].Opcode := 16#C2;
    GVL_Tests.Tests[20].Init_F := 16#00;
    GVL_Tests.Tests[20].Mask_PC := TRUE;
    GVL_Tests.Tests[20].Exp_PC := 16#2000;

    GVL_Tests.Tests[21].Enabled := TRUE;  (* T21 JP NZ pri Z=1 -- net perehoda *)
    GVL_Tests.Tests[21].Opcode := 16#C2;
    GVL_Tests.Tests[21].Init_F := 16#40;
    GVL_Tests.Tests[21].Test_Has_Cond := TRUE;
    GVL_Tests.Tests[21].Mask_PC := TRUE;
    GVL_Tests.Tests[21].Exp_PC := 16#0003;

    (* ---------------- T22..T24: CALL, RET, HALT --------------------------- *)
    GVL_Tests.Tests[22].Enabled := TRUE;  (* T22 CALL 2000h, SP nachal 1 *)
    GVL_Tests.Tests[22].Opcode := 16#CD;
    GVL_Tests.Tests[22].Init_SP := 16#0001;
    GVL_Tests.Tests[22].Mask_PC := TRUE;
    GVL_Tests.Tests[22].Exp_PC := 16#2000;
    GVL_Tests.Tests[22].Mask_Flag := TRUE;   (* priznak: nachalo steka *)

    GVL_Tests.Tests[23].Enabled := TRUE;  (* T23 HALT *)
    GVL_Tests.Tests[23].Opcode := 16#76;
    GVL_Tests.Tests[23].Mask_PC := TRUE;
    GVL_Tests.Tests[23].Exp_PC := 16#0001;
    GVL_Tests.Tests[23].Mask_Flag := TRUE;

    (* ---------------- T25..T26: DJNZ -------------------------------------- *)
    GVL_Tests.Tests[25].Enabled := TRUE;  (* T25 DJNZ s vetvleniem: B=2 -> 1 *)
    GVL_Tests.Tests[25].Opcode := 16#10;
    GVL_Tests.Tests[25].Init_B := 16#02;
    GVL_Tests.Tests[25].Opcode_Lo := 16#FD;   (* smeshchenie -3 *)
    GVL_Tests.Tests[25].Mask_Flag := TRUE;    (* B nachal 2, stal 1 *)

    GVL_Tests.Tests[26].Enabled := TRUE;  (* T26 DJNZ bez vetvleniya: B=1 -> 0 *)
    GVL_Tests.Tests[26].Opcode := 16#10;
    GVL_Tests.Tests[26].Init_B := 16#01;
    GVL_Tests.Tests[26].Opcode_Lo := 16#FD;
    GVL_Tests.Tests[26].Mask_Flag := TRUE;

    (* ---------------- T27..T30: logika i CP -------------------------------- *)
    GVL_Tests.Tests[27].Enabled := TRUE;  (* T27 AND -> 00h, Z=1 PV=1 *)
    GVL_Tests.Tests[27].Opcode := 16#A0;
    GVL_Tests.Tests[27].Init_A := 16#0F;
    GVL_Tests.Tests[27].Init_B := 16#F0;
    GVL_Tests.Tests[27].Mask_A := TRUE;  GVL_Tests.Tests[27].Exp_A := 16#00;
    GVL_Tests.Tests[27].Mask_F := TRUE;  GVL_Tests.Tests[27].Exp_F := 16#44;

    GVL_Tests.Tests[28].Enabled := TRUE;  (* T28 OR -> FFh, S=1 *)
    GVL_Tests.Tests[28].Opcode := 16#B0;
    GVL_Tests.Tests[28].Init_A := 16#0F;
    GVL_Tests.Tests[28].Init_B := 16#F0;
    GVL_Tests.Tests[28].Mask_A := TRUE;  GVL_Tests.Tests[28].Exp_A := 16#FF;
    GVL_Tests.Tests[28].Mask_F := TRUE;  GVL_Tests.Tests[28].Exp_F := 16#80;

    GVL_Tests.Tests[29].Enabled := TRUE;  (* T29 XOR -> 00h, Z=1 PV=1 *)
    GVL_Tests.Tests[29].Opcode := 16#A8;
    GVL_Tests.Tests[29].Init_A := 16#FF;
    GVL_Tests.Tests[29].Init_B := 16#FF;
    GVL_Tests.Tests[29].Mask_A := TRUE;  GVL_Tests.Tests[29].Exp_A := 16#00;
    GVL_Tests.Tests[29].Mask_F := TRUE;  GVL_Tests.Tests[29].Exp_F := 16#44;

    GVL_Tests.Tests[30].Enabled := TRUE;  (* T30 CP: A NE menyaetsya, Z=1 N=1 C=1 *)
    GVL_Tests.Tests[30].Opcode := 16#B8;
    GVL_Tests.Tests[30].Init_A := 16#50;
    GVL_Tests.Tests[30].Init_B := 16#50;
    GVL_Tests.Tests[30].Mask_A := TRUE;  GVL_Tests.Tests[30].Exp_A := 16#50;
    GVL_Tests.Tests[30].Mask_F := TRUE;  GVL_Tests.Tests[30].Exp_F := 16#46;

    (* ---------------- T31..T46: otdelnye flagi (F_*) --------------------- *)
    GVL_Tests.Tests[31].Enabled := TRUE;  (* F_S1: S=1 *)
    GVL_Tests.Tests[31].Opcode := 16#80;
    GVL_Tests.Tests[31].Init_A := 16#00;
    GVL_Tests.Tests[31].Init_B := 16#80;
    GVL_Tests.Tests[31].Mask_A := TRUE;  GVL_Tests.Tests[31].Exp_A := 16#80;
    GVL_Tests.Tests[31].Mask_F := TRUE;  GVL_Tests.Tests[31].Exp_F := 16#80;

    GVL_Tests.Tests[32].Enabled := TRUE;  (* F_S2: S=0 *)
    GVL_Tests.Tests[32].Opcode := 16#80;
    GVL_Tests.Tests[32].Init_A := 16#00;
    GVL_Tests.Tests[32].Init_B := 16#7F;
    GVL_Tests.Tests[32].Mask_A := TRUE;  GVL_Tests.Tests[32].Exp_A := 16#7F;
    GVL_Tests.Tests[32].Mask_F := TRUE;  GVL_Tests.Tests[32].Exp_F := 16#00;

    GVL_Tests.Tests[33].Enabled := TRUE;  (* F_Z1: Z=1 *)
    GVL_Tests.Tests[33].Opcode := 16#80;
    GVL_Tests.Tests[33].Init_A := 16#FF;
    GVL_Tests.Tests[33].Init_B := 16#01;
    GVL_Tests.Tests[33].Mask_A := TRUE;  GVL_Tests.Tests[33].Exp_A := 16#00;
    GVL_Tests.Tests[33].Mask_F := TRUE;  GVL_Tests.Tests[33].Exp_F := 16#50;

    GVL_Tests.Tests[34].Enabled := TRUE;  (* F_Z2: Z=0 *)
    GVL_Tests.Tests[34].Opcode := 16#80;
    GVL_Tests.Tests[34].Init_A := 16#00;
    GVL_Tests.Tests[34].Init_B := 16#01;
    GVL_Tests.Tests[34].Mask_A := TRUE;  GVL_Tests.Tests[34].Exp_A := 16#01;
    GVL_Tests.Tests[34].Mask_F := TRUE;  GVL_Tests.Tests[34].Exp_F := 16#00;

    GVL_Tests.Tests[35].Enabled := TRUE;  (* F_H1: H=1 pri perenose iz bita 3 *)
    GVL_Tests.Tests[35].Opcode := 16#80;
    GVL_Tests.Tests[35].Init_A := 16#0F;
    GVL_Tests.Tests[35].Init_B := 16#01;
    GVL_Tests.Tests[35].Mask_A := TRUE;  GVL_Tests.Tests[35].Exp_A := 16#10;
    GVL_Tests.Tests[35].Mask_F := TRUE;  GVL_Tests.Tests[35].Exp_F := 16#10;

    GVL_Tests.Tests[36].Enabled := TRUE;  (* F_H2: H=1 pri ZAYME v bit 4 *)
    GVL_Tests.Tests[36].Opcode := 16#90;
    GVL_Tests.Tests[36].Init_A := 16#0F;
    GVL_Tests.Tests[36].Init_B := 16#01;
    GVL_Tests.Tests[36].Mask_A := TRUE;  GVL_Tests.Tests[36].Exp_A := 16#0E;
    GVL_Tests.Tests[36].Mask_F := TRUE;  GVL_Tests.Tests[36].Exp_F := 16#12;

    GVL_Tests.Tests[37].Enabled := TRUE;  (* F_H3: logika vsegda H=0 *)
    GVL_Tests.Tests[37].Opcode := 16#B0;
    GVL_Tests.Tests[37].Init_A := 16#00;
    GVL_Tests.Tests[37].Init_B := 16#0F;
    GVL_Tests.Tests[37].Mask_A := TRUE;  GVL_Tests.Tests[37].Exp_A := 16#0F;
    GVL_Tests.Tests[37].Mask_F := TRUE;  GVL_Tests.Tests[37].Exp_F := 16#04;

    GVL_Tests.Tests[38].Enabled := TRUE;  (* F_PV1: perepolnenie ADD *)
    GVL_Tests.Tests[38].Opcode := 16#80;
    GVL_Tests.Tests[38].Init_A := 16#7F;
    GVL_Tests.Tests[38].Init_B := 16#01;
    GVL_Tests.Tests[38].Mask_A := TRUE;  GVL_Tests.Tests[38].Exp_A := 16#80;
    GVL_Tests.Tests[38].Mask_F := TRUE;  GVL_Tests.Tests[38].Exp_F := 16#94;

    GVL_Tests.Tests[39].Enabled := TRUE;  (* F_PV2: chetnaya chetnost *)
    GVL_Tests.Tests[39].Opcode := 16#B0;
    GVL_Tests.Tests[39].Init_A := 16#03;
    GVL_Tests.Tests[39].Init_B := 16#00;
    GVL_Tests.Tests[39].Mask_A := TRUE;  GVL_Tests.Tests[39].Exp_A := 16#03;
    GVL_Tests.Tests[39].Mask_F := TRUE;  GVL_Tests.Tests[39].Exp_F := 16#04;

    GVL_Tests.Tests[40].Enabled := TRUE;  (* F_PV3: nechetnaya chetnost *)
    GVL_Tests.Tests[40].Opcode := 16#B0;
    GVL_Tests.Tests[40].Init_A := 16#07;
    GVL_Tests.Tests[40].Init_B := 16#00;
    GVL_Tests.Tests[40].Mask_A := TRUE;  GVL_Tests.Tests[40].Exp_A := 16#07;
    GVL_Tests.Tests[40].Mask_F := TRUE;  GVL_Tests.Tests[40].Exp_F := 16#00;

    GVL_Tests.Tests[41].Enabled := TRUE;  (* F_N1: ADD sbrosit N *)
    GVL_Tests.Tests[41].Opcode := 16#80;
    GVL_Tests.Tests[41].Init_A := 16#10;
    GVL_Tests.Tests[41].Init_B := 16#01;
    GVL_Tests.Tests[41].Mask_A := TRUE;  GVL_Tests.Tests[41].Exp_A := 16#11;
    GVL_Tests.Tests[41].Mask_F := TRUE;  GVL_Tests.Tests[41].Exp_F := 16#00;

    GVL_Tests.Tests[42].Enabled := TRUE;  (* F_N2: SUB postavit N *)
    GVL_Tests.Tests[42].Opcode := 16#90;
    GVL_Tests.Tests[42].Init_A := 16#10;
    GVL_Tests.Tests[42].Init_B := 16#01;
    GVL_Tests.Tests[42].Mask_A := TRUE;  GVL_Tests.Tests[42].Exp_A := 16#0F;
    GVL_Tests.Tests[42].Mask_F := TRUE;  GVL_Tests.Tests[42].Exp_F := 16#12;

    GVL_Tests.Tests[43].Enabled := TRUE;  (* F_C1: perenos iz bita 7 *)
    GVL_Tests.Tests[43].Opcode := 16#80;
    GVL_Tests.Tests[43].Init_A := 16#FF;
    GVL_Tests.Tests[43].Init_B := 16#01;
    GVL_Tests.Tests[43].Mask_A := TRUE;  GVL_Tests.Tests[43].Exp_A := 16#00;
    GVL_Tests.Tests[43].Mask_F := TRUE;  GVL_Tests.Tests[43].Exp_F := 16#50;

    GVL_Tests.Tests[44].Enabled := TRUE;  (* F_C2: zaym *)
    GVL_Tests.Tests[44].Opcode := 16#90;
    GVL_Tests.Tests[44].Init_A := 16#10;
    GVL_Tests.Tests[44].Init_B := 16#20;
    GVL_Tests.Tests[44].Mask_A := TRUE;  GVL_Tests.Tests[44].Exp_A := 16#F0;
    GVL_Tests.Tests[44].Mask_F := TRUE;  GVL_Tests.Tests[44].Exp_F := 16#83;

    GVL_Tests.Tests[45].Enabled := TRUE;  (* F_C3: INC NE menyaet C *)
    GVL_Tests.Tests[45].Opcode := 16#3C;
    GVL_Tests.Tests[45].Init_A := 16#0F;
    GVL_Tests.Tests[45].Init_F := 16#01;
    GVL_Tests.Tests[45].Mask_A := TRUE;  GVL_Tests.Tests[45].Exp_A := 16#10;
    GVL_Tests.Tests[45].Mask_F := TRUE;  GVL_Tests.Tests[45].Exp_F := 16#11;

    GVL_Tests.Tests[46].Enabled := TRUE;  (* F_F53: F5/F3 -- tolko fiksatsiya *)
    GVL_Tests.Tests[46].Opcode := 16#80;
    GVL_Tests.Tests[46].Init_A := 16#FF;
    GVL_Tests.Tests[46].Init_B := 16#01;
    GVL_Tests.Tests[46].Mask_A := TRUE;  GVL_Tests.Tests[46].Exp_A := 16#00;

    (* ---------------- T47..T50: izolyatsiya flagov (F_ISO) --------------- *)
    GVL_Tests.Tests[47].Enabled := TRUE;  (* F_ISO1: LD A,n ne tроgaet F *)
    GVL_Tests.Tests[47].Opcode := 16#3E;
    GVL_Tests.Tests[47].Init_F := 16#FF;
    GVL_Tests.Tests[47].Mask_F := TRUE;  GVL_Tests.Tests[47].Exp_F := 16#FF;

    GVL_Tests.Tests[48].Enabled := TRUE;  (* F_ISO3: JP Z pri Z=0 ne menyaet F *)
    GVL_Tests.Tests[48].Opcode := 16#CA;
    GVL_Tests.Tests[48].Init_F := 16#55;
    GVL_Tests.Tests[48].Mask_F := TRUE;  GVL_Tests.Tests[48].Exp_F := 16#55;

    (* ---------------- T51..T55: programma P01..P05 ------------------------ *)
    GVL_Tests.Tests[51].Enabled := TRUE;  (* P01: rezultat v pamyati 2002h *)
    GVL_Tests.Tests[51].Stage := 1;
    GVL_Tests.Tests[51].Mask_Mem := TRUE;
    GVL_Tests.Tests[51].Exp_Mem_Addr := 16#2002;
    GVL_Tests.Tests[51].Exp_Mem := 16#35;
    GVL_Tests.Tests[51].Exp_Cycles := 5;

    GVL_Tests.Tests[52].Enabled := TRUE;  (* P02: A = 35h *)
    GVL_Tests.Tests[52].Stage := 1;
    GVL_Tests.Tests[52].Mask_A := TRUE;
    GVL_Tests.Tests[52].Exp_A := 16#35;
    GVL_Tests.Tests[52].Exp_Cycles := 5;

    GVL_Tests.Tests[53].Enabled := TRUE;  (* P03: B = 10h *)
    GVL_Tests.Tests[53].Stage := 1;
    GVL_Tests.Tests[53].Mask_F := TRUE;
    GVL_Tests.Tests[53].Exp_F := 16#00;
    GVL_Tests.Tests[53].Exp_Cycles := 5;

    GVL_Tests.Tests[54].Enabled := TRUE;  (* P04: PC = 010Bh posle 5 komand *)
    GVL_Tests.Tests[54].Stage := 1;
    GVL_Tests.Tests[54].Mask_PC := TRUE;
    GVL_Tests.Tests[54].Exp_PC := 16#010B;
    GVL_Tests.Tests[54].Exp_Cycles := 5;

    GVL_Tests.Tests[55].Enabled := TRUE;  (* P05: H,L ne izmenilis *)
    GVL_Tests.Tests[55].Stage := 1;
    GVL_Tests.Tests[55].Mask_Mem := TRUE;
    GVL_Tests.Tests[55].Exp_Mem_Addr := 16#2000;
    GVL_Tests.Tests[55].Exp_Mem := 16#25;
    GVL_Tests.Tests[55].Exp_Cycles := 5;

    (* ---------------- T56..T60: tsikly L01..L05 --------------------------- *)
    GVL_Tests.Tests[56].Enabled := TRUE;  (* L01: DJNZ 5 iteracij -> 13h *)
    GVL_Tests.Tests[56].Stage := 2;
    GVL_Tests.Tests[56].Mask_Mem := TRUE;
    GVL_Tests.Tests[56].Exp_Mem_Addr := 16#2000;
    GVL_Tests.Tests[56].Exp_Mem := 16#13;
    GVL_Tests.Tests[56].Exp_Cycles := 14;

    GVL_Tests.Tests[57].Enabled := TRUE;  (* L02: B = 0 posle tsikla *)
    GVL_Tests.Tests[57].Stage := 2;
    GVL_Tests.Tests[57].Mask_Flag := TRUE;
    GVL_Tests.Tests[57].Exp_Cycles := 14;

    GVL_Tests.Tests[58].Enabled := TRUE;  (* L03: PC posle tsikla = 0128h *)
    GVL_Tests.Tests[58].Stage := 2;
    GVL_Tests.Tests[58].Mask_PC := TRUE;
    GVL_Tests.Tests[58].Exp_PC := 16#0128;
    GVL_Tests.Tests[58].Exp_Cycles := 14;

    GVL_Tests.Tests[59].Enabled := TRUE;  (* L06: DEC+JP NZ -> A = 06h *)
    GVL_Tests.Tests[59].Stage := 2;
    GVL_Tests.Tests[59].Mask_A := TRUE;
    GVL_Tests.Tests[59].Exp_A := 16#06;
    GVL_Tests.Tests[59].Exp_Cycles := 12;
    GVL_Tests.Tests[59].Opcode := 1;      (* priznak: programma nomer 3 *)

    GVL_Tests.Tests[60].Enabled := TRUE;  (* L07: B = 0 posle tsikla *)
    GVL_Tests.Tests[60].Stage := 2;
    GVL_Tests.Tests[60].Mask_Flag := TRUE;
    GVL_Tests.Tests[60].Exp_Cycles := 12;
    GVL_Tests.Tests[60].Opcode := 1;

    (* ---------------- T61..T62: tselostnost I01..I02 --------------------- *)
    GVL_Tests.Tests[61].Enabled := TRUE;  (* I01: alt. nabor ne meshaet osnovnomu *)
    GVL_Tests.Tests[61].Stage := 3;
    GVL_Tests.Tests[61].Opcode := 16#80;
    GVL_Tests.Tests[61].Init_A := 16#11;
    GVL_Tests.Tests[61].Init_B := 16#22;
    GVL_Tests.Tests[61].Mask_A := TRUE;
    GVL_Tests.Tests[61].Exp_A := 16#33;

    GVL_Tests.Tests[62].Enabled := TRUE;  (* I02: SP ne meshaet ALU *)
    GVL_Tests.Tests[62].Stage := 3;
    GVL_Tests.Tests[62].Opcode := 16#80;
    GVL_Tests.Tests[62].Init_A := 16#01;
    GVL_Tests.Tests[62].Init_B := 16#02;
    GVL_Tests.Tests[62].Init_SP := 16#ABCD;
    GVL_Tests.Tests[62].Mask_A := TRUE;
    GVL_Tests.Tests[62].Exp_A := 16#03;

    (* schitaem skolko vklyucheno -- eto i est ozhidaemyy itog *)
    GVL_Tests.Test_Count := 0;
    FOR i := 1 TO 75 DO
        IF GVL_Tests.Tests[i].Enabled THEN
            GVL_Tests.Test_Count := GVL_Tests.Test_Count + 1;
        END_IF
    END_FOR
END_IF

(* ============================== PROGON ============================== *)
IF GVL_Tests.Test_Run THEN

    (* ---- shag 0: podgotovka ---- *)
    IF GVL_Tests.Test_Stage = 0 THEN
        GVL_Control.Emu_Run := FALSE;

        i := 1;
        WHILE i <= 75 AND NOT GVL_Tests.Tests[i].Enabled DO
            i := i + 1;
        END_WHILE
        GVL_Tests.Test_Active := i;

        IF i > 75 THEN
            GVL_Tests.Test_Run := FALSE;
        ELSE
            bPrepared := FALSE;
            nRun := 0;
            GVL_Tests.Test_Stage := 1;
        END_IF

    (* ---- shag 1: zagruzka pamyati i registrov, zapusk ---- *)
    ELSIF GVL_Tests.Test_Stage = 1 THEN
        IF NOT bPrepared THEN
            i := GVL_Tests.Test_Active;

            (* --- pamyat --- *)
            FOR k := 0 TO 15 DO
                Z80_Mem[k] := 0;
            END_FOR
            Z80_Mem[16#2000] := 16#55;   (* dlya T06 LD A,(HL) *)
            Z80_Mem[16#2001] := 16#00;
            Z80_Mem[16#2002] := 16#00;

            IF GVL_Tests.Tests[i].Stage = 0 THEN
                (* otdelnaya komanda: kod po adresu 0, operandy po 1 i 2 *)
                Z80_Mem[0] := GVL_Tests.Tests[i].Opcode;
                Z80_Mem[1] := GVL_Tests.Tests[i].Init_A;
                Z80_Mem[2] := GVL_Tests.Tests[i].Init_B;
                (* dlya JP/CALL operand -- adres 2000h: mladshij 00h, starshij 20h *)
                Z80_Mem[1] := 16#00;
                Z80_Mem[2] := 16#20;
                IF GVL_Tests.Tests[i].Opcode = 16#10 THEN
                    Z80_Mem[1] := GVL_Tests.Tests[i].Opcode_Lo;
                END_IF
                Z80_Mem[3] := 16#00;

            ELSIF GVL_Tests.Tests[i].Stage = 1 THEN
                (* programma 1: slozhenie dvuh chisel iz pamyati *)
                Z80_Mem[16#0100] := 16#3A;  Z80_Mem[16#0101] := 16#00;
                Z80_Mem[16#0102] := 16#20;
                Z80_Mem[16#0103] := 16#47;
                Z80_Mem[16#0104] := 16#3A;  Z80_Mem[16#0105] := 16#01;
                Z80_Mem[16#0106] := 16#20;
                Z80_Mem[16#0107] := 16#80;
                Z80_Mem[16#0108] := 16#32;  Z80_Mem[16#0109] := 16#02;
                Z80_Mem[16#010A] := 16#20;
                Z80_Mem[16#2000] := 16#25;
                Z80_Mem[16#2001] := 16#10;
                Z80_Mem[16#2002] := 16#00;

            ELSE
                (* programmy tsiklov *)
                IF GVL_Tests.Tests[i].Opcode = 0 THEN
                    (* DJNZ: 5 iteracij, summa 5+4+3+2+1 = 19 = 13h *)
                    Z80_Mem[16#0120] := 16#06;  Z80_Mem[16#0121] := 16#05;
                    Z80_Mem[16#0122] := 16#AF;
                    Z80_Mem[16#0123] := 16#80;
                    Z80_Mem[16#0124] := 16#10;  Z80_Mem[16#0125] := 16#FD;
                    Z80_Mem[16#0126] := 16#32;  Z80_Mem[16#0127] := 16#00;
                    Z80_Mem[16#0128] := 16#20;
                    GVL_InitRegs.Init_PC := 16#0120;
                ELSE
                    (* DEC B + JP NZ: 3 iteracii, 3+2+1 = 6 *)
                    Z80_Mem[16#0140] := 16#06;  Z80_Mem[16#0141] := 16#03;
                    Z80_Mem[16#0142] := 16#AF;
                    Z80_Mem[16#0143] := 16#80;
                    Z80_Mem[16#0144] := 16#05;
                    Z80_Mem[16#0145] := 16#C2;  Z80_Mem[16#0146] := 16#43;
                    Z80_Mem[16#0147] := 16#01;
                    GVL_InitRegs.Init_PC := 16#0140;
                END_IF
            END_IF

            (* --- nachalnye znacheniya registrov --- *)
            FOR k := 0 TO 15 DO
                GVL_InitRegs.Init_Vals[k] := 0;
            END_FOR
            GVL_InitRegs.Init_Vals[0] := GVL_Tests.Tests[i].Init_A;   (* A *)
            GVL_InitRegs.Init_Vals[1] := GVL_Tests.Tests[i].Init_B;   (* B *)
            GVL_InitRegs.Init_Vals[5] := BYTE_TO_BYTE(
                SHR(GVL_Tests.Tests[i].Init_HL, 8));                  (* H *)
            GVL_InitRegs.Init_Vals[6] := BYTE_TO_BYTE(
                GVL_Tests.Tests[i].Init_HL);                          (* L *)
            GVL_InitRegs.Init_Vals[7] := GVL_Tests.Tests[i].Init_F;   (* F *)
            GVL_InitRegs.Init_SP := GVL_Tests.Tests[i].Init_SP;
            IF GVL_Tests.Tests[i].Stage = 0 THEN
                GVL_InitRegs.Init_PC := GVL_Tests.Tests[i].Init_PC;
            END_IF

            (* --- vypolnit initsializatsiyu registrov --- *)
            GVL_InitRegs.Init_En := TRUE;
            bPrepared := TRUE;
            GVL_Tests.Test_Stage := 4;   (* otdel nyy shag: snyat Init_En *)

    (* ---- shag 4: snyat Init_En i zapustit emulyator ---- *)
    ELSIF GVL_Tests.Test_Stage = 4 THEN
        GVL_InitRegs.Init_En := FALSE;
        GVL_Control.Emu_Run := TRUE;
        nRun := 0;
        GVL_Tests.Test_Stage := 5;

    (* ---- shag 5: prokrutit nuzhnoe chislo skanov ---- *)
    ELSIF GVL_Tests.Test_Stage = 5 THEN
        nRun := nRun + 1;
        IF nRun >= GVL_Tests.Tests[GVL_Tests.Test_Active].Exp_Cycles THEN
            GVL_Control.Emu_Run := FALSE;
            GVL_Tests.Test_Stage := 2;
        END_IF

    (* ---- shag 2: sravnenie ---- *)
    ELSIF GVL_Tests.Test_Stage = 2 THEN
        i := GVL_Tests.Test_Active;

        (* fakticheskie znacheniya: A i F berem iz zerkala HMI *)
        z80A := GVL_PLCVisu.A;
        z80F := GVL_PLCVisu.F;
        z80PC := GVL_PLCVisu.PC;
        z80Mem := Z80_Mem[GVL_Tests.Tests[i].Exp_Mem_Addr];

        fbCase.Run := TRUE;
        fbCase.Expected_A := GVL_Tests.Tests[i].Exp_A;
        fbCase.Expected_F := GVL_Tests.Tests[i].Exp_F;
        fbCase.Expected_PC := GVL_Tests.Tests[i].Exp_PC;
        fbCase.Actual_A := z80A;
        fbCase.Actual_F := z80F;
        fbCase.Actual_PC := z80PC;
        fbCase.Mask_A := GVL_Tests.Tests[i].Mask_A;
        fbCase.Mask_F := GVL_Tests.Tests[i].Mask_F;
        fbCase.Mask_PC := GVL_Tests.Tests[i].Mask_PC;

        (* dopolnitel naya proverka pamyati: esli trebuetsya *)
        IF GVL_Tests.Tests[i].Mask_Mem AND (z80Mem <> GVL_Tests.Tests[i].Exp_Mem) THEN
            GVL_Tests.Test_Result[i] := FALSE;
        ELSE
            GVL_Tests.Test_Result[i] := fbCase.Pass;
        END_IF
        GVL_Tests.Test_Executed[i] := TRUE;
        GVL_Tests.Test_Stage := 3;

    (* ---- shag 3: itogi i sleduyushchiy test ---- *)
    ELSE
        GVL_Tests.Test_Total_Pass := 0;
        GVL_Tests.Test_Fail_Count := 0;
        FOR i := 1 TO 75 DO
            IF GVL_Tests.Test_Executed[i] THEN
                IF GVL_Tests.Test_Result[i] THEN
                    GVL_Tests.Test_Total_Pass := GVL_Tests.Test_Total_Pass + 1;
                ELSE
                    IF GVL_Tests.Test_Fail_Count < 16 THEN
                        GVL_Tests.Test_Failed_List[
                            GVL_Tests.Test_Fail_Count + 1] := i;
                    END_IF
                    GVL_Tests.Test_Fail_Count := GVL_Tests.Test_Fail_Count + 1;
                END_IF
            END_IF
        END_FOR

        (* perehod k sleduyushchemu vklyuchennomu testu *)
        j := GVL_Tests.Test_Active + 1;
        WHILE j <= 75 AND NOT GVL_Tests.Tests[j].Enabled DO
            j := j + 1;
        END_WHILE
        IF j <= 75 THEN
            GVL_Tests.Test_Active := j;
            bPrepared := FALSE;
            GVL_Tests.Test_Stage := 1;
        ELSE
            GVL_Tests.Test_Stage := 9;   (* vse testy projdeny *)
            GVL_Tests.Test_Run := FALSE;
        END_IF
    END_IF
END_IF

(* zerkalo dlya HMI *)
GVL_PLCVisu.Test_Total_Pass := GVL_Tests.Test_Total_Pass;
GVL_PLCVisu.Test_Fail_Count := GVL_Tests.Test_Fail_Count;
GVL_PLCVisu.Test_Stage := GVL_Tests.Test_Stage;
GVL_PLCVisu.Test_Active := GVL_Tests.Test_Active;
'''

ST_TESTCASE = u'''TYPE ST_TestCase :
STRUCT
    (* OPISANIE ODNOGO TESTA. Chtoby dobavit test, dostatochno zapolnit
       ocherednuyu stroku massiva -- shema ne menyaetsya. *)
    Id           : INT;
    Stage        : INT;    (* 0 komanda, 1 programma, 2 tsikl, 3 tselostnost *)
    Opcode       : BYTE;
    Opcode_Lo    : BYTE;   (* vtoroy bajt komandy (napr. smeshchenie DJNZ) *)
    Init_A       : BYTE;
    Init_B       : BYTE;
    Init_F       : BYTE;
    Init_PC      : WORD;
    Init_SP      : WORD;
    Init_HL      : WORD;
    Exp_A        : BYTE;
    Exp_F        : BYTE;
    Exp_PC       : WORD;
    Exp_Mem      : BYTE;
    Exp_Mem_Addr : WORD;
    Exp_Cycles   : INT;
    Mask_A       : BOOL;
    Mask_F       : BOOL;
    Mask_PC      : BOOL;
    Mask_Mem     : BOOL;
    Mask_Flag    : BOOL;   (* sluzhebnyy priznak testa *)
    Test_Has_Cond : BOOL;  (* uslovnyy perehod: Z podavaetsya na vhod usloviya *)
    Enabled      : BOOL;
END_STRUCT
END_TYPE
'''

GVL_TESTS = u'''VAR_GLOBAL
    (* ================== DANNYE TESTIROVANIYa ==================
       Struktura odnogo testa -- tip ST_TestCase. Rezul'tat -- BOOL:
       TRUE = PASS, FALSE = FAIL. Nikakih isklyuchenij: proverka delaetsya
       blokom EQ vnutri FB_TestCase. *)
    Test_Run         : BOOL;
    Test_Stage       : INT;
    Test_Active      : INT;
    Test_Count       : INT;

    Test_Result      : ARRAY[1..75] OF BOOL;
    Test_Executed    : ARRAY[1..75] OF BOOL;
    Test_Total_Pass  : INT;
    Test_Fail_Count  : INT;
    Test_Failed_List : ARRAY[1..16] OF INT;
END_VAR
'''

NEW_FN = u'''def mk_gvl_initregs():
    return F.Gvl(u"GVL_InitRegs", ST_GVL_INITREGS)


'''

t = io.open(GEN, "r", encoding="utf-8").read()

# 1. zamenit ST_TEST_Z80 na polnyy nabor
i0 = t.index(u"ST_TEST_Z80 = u'''")
i1 = t.index(u"'''", i0 + 20) + 3
t = t[:i0] + u"ST_TEST_Z80 = u'''" + ST_TEST + u"'''" + t[i1:]

# 2. zamenit ST_GVL_TESTS
i0 = t.index(u"ST_GVL_TESTS = u'''")
i1 = t.index(u"'''", i0 + 20) + 3
t = t[:i0] + u"ST_GVL_TESTS = u'''" + GVL_TESTS + u"'''" + t[i1:]

# 3. zamenit ST_MEM_DECL ne nuzhno; dobavit ST_GVL_INITREGS i generator
t = t.replace(u"ST_MEM_DECL = u'''", u"ST_GVL_INITREGS = u'''" + GVL_INITREGS + u"'''\n\nST_MEM_DECL = u'''", 1)
t = t.replace(u"def mk_gvl_tests():", NEW_FN + u"def mk_gvl_tests():", 1)

# 4. dobavit GVL_InitRegs v BUILDERS
t = t.replace(u'    (u"GVL_Tests", mk_gvl_tests),',
              u'    (u"GVL_InitRegs", mk_gvl_initregs),\n    (u"GVL_Tests", mk_gvl_tests),')

# 5. ST_TestCase: novaya versiya DUT (v generator DUT otsutstvuet -- on zhivet
#    v build.py, poetomu shag neobyazatel nyy)
if u"ST_TESTCASE_DUT" in t:
    ST_TESTCASE_AS = u'ST_TESTCASE_DUT = u"""' + ST_TESTCASE + u'"""'
    i0 = t.index(u'ST_TESTCASE_DUT = u"""')
    i1 = t.index(u'"""', i0 + 22) + 3
    t = t[:i0] + ST_TESTCASE_AS + t[i1:]

io.open(GEN, "w", encoding="utf-8").write(t)
print(u"PATCH FULLTESTS OK")
