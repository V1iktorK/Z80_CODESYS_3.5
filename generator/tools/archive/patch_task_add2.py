# -*- coding: utf-8 -*-
u"""Ubrat' opasnye sposoby registracii programm v zadache.

ZAPUSKAT SISTEMNYM PYTHON 3.

ChTO SLUChILOS. Dobavlenie tryoh sposobov registracii privelo k avarijnomu
zaversheniyu CODESYS: "Fatal error. Internal CLR error. (0x80131506)" i
exit=-1. Vinovnik -- app.pou_call(imya): takogo metoda u Application net,
i popytka vyzvat' ego valit CLR tselikom (eto vidno po tomu, chto build.log
obryvaetsya na pervoj zhe sekcii).

Ostavlyaem dva bezopasnyh sposoba (add i indeksnoe prisvaivanie) i dobavlyaem
chtenie spiska urovney zadachi -- chtoby VIDET, chto real'no zaregistrirovalos.
"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILD_PY = os.path.join(ROOT, u"generator", u"build.py")

OLD = (
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

NEW = (
    u"            #  V N I M A N I E: app.pou_call(imya) VALIT CLR\n"
    u"            #  (\"Fatal error. Internal CLR error. (0x80131506)\"), poetomu\n"
    u"            #  ostayutsya tolko dva bezopasnyh sposoba.\n"
    u"            ok = False\n"
    u"            for how in (1, 2):\n"
    u"                try:\n"
    u"                    if how == 1:\n"
    u"                        task.pous.add(prg, prg)\n"
    u"                    else:\n"
    u"                        task.pous[prg] = prg\n"
    u"                    ok = True\n"
    u"                    break\n"
    u"                except Exception as e:\n"
    u"                    log(u\"    sposob %d dlya %s ne podoshel: %s\" % (how, prg, e))\n"
    u"            if not ok:\n"
    u"                log(u\"  NE UDALOS dobavit v zadachu: %s\" % prg)\n"
    u"                err()\n"
    u"        #  Ch T O   R E A L N O   Z A R E G I S T R I R O V A N O.\n"
    u"        #  Bez etoj proverki my ne vidim raznicy mezhdu \"add() ne brosil\n"
    u"        #  isklyuchenie\" i \"programma deystvitel'no v zadache\".\n"
    u"        try:\n"
    u"            lst = list(task.pous)\n"
    u"            log(u\"  v zadache chisel: %d\" % len(lst))\n"
    u"            for it in lst:\n"
    u"                log(u\"    urovень: %r\" % (it,))\n"
    u"        except Exception as e:\n"
    u"            log(u\"  spisok urovney zadachi prochitat ne udalos: %s\" % e)\n"
)


def main():
    t = io.open(BUILD_PY, encoding=u"utf-8").read()
    if u"app.pou_call" not in t:
        sys.stdout.write(u"opasnyj sposob uzhe ubran\n")
        return
    if OLD not in t:
        sys.stdout.write(u"SHABLON NE NAJDEN\n")
        return
    t = t.replace(OLD, NEW, 1)
    io.open(BUILD_PY, u"w", encoding=u"utf-8").write(t)
    sys.stdout.write(u"build.py: opasnyj sposob ubran, dobavlen kontrol' spiska\n")


if __name__ == u"__main__":
    main()
