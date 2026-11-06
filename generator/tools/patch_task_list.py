# -*- coding: utf-8 -*-
u"""Pravka build.py: upravlyaemyj spisok programm v zadache.

ZAPUSKAT SISTEMNYM PYTHON 3.

ZADAChA. Ustanovleno eksperimentom: bez nastroyki zadachi sborka daet 0 oshibok,
s nastroykoj -- 12 oshibok C32 plyus 12 oshibok "Identifikator ne zadаn".
Znachit vinovata registraciya programm v zadache. Nuzhen sposob bystro
perebrat' sostavy, chtoby ponyat, kakaya imenno programma ih daet.

Zdes dobavlyaem chtenie spiska iz peremennoj okruzheniya Z80_TASK_POUS
(imena cherez zapyatuyu). Po umolchaniyu -- kak bylo.
"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILD_PY = os.path.join(ROOT, u"generator", u"build.py")

OLD = (
    u"        for prg in (u\"PRG_InitMemory\", u\"PRG_CPM_Boot\", u\"TEST_Z80\",\n"
    u"                u\"PRG_CPM_BDOS\", u\"TEST_Z80_CPM\", u\"PLC_PRG\"):\n"
)

NEW = (
    u"        #  Spisok programm v zadache mozhno pereopredelit cherez\n"
    u"        #  peremennuyu okruzheniya Z80_TASK_POUS (imena cherez zapyatuyu).\n"
    u"        #  Eto nuzhno dlya diagnostiki: ustanovleno, chto imenno\n"
    u"        #  registraciya programm v zadache porozhdaet oshibki C32.\n"
    u"        _env = os.environ.get(u\"Z80_TASK_POUS\")\n"
    u"        if _env:\n"
    u"            _pous = [x.strip() for x in _env.split(u\",\") if x.strip()]\n"
    u"            log(u\"  spisok zadach iz Z80_TASK_POUS: %s\" % _pous)\n"
    u"        else:\n"
    u"            _pous = [u\"PRG_InitMemory\", u\"PRG_CPM_Boot\", u\"TEST_Z80\",\n"
    u"                     u\"PRG_CPM_BDOS\", u\"TEST_Z80_CPM\", u\"PLC_PRG\"]\n"
    u"        for prg in _pous:\n"
)


def main():
    t = io.open(BUILD_PY, encoding=u"utf-8").read()
    if u"Z80_TASK_POUS" in t:
        sys.stdout.write(u"pravka uzhe primenena\n")
        return
    if OLD not in t:
        sys.stdout.write(u"SHABLON NE NAJDEN\n")
        return
    t = t.replace(OLD, NEW, 1)
    io.open(BUILD_PY, u"w", encoding=u"utf-8").write(t)
    sys.stdout.write(u"build.py: spisok zadach teper' nastraivaemyj\n")


if __name__ == u"__main__":
    main()
