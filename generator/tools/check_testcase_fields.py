# -*- coding: utf-8 -*-
u"""Sverit polya ST_TestCase / ST_TestCase_CPM s tem, chto ispolzuet ST-kod.

ZAPUSKAT SISTEMNYM PYTHON 3.

ZADAChA. V build.py struktura ST_TestCase obyavlena DVAZhDY, i vtoroe
obyavlenie koroche -- ono perekryvaet pervoe. Iz-za etogo ischezli polya
Init_HL, Opcode_Lo, Exp_Mem i drugie, i kompilyator soobshchaet
"C0004: 'Init_HL' ne yavlyaetsya komponentom 'ST_TestCase'".

Zdes schitaem, kakie polya realno nuzhny (po kodam ST v generatore),
i kakie obyavleny v kazhdom iz dvuh variantov.
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEN = os.path.join(ROOT, u"generator", u"gen_z80.py")
BUILD = os.path.join(ROOT, u"generator", u"build.py")


def main():
    gen = io.open(GEN, encoding=u"utf-8").read()
    build = io.open(BUILD, encoding=u"utf-8").read()

    # 1) polya STRUKTURY: tolko obrashcheniya k elementu massiva
    #    GVL_Tests.Tests[i].<pole>. Vhod v fbCase.<pole> -- eto interfejs
    #    FB_TestCase, a ne polya struktury, i v etu proverku ne vhodit.
    struct_fields = set()
    for m in re.finditer(u"Tests\\[[^\\]]+\\]\\.(\\w+)", gen):
        struct_fields.add(m.group(1))
    used = struct_fields
    sys.stdout.write(u"=== polya STRUKTURY, ispolzuemye kodom ST (%d) ===\n" % len(used))
    for f in sorted(used):
        sys.stdout.write(u"   %s\n" % f)

    # 1b) otdelno -- interfejs FB_TestCase (dlya spravki)
    fb_fields = set()
    for m in re.finditer(u"fbCase\\.(\\w+)", gen):
        fb_fields.add(m.group(1))
    sys.stdout.write(u"\n=== polya FB_TestCase (interfeys, %d) ===\n" % len(fb_fields))
    sys.stdout.write(u"   %s\n" % u", ".join(sorted(fb_fields)))

    # 2) varianty obyavleniya
    sys.stdout.write(u"\n=== varianty DUT_TESTCASE v build.py ===\n")
    n = 0
    for m in re.finditer(u"DUT_TESTCASE = u\"\"\"TYPE ST_TestCase :(.*?)END_TYPE", build, re.S):
        n += 1
        names = re.findall(u"(\\w+)\\s*:", m.group(1))
        sys.stdout.write(u"   variant %d: %d polej\n      %s\n" % (n, len(names), u", ".join(names)))

    sys.stdout.write(u"\n=== varianty DUT_TESTCASE_CPM ===\n")
    n = 0
    for m in re.finditer(u"DUT_TESTCASE_CPM = u\"\"\"TYPE ST_TestCase_CPM :(.*?)END_TYPE", build, re.S):
        n += 1
        names = re.findall(u"(\\w+)\\s*:", m.group(1))
        sys.stdout.write(u"   variant %d: %d polej\n      %s\n" % (n, len(names), u", ".join(names)))

    # 3) sravnenie
    sys.stdout.write(u"\n=== chego ne hvataet v POSLEDNEM variante ===\n")
    last = None
    for m in re.finditer(u"DUT_TESTCASE = u\"\"\"TYPE ST_TestCase :(.*?)END_TYPE", build, re.S):
        last = set(re.findall(u"(\\w+)\\s*:", m.group(1)))
    if last is not None:
        missing = sorted(used - last)
        for f in missing:
            sys.stdout.write(u"   NET: %s\n" % f)
        if not missing:
            sys.stdout.write(u"   vse polya na meste\n")


if __name__ == u"__main__":
    main()
