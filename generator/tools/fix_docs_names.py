# -*- coding: utf-8 -*-
u"""Obnovlenie dokumentacii posle migracii imen GVL.

ZAPUSKAT SISTEMNYM PYTHON 3.

Posle pereimenovaniya peremennyh (Cpu_Test_*, Cpm_Test_*, Visu_Test_*,
Bus_* tolko v GVL_Bus) v dokumentah ostalis starye imena. Ih nado
sinhronizirovat, inache polzovatel budet iskat v proekte to, chego net.
"""
import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOCS = os.path.join(ROOT, u"docs")

TESTS = [u"Test_Run", u"Test_Count", u"Test_Result", u"Test_Total_Pass",
         u"Test_Fail_Count", u"Test_Failed_List", u"Test_Stage",
         u"Test_Active", u"Test_Executed"]

RULES = []
for _v in TESTS:
    RULES.append((u"GVL_Tests_CPM." + _v, u"GVL_Tests_CPM.Cpm_" + _v))
for _v in TESTS:
    RULES.append((u"GVL_Tests." + _v, u"GVL_Tests.Cpu_" + _v))
for _v in TESTS:
    RULES.append((u"GVL_PLCVisu." + _v, u"GVL_PLCVisu.Visu_" + _v))
RULES.append((u"GVL_PLCVisu.Bus_Addr", u"GVL_Bus.Bus_Addr"))
RULES.append((u"GVL_PLCVisu.Bus_Data", u"GVL_Bus.Bus_Data"))


def main():
    for fn in sorted(os.listdir(DOCS)):
        if not fn.endswith(u".md"):
            continue
        path = os.path.join(DOCS, fn)
        t = io.open(path, encoding=u"utf-8").read()
        orig = t
        n = 0
        for old, new in RULES:
            pat = re.compile(r"(?<![A-Za-z0-9_.])" + re.escape(old) + r"(?![A-Za-z0-9_])")
            t, k = pat.subn(new, t)
            n += k
        if t != orig:
            io.open(path, u"w", encoding=u"utf-8").write(t)
        print(u"%-32s zamen %d" % (fn, n))


if __name__ == u"__main__":
    main()
