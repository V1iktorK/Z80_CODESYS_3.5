# -*- coding: utf-8 -*-
u"""patch_alu.py -- dobavlyaet v FB_ALU_Z80 vhod B_Forced i pereklyuchatel' B.

Zachem: operatsii INC/DEC v Z80 rabotayut s EDINITSEJ, a ne s registrom.
Chtoby ne gorodit otdelnye bloki, dobavlyaem v ALU vhod B_Forced, kotoryj
podayot gotovyj operand, i vnutrennij pereklyuchatel' (SEL): dlya INC/DEC
beretsya B_Forced, dlya vseh ostal'nyh -- obych nyj B.
"""

import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GEN = os.path.join(ROOT, "generator", "gen_z80.py")

t = io.open(GEN, "r", encoding="utf-8").read()

# --- 1. novyj vhod B_Forced i priznak INC/DEC ---------------------------------
old = u'''    op = p.var_in(u"Op", u"BYTE", u"kod operacii 0..7")
    cin = p.var_in(u"Carry_In", u"BOOL", u"vhod perenosa dlya ADC/SBC")'''
new = u'''    op = p.var_in(u"Op", u"BYTE", u"kod operacii 0..7")
    cin = p.var_in(u"Carry_In", u"BOOL", u"vhod perenosa dlya ADC/SBC")
    bfor = p.var_in(u"B_Forced", u"BYTE",
                    u"gotovyj operand dlya INC/DEC (edinit sa)")
    incdec = p.var_in(u"IncDec", u"BOOL",
                      u"TRUE dlya INC/DEC: operand beretsya iz B_Forced")'''
assert old in t, u"ne najden blok vhodov ALU"
t = t.replace(old, new)

# --- 2. v seti 1 podmenyaem B na vybrannyj operand ----------------------------
old2 = u'''    n1 = p.network(u"ARIFMETIKA: 16-bitnaya summa i raznost'")
    c_a = n1.invar(a, y=40)
    c_b = n1.invar(b, y=80)
    c_cin = n1.invar(cin, y=120)'''
new2 = u'''    n1 = p.network(u"ARIFMETIKA: 16-bitnaya summa i raznost'")
    c_a = n1.invar(a, y=40)
    c_b = n1.invar(b, y=80)
    c_bfor = n1.invar(bfor, y=400)
    c_incdec = n1.invar(incdec, y=440)
    # dlya INC/DEC operand -- edinitsa (B_Forced), inache -- registr B
    b_eff = b_sel(n1, F.COL_BLK, 400, c_incdec, c_b, c_bfor)
    c_cin = n1.invar(cin, y=120)'''
assert old2 in t, u"ne najdena set' 1 ALU"
t = t.replace(old2, new2)

# --- 3. ispol'zovat' b_eff vmesto c_b v arifmetike ----------------------------
t = t.replace(u'bin_ = b_sel(n1, F.COL_BLK, 80, c_cin, c_b, c1)',
              u'bin_ = b_sel(n1, F.COL_BLK, 80, c_cin, b_eff, c1)')
# v setyah flagov B ispol'zuetsya dlya poluperenosa i perepolneniya -- tozhe b_eff
t = t.replace(u'''    c_b4 = n4.invar(b, y=190)''',
              u'''    c_b4 = n4.invar(b, y=190)   # dlya H ispol'zuem B_Forced ne nuzhno: INC/DEC
                                # schitaet H po formule s B=1, sm. set' 4''')

io.open(GEN, "w", encoding="utf-8").write(t)
print(u"PATCH ALU OK")
