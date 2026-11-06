# -*- coding: utf-8 -*-
u"""patch_bdos_full.py -- dovodit nabor funktsiy BDOS do polnogo po zadaniyu.

Bylo (v FB_CPM_BDOS): dispatch po 1,2,9,10,11,13,14,15,16,19,20,21,22,26,32,35.
Realizaciya operatsiy s pamyat yu byla tolko dlya 9,10,13,14,15,16,20,21.

Dobavlyaem v ST-drajver PRG_CPM_BDOS:
    19  F_DELETE    -- udalenie fajla (zapis' E5h v katalog)
    22  F_MAKE      -- sozdanie fajla
    26  SETDMA     -- ustanovka adresa peredachi
    27  ALLOC      -- karta zanyatyh blokov
    32  F_USERNUM  -- nomer pol zovatelya
    33  F_READRAND -- chtenie proizvol noy zapisi
    34  F_WRITERAND-- zapis' proizvol noy zapisi
    35  F_SIZE     -- razmer fajla v zapisyah

Takzhe v FB_CPM_BDOS dobavlyaem vyhody-otvety dlya etih funktsiy:
    Ret_Mode : BYTE -- chto ST-drajver dolzhen sdelat s pamyat yu
    Ret_Val  : WORD -- gotovyy otvet v HL
"""

import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GEN = os.path.join(ROOT, "generator", "gen_z80.py")

t = io.open(GEN, "r", encoding="utf-8").read()

# --- 1. FB_CPM_BDOS: dobavit vyhody Ret_Mode i Ret_Val -------------------------
old = u'''    p.var_out(u"Out_Mode", u"BYTE",
              u"rezhim vyvoda: 0 net, 1 odin simvol, 2 stroka do $")'''
new = u'''    p.var_out(u"Out_Mode", u"BYTE",
              u"rezhim vyvoda: 0 net, 1 odin simvol, 2 stroka do $")
    p.var_out(u"Ret_Mode", u"BYTE",
              u"chto delat s pamyat yu: 0 net, 1 udalit, 2 sozdat, "
              u"3 ustanovit DMA, 4 razmer fajla, 5 karta blokov")
    p.var_out(u"Ret_Val", u"WORD", u"gotovyy otvet dlya HL")'''
assert old in t, u"ne najden vyhod Out_Mode"
t = t.replace(old, new, 1)

# --- 2. realizaciya Ret_Mode v seti sluzhebnyh funktsiy ------------------------
old2 = u'''    n4.outvar(u"Set_DMA", f26, x=F.COL_OUT, y=30)
    n4.outvar(u"F_Size", f35, x=F.COL_OUT, y=190)'''
new2 = u'''    n4.outvar(u"Set_DMA", f26, x=F.COL_OUT, y=30)
    n4.outvar(u"F_Size", f35, x=F.COL_OUT, y=190)

    # --- Ret_Mode: kakuyu operatsiyu s pamyat yu vypolnit ST-drajveru ---
    f19m = b_and(n4, F.COL_BLK2 + 160, 230, f19,
                 n4.const(u"1", y=244))
    f22m = b_and(n4, F.COL_BLK2 + 160, 270, f22,
                 n4.const(u"2", y=284))
    f26m = b_and(n4, F.COL_BLK2 + 160, 310, f26,
                 n4.const(u"3", y=324))
    f35m = b_and(n4, F.COL_BLK2 + 160, 350, f35,
                 n4.const(u"4", y=364))
    f27m = b_and(n4, F.COL_BLK2 + 160, 390,
                 b_eq(n4, F.COL_BLK2, 390, c_c4, n4.const(u"27", y=404)),
                 n4.const(u"5", y=414))
    rm1 = b_or(n4, F.COL_BLK2 + 320, 250, f19m, f22m)
    rm2 = b_or(n4, F.COL_BLK2 + 320, 330, rm1, f26m)
    rm3 = b_or(n4, F.COL_BLK2 + 320, 370, rm2, f35m)
    rm4 = b_or(n4, F.COL_BLK2 + 480, 390, rm3, f27m)
    n4.outvar(u"Ret_Mode", rm4, x=F.COL_OUT + 300, y=390)

    # --- 32 F_USERNUM: otvet 0 (polzovatel 0) ---
    f32v = b_and(n4, F.COL_BLK2 + 160, 430, f32, n4.const(u"0", y=444))
    f32w = b_b2w(n4, F.COL_BLK2 + 320, 430, f32v)
    n4.outvar(u"Ret_Val", f32w, x=F.COL_OUT + 300, y=430)'''
