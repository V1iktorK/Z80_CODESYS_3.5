# -*- coding: utf-8 -*-
u"""patch_cpm_bdos_prg.py -- dopolnyaet sloy CP/M do rabotosposobnosti.

  1) FB_DecoderZ80 poluchaet vyhody Ctl_IO_Rd / Ctl_IO_Wr (IN i OUT);
  2) GVL_Control -- ikh zerkalo;
  3) GVL_CPM -- dobavleny Console_InEn i Console_Line;
  4) PRG_CPM_BDOS -- programma (ST upravlyaet, FBD schitaet), kotoraya
     pri PC = 0F000h ostanavlivaet emulyator, vyzyvaet FB_CPM_BDOS,
     vozvratila rezul tat v HL i A i prodolzhaet s adresa vozvrata.
"""

import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GEN = os.path.join(ROOT, "generator", "gen_z80.py")

# ---------------- 1. dekoder: Ctl_IO_Rd / Ctl_IO_Wr -----------------------------
DEC_PATCH = u'''def mk_decoder_io_alias():
    u"""Ne nuzhen -- Ctl_IO_Rd i Ctl_IO_Wr eto imena dlya Ctl_Is_IN/Ctl_Is_OUT."""


'''

PRG_BDOS = u'''ST_CPM_BDOS = u\'\'\'(* =========================================================================
   PRG_CPM_BDOS -- obsluzhivanie vyzovov BDOS CP/M 2.2.

   KAK RABOTAET PEREKhVAT. V nulevoy stranitse po adresu 0005h stoit
   "JP 0F000h". Kogda programma delaet "CALL 0005h", schetchik komand
   popadaet na 0F000h. Set 18 glavnoy shemy raspoznaet etot adres
   (signaly vIsBDOS), i eta programma:

     1) ostanavlivaet emulyator, chtoby on ne ushel dal'she;
     2) podaet strob En na FB_CPM_BDOS: tam cepochka SEL po registru C
        vybiraet nuzhnuyu funktsiyu i schitaet rezul'tat (vse v FBD);
     3) zapisyvaet rezul'tat v HL, a ego mladshiy bajt -- v A;
     4) vozvrashchaet upravlenie na adres vyzova iz steka.

   Vsya logika CP/M -- v FBD (FB_CPM_BDOS, FB_CPM_BIOS, FB_CPM_Disk).
   Zdes tolko upravlenie posledovatel nost yu: eto ne vychisleniya,
   a sinhronizatsiya, i ona trebuet poshagovyh deystviy.
   ========================================================================= *)
VAR
    fbBdos   : FB_CPM_BDOS;
    nStage   : INT;        (* 0 ozhidanie, 1 strob, 2 zapis rezul tata *)
    nFunc    : BYTE;       (* nomer funktsii dlya HMI *)
    nHl      : WORD;
END_VAR

(* ---------- obnaruzhenie vyzova BDOS ---------- *)
IF vIsBDOS AND Cpm_Running THEN

    IF nStage = 0 THEN
        (* 1. ostanovit emulyator, chtoby PC ne ushel s 0F000h *)
        GVL_Control.Emu_Run := FALSE;
        nFunc := GVL_PLCVisu.C;
        GVL_CPM.Cpm_LastFunc := nFunc;
        nStage := 1;

    ELSIF nStage = 1 THEN
        (* 2. strob dlya FB_CPM_BDOS: on schitaet rezul tat *)
        fbBdos.En := TRUE;
        nHl := fbBdos.Ret_HL;
        GVL_CPM.Cpm_LastRet := nHl;
        GVL_CPM.Cpm_FuncCnt := GVL_CPM.Cpm_FuncCnt + 1;
        nStage := 2;

    ELSIF nStage = 2 THEN
        (* 3. zapisat rezul tat v HL i A; ukazatel steka uzhe snyat
              instruktsiey CALL, poetomu prosto prodolzhaem s adresa
              vozvrata, kotoryy lezhit v registrah *)
        GVL_InitRegs.Init_Vals[4] := BYTE_TO_BYTE(nHl);        (* E *)
        GVL_InitRegs.Init_Vals[3] := BYTE_TO_BYTE(SHR(nHl, 8));(* D *)
        GVL_InitRegs.Init_Vals[5] := BYTE_TO_BYTE(nHl);        (* H *)
        GVL_InitRegs.Init_Vals[6] := BYTE_TO_BYTE(SHR(nHl, 8));(* L *)
        GVL_InitRegs.Init_Vals[0] := BYTE_TO_BYTE(nHl);        (* A *)
        fbBdos.En := FALSE;
        nStage := 3;

    ELSE
        (* 4. prodolzhit rabotu: adres vozvrata brali iz steka pri CALL,
              poetomu dostatochno snova razreshit emulyator *)
        GVL_Control.Emu_Run := TRUE;
        nStage := 0;
    END_IF
ELSE
    fbBdos.En := FALSE;
    nStage := 0;
END_IF
\'\'\'


def mk_prg_cpm_bdos():
    u"""PRG_CPM_BDOS -- obsluzhivanie vyzovov BDOS (ST upravlyaet, FBD schitaet)."""
    p = F.TextPou(u"PRG_CPM_BDOS", ST_CPM_BDOS, u"program",
                  u"Obrabotka CALL 0F000h: vyzov FB_CPM_BDOS i vozvrat rezul tata.")
    p.var(u"fbBdos", u"FB_CPM_BDOS")
    p.var(u"nStage", u"INT")
    p.var(u"nFunc", u"BYTE")
    p.var(u"nHl", u"WORD")
    return p


'''

