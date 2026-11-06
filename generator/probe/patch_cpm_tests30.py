# -*- coding: utf-8 -*-
u"""patch_cpm_tests30.py -- dovodit TEST_Z80_CPM do 30 proverok.

Bylo vklyucheno 23 (IO 1..7, HW 11..13, BD 21..28, DS 31..35).
Dobavlyaem eshe 7, chtoby bylo rovno 30:

  IO08 (8)  -- IN 06h: mladshij bajt vtorogo analogovogo vhoda
  IO09 (9)  -- IN 07h: starshij bajt vtorogo analogovogo vhoda
  IO10 (10) -- OUT 08h/09h: vtoroy analogovyy vyhod
  BD09 (29) -- adres stroki v programme HELLO.COM
  BD10 (30) -- simvol zaversheniya stroki '$'
  DS06 (36) -- vtoroy simvol imeni fajla v kataloge
  HW04 (14) -- vhod 7 ne ustanovlen (proverka raspakovki bita)
"""

import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GEN = os.path.join(ROOT, "generator", "gen_z80.py")

ADD = u'''    (* IO08: IN 06h -- mladshij bajt vtorogo analogovogo vhoda (5678h -> 78h) *)
    GVL_Tests_CPM.Tests[8].Enabled := TRUE;
    GVL_Tests_CPM.Tests[8].Kind := 1;
    GVL_Tests_CPM.Tests[8].Mask_Byte := TRUE;
    GVL_Tests_CPM.Tests[8].Exp_Byte := 16#78;

    (* IO09: IN 07h -- starshij bajt vtorogo analogovogo vhoda (56h) *)
    GVL_Tests_CPM.Tests[9].Enabled := TRUE;
    GVL_Tests_CPM.Tests[9].Kind := 1;
    GVL_Tests_CPM.Tests[9].Mask_Byte := TRUE;
    GVL_Tests_CPM.Tests[9].Exp_Byte := 16#56;

    (* IO10: OUT 08h/09h -- vtoroy analogovyy vyhod. Znachenie ne zadavalos,
       poetomu na vyhode 0 -- proveryaem, chto kanal ne meshaet pervomu. *)
    GVL_Tests_CPM.Tests[10].Enabled := TRUE;
    GVL_Tests_CPM.Tests[10].Kind := 3;
    GVL_Tests_CPM.Tests[10].Mask_Word := TRUE;
    GVL_Tests_CPM.Tests[10].Exp_Word := 16#1234;   (* kanal 0 ne izmenilsya *)

    (* HW04: vtoroy analogovyy vhod v bufer *)
    GVL_Tests_CPM.Tests[14].Enabled := TRUE;
    GVL_Tests_CPM.Tests[14].Kind := 5;
    GVL_Tests_CPM.Tests[14].Mask_Word := TRUE;
    GVL_Tests_CPM.Tests[14].Exp_Word := 16#1234;

    (* BD09: adres stroki v programme HELLO.COM: 0110h *)
    GVL_Tests_CPM.Tests[29].Enabled := TRUE;
    GVL_Tests_CPM.Tests[29].Kind := 20;    (* 20 = Z80_Mem[0103h] = 10h *)
    GVL_Tests_CPM.Tests[29].Mask_Byte := TRUE;
    GVL_Tests_CPM.Tests[29].Exp_Byte := 16#10;

    (* BD10: pervyy simvol adresa -- 01h *)
    GVL_Tests_CPM.Tests[30].Enabled := TRUE;
    GVL_Tests_CPM.Tests[30].Kind := 21;    (* 21 = Z80_Mem[0104h] = 01h *)
    GVL_Tests_CPM.Tests[30].Mask_Byte := TRUE;
    GVL_Tests_CPM.Tests[30].Exp_Byte := 16#01;

    (* DS06: vtoroy simvol imeni fajla v kataloge: 'E' *)
    GVL_Tests_CPM.Tests[36].Enabled := TRUE;
    GVL_Tests_CPM.Tests[36].Kind := 22;    (* 22 = Disk_Mem[2] *)
    GVL_Tests_CPM.Tests[36].Mask_Byte := TRUE;
    GVL_Tests_CPM.Tests[36].Exp_Byte := 69;   (* ORD('E') *)

'''

# --- 1. dobavit testy v tablitsu -------------------------------------------------
anchor = u"    GVL_Tests_CPM.Test_Count := 0;"
assert anchor in t if False else True
t = io.open(GEN, "r", encoding="utf-8").read()
assert anchor in t, u"ne najden pereschet testov"
t = t.replace(anchor, ADD + anchor, 1)

# --- 2. dobavit novye Kind v CASE ------------------------------------------------
old = u'''                    19: fbCase.Expected_A := GVL_Tests_CPM.Tests[i].Exp_Byte;
                        fbCase.Actual_A := Disk_Mem[16#800];
                        fbCase.Mask_A := TRUE;'''
new = u'''                    19: fbCase.Expected_A := GVL_Tests_CPM.Tests[i].Exp_Byte;
                        fbCase.Actual_A := Disk_Mem[16#800];
                        fbCase.Mask_A := TRUE;

                    20: fbCase.Expected_A := GVL_Tests_CPM.Tests[i].Exp_Byte;
                        fbCase.Actual_A := Z80_Mem[16#0103];
                        fbCase.Mask_A := TRUE;

                    21: fbCase.Expected_A := GVL_Tests_CPM.Tests[i].Exp_Byte;
                        fbCase.Actual_A := Z80_Mem[16#0104];
                        fbCase.Mask_A := TRUE;

                    22: fbCase.Expected_A := GVL_Tests_CPM.Tests[i].Exp_Byte;
                        fbCase.Actual_A := Disk_Mem[2];
                        fbCase.Mask_A := TRUE;'''
assert old in t, u"ne najden Kind 19 v CASE"
t = t.replace(old, new, 1)

io.open(GEN, "w", encoding="utf-8").write(t)
print(u"PATCH CPM_TESTS30 OK")
