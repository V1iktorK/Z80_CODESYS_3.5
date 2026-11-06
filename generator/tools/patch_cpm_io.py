# -*- coding: utf-8 -*-
u"""PATCH_CPM_IO -- stend CP/M prokruchivaet korotkuyu programmu I/O.

Z A Ch E M. Desyat proverok gruppy IO/HW sravnivayut to, chto dolzhno poyavitsya
POSLE vypolneniya komand IN i OUT: soderzhimoe shin I/O, vyhodnye bufery PLK,
nomer porta. Ranshe stend ostanavlival emulyator i sravnival bufery -- to est
proveryal tol ko vhodnye kanaly, kotorye schityvayutsya kombinationno.

Ch T O  D E L A E M.
 1) V pamyat' po adresu 0 kladem JP 4000h -- eto edinstvennoe mesto, kotoroe
    ne proveryaetsya drugimi testami (oni chitayut 0005h, 0100h i dalee).
 2) Po adresu 4000h -- programma tol ko iz podderzhivaemyh komand:
        LD H,20h ; LD L,00h ; IN A,(nn) ; LD (HL),A ; LD L,kk ; ...
    Ona chitaet vse vhodnye porty i kladet otvety v 2000h..2006h, a potom
    vypolnyaet OUT na porty 01h, 04h i 05h.
 3) Stend posle podgotovki: sBros processora, Emu_Run = TRUE na 200 skanov,
    zat, ostanovka i sravnenie.
 4) Novye vidy proverok (Kind 30..35) chitayut pamyat' 2000h + k.
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


# ---------------------------------------------------------------- 1. stend ----
OLD = (u'    (* shag 0: podgotovka -- nastrojka vhodov PLK i konsoli *)\n'
       u'    IF nStage = 0 THEN\n')
NEW = (u'    (* shag 0: podgotovka -- nastrojka vhodov PLK i konsoli, zagruzka\n'
       u'       korotkoj programmy I/O i eyo progon (sm. kommentarij vyshe) *)\n'
       u'    IF nStage = 0 THEN\n')
rep(OLD, NEW)

OLD = (u'        (* na vremya proverok emulyator ostanovlen, chtoby snimki ne menyalis *)\n'
       u'        GVL_Control.Emu_Run := FALSE;\n'
       u'        nCyc := 0;\n'
       u'        nStage := 1;\n')
NEW = (u'        (*  K O R O T K A Ya  P R O G R A M M A  V V O D A - V Y V O D A.\n'
       u'            Bez neyo proverki portov schityvayut nenuzhnye im polya: oni\n'
       u'            zhdut rezul tat komand IN/OUT, a ne sostoyanie buferov. *)\n'
       u'        Z80_Mem[0] := 16#C3;   (* JP 4000h *)\n'
       u'        Z80_Mem[1] := 16#00;\n'
       u'        Z80_Mem[2] := 16#40;\n'
       u'        Z80_Mem[16#4000] := 16#26;  Z80_Mem[16#4001] := 16#20;  (* LD H,20h *)\n'
       u'        (* chtenie vhodnyh portov: (2Eh kk) IN nnn (77h) *)\n'
       u'        Z80_Mem[16#4002] := 16#2E;  Z80_Mem[16#4003] := 16#00;\n'
       u'        Z80_Mem[16#4004] := 16#DB;  Z80_Mem[16#4005] := 16#02;\n'
       u'        Z80_Mem[16#4006] := 16#77;\n'
       u'        Z80_Mem[16#4007] := 16#2E;  Z80_Mem[16#4008] := 16#01;\n'
       u'        Z80_Mem[16#4009] := 16#DB;  Z80_Mem[16#400A] := 16#03;\n'
       u'        Z80_Mem[16#400B] := 16#77;\n'
       u'        Z80_Mem[16#400C] := 16#2E;  Z80_Mem[16#400D] := 16#02;\n'
       u'        Z80_Mem[16#400E] := 16#DB;  Z80_Mem[16#400F] := 16#06;\n'
       u'        Z80_Mem[16#4010] := 16#77;\n'
       u'        Z80_Mem[16#4011] := 16#2E;  Z80_Mem[16#4012] := 16#03;\n'
       u'        Z80_Mem[16#4013] := 16#DB;  Z80_Mem[16#4014] := 16#07;\n'
       u'        Z80_Mem[16#4015] := 16#77;\n'
       u'        Z80_Mem[16#4016] := 16#2E;  Z80_Mem[16#4017] := 16#04;\n'
       u'        Z80_Mem[16#4018] := 16#DB;  Z80_Mem[16#4019] := 16#10;\n'
       u'        Z80_Mem[16#401A] := 16#77;\n'
       u'        Z80_Mem[16#401B] := 16#2E;  Z80_Mem[16#401C] := 16#05;\n'
       u'        Z80_Mem[16#401D] := 16#DB;  Z80_Mem[16#401E] := 16#21;\n'
       u'        Z80_Mem[16#401F] := 16#77;\n'
       u'        Z80_Mem[16#4020] := 16#2E;  Z80_Mem[16#4021] := 16#06;\n'
       u'        Z80_Mem[16#4022] := 16#DB;  Z80_Mem[16#4023] := 16#00;\n'
       u'        Z80_Mem[16#4024] := 16#77;\n'
       u'        (* vyhodnye porty: LD A,nn ; OUT (n),A *)\n'
       u'        Z80_Mem[16#4025] := 16#3E;  Z80_Mem[16#4026] := 16#3C;\n'
       u'        Z80_Mem[16#4027] := 16#D3;  Z80_Mem[16#4028] := 16#01;\n'
       u'        Z80_Mem[16#4029] := 16#3E;  Z80_Mem[16#402A] := 16#34;\n'
       u'        Z80_Mem[16#402B] := 16#D3;  Z80_Mem[16#402C] := 16#04;\n'
       u'        Z80_Mem[16#402D] := 16#3E;  Z80_Mem[16#402E] := 16#12;\n'
       u'        Z80_Mem[16#402F] := 16#D3;  Z80_Mem[16#4030] := 16#05;\n'
       u'        Z80_Mem[16#4031] := 16#76;   (* HALT *)\n'
       u'\n'
       u'        (* sBros pered zapuskom: PC = 0, registry v nol *)\n'
       u'        GVL_Control.Emu_Reset := TRUE;\n'
       u'        GVL_Control.Emu_Run := FALSE;\n'
       u'        nCyc := 0;\n'
       u'        nStage := 40;\n'
       u'\n'
       u'    (* shag 40: snyat sBros i zapustit programmu *)\n'
       u'    ELSIF nStage = 40 THEN\n'
       u'        GVL_Control.Emu_Reset := FALSE;\n'
       u'        GVL_Control.Emu_Run := TRUE;\n'
       u'        nCyc := 0;\n'
       u'        nStage := 41;\n'
       u'\n'
       u'    (* shag 41: prokrutit programmu (31 komanda po dva skana i zapas) *)\n'
       u'    ELSIF nStage = 41 THEN\n'
       u'        nCyc := nCyc + 1;\n'
       u'        IF nCyc >= 200 THEN\n'
       u'            GVL_Control.Emu_Run := FALSE;\n'
       u'            nCyc := 0;\n'
       u'            nStage := 1;\n'
       u'        END_IF;\n')
rep(OLD, NEW)

# ------------------------------------------------------- 2. novye Kind 30..35 --
OLD = (u'                    22: fbCase.Expected_A := GVL_Tests_CPM.Cpm_Tests[i].Exp_Byte;\n'
       u'                        fbCase.Actual_A := Disk_Mem[2];\n'
       u'                        fbCase.Mask_A := TRUE;\n')
NEW = (u'                    22: fbCase.Expected_A := GVL_Tests_CPM.Cpm_Tests[i].Exp_Byte;\n'
       u'                        fbCase.Actual_A := Disk_Mem[2];\n'
       u'                        fbCase.Mask_A := TRUE;\n'
       u'\n'
       u'                    (*  30..35 -- otvety komand IN, snimaemye programmoj\n'
       u'                        v pamyat po adresu 2000h + (Kind - 30). *)\n'
       u'                    30: fbCase.Expected_A := GVL_Tests_CPM.Cpm_Tests[i].Exp_Byte;\n'
       u'                        fbCase.Actual_A := Z80_Mem[16#2000];\n'
       u'                        fbCase.Mask_A := TRUE;\n'
       u'\n'
       u'                    31: fbCase.Expected_A := GVL_Tests_CPM.Cpm_Tests[i].Exp_Byte;\n'
       u'                        fbCase.Actual_A := Z80_Mem[16#2001];\n'
       u'                        fbCase.Mask_A := TRUE;\n'
       u'\n'
       u'                    32: fbCase.Expected_A := GVL_Tests_CPM.Cpm_Tests[i].Exp_Byte;\n'
       u'                        fbCase.Actual_A := Z80_Mem[16#2002];\n'
       u'                        fbCase.Mask_A := TRUE;\n'
       u'\n'
       u'                    33: fbCase.Expected_A := GVL_Tests_CPM.Cpm_Tests[i].Exp_Byte;\n'
       u'                        fbCase.Actual_A := Z80_Mem[16#2003];\n'
       u'                        fbCase.Mask_A := TRUE;\n'
       u'\n'
       u'                    34: fbCase.Expected_A := GVL_Tests_CPM.Cpm_Tests[i].Exp_Byte;\n'
       u'                        fbCase.Actual_A := Z80_Mem[16#2004];\n'
       u'                        fbCase.Mask_A := TRUE;\n'
       u'\n'
       u'                    35: fbCase.Expected_A := GVL_Tests_CPM.Cpm_Tests[i].Exp_Byte;\n'
       u'                        fbCase.Actual_A := Z80_Mem[16#2005];\n'
       u'                        fbCase.Mask_A := TRUE;\n'
       u'\n'
       u'                    36: fbCase.Expected_A := GVL_Tests_CPM.Cpm_Tests[i].Exp_Byte;\n'
       u'                        fbCase.Actual_A := Z80_Mem[16#2006];\n'
       u'                        fbCase.Mask_A := TRUE;\n')
rep(OLD, NEW)

# --------------------------------------------- 3. perevodim 6 testov na Kind 30+ --
PAIRS = ((3, u"30", u"16#34"),
         (4, u"31", u"16#12"),
         (6, u"34", u"16#FF"),
         (7, u"35", u"16#01"),
         (8, u"32", u"16#78"),
         (9, u"33", u"16#56"))
for idx, kind, exp in PAIRS:
    old_k = (u'    GVL_Tests_CPM.Cpm_Tests[%d].Kind := 1;\n' % idx)
    new_k = (u'    GVL_Tests_CPM.Cpm_Tests[%d].Kind := %s;   (* otvet IN iz pamyati *)\n'
             % (idx, kind))
    rep(old_k, new_k)

io.open(P, u"w", encoding=u"utf-8").write(t)
print(u"patch_cpm_io: %d zamen" % n)
print(u"nonascii: %d" % sum(1 for c in t if ord(c) > 127))
