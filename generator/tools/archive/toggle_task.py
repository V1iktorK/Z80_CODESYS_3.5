# -*- coding: utf-8 -*-
u"""Vremenno otklyuchit' nastrojku zadachi v build.py (dlya diagnostiki).

ZAPUSKAT SISTEMNYM PYTHON 3.
    python toggle_task.py off   -- otklyuchit blok nastroyki zadachi
    python toggle_task.py on    -- vernut kak bylo
"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILD_PY = os.path.join(ROOT, u"generator", u"build.py")

MARK = u'    head(u"nastroyka zadachi")\n'
OFF = u'    head(u"nastroyka zadachi")  # OTKLYuChENO DLYa DIAGNOSTIKI\n'
GUARD_OFF = u"    if False:  # <<< diagnostika: zadacha otklyuchena\n"
GUARD_ON = u"    if True:\n"


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else u"off"
    t = io.open(BUILD_PY, encoding=u"utf-8").read()
    if mode == u"off":
        if GUARD_OFF in t:
            sys.stdout.write(u"uzhe otklyucheno\n")
            return
        # oborachivaem telo bloka v if False -- otstup +4
        start = t.find(MARK)
        if start < 0:
            sys.stdout.write(u"MARK NE NAJDEN\n")
            return
        end = t.find(u"    except Exception:\n        log(u\"  OSHIBKA nastroyki zadachi\")", start)
        if end < 0:
            sys.stdout.write(u"KONEC BLOKA NE NAJDEN\n")
            return
        end = t.find(u"\n", t.find(u"err()", end)) + 1
        body = t[start:end]
        body = GUARD_OFF + body.replace(u"\n", u"\n    ").rstrip() + u"\n"
        t = t[:start] + body + t[end:]
        io.open(BUILD_PY, u"w", encoding=u"utf-8").write(t)
        sys.stdout.write(u"zadacha otklyuchena\n")
    else:
        if GUARD_OFF not in t:
            sys.stdout.write(u"ne bylo otklyucheno\n")
            return
        t = t.replace(GUARD_OFF, u"")
        io.open(BUILD_PY, u"w", encoding=u"utf-8").write(t)
        sys.stdout.write(u"zadacha vozvrashchena\n")


if __name__ == u"__main__":
    main()
