# -*- coding: utf-8 -*-
u"""S u H O J   P R O G O N: skolko mest vida fbXX.PIN v PLC_PRG i kakie.

ZAPUSKAT SISTEMNYM PYTHON 3. Nish ego ne menyaet -- tolko pokazyvaet.
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEN = os.path.join(ROOT, u"generator", u"gen_z80.py")

PAT = re.compile(
    u'(?P<ind>[ \t]*)(?P<net>n\\d+[a-z]*)\\.outvar\\(u"(?P<dest>[^"]+)"'
    u'[^)]*?(?P=net)\\.invar\\(u"(?P<fb>fb\\w+)\\.(?P<pin>\\w+)"')


def main():
    t = io.open(GEN, encoding=u"utf-8").read()
    i = t.find(u"def mk_plc_prg():")
    j = t.find(u"\ndef ", i + 10)
    body = t[i:j]
    ms = list(PAT.finditer(body))
    sys.stdout.write(u"najdeno mest s ssylkoj na vyhod FB: %d\n\n" % len(ms))
    seen = set()
    for m in ms:
        key = (m.group(u"net"), m.group(u"dest"), m.group(u"fb"), m.group(u"pin"))
        if key in seen:
            continue
        seen.add(key)
        sys.stdout.write(u"  %-7s %-26s <- %s.%s\n"
                         % (m.group(u"net"), m.group(u"dest"),
                            m.group(u"fb"), m.group(u"pin")))
    sys.stdout.write(u"\nunikalnyh: %d\n" % len(seen))


if __name__ == u"__main__":
    main()