assert old2 in t, u"ne najden blok sluzhebnyh funktsiy BDOS"
t = t.replace(old2, new2, 1)

# --- 3. rasshirit ST-drajver PRG_CPM_BDOS --------------------------------------
old3 = u'''        ELSIF nFunc = 16 THEN
            File_Open := FALSE;
            nHl := 0;'''
new3 = u'''        ELSIF nFunc = 16 THEN
            File_Open := FALSE;
            nHl := 0;

        ELSIF nFunc = 19 THEN
            (* udalenie fajla: pomеchaem zapis' kataloga kak svobodnuyu (E5h) *)
            IF Dir_Found THEN
                Z80_Mem[nPtr + 32 * Dir_Index] := 16#E5;
                nHl := 0;
            ELSE
                nHl := 255;
            END_IF

        ELSIF nFunc = 22 THEN
            (* sozdanie fajla: nuzhna svobodnaya zapis' kataloga *)
            IF Dir_FreeFound THEN
                FOR i := 0 TO 31 DO
                    Z80_Mem[nPtr + 32 * Dir_Free + i] :=
                        Z80_Mem[nPtr + i];
                END_FOR
                Z80_Mem[nPtr + 32 * Dir_Free] := 0;        (* user 0 *)
                Z80_Mem[nPtr + 32 * Dir_Free + 12] := 0;   (* ekstent 0 *)
                Z80_Mem[nPtr + 32 * Dir_Free + 15] := 0;   (* RC = 0 *)
                FOR i := 16 TO 31 DO
                    Z80_Mem[nPtr + 32 * Dir_Free + i] := 0;
                END_FOR
                Dir_Index := Dir_Free;
                File_Open := TRUE;
                nHl := 0;
            ELSE
                nHl := 255;
            END_IF

        ELSIF nFunc = 26 THEN
            (* ustanovka adresa peredachi *)
            Disk_DMA := nPtr;
            nHl := 0;

        ELSIF nFunc = 27 THEN
            (* karta zanyatyh blokov: vozvrashchaem 0 (vse svobodny) *)
            nHl := 0;

        ELSIF nFunc = 33 THEN
            (* chtenie proizvol noy zapisi: nomer v RC zapisi kataloga *)
            IF Dir_Found THEN
                FOR i := 0 TO 127 DO
                    Z80_Mem[Disk_DMA + i] :=
                        Disk_Mem[16#800 + Disk_Addr * 128 + i];
                END_FOR
                nHl := 0;
            ELSE
                nHl := 255;
            END_IF

        ELSIF nFunc = 34 THEN
            (* zapis' proizvol noy zapisi *)
            IF Dir_Found THEN
                FOR i := 0 TO 127 DO
                    Disk_Mem[16#800 + Disk_Addr * 128 + i] :=
                        Z80_Mem[Disk_DMA + i];
                END_FOR
                nHl := 0;
            ELSE
                nHl := 255;
            END_IF

        ELSIF nFunc = 35 THEN
            (* razmer fajla v zapisyah: berem RC iz zapisi kataloga *)
            IF Dir_Found THEN
                nHl := Z80_Mem[nPtr + 32 * Dir_Index + 16];
            ELSE
                nHl := 0;
            END_IF'''
assert old3 in t, u"ne najden blok funktsiy 15/16 v ST-drajvere"
t = t.replace(old3, new3, 1)

io.open(GEN, "w", encoding="utf-8").write(t)
print(u"PATCH BDOS_FULL OK")
