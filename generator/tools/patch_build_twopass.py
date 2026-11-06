# -*- coding: utf-8 -*-
u"""Pravka build.py: dva prohoda sborki.

ZAPUSKAT SISTEMNYM PYTHON 3 ODIN RAZ.

ZADAChA. Polnaya sborka daet 36 oshibok C32, a izolirovannaya sborka iz TEH ZhE
fajlov -- ni odnoj. Raznica v posledovatel'nosti: v izolyacii pered
generate_code() uzhe vypolnen build(), v boevoj -- net.
Znachit pered nastoyashchej kompilyaciej nuzhen promezhutochnyj prohod:
    build() -> generate_code() -> build() -> generate_code()
"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILD_PY = os.path.join(ROOT, u"generator", u"build.py")

OLD = (
    u"    try:\n"
    u"        app.build()\n"
    u'        log(u">>> app.build() -- bez isklyucheniya (sborka prilozheniya)")\n'
)

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


def main():
    t = io.open(BUILD_PY, encoding=u"utf-8").read()
    if NEW in t:
        sys.stdout.write(u"pravka uzhe primenena\n")
        return
    if OLD not in t:
        sys.stdout.write(u"SHABLON NE NAJDEN -- pravte vruchnuyu\n")
        return
    t = t.replace(OLD, NEW, 1)
    io.open(BUILD_PY, u"w", encoding=u"utf-8").write(t)
    sys.stdout.write(u"build.py: dobavlen pervyj prohod\n")


if __name__ == u"__main__":
    main()