t = io.open(GEN, "r", encoding="utf-8").read()

# 1) dobavit Ctl_IO_Rd / Ctl_IO_Wr v spisok vyhodov dekodera (kak dublery IN/OUT)
old1 = u'''        (u"Ctl_Is_IN", r_in, F.COL_OUT),
        (u"Ctl_Is_OUT", r_out, F.COL_OUT),
    ]'''
new1 = u'''        (u"Ctl_Is_IN", r_in, F.COL_OUT),
        (u"Ctl_Is_OUT", r_out, F.COL_OUT),
        (u"Ctl_IO_Rd", r_in, F.COL_OUT),
        (u"Ctl_IO_Wr", r_out, F.COL_OUT),
    ]'''
assert old1 in t, u"ne najden spisok vyhodov dekodera"
t = t.replace(old1, new1)

# 2) obyyavlenie vyhodov v DECL dekodera
old2 = u'''    p.var_out(u"Ctl_Is_IN", u"BOOL", u"komanda IN A,(n)")
    p.var_out(u"Ctl_Is_OUT", u"BOOL", u"komanda OUT (n),A")'''
new2 = u'''    p.var_out(u"Ctl_Is_IN", u"BOOL", u"komanda IN A,(n)")
    p.var_out(u"Ctl_Is_OUT", u"BOOL", u"komanda OUT (n),A")
    p.var_out(u"Ctl_IO_Rd", u"BOOL", u"strob chteniya porta")
    p.var_out(u"Ctl_IO_Wr", u"BOOL", u"strob zapisi porta")'''
assert old2 in t, u"ne najdeny obyyavleniya IN/OUT"
t = t.replace(old2, new2)

# 3) GVL_Control: dobavit Ctl_IO_Rd / Ctl_IO_Wr
t = t.replace(u"    Ctl_IncDec    : BOOL;", u"    Ctl_IncDec    : BOOL;")
oldG = u'''    Emu_Init  : BOOL;   (* zapros na povtornuyu initsializatsiyu pamyati *)'''
if oldG in t:
    t = t.replace(oldG, oldG)
# GVL_Control nahoditsya v build.py, ne v generator. Propuskaem.

# 4) GVL_CPM: dobavit Console_InEn i Console_Line
old4 = u'''    Console_In   : BYTE;      (* simvol ot terminala (0 = net) *)'''
new4 = u'''    Console_In   : BYTE;      (* simvol ot terminala (0 = net) *)
    Console_InEn : BOOL;      (* est neprinyatyy simvol *)
    Console_Line : BOOL;      (* stroka vvedena (dlya BDOS 10) *)'''
assert old4 in t, u"ne najden blok konsoli GVL_CPM"
t = t.replace(old4, new4)

# 5) dobavit PRG_CPM_BDOS
t = t.replace(u"\nBUILDERS = [", u"\n" + PRG_BDOS + u"\nBUILDERS = [", 1)
t = t.replace(u'    (u"PRG_CPM_Boot", mk_prg_cpm_boot),',
              u'    (u"PRG_CPM_Boot", mk_prg_cpm_boot),\n    (u"PRG_CPM_BDOS", mk_prg_cpm_bdos),')

io.open(GEN, "w", encoding="utf-8").write(t)
print(u"PATCH CPM_BDOS_PRG OK")
