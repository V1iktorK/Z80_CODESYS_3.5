# -*- coding: utf-8 -*-
u"""Migraciya imen GVL: final'naya, tochechnaya versiya.

ZAPUSKAT SISTEMNYM PYTHON 3 ODIN RAZ, zatem gen_z80.py, sverka, sborka, verify.

ZADAChA. Ubranit 10 kollizij imen mezhdu GVL (odno imya -- dva-tri GVL).
Kompilyator SP17 takie kollizii NE schitaet oshibkoj, no oni delayut proekt
nepredskazuemym: Test_Result imeet razmer [1..75] v GVL_Tests i [1..40] v
GVL_Tests_CPM, a v Watch-okne odno imya pokazyvaet dva raznyh znacheniya.

PRAVILO IMENOVANIYA (posle migracii):
    GVL_Tests      Cpu_Test_*    testy protsessora
    GVL_Tests_CPM  Cpm_Test_*    testy CP/M i I/O
    GVL_PLCVisu    Visu_Test_*   zerkalo dlya HMI (tolko chtenie)
    GVL_Bus        Bus_Addr, Bus_Data -- edinstvennyj vladelec shin
    GVL_Disk       Disk_DMA      -- edinstvennyj vladelec adresa peredachi

POCHEMU TAK, A NE INAChe. Pervaya popytka primenila odni i te zhe pravila
ko vsemu gen_z80.py, i oni popali v deklaracii vnutri samih GVL (oni tozhe
nachinayutsya s probelov). V itoge imena poluchili lishnie prefiksy. Zdes
granicy blokov znajutsya tochno, i kazhdoe izmenenie lokalizovano.
"""
import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEN = os.path.join(ROOT, u"generator", u"gen_z80.py")

TESTS = [u"Test_Run", u"Test_Count", u"Test_Result", u"Test_Total_Pass",
         u"Test_Fail_Count", u"Test_Failed_List", u"Test_Stage",
         u"Test_Active", u"Test_Executed"]


def in_block(text, marker, fn):
    u"""Primenit fn k bloku ot marker do END_VAR."""
    start = text.find(marker)
    if start < 0:
        raise SystemExit(u"NE NAJDEN blok: %s" % marker)
    end = text.find(u"END_VAR", start)
    return text[:start] + fn(text[start:end]) + text[end:]


def decl_prefix(prefix):
    def fn(block):
        n = 0
        for v in TESTS:
            block, k = re.subn(u"(?m)^(\\s*)" + v + u"(\\s*:)", u"\\g<1>" + prefix + v + u"\\g<2>", block)
            n += k
        print(u"    prefiks %s: %d obyavlenij" % (prefix, n))
        return block
    return fn


def main():
    src = io.open(GEN, encoding=u"utf-8").read()

    print(u"1) prefiksy v deklaraciyah GVL (bez tela programm):")
    src = in_block(src, u"ST_GVL_TESTS = u'''VAR_GLOBAL", decl_prefix(u"Cpu_"))
    src = in_block(src, u"ST_GVL_TESTS_CPM = u'''VAR_GLOBAL", decl_prefix(u"Cpm_"))

    print(u"2) GVL_PLCVisu: ubiraem dubl shin (oni v GVL_Bus) i dobavlyaem zerkala testov:")
    # neskolko prohodov, poka ne ostabetsya Bus_Addr/Bus_Data
    for _ in range(4):
        src = re.sub(u"[ \\t]*Bus_Addr : WORD;[^\\n]*\\n", u"", src)
        src = re.sub(u"[ \\t]*Bus_Data : BYTE;[^\\n]*\\n", u"", src)
    old = (u"    Dump_Base : WORD;\n"
           u"    (* itogi testov dlya HMI *)\n"
           u"    Test_Total_Pass : INT;\n"
           u"    Test_Fail_Count : INT;\n"
           u"    Test_Stage      : INT;\n")
    new = (u"    Dump_Base : WORD;\n"
           u"    (* itogi testov dlya HMI. ETO ZERKALA: ih pishet PLC_PRG iz\n"
           u"       GVL_Tests / GVL_Tests_CPM, HMI tolko chitaet. *)\n"
           u"    Visu_Test_Total_Pass : INT;\n"
           u"    Visu_Test_Fail_Count : INT;\n"
           u"    Visu_Test_Stage      : INT;\n"
           u"    Visu_Test_Active     : INT;\n")
    if old in src:
        src = src.replace(old, new)
        print(u"    blok zerkal perepisan")
    else:
        print(u"    VNIMANIE: blok zerkal ne najden po shablonu -- proverte vruchnuyu")

    io.open(GEN, u"w", encoding=u"utf-8").write(src)
    print(u"gotovo. Dalee: python generator/gen_z80.py")


if __name__ == u"__main__":
    main()
