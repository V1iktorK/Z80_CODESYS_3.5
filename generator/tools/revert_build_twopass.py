# -*- coding: utf-8 -*-
u"""Otkat pravki build.py: dva prohoda ne nuzhny.

ZAPUSKAT SISTEMNYM PYTHON 3 ODIN RAZ.

POCHEMU OTKAT. Prohod build()+generate_code() dvazhdy NE ustranyaet oshibki
C32, a VDV OE ih schislyaet: v itoge 112 soobshchenij vmesto 56. Znachit
gipoteza o posledovatel'nosti byla neverna, i lishnij prohod nado ubrat.
"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILD_PY = os.path.join(ROOT, u"generator", u"build.py")

NEW = (
    u"    #  D V A   P R O H O D A.  Pervyj build() bez generate_code() tolko\n"
    u"    #  gotovit model prilozheniya. Bez nego pervaya kompilyaciya daet\n"
    u"    #  36 oshibok C32, kotoryh net v izolirovannom proekte iz teh zhe\n"
    u"    #  fajlov (proverено sravneniem dvuh sborkok podryad).\n"
    u"    try:\n"
    u"        app.build()\n"
    u'        log(u">>> app.build() -- prohod 1 (podgotovka modeli)")\n'
    u"    except Exception:\n"
    u"        err()\n"
    u"    try:\n"
    u"        app.generate_code()\n"
    u'        log(u">>> app.generate_code() -- prohod 1")\n'
    u"    except Exception:\n"
    u"        err()\n"
    u"    try:\n"
    u"        app.build()\n"
    u'        log(u">>> app.build() -- bez isklyucheniya (sborka prilozheniya)")\n'
)

OLD = (
    u"    try:\n"
    u"        app.build()\n"
    u'        log(u">>> app.build() -- bez isklyucheniya (sborka prilozheniya)")\n'
)


def main():
    t = io.open(BUILD_PY, encoding=u"utf-8").read()
    if NEW not in t:
        sys.stdout.write(u"pravka uzhe otkachena\n")
        return
    t = t.replace(NEW, OLD, 1)
    io.open(BUILD_PY, u"w", encoding=u"utf-8").write(t)
    sys.stdout.write(u"build.py: lishnij prohod ubrаn\n")


if __name__ == u"__main__":
    main()
