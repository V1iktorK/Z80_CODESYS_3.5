# -*- coding: utf-8 -*-
u"""Pravka build.py: nadezhnaya registraciya programm v zadache.

ZAPUSKAT SISTEMNYM PYTHON 3.

ZADAChA. Ustanovleno (pereborom i proverkoj na stabil'nost'):
  * bez nastroyki zadachi -- 0 oshibok;
  * s PLC_PRG v zadache -- 36 oshibok C32;
  * kazhdaya ST-programma v zadache -- 4 oshibki "Identifikator ne zadаn".
To oznachaet, chto task.pous.add(imya, imya) NE registriruet programmu,
hotya isklyucheniya ne brosaet (nasledie togo, chto API vozvratilo drugoj tip
i add() sozdal ne to, chto nado).

Zdes probuem tri sposoba po ocheredi i v log popadaet, kakoy srabotal:
  1) task.pous.add(imya, imya)                -- kak bylo;
  2) task.pous[imya] = imya                   -- po indeksu;
  3) app.pou_call(imya)                       -- po imeni POU.
"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILD_PY = os.path.join(ROOT, u"generator", u"build.py")

OLD = (
    u"        for prg in _pous:\n"
    u"            try:\n"
    u"                task.pous.add(prg, prg)\n"
    u"                log(u\"  v zadachu dobavlena: %s\" % prg)\n"
    u"            except Exception:\n"
    u"                log(u\"  ne udalos dobavit %s\" % prg)\n"
    u"                err()\n"
)

NEW = (
    u"        for prg in _pous:\n"
    u"            #  T R I   S P O S O B A. task.pous.add(imya, imya) v etom\n"
    u"            #  build isklyucheniya ne brosaet, no programmu NE registriruet:\n"
    u"            #  togda kompilyator soobshchaet \"Identifikator 'X' ne zadan\".\n"
    u"            #  Probуем po ocheredi i pishem v log, kakoy srabotal.\n"
    u"            ok = False\n"
    u"            for how in (1, 2, 3):\n"
    u"                try:\n"
    u"                    if how == 1:\n"
    u"                        task.pous.add(prg, prg)\n"
    u"                    elif how == 2:\n"
    u"                        task.pous[prg] = prg\n"
    u"                    else:\n"
    u"                        app.pou_call(prg)\n"
    u"                    log(u\"  v zadachu dobavlena: %s (sposob %d)\" % (prg, how))\n"
    u"                    ok = True\n"
    u"                    break\n"
    u"                except Exception as e:\n"
    u"                    log(u\"    sposob %d dlya %s ne podoshel: %s\" % (how, prg, e))\n"
    u"            if not ok:\n"
    u"                log(u\"  NE UDALOS dobavit v zadachu: %s\" % prg)\n"
    u"                err()\n"
)


def main():
    t = io.open(BUILD_PY, encoding=u"utf-8").read()
    if u"T R I   S P O S O B A" in t:
        sys.stdout.write(u"pravka uzhe primenena\n")
        return
    if OLD not in t:
        sys.stdout.write(u"SHABLON NE NAJDEN\n")
        return
    t = t.replace(OLD, NEW, 1)
    io.open(BUILD_PY, u"w", encoding=u"utf-8").write(t)
    sys.stdout.write(u"build.py: dobavleny tri sposoba registracii\n")


if __name__ == u"__main__":
    main()
