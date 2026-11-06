# -*- coding: utf-8 -*-
u"""Razovaya migraciya: ustranenie kollizij imen mezhdu GVL.

ZAPUSKAT SISTEMNYM PYTHON 3 ODIN RAZ, zatem gen_z80.py.

PROBLEMA. Kompilyator CODESYS 3.5 SP17 NE schitaet oshibkoj, kogda odno imya
ob''yavleno v neskolkih GVL. V proekte takih imen okazalos 10: Test_Run,
Test_Count, Test_Result, Test_Total_Pass, Test_Fail_Count, Test_Failed_List,
Test_Stage, Test_Active, Test_Executed, Bus_Addr, Bus_Data, Disk_DMA.
Formal'no rabotaet, no:
  * neponyatno, kakuyu imenno peremennuyu chitaet shema;
  * Test_Result v GVL_Tests imeet razmer [1..75], a v GVL_Tests_CPM [1..40] --
    odno imya, raznye tipy;
  * v Watch-okne polzovatel vidit odno znachenie, a v drugom GVL -- drugoe.

REShENIE. Kazhdyj GVL-polzovatel poluchaet sobstvennyj prefiks:
    GVL_Tests      -> Cpu_Test_*   (testy protsessora)
    GVL_Tests_CPM  -> Cpm_Test_*   (testy CP/M i I/O)
    GVL_PLCVisu    -> Visu_Test_*  (zerkalo dlya HMI)
Real'nye shiny Bus_Addr / Bus_Data ostayutsya v GVL_Bus (edinstvennyj
vladelec), a zerkalo dlya HMI -- GVL_Bus zhe. Disk_DMA -- tolko v GVL_Disk.

POCHEMU PRAVIM TOLKO gen_z80.py: fajly .gvl tozhe generiruemye -- ih pishet
gen_z80.py iz strok ST_GVL_*, i lyubaya ruchnaya pravka .gvl poteryaetsya pri
sleduyushchej regeneracii. Edinstvennyj istochnik pravdy -- generator.

POSLE MIGRACII obyazatel'no: python generator/gen_z80.py, sverka deklaracij,
sborka, verify.py.
"""
import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEN = os.path.join(ROOT, u"generator", u"gen_z80.py")

TEST_VARS = [u"Test_Run", u"Test_Count", u"Test_Result", u"Test_Total_Pass",
             u"Test_Fail_Count", u"Test_Failed_List", u"Test_Stage",
             u"Test_Active", u"Test_Executed"]

RULES = []
for _v in TEST_VARS:
    RULES.append((u"GVL_Tests_CPM." + _v, u"GVL_Tests_CPM.Cpm_" + _v))
for _v in TEST_VARS:
    RULES.append((u"GVL_Tests." + _v, u"GVL_Tests.Cpu_" + _v))
for _v in TEST_VARS:
    RULES.append((u"GVL_PLCVisu." + _v, u"GVL_PLCVisu.Visu_" + _v))
RULES.append((u"GVL_PLCVisu.Bus_Addr", u"GVL_Bus.Bus_Addr"))
RULES.append((u"GVL_PLCVisu.Bus_Data", u"GVL_Bus.Bus_Data"))
# deklaracii vnutri GVL_PLCVisu (bez prefiksa GVL_)
for _v in (u"Test_Total_Pass", u"Test_Fail_Count", u"Test_Stage"):
    RULES.append((u"    " + _v, u"    Visu_" + _v))


def apply(text, rules):
    n = 0
    for old, new in rules:
        pat = re.compile(r"(?<![A-Za-z0-9_.])" + re.escape(old) + r"(?![A-Za-z0-9_])")
        text, k = pat.subn(new, text)
        n += k
    return text, n


def main():
    src = io.open(GEN, encoding=u"utf-8").read()
    new, n = apply(src, RULES)
    if n:
        io.open(GEN, u"w", encoding=u"utf-8").write(new)
    print(u"gen_z80.py: zamen %d" % n)
    print(u"teper zapustite: python generator/gen_z80.py")


if __name__ == u"__main__":
    main()
