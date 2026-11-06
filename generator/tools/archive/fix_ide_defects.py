# -*- coding: utf-8 -*-
u"""Ispravlenie tryoh sistemnyh defektov po otchyotu iz IDE.

ZAPUSKAT SISTEMNYM PYTHON 3 ODIN RAZ.

D E F E K T  1. V build.py struktura ST_TestCase obyavlena DVAZhDY:
snachala polnaya (23 polya), zatem urezannaya (16 polej). Python ostavlyaet
posledneyu, poetomu ischezli Opcode_Lo, Init_HL, Exp_Mem, Exp_Mem_Addr,
Mask_Mem, Mask_Flag, Test_Has_Cond. ST-kod ih ispolzuet -- otsyuda sotni
"C0046: Identifikator 'Init_HL' ne zadаn" i "C0004: ... ne yavlyaetsya
komponentom 'ST_TestCase'". Ubiraem vtoroe (korotkoe) opredelenie.

D E F E K T  2. V GVL_Tests i GVL_Tests_CPM net massiva Tests (massiv
struktur s opisaniem proverok), hotya ST-kod aktivno ego zapolnyaet:
"GVL_Tests_CPM.Tests[i].Id := i". Bez nego ne rabotaet ni odin test.
Dobavlyaem obyavleniya.

D E F E K T  3. Vyzyvayutsya funkcii, kotoryh v IEC ne sushchestvuet:
BYTE_TO_BYTE i WORD_TO_WORD ("C0046: Identifikator ... ne zadаn").
Zamенyaem na pravilnye preobrazovaniya.
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILD = os.path.join(ROOT, u"generator", u"build.py")
GEN = os.path.join(ROOT, u"generator", u"gen_z80.py")

#  korotkoe (vtoroe) opredelenie ST_TestCase -- ego udalyaem
SHORT_DUT = u'''DUT_TESTCASE = u"""TYPE ST_TestCase :
STRUCT
    (* OPISANIE ODNOGO TESTA. Chtoby dobavit test, dostatochno zapolnit
       ocherednuyu stroku massiva -- shema ne menyaetsya. *)
    Id         : INT;
    Stage      : INT;
    Opcode     : BYTE;
    Init_A     : BYTE;
    Init_B     : BYTE;
    Init_F     : BYTE;
    Init_PC    : WORD;
    Init_SP    : WORD;
    Exp_A      : BYTE;
    Exp_F      : BYTE;
    Exp_PC     : WORD;
    Exp_Cycles : INT;
    Mask_A     : BOOL;
    Mask_F     : BOOL;
    Mask_PC    : BOOL;
    Enabled    : BOOL;
END_STRUCT
END_TYPE
"""
'''

TESTS_TESTS = u'''    Cpu_Test_Result      : ARRAY[1..75] OF BOOL;'''
TESTS_TESTS_NEW = u'''    (* OPISANIE PROVEROK: odna stroka -- odin test. Razmer 75 --
       stolko zaranee otvedeno pod proverki protsessora. *)
    Cpu_Tests            : ARRAY[1..75] OF ST_TestCase;

    Cpu_Test_Result      : ARRAY[1..75] OF BOOL;'''

CPM_TESTS = u'''    Cpm_Test_Result      : ARRAY[1..40] OF BOOL;'''
CPM_TESTS_NEW = u'''    (* OPISANIE PROVEROK CP/M: 40 strok. *)
    Cpm_Tests            : ARRAY[1..40] OF ST_TestCase_CPM;

    Cpm_Test_Result      : ARRAY[1..40] OF BOOL;'''


def main():
    # ---- defekt 1 ----
    b = io.open(BUILD, encoding=u"utf-8").read()
    if SHORT_DUT in b:
        b = b.replace(SHORT_DUT, u"", 1)
        sys.stdout.write(u"defekt 1: udaleno korotkoe opredelenie ST_TestCase\n")
    else:
        sys.stdout.write(u"defekt 1: korotkoe opredelenie NE NAJDENO (prover'te vruchnuyu)\n")
    io.open(BUILD, u"w", encoding=u"utf-8").write(b)

    g = io.open(GEN, encoding=u"utf-8").read()

    # ---- defekt 2 ----
    if TESTS_TESTS in g:
        g = g.replace(TESTS_TESTS, TESTS_TESTS_NEW, 1)
        sys.stdout.write(u"defekt 2a: GVL_Tests -- dobavlen massiv Cpu_Tests\n")
    else:
        sys.stdout.write(u"defekt 2a: shablon GVL_Tests ne najden\n")
    if CPM_TESTS in g:
        g = g.replace(CPM_TESTS, CPM_TESTS_NEW, 1)
        sys.stdout.write(u"defekt 2b: GVL_Tests_CPM -- dobavlen massiv Cpm_Tests\n")
    else:
        sys.stdout.write(u"defekt 2b: shablon GVL_Tests_CPM ne najden\n")

    # ---- pereimenovanie ssylok Tests -> Cpu_Tests / Cpm_Tests ----
    n1 = len(re.findall(u"GVL_Tests\\.Tests\\b", g))
    n2 = len(re.findall(u"GVL_Tests_CPM\\.Tests\\b", g))
    g = re.sub(u"GVL_Tests_CPM\\.Tests\\b", u"GVL_Tests_CPM.Cpm_Tests", g)
    g = re.sub(u"GVL_Tests\\.Tests\\b", u"GVL_Tests.Cpu_Tests", g)
    sys.stdout.write(u"       ssylok pereimenovano: GVL_Tests.Tests=%d, GVL_Tests_CPM.Tests=%d\n"
                     % (n1, n2))

    # ---- defekt 3 ----
    n = 0
    #  BYTE_TO_BYTE -> WORD_TO_BYTE: v etih mestah suzhaetsya WORD do bajta
    g, k = re.subn(u"BYTE_TO_BYTE\\(", u"WORD_TO_BYTE(", g)
    n += k
    #  WORD_TO_WORD(x) -> (x): preobrazovanie tipa v samogo sebya ne nuzhno
    g, k = re.subn(u"WORD_TO_WORD\\(([^()]*)\\)", u"(\\1)", g)
    n += k
    sys.stdout.write(u"defekt 3: ispravleno konversij: %d\n" % n)

    io.open(GEN, u"w", encoding=u"utf-8").write(g)
    sys.stdout.write(u"gotovo. Dalee: python generator/gen_z80.py\n")


if __name__ == u"__main__":
    main()
