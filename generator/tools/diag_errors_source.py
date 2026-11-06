# -*- coding: utf-8 -*-
u"""Diagnostika: kakoj prohod daet 12 oshibok C32.

ZAPUSKAT SISTEMNYM PYTHON 3.

ZADAChA. V itoge kompilyacii 28 oshibok, iz nih 12 -- oshibki C32
(konverziya tipov). V izolirovannom proekte iz teh zhe fajlov takih oshibok
NET. Znachit ikh porozhdaet chto-to, chto est tolko v boevoj sborke:
nastrojka zadachi libo nabor POU.

Zdes schitaem, skolko oshibok C32 v kazhdom prohode po otdel'nosti.
"""
import io
import os
import re
import sys
import collections
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOG = os.path.join(ROOT, u"log", u"codesys_out.txt")
BUILD_PY = os.path.join(ROOT, u"generator", u"build.py")
BAK = BUILD_PY + u".bak"


def read_counts():
    t = open(LOG, "rb").read().decode("utf-8", "replace").split("\n")
    errs = [l.strip() for l in t if "Error" in l]
    c = collections.Counter()
    for l in errs:
        m = re.search(r"(C\d+):", l)
        c[m.group(1) if m else "?"] += 1
    return len(errs), dict(c)


def main():
    sys.stdout.write(u"tekushchij vyvod: %s\n" % (read_counts(),))
    sys.stdout.write(u"\nCHTOBY PONYAT ISTOChNIK, NUZhNO PRAVIT build.py.\n")
    sys.stdout.write(u"Zakommentirujte blok 'nastroyka zadachi' i povtorite sborku:\n")
    sys.stdout.write(u"  * esli C32 ischezli -- vinovata nastroyka zadachi;\n")
    sys.stdout.write(u"  * esli ostalis -- vinovata raznica v naborе POU.\n")


if __name__ == u"__main__":
    main()
