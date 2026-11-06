# -*- coding: utf-8 -*-
u"""PATCH_TESTS62 -- dovodim chislo proverok processora do 62 (bylo 40).

Z A Ch E M. Plany (docs/01, docs/02) i priyomochnyy progon (run_simulation.py)
zadayut 62 proverki processora, a v tablitse bylo 40. Chisla dolzhny sovpadat,
inache progon ne mozhet zavershit sya uspeshno v prinzipe.

Ch T O  D O B A V L Ya E M. Dvadtsat' dve proverki na to, chto uzhe est v
tablitse, no bylo pokryto odnoj-dvumya strolami:
    LD r,r'  -- shest par (tol ko odna storona registra),
    LD r,n   -- pyat' priemnikov,
    ADD/SUB  -- esli istochnik H ili L,
    INC/DEC  -- ne tol ko akkumulyator,
    CP A     -- sravnenie samogo sebya,
    ADD A,(HL) -- operand iz pamyati (port kosvennoj adresacii).

Ozhidaemye znacheniya zdes postavleny nulevymi zaglushkami: ih pereschitaet
nezavisimaya model Z80 (generator/tools/regen_tests.py), kotoraya idet sleduyushchey.
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


# (nomer, kod, Init_A, Init_B, Init_F, Init_HL, kommentarij)
CASES = [
    (41, 0x41, 0x00, 0x00, 0xFF, 0x0000, u"LD B,C -- B := C"),
    (42, 0x4F, 0x3A, 0x00, 0xFF, 0x0000, u"LD C,A -- C := A"),
    (43, 0x50, 0x00, 0x77, 0xFF, 0x0000, u"LD D,B -- D := B"),
    (44, 0x67, 0x5C, 0x00, 0xFF, 0x0000, u"LD H,A -- H := A"),
    (45, 0x6F, 0x6B, 0x00, 0xFF, 0x0000, u"LD L,A -- L := A"),
    (46, 0x7F, 0x19, 0x00, 0xFF, 0x0000, u"LD A,A -- A := A"),
    (47, 0x0E, 0x00, 0x00, 0xFF, 0x0000, u"LD C,n -- C := Mem[1]"),
    (48, 0x16, 0x00, 0x00, 0xFF, 0x0000, u"LD D,n -- D := Mem[1]"),
    (49, 0x1E, 0x00, 0x00, 0xFF, 0x0000, u"LD E,n -- E := Mem[1]"),
    (50, 0x26, 0x00, 0x00, 0xFF, 0x1234, u"LD H,n -- H := Mem[1]"),
    (51, 0x2E, 0x00, 0x00, 0xFF, 0x1234, u"LD L,n -- L := Mem[1]"),
    (52, 0x84, 0x0F, 0x00, 0x00, 0x5500, u"ADD A,H -- A := A + H"),
    (53, 0x85, 0x0F, 0x00, 0x00, 0x0055, u"ADD A,L -- A := A + L"),
    (54, 0x94, 0x0F, 0x00, 0x00, 0x0500, u"SUB H -- A := A - H"),
    (55, 0x95, 0x0F, 0x00, 0x00, 0x0005, u"SUB L -- A := A - L"),
    (56, 0x04, 0x00, 0x0F, 0x01, 0x0000, u"INC B -- B := B + 1, C sohranen"),
    (57, 0x0D, 0x00, 0x00, 0x01, 0x0000, u"DEC C -- C := C - 1"),
    (58, 0x24, 0x00, 0x00, 0x00, 0x7F00, u"INC H -- H := H + 1"),
    (59, 0x2D, 0x00, 0x00, 0x00, 0x0001, u"DEC L -- L := L - 1"),
    (60, 0xBF, 0x40, 0x00, 0x00, 0x0000, u"CP A -- sravnenie samogo sebya"),
    (61, 0x86, 0x01, 0x00, 0x00, 0x2000, u"ADD A,(HL) -- A := A + Mem[HL]"),
    (62, 0x96, 0x55, 0x00, 0x00, 0x2000, u"SUB (HL) -- A := A - Mem[HL]"),
]

BLOCK = u""
for idx, op, ia, ib, iff, ihl, cmt in CASES:
    BLOCK += (u"    GVL_Tests.Cpu_Tests[%d].Enabled := TRUE;   (* T%02d %s *)\n"
              % (idx, idx, cmt))
    BLOCK += u"    GVL_Tests.Cpu_Tests[%d].Opcode := 16#%02X;\n" % (idx, op)
    if ia:
        BLOCK += u"    GVL_Tests.Cpu_Tests[%d].Init_A := 16#%02X;\n" % (idx, ia)
    if ib:
        BLOCK += u"    GVL_Tests.Cpu_Tests[%d].Init_B := 16#%02X;\n" % (idx, ib)
    if iff:
        BLOCK += u"    GVL_Tests.Cpu_Tests[%d].Init_F := 16#%02X;\n" % (idx, iff)
    if ihl:
        BLOCK += u"    GVL_Tests.Cpu_Tests[%d].Init_HL := 16#%04X;\n" % (idx, ihl)
    BLOCK += (u"    GVL_Tests.Cpu_Tests[%d].Mask_A := TRUE;  "
              u"GVL_Tests.Cpu_Tests[%d].Exp_A := 16#00;\n" % (idx, idx))
    BLOCK += (u"    GVL_Tests.Cpu_Tests[%d].Mask_F := TRUE;  "
              u"GVL_Tests.Cpu_Tests[%d].Exp_F := 16#00;\n" % (idx, idx))
    BLOCK += u"\n"

rep(u"    (* ---------------- T47..T50: izolyatsiya flagov (F_ISO) --------------- *)",
    u"    (* ---------------- T41..T62: rasshirenie pokrytiya -------------------- *)\n"
    + BLOCK
    + u"    (* ---------------- T47..T50: izolyatsiya flagov (F_ISO) --------------- *)")

# cikly po 40 -> po 62
rep(u"""    FOR i := 1 TO 40 DO
        GVL_Tests.Cpu_Tests[i].Id := i;""",
    u"""    FOR i := 1 TO 62 DO
        GVL_Tests.Cpu_Tests[i].Id := i;""")
rep(u"""    FOR i := 1 TO 40 DO
        IF GVL_Tests.Cpu_Tests[i].Enabled THEN""",
    u"""    FOR i := 1 TO 62 DO
        IF GVL_Tests.Cpu_Tests[i].Enabled THEN""")
rep(u"""        FOR i := 1 TO 40 DO
            IF GVL_Tests.Cpu_Test_Executed[i] THEN""",
    u"""        FOR i := 1 TO 62 DO
            IF GVL_Tests.Cpu_Test_Executed[i] THEN""")

io.open(P, u"w", encoding=u"utf-8").write(t)
print(u"patch_tests62: %d zamen" % n)
print(u"nonascii: %d" % sum(1 for c in t if ord(c) > 127))
