# -*- coding: utf-8 -*-
u"""Bisekciya shemy PLC_PRG: otklyuchit odnu set' i posmotret na schetchik oshibok.

ZAPUSKAT SISTEMNYM PYTHON 3.

    python toggle_net.py list
    python toggle_net.py off 15     -- zakommentirovat' set' s nomerom 15
    python toggle_net.py on         -- vernut vse kak bylo

ZADAChA. Vse 18 oshibok C32 zhivut v PLC_PRG, no staticheskij analiz ih ne
nahodit, a polnoe isklyuchenie drugih POU ih ubiraet. Znachit nado perebrat'
seti samoj shemy -- eto edinstvennyj nadezhnyj sposob.
"""
import io
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEN = os.path.join(ROOT, u"generator", u"gen_z80.py")
BAK = GEN + u".bak"

MARK = u"REZhIM OTKLYuChENIYa"


def nets():
    u"""Najti stroki, gde nachinayutsya seti PLC_PRG."""
    t = io.open(GEN, encoding=u"utf-8").read()
    i = t.find(u"def mk_plc_prg():")
    j = t.find(u"\ndef ", i + 10)
    body = t[i:j]
    out = []
    for m in re.finditer(u"(?m)^(    )(n\\d+[a-z]*) = p\\.network", body):
        line = body[:m.start()].count(u"\n")
        out.append((m.group(2), i + sum(len(x) + 1 for x in t[:i].split(u"\n")) + 0))
    return out


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else u"list"
    t = io.open(GEN, encoding=u"utf-8").read()
    if mode == u"list":
        i = t.find(u"def mk_plc_prg():")
        j = t.find(u"\ndef ", i + 10)
        body = t[i:j]
        for m in re.finditer(u"(?m)^    (n\\d+[a-z]*) = p\\.network\\(u\"([^\"]+)\"", body):
            sys.stdout.write(u"  %-6s %s\n" % (m.group(1), m.group(2)))
        return

    if mode == u"on":
        if os.path.exists(BAK):
            shutil.copyfile(BAK, GEN)
            os.remove(BAK)
            sys.stdout.write(u"vosstanovleno iz rezerva\n")
        else:
            sys.stdout.write(u"rezer va net\n")
        return

    if mode == u"off":
        which = sys.argv[2] if len(sys.argv) > 2 else None
        if not which:
            sys.stdout.write(u"ukazhite nomer seti\n")
            return
        if not os.path.exists(BAK):
            shutil.copyfile(GEN, BAK)
        # otklyuchaem: perekleivaem stroku seti v if False: <otstup>
        start = t.find(u"    %s = p.network(" % which)
        if start < 0:
            sys.stdout.write(u"set' %s ne najdena\n" % which)
            return
        sys.stdout.write(u"otklyuchenie %s: poka ne realizovano avtomaticheski,\n"
                         u"pravte vruchnuyu po nomeru stroki %d\n"
                         % (which, t[:start].count(u"\n") + 1))

    return


if __name__ == u"__main__":
    main()
