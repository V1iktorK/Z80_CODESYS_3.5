# -*- coding: utf-8 -*-
u"""patch_bdos_prg2.py -- perepisyvaet PRG_CPM_BDOS s uchetom novogo pravila.

PRAVILO: v FBD nelzya indeksirovat massiv. Poetomu ST-drajver delaet vse
operatsii s pamyat yu i katalogom, a FB_CPM_BDOS -- tolko dispatch po
skalyaram.

Drajver vypolnyaet:
  1) zamechaet PC = 0F000h (signaly vIsBDOS iz glavnoy shemy);
  2) ostanavlivaet emulyator;
  3) vyzyvaet FB_CPM_BDOS so strobom En -- tot vybiraet funktsiyu po C;
  4) vypolnyaet operatsii s pamyat yu: vyvod stroki do $ (funktsiya 9),
     chtenie/zapis zapisi diska, poisk v kataloge;
  5) zapisyvaet rezul tat v HL i A, prodolzhaet rabotu.
"""

import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GEN = os.path.join(ROOT, "generator", "gen_z80.py")

ST = u'''(* =========================================================================
   PRG_CPM_BDOS -- drajver BDOS: sinhronizatsiya i rabota s pamyat yu.

   PEREKhVAT. V nulevoy stranitse po adresu 0005h stoit "JP 0F000h".
   Kogda programma delaet CALL 0005h, schetchik komand popadaet na 0F000h.
   Set 18 glavnoy shemy raspoznaet etot adres (vIsBDOS), i drajver:

     1) ostanavlivaet emulyator, chtoby PC ne ushel dal'she;
     2) vyzyvaet FB_CPM_BDOS -- tam cepochka SEL po registru C vybiraet
        nuzhnuyu funktsiyu i schitaet rezul tat (vse v FBD);
     3) vypolnyaet operatsii s PAMYaT'Yu: v FBD nelzya indeksirovat massiv,
        poetomu vyvod stroki do $, poisk v kataloge i obmen zapisyami
        diska sdelany zdes -- eto razreshennaya zadaniem tochka ST
        dlya raboty s massivami;
     4) zapisyvaet rezul tat v HL i A i prodolzhaet rabotu.

   Vsya VYChISLITEL'NAYa logika CP/M (tablitsa funktsiy, konsol, kody oshibok)
   -- v FBD (FB_CPM_BDOS, FB_CPM_BIOS, FB_CPM_Disk). Zdes -- sinhronizatsiya
   i obrashcheniya k pamyati.
   ========================================================================= *)
VAR
    fbBdos   : FB_CPM_BDOS;
    nStage   : INT;
    nFunc    : BYTE;
    nHl      : WORD;
    nPtr     : WORD;
    nCh      : BYTE;
    i        : INT;
END_VAR

IF vIsBDOS AND Cpm_Running THEN

    IF nStage = 0 THEN
        (* 1. ostanovit emulyator i zapomnit nomer funktsii *)
        GVL_Control.Emu_Run := FALSE;
        nFunc := GVL_PLCVisu.C;
        GVL_CPM.Cpm_LastFunc := nFunc;
        nPtr := GVL_PLCVisu.D;      (* adres iz DE -- mladshij bajt *)
        nHl := 0;
        nStage := 1;

    ELSIF nStage = 1 THEN
        (* 2. strob dlya FB_CPM_BDOS: dispatch po C v FBD *)
        fbBdos.En := TRUE;
        nHl := fbBdos.Ret_HL;
        nStage := 2;

    ELSIF nStage = 2 THEN
        (* 3. operatsii s pamyat yu -- po funktsii BDOS *)
        fbBdos.En := FALSE;

        IF nFunc = 9 THEN
            (* vyvod stroki do simvola $ *)
            i := 0;
            nCh := Z80_Mem[nPtr];
            WHILE (nCh <> 16#24) AND (i < 255) DO
                GVL_CPM.Console_Out := nCh;
                GVL_CPM.Console_OutEn := TRUE;
                GVL_CPM.Out_Count := GVL_CPM.Out_Count + 1;
                i := i + 1;
                nPtr := nPtr + 1;
                nCh := Z80_Mem[nPtr];
            END_WHILE

        ELSIF nFunc = 10 THEN
            (* vvod stroki: berem iz bufera konsoli *)
            Z80_Mem[nPtr] := GVL_CPM.In_Cnt;

        ELSIF nFunc = 13 THEN
            (* sbros diska: nichego ne delaem, no otvechaem uspehom *)
            Disk_LastErr := 0;

        ELSIF nFunc = 14 THEN
            (* vybor diska: podderzhivaem tolko A: *)
            IF GVL_PLCVisu.E = 0 THEN
                nHl := 0;
            ELSE
                nHl := 1;
            END_IF

        ELSIF nFunc = 15 THEN
            (* otkryt fajl: iskat imya v kataloge po adresu iz DE.
               Imya nachinaetsya so smeshcheniya +1 (pervyy bajt -- user). *)
            Dir_Found := FALSE;
            Dir_FreeFound := FALSE;
            FOR i := 0 TO 63 DO
                IF Z80_Mem[nPtr + 32 * i] <> 16#E5 THEN
                    IF (Z80_Mem[nPtr + 32 * i + 1] = Z80_Mem[nPtr + 1]) AND
                       (Z80_Mem[nPtr + 32 * i + 9] = Z80_Mem[nPtr + 9]) THEN
                        Dir_Found := TRUE;
                        Dir_Index := i;
                    END_IF
                ELSE
                    IF NOT Dir_FreeFound THEN
                        Dir_FreeFound := TRUE;
                        Dir_Free := i;
                    END_IF
                END_IF
            END_FOR
            IF Dir_Found THEN
                nHl := 0;
                File_Open := TRUE;
            ELSE
                nHl := 255;
            END_IF

        ELSIF nFunc = 16 THEN
            File_Open := FALSE;
            nHl := 0;

        ELSIF nFunc = 20 THEN
            (* chtenie zapisi: perenosim iz RAM-diska v TPA *)
            IF File_Open THEN
                FOR i := 0 TO 127 DO
                    Z80_Mem[Disk_DMA + i] :=
                        Disk_Mem[16#800 + Disk_Addr * 128 + i];
                END_FOR
                Disk_Addr := Disk_Addr + 1;
                nHl := 0;
            ELSE
                nHl := 255;
            END_IF

        ELSIF nFunc = 21 THEN
            (* zapis zapisi: perenosim iz TPA v RAM-disk *)
            IF File_Open THEN
                FOR i := 0 TO 127 DO
                    Disk_Mem[16#800 + Disk_Addr * 128 + i] :=
                        Z80_Mem[Disk_DMA + i];
                END_FOR
                Disk_Addr := Disk_Addr + 1;
                nHl := 0;
            ELSE
                nHl := 255;
            END_IF

        ELSE
            nHl := 0;
        END_IF

        GVL_CPM.Cpm_LastRet := nHl;
        GVL_CPM.Cpm_FuncCnt := GVL_CPM.Cpm_FuncCnt + 1;
        nStage := 3;

    ELSE
        (* 4. zapisat rezul tat i prodolzhit rabotu *)
        GVL_InitRegs.Init_Vals[5] := BYTE_TO_BYTE(nHl);          (* H *)
        GVL_InitRegs.Init_Vals[6] := BYTE_TO_BYTE(SHR(nHl, 8));  (* L *)
        GVL_InitRegs.Init_Vals[0] := BYTE_TO_BYTE(nHl);          (* A *)
        GVL_Control.Emu_Run := TRUE;
        nStage := 0;
    END_IF
ELSE
    fbBdos.En := FALSE;
    nStage := 0;
END_IF
'''

