# -*- coding: utf-8 -*-
u"""B i S E K C I Ya: kakoy POU valit kompilyator CODESYS.

ZAPUSKAT SISTEMNYM PYTHON 3.
    python toggle_import.py list
    python toggle_import.py off TEST_Z80 TEST_Z80_CPM
    python toggle_import.py on

ZADAChA. Posle vosstanovleniya massivov Cpu_Tests/Cpm_Tests sborka stala
padat na kompilyacii ("Kompilyaciya : Prilozhenie" i vsyo). Nado ponyat,
kakoj imenno POU eto vyzyvaet, isklyuchaya ih po ocheredi iz IMPORT_ORDER.
"""
import io
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILD = os.path.join(ROOT, u"generator", u"build.py")
BAK = BUILD + u".orig"

MARK = u"# ISKLYuChENO DLYa BISEKCII"


def order_block(text):
    i = text.find(u"IMPORT_ORDER = [")
    j = text.find(u"]", i)
    return i, j + 1, text[i:j + 1]


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else u"list"
    if mode == u"on":
        if os.path.exists(BAK):
            shutil.copyfile(BAK, BUILD)
            os.remove(BAK)
            sys.stdout.write(u"IMPORT_ORDER vosstanovlen\n")
        else:
            sys.stdout.write(u"rezerva net\n")
        return

    t = io.open(BUILD, encoding=u"utf-8").read()
    i, j, blk = order_block(t)
    if mode == u"list":
        for m in re.finditer(u'u"(\\w+)"', blk):
            sys.stdout.write(u"  %s\n" % m.group(1))
        return

    if mode != u"off":
        return
    names = sys.argv[2:]
    if not os.path.exists(BAK):
        shutil.copyfile(BUILD, BAK)
        t = io.open(BUILD, encoding=u"utf-8").read()
        i, j, blk = order_block(t)
    else:
        t = io.open(BAK, encoding=u"utf-8").read()
        i, j, blk = order_block(t)

    n = 0
    for nm in names:
        pat = u'\\s*u"%s",?' % nm
        if re.search(pat, blk):
            blk = re.sub(pat, u"", blk)
            n += 1
    #  ubiraem lishnie zapyatye
    blk = re.sub(u",\\s*]", u"]", blk)
    blk = re.sub(u"\\[\\s*,", u"[", blk)
    t = t[:i] + blk + t[j:]
    io.open(BUILD, u"w", encoding=u"utf-8").write(t)
    sys.stdout.write(u"iskljucheno POU: %d\n" % n)


if __name__ == u"__main__":
    main()
