# -*- coding: utf-8 -*-
u"""patch_io_decoder.py -- dobavlyaet v FB_DecoderZ80 komandy IN i OUT.

  IN  A,(n)  = 16#DB  -- vvod iz porta n v akkumulyator
  OUT (n),A  = 16#D3  -- vyvod akkumulyatora v port n

Novye vyhody:
    Ctl_Is_IN      -- eto komanda vvoda
    Ctl_Is_OUT     -- eto komanda vyvoda
    Ctl_IO_Addr_En -- adres porta beretsya iz operanda (n), a ne iz C
"""

import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GEN = os.path.join(ROOT, "generator", "gen_z80.py")

t = io.open(GEN, "r", encoding="utf-8").read()

# --- 1. novye vyhody -----------------------------------------------------------
old = u'''    p.var_out(u"Ctl_IncDec", u"BOOL", u"TRUE dlya INC/DEC: operand = 1")'''
new = u'''    p.var_out(u"Ctl_IncDec", u"BOOL", u"TRUE dlya INC/DEC: operand = 1")
    p.var_out(u"Ctl_Is_IN", u"BOOL", u"komanda IN A,(n)")
    p.var_out(u"Ctl_Is_OUT", u"BOOL", u"komanda OUT (n),A")'''
assert old in t, u"ne najdeny vyhody dekodera"
t = t.replace(old, new)

# --- 2. raspoznavanie kodov ----------------------------------------------------
old2 = u'''    r_ldnna = eq_const(0x32, F.COL_BLK, y); y += 26'''
new2 = u'''    r_ldnna = eq_const(0x32, F.COL_BLK, y); y += 26
    r_in = eq_const(0xDB, F.COL_BLK, y); y += 26
    r_out = eq_const(0xD3, F.COL_BLK, y); y += 26'''
assert old2 in t, u"ne najden spisok sravnenij dekodera"
t = t.replace(old2, new2)

# --- 3. dobavit v spisok vyhodov ----------------------------------------------
old3 = u'''        (u"Ctl_IncDec", incdec, F.COL_OUT),
    ]'''
new3 = u'''        (u"Ctl_IncDec", incdec, F.COL_OUT),
        (u"Ctl_Is_IN", r_in, F.COL_OUT),
        (u"Ctl_Is_OUT", r_out, F.COL_OUT),
    ]'''
assert old3 in t, u"ne najden spisok vyhodov"
t = t.replace(old3, new3)

# --- 4. Ctl_Imm_Mode dolzhen byt istinnen i dlya IN/OUT (est operand n) --------
old4 = u'''        (u"Ctl_Imm_Mode", b_or(n, F.COL_BLK2 + 320, y + 560,
                               b_or(n, F.COL_BLK2 + 320, y + 520, r_ldn, r_call),
                               n.const(u"0", y=y + 574)), F.COL_OUT),'''
new4 = u'''        (u"Ctl_Imm_Mode", b_or(n, F.COL_BLK2 + 320, y + 560,
                               b_or(n, F.COL_BLK2 + 320, y + 520, r_ldn, r_call),
                               b_or(n, F.COL_BLK2 + 320, y + 600, r_in, r_out)),
         F.COL_OUT),'''
assert old4 in t, u"ne najden Ctl_Imm_Mode"
t = t.replace(old4, new4)

io.open(GEN, "w", encoding="utf-8").write(t)
print(u"PATCH IO_DECODER OK")
