# -*- coding: utf-8 -*-
u"""Pochinka posle migracii: vernut imena v deklaraciyah nuzhnyh GVL.

ChTO SLUChILOS. Pravila migracii "GVL_Tests.Test_X -> GVL_Tests.Cpu_Test_X"
i "4 probela + Test_X -> Visu_Test_X" primenyalis ko VSEMU tekstu gen_z80.py,
a vklyuchaet li on Deklaracii vnutri samih GVL -- da, vklyuchaet.
V itoge vnutri blokov ST_GVL_TESTS / ST_GVL_TESTS_CPM imena okazalis
s lishnimi prefiksami, i kollizii ostalis, tolko pod drugimi imenami.

RAZBOR PRAVILA. Vnutri bloka GVL deklaracii dolzhny byt BEZ prefiksa:
imya Cpu_Test_Stage zhivet v GVL_Tests, i obrasheniya k nemu idut cherez
"GVL_Tests.Cpu_Test_Stage". Znachit vnutri bloka nado snyat Cpu_/Cpm_/Visu_.

Zdes my tochno znaem granicy blokov (ot ST_GVL_... do END_VAR) i pravim
tolko vnutri nih, poetomu ne zatragivaem ni shemy, ni tela ST-programm.
"""
import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEN = os.path.join(ROOT, u"generator", u"gen_z80.py")

TESTS = [u"Test_Run", u"Test_Count", u"Test_Result", u"Test_Total_Pass",
         u"Test_Fail_Count", u"Test_Failed_List", u"Test_Stage",
         u"Test_Active", u"Test_Executed"]


def fix_block(text, marker, prefixes):
    u"""Vnutri bloka ot marker do END_VAR snyat lishnie prefiksy."""
    start = text.find(marker)
    if start < 0:
        print(u"  %s: NE NAJDEN" % marker)
        return text, 0
    end = text.find(u"END_VAR", start)
    block = text[start:end]
    n = 0
    for pre in prefixes:
        for v in TESTS:
            block, k = re.subn(re.escape(pre + v), v, block)
            n += k
    print(u"  %s: ispravleno %d" % (marker, n))
    return text[:start] + block + text[end:], n


def main():
    src = io.open(GEN, encoding=u"utf-8").read()
    src, n1 = fix_block(src, u"ST_GVL_TESTS = u'''VAR_GLOBAL", [u"Visu_", u"Cpu_"])
    src, n2 = fix_block(src, u"ST_GVL_TESTS_CPM = u'''VAR_GLOBAL", [u"Visu_", u"Cpm_"])
    io.open(GEN, u"w", encoding=u"utf-8").write(src)
    print(u"vsego ispravleno: %d" % (n1 + n2))


if __name__ == u"__main__":
    main()
