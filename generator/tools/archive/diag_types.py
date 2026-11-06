# -*- coding: utf-8 -*-
u"""Diagnostika tipovyh oshibok: kto imenno pitает blok ne tem tipom.

ZAPUSKAT SISTEMNYM PYTHON 3.

ZADAChA. Kompilyator daet 40 oshibok C32 "Nevozmozhno konvertirovat tip
'BOOL' v tip 'USINT'" i t. p. Nuzhno ponyat, kakie imenno shemy i bloki ih
dayut, chtoby pochinit prichinu, a ne sledstvie.
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(os.path.dirname(HERE)), u"src")


def gvl_types():
    u"""Tip kazhdoj globalnoj peremennoj."""
    out = {}
    for f in sorted(os.listdir(SRC)):
        if not f.endswith(u".gvl"):
            continue
        t = re.sub(u"\\(\\*.*?\\*\\)", u" ", io.open(os.path.join(SRC, f),
                                                    encoding=u"utf-8").read(), flags=re.S)
        for m in re.finditer(u"(?m)^\\s*(\\w+)\\s*:\\s*([A-Za-z0-9_\\[\\]\\. ]+?)\\s*;", t):
            out[m.group(1)] = m.group(2).strip()
    return out


CONV = re.compile(u"^(BOOL|BYTE|WORD|DWORD|INT|UINT|DINT|UDINT|USINT|SINT)_TO_"
                  u"(BOOL|BYTE|WORD|DWORD|INT|UINT|DINT|UDINT|USINT|SINT)$")


def main():
    g = gvl_types()
    sys.stdout.write(u"globalnyh peremennyh: %d\n\n" % len(g))

    # 1) vse vyzovy BOOL_TO_* -- provrit, chto na vhode dejstvitelno BOOL
    sys.stdout.write(u"=== bloki konvertacii BOOL_TO_xxx ===\n")
    for f in sorted(os.listdir(SRC)):
        if not f.endswith(u".plcopenxml"):
            continue
        t = io.open(os.path.join(SRC, f), encoding=u"utf-8").read()
        for m in re.finditer(u'<block localId="(\\d+)" typeName="(\\w+_TO_\\w+)"', t):
            bid, conv = m.group(1), m.group(2)
            if not CONV.match(conv):
                continue
            # naydem vhod etogo bloka
            seg = t[m.end():m.end() + 900]
            ref = re.search(u'<connection refLocalId="(\\d+)"', seg)
            src_id = ref.group(1) if ref else None
            src = u"?"
            if src_id:
                sm = re.search(u'<inVariable localId="%s".*?<expression>([^<]+)</expression>'
                               % src_id, t, re.S)
                if sm:
                    src = sm.group(1)
                else:
                    bm = re.search(u'<block localId="%s" typeName="(\\w+)"' % src_id, t)
                    src = u"<%s>" % bm.group(1) if bm else u"<blok %s>" % src_id
            tp = g.get(src, u"?")
            flag = u""
            if conv.startswith(u"BOOL_TO") and tp not in (u"BOOL", u"?"):
                flag = u"   <<< VHOD NE BOOL (%s)" % tp
            sys.stdout.write(u"  %-20s %s <- %-24s тип=%s%s\n"
                             % (f.replace(u".plcopenxml", u""), conv, src, tp, flag))

    # 2) gde v GVL ozhidayutsya BOOL, a ispolzuetsya BYTE i naoborot
    sys.stdout.write(u"\n=== peremennye, kotorye prinimayut BOOL i BYTE ===\n")
    for name in (u"Halted", u"F", u"F5", u"F3", u"Flag_C", u"Flag_N"):
        sys.stdout.write(u"  %-10s GVL tip = %s\n" % (name, g.get(name, u"NET")))


if __name__ == u"__main__":
    main()
