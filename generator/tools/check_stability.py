# -*- coding: utf-8 -*-
u"""Stabil'nost' sborki: dva prohoda podryad i sravnenie.

ZAPUSKAT SISTEMNYM PYTHON 3.

ZADAChA. Schedchiki oshibok ot progona k progonu rashodyatsya (36, 56, 112...),
hotya fajly ne menyayutsya. Nado ponyat, stabilen li rezul'tat voobshche:
esli net, to lyubye vyvody o prichinah nedostoverny i snachala nuzhno
ustranit' nestabil'nost'.
"""
import hashlib
import os
import re
import subprocess
import sys
import collections

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CMD = os.path.join(ROOT, u"generator", u"run_build_log.cmd")
LOG = os.path.join(ROOT, u"log", u"codesys_out.txt")


def run_once():
    subprocess.call([u"cmd", u"/c", CMD])
    raw = open(LOG, "rb").read()
    t = raw.decode("utf-8", "replace").split("\n")
    errs = [l.strip() for l in t if "Error" in l]
    c = collections.Counter()
    for l in errs:
        m = re.search(r"(C\d+):", l)
        c[m.group(1) if m else "?"] += 1
    itog = u""
    for l in t:
        if u"zavershena" in l:
            itog = l.strip()
    return len(errs), dict(c), hashlib.md5(raw).hexdigest()[:10], itog


def main():
    for i in (1, 2, 3):
        n, c, h, itog = run_once()
        sys.stdout.write(u"progon %d: oshibok=%d %s  md5=%s\n" % (i, n, c, h))
        if itog:
            sys.stdout.write(u"          %s\n" % itog[:120])


if __name__ == u"__main__":
    main()
