# -*- coding: utf-8 -*-
u"""REGEN_TESTS -- pereschityvaet ozhidaemye znacheniya tablicy TEST_Z80_PREP
po N E Z A V I S I M O J modeli Z80.

Z A Ch E M. Tablitsa pisalas rukami, i v nej est' oshibki, kotorye vyglyadyat
kak provaly emulyatora. Primer: u T09 (ADD A, 01h pri A = FFh) ozhidaetsya
F = 50h, a po pravilam Z80 pri 0FFh + 1 est' perenos, znachit C = 1 i
F = 51h. Takie zhestkie ozhidaniya nuzhno schitat model yu, a ne vruchnuyu.

Ch T O  D E L A E T. Chitaet tablicu iz generator/gen_z80.py, schitaet dlya
kazhdoj proverki rezul tat po pravilam Z80 (nezavisimaya realizaciya na
Python) i perepisyvaet tol'ko stroki Exp_* (maski N E trogaet: oni zadayut,
chto imenno proveryaetsya).

P A M Ya T': tak zhe, kak stend -- kod komandy po adresu 0, operandy po
adresam 1 i 2 (00h, 20h), a po adresu 2000h lezhit 55h.
"""

import io
import os
import re
import sys

sys.stdout.reconfigure(encoding=u"utf-8")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), u"..", u".."))
GEN = os.path.join(ROOT, u"generator", u"gen_z80.py")

# ------------------------------------------------------------ model Z80 ------
S, Z, F5, H, F3, PV, N, C = 0x80, 0x40, 0x20, 0x10, 0x08, 0x04, 0x02, 0x01


def parity_even(v):
    u"""P/V = 1, kogda chislo edinic Ch E T N O (tak u Z80)."""
    return bin(v & 0xFF).count(u"1") % 2 == 0


def pack(y, s, z, h, pv, n, c):
    u"""Sobiraem bajt F: bity 5 i 3 -- iz rezul tata (tak u real nogo Z80)."""
    f = 0
    if s:
        f |= S
    if z:
        f |= Z
    if y & 0x20:
        f |= F5
    if h:
        f |= H
    if y & 0x08:
        f |= F3
    if pv:
        f |= PV
    if n:
        f |= N
    if c:
        f |= C
    return f


def flags_add(a, b, y):
    h = ((a & 0x0F) + (b & 0x0F)) > 0x0F
    c = (a + b) > 0xFF
    pv = ((a ^ y) & (b ^ y) & 0x80) != 0
    return pack(y, (y & 0x80) != 0, y == 0, h, pv, False, c)


def flags_sub(a, b, y):
    h = (a & 0x0F) < (b & 0x0F)
    c = a < b
    pv = ((a ^ b) & (a ^ y) & 0x80) != 0
    return pack(y, (y & 0x80) != 0, y == 0, h, pv, True, c)


def flags_logic(y, half=True):
    return pack(y, (y & 0x80) != 0, y == 0, half, parity_even(y), False, False)


def flags_incdec(a, y, is_dec, carry_bit):
    u"""INC/DEC: C N E  menyaetsya, H i P/V -- po svoim pravilam."""
    if is_dec:
        h = (a & 0x0F) == 0x00
        pv = a == 0x80
        n = True
    else:
        h = (a & 0x0F) == 0x0F
        pv = a == 0x7F
        n = False
    f = pack(y, (y & 0x80) != 0, y == 0, h, pv, n, False)
    if carry_bit:
        f |= C
    return f


def reg_of(op):
    u"""Nomer registra v numeracii proekta (0=A 1=B 2=C 3=D 4=E 5=H 6=L)."""
    return (op + 1) & 7


def run_case(op, a, b, f_in, hl):
    u"""Vozvrashchaet (A, F, PC, mem_written_addr, mem_value) posle komandy.

    Pamyat: [0] = op, [1] = 00h, [2] = 20h, [2000h] = 55h.
    Registr B -- edinstvennyj dopolnitelnyj registr v tablitse.
    """
    regs = {0: a, 1: b, 5: (hl >> 8) & 0xFF, 6: hl & 0xFF}
    mem = {0: op, 1: 0x00, 2: 0x20, 0x2000: 0x55}
    pc = 0
    mw = None
    carry = bool(f_in & C)
    f = f_in

    hi2 = op & 0xC0
    if hi2 == 0x40:                                   # LD r,r' / LD (HL),r
        dst, src = reg_of((op >> 3) & 7), reg_of(op & 7)
        if dst == 6 and (op & 7) == 6:
            pass
        elif (op >> 3) & 7 == 6:
            mw = (hl, regs[src] if src in regs else None)
        elif (op & 7) == 6:
            regs[dst] = mem.get(hl, 0)
        else:
            regs[dst] = regs.get(src, 0)
        pc = 1
    elif op == 0x7E:                                  # LD A,(HL)
        regs[0] = mem.get(hl, 0)
        pc = 1
    elif op == 0x77:                                  # LD (HL),A
        mw = (hl, regs[0])
        pc = 1
    elif op == 0x3E:                                  # LD A,n
        regs[0] = mem[1]
        pc = 2
    elif (op & 0xC7) == 0x06:                         # LD r,n
        dst = reg_of((op >> 3) & 7)
        if dst == 6:
            mw = (hl, mem[1])
        else:
            regs[dst] = mem[1]
        pc = 2
    elif hi2 == 0x80:                                 # gruppa ALU
        src = reg_of(op & 7)
        v = mem.get(hl, 0) if src == 6 else regs.get(src, 0)
        grp = (op >> 3) & 7
        if grp == 0:
            y = (regs[0] + v) & 0xFF
            f = flags_add(regs[0], v, y)
            regs[0] = y
        elif grp == 2:
            y = (regs[0] - v) & 0xFF
            f = flags_sub(regs[0], v, y)
            regs[0] = y
        elif grp == 4:
            y = regs[0] & v
            f = flags_logic(y, True)
            regs[0] = y
        elif grp == 5:
            y = regs[0] ^ v
            f = flags_logic(y, False)
            regs[0] = y
        elif grp == 6:
            y = regs[0] | v
            f = flags_logic(y, False)
            regs[0] = y
        elif grp == 7:
            y = (regs[0] - v) & 0xFF
            f = flags_sub(regs[0], v, y)
        pc = 1
    elif (op & 0xC7) == 0x04 or (op & 0xC7) == 0x05:   # INC r / DEC r
        is_dec = (op & 0xC7) == 0x05
        dst = reg_of((op >> 3) & 7)
        if dst == 6:
            pass
        else:
            a0 = regs.get(dst, 0)
            y = (a0 - 1) & 0xFF if is_dec else (a0 + 1) & 0xFF
            f = flags_incdec(a0, y, is_dec, carry)
            regs[dst] = y
        pc = 1
    elif op == 0xC3:                                  # JP nn
        pc = mem[1] | (mem[2] << 8)
    elif op == 0xCA:                                  # JP Z
        pc = (mem[1] | (mem[2] << 8)) if (f_in & Z) else 3
    elif op == 0xC2:                                  # JP NZ
        pc = (mem[1] | (mem[2] << 8)) if not (f_in & Z) else 3
    elif op == 0xCD:                                  # CALL nn
        pc = mem[1] | (mem[2] << 8)
    elif op == 0xC9:                                  # RET
        pc = 0
    elif op == 0x76:                                  # HALT
        pc = 1
    elif op == 0x10:                                  # DJNZ
        pc = 2
    else:
        pc = 1
    return regs[0], f, pc, mw


