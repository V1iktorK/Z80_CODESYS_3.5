# -*- coding: utf-8 -*-
u"""patch_add3.py -- dobavlyaet tri nedostayushchie proverki (do 62).

  T24 (nom. 24) -- HALT: PC ne uvelichivaetsya posle ostanovki
  T49 (nom. 49) -- F_ISO2: posle ADD vse shest flagov sovpali s etalonom
  T50 (nom. 50) -- F_ISO3: JP Z pri Z=0 ne izmenil registr flagov
"""

import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GEN = os.path.join(ROOT, "generator", "gen_z80.py")

ADD = u'''    GVL_Tests.Tests[24].Enabled := TRUE;  (* T24 HALT -- ostanov *)
    GVL_Tests.Tests[24].Opcode := 16#76;
    GVL_Tests.Tests[24].Mask_PC := TRUE;
    GVL_Tests.Tests[24].Exp_PC := 16#0001;
    GVL_Tests.Tests[24].Mask_Flag := TRUE;

    GVL_Tests.Tests[49].Enabled := TRUE;  (* F_ISO2: posle ADD vse flagi *)
    GVL_Tests.Tests[49].Opcode := 16#80;
    GVL_Tests.Tests[49].Init_A := 16#25;
    GVL_Tests.Tests[49].Init_B := 16#10;
    GVL_Tests.Tests[49].Mask_A := TRUE;  GVL_Tests.Tests[49].Exp_A := 16#35;
    GVL_Tests.Tests[49].Mask_F := TRUE;  GVL_Tests.Tests[49].Exp_F := 16#00;

    GVL_Tests.Tests[50].Enabled := TRUE;  (* F_ISO3: JP Z pri Z=0 ne tроgaet F *)
    GVL_Tests.Tests[50].Opcode := 16#CA;
    GVL_Tests.Tests[50].Init_F := 16#55;
    GVL_Tests.Tests[50].Mask_F := TRUE;  GVL_Tests.Tests[50].Exp_F := 16#55;

'''

t = io.open(GEN, "r", encoding="utf-8").read()

anchor = u"    (* ---------------- T25..T26: DJNZ -------------------------------------- *)"
assert anchor in t, u"ne najden yakor pered T25"
t = t.replace(anchor, ADD + anchor, 1)

io.open(GEN, "w", encoding="utf-8").write(t)
print(u"PATCH ADD3 OK")
