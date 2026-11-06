# -*- coding: utf-8 -*-
u"""Perevesti potrebitelej Ctl_* vnutri PLC_PRG na lokalnye peremennye.

ZAPUSKAT SISTEMNYM PYTHON 3 ODIN RAZ.

ZADAChA. Vyhody dekodera teper' idut v lokalnye peremennye vCtl_* (i ottuda
v GVL dlya drugih POU, u kotorvh svoi ekzemplyary dekodera ne nuzhny).
Vnutri PLC_PRG chitat' nado lokalnye -- inache ostayutsya ssylki na
GVL_Control.Ctl_*, i smysl pravki teryaetsya.

Pravim tolko telo funkcii mk_plc_prg, chtoby ne zadet' drugie POU.
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEN = os.path.join(ROOT, u"generator", u"gen_z80.py")


def main():
    t = io.open(GEN, encoding=u"utf-8").read()
    i = t.find(u"def mk_plc_prg():")
    j = t.find(u"\ndef ", i + 10)
    if i < 0 or j < 0:
        sys.stdout.write(u"funkciya ne najdena\n")
        return
    body = t[i:j]
    n = 0

    # 1) chtenie Ctl_* vnutri PLC_PRG -> lokalnye vCtl_*
    def sub_read(m):
        return u"%sinvar(u\"v%s\"" % (m.group(1), m.group(2))

    body, k = re.subn(u'(n\\d+[a-z]*\\.)invar\\(u"GVL_Control\\.(Ctl_\\w+)"',
                      sub_read, body)
    n += k

    # 2) set' zapisi v GVL ne trogaem -- tam kak raz i dolzhno byt GVL_Control.Ctl_*
    io.open(GEN, u"w", encoding=u"utf-8").write(t[:i] + body + t[j:])
    sys.stdout.write(u"zamen chteniya Ctl_*: %d\n" % n)


if __name__ == u"__main__":
    main()