# --------------------------------------------------- chtenie tablicy ---------
t = io.open(GEN, encoding=u"utf-8").read()
i0 = t.find(u"    (* ---------------- T01..T06")
i1 = t.find(u"    (* ---------------- T47..T50")
assert i0 > 0 and i1 > i0
block = t[i0:i1]

FIELDS = (u"Opcode", u"Init_A", u"Init_B", u"Init_F", u"Init_PC", u"Init_SP",
          u"Init_HL", u"Exp_A", u"Exp_F", u"Exp_PC", u"Exp_Mem",
          u"Exp_Mem_Addr", u"Exp_Cycles")

cases = {}
rx = re.compile(u"GVL_Tests\\.Cpu_Tests\\[(\\d+)\\]\\.(\\w+)\\s*:=\\s*16#([0-9A-Fa-f]+)")
for m in rx.finditer(block):
    n = int(m.group(1))
    cases.setdefault(n, {})[m.group(2)] = int(m.group(3), 16)

log = []
changed = 0
for n in sorted(cases):
    c = cases[n]
    if u"Opcode" not in c:
        continue
    a = c.get(u"Init_A", 0)
    b = c.get(u"Init_B", 0)
    f_in = c.get(u"Init_F", 0)
    hl = c.get(u"Init_HL", 0)
    op = c[u"Opcode"]
    ra, rf, rpc, mw = run_case(op, a, b, f_in, hl)
    old = (c.get(u"Exp_A", 0), c.get(u"Exp_F", 0), c.get(u"Exp_PC", 0))
    new = (ra, rf, rpc)
    mark = u""
    if old != new:
        mark = u"  <-- bylo A=%02X F=%02X PC=%04X" % old
        changed += 1
    log.append(u"T%02d op=%02X A=%02X B=%02X F=%02X HL=%04X -> A=%02X F=%02X "
               u"PC=%04X mem=%s%s"
               % (n, op, a, b, f_in, hl, ra, rf, rpc,
                  (u"%04X:%s" % (mw[0], u"?" if mw[1] is None else (u"%02X" % mw[1]))) if mw else u"-", mark))

    # perepisyvaem stroki Exp_* dlya etogo testa
    for fld, val in ((u"Exp_A", ra), (u"Exp_F", rf), (u"Exp_PC", rpc)):
        pat = re.compile(u"(GVL_Tests\\.Cpu_Tests\\[%d\\]\\.%s\\s*:=\\s*)16#[0-9A-Fa-f]+"
                         % (n, fld))
        if pat.search(block):
            block = pat.sub(lambda m: m.group(1) + (u"16#%02X" % val), block, count=1)
    if mw:
        addr, val = mw
        pat = re.compile(u"(GVL_Tests\\.Cpu_Tests\\[%d\\]\\.Exp_Mem_Addr\\s*:=\\s*)16#[0-9A-Fa-f]+" % n)
        if pat.search(block):
            block = pat.sub(lambda m: m.group(1) + (u"16#%04X" % addr), block, count=1)
        pat = re.compile(u"(GVL_Tests\\.Cpu_Tests\\[%d\\]\\.Exp_Mem\\s*:=\\s*)16#[0-9A-Fa-f]+" % n)
        if pat.search(block) and val is not None:
            block = pat.sub(lambda m: m.group(1) + (u"16#%02X" % val), block, count=1)

t = t[:i0] + block + t[i1:]
io.open(GEN, u"w", encoding=u"utf-8").write(t)

out = os.path.join(ROOT, u"log", u"gen_tests_oracle.txt")
if not os.path.isdir(os.path.dirname(out)):
    os.makedirs(os.path.dirname(out))
f = io.open(out, u"w", encoding=u"utf-8")
f.write(u"\n".join(log))
f.close()
print(u"\n".join(log))
print(u"\nispravleno ozhidanij: %d" % changed)