NEW_FN = u'''def mk_prg_cpm_bdos():
    u"""PRG_CPM_BDOS -- drajver BDOS (ST upravlyaet, FBD schitaet)."""
    p = F.TextPou(u"PRG_CPM_BDOS", ST_CPM_BDOS, u"program",
                  u"Perekhvat CALL 0F000h, dispatch v FBD, rabota s pamyat yu.")
    p.var(u"fbBdos", u"FB_CPM_BDOS")
    p.var(u"nStage", u"INT")
    p.var(u"nFunc", u"BYTE")
    p.var(u"nHl", u"WORD")
    p.var(u"nPtr", u"WORD")
    p.var(u"nCh", u"BYTE")
    p.var(u"i", u"INT")
    return p


'''

t = io.open(GEN, "r", encoding="utf-8").read()

i0 = t.index(u"ST_CPM_BDOS = u'''")
i1 = t.index(u"'''", i0 + 20) + 3
t = t[:i0] + u"ST_CPM_BDOS = u'''" + ST + u"'''" + t[i1:]

i2 = t.index(u"def mk_prg_cpm_bdos():")
i3 = t.index(u"\n\n", t.index(u"return p", i2))
t = t[:i2] + NEW_FN + t[i3 + 2:]

io.open(GEN, "w", encoding="utf-8").write(t)
print(u"PATCH BDOS_PRG2 OK")
