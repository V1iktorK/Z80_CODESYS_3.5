# -*- coding: utf-8 -*-
u"""Poslednie dve pravki migracii imen.

1) Disk_DMA ob''yavlen i v GVL_CPM, i v GVL_Disk -- ostavlyaem tolko v
   GVL_Disk (tam ego i ispolzuet PRG_CPM_BDOS). Odno imya -- odin vladelec.
2) V GVL_PLCVisu dobavlyaem zerkalo Visu_Test_Active: PLC_PRG ego pishet,
   a obyavleniya ne bylo (v TEST_Z80 ono est, poetomu kompilyator molchal).
"""
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEN = os.path.join(ROOT, u"generator", u"gen_z80.py")


def main():
    src = io.open(GEN, encoding=u"utf-8").read()

    # --- 1) Disk_DMA tolko v GVL_Disk ---
    start = src.find(u"ST_GVL_CPM = u'''VAR_GLOBAL")
    end = src.find(u"END_VAR", start)
    block = src[start:end]
    before = block
    lines = [ln for ln in block.split(u"\n") if u"Disk_DMA" not in ln]
    block = u"\n".join(lines)
    if block != before:
        src = src[:start] + block + src[end:]
        print(u"GVL_CPM: stroka Disk_DMA udalena")
    else:
        print(u"GVL_CPM: Disk_DMA ne najden (uzhe udalen?)")

    # --- 2) zerkalo Visu_Test_Active ---
    old = u"    Visu_Test_Stage      : INT;\n"
    new = u"    Visu_Test_Stage      : INT;\n    Visu_Test_Active     : INT;\n"
    if old in src and u"Visu_Test_Active" not in src:
        src = src.replace(old, new)
        print(u"GVL_PLCVisu: dobavleno Visu_Test_Active")
    else:
        print(u"GVL_PLCVisu: Visu_Test_Active uzhe est ili shablon ne najden")

    io.open(GEN, u"w", encoding=u"utf-8").write(src)
    print(u"gotovo. Dalee: python generator/gen_z80.py")


if __name__ == u"__main__":
    main()
