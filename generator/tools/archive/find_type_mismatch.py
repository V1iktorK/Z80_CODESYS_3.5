# -*- coding: utf-8 -*-
u"""P O I S K  m e s t, gde BOOL podayotsya tuda, gde nuzhen BYTE.

Z A Ch E M. Kompilyator soobshchaet po parе na kazhdyj sluchaj:
    C32: Nevozmozhno konvertirovat tip 'BOOL' v tip 'USINT'
    C32: Nevozmozhno konvertirovat tip 'USINT' v tip 'BOOL'
Ni imeni POU, ni nomera seti on ne ukazyvaet. Poshuk "na glaz" po 24 shemam
uzhe odin raz zanyal chas i ne dal rezul tata, poetomu ishchem programmno.

Ch T O  D E L A E M. Berem sgenerirovannyj XML kazhdogo POU. Dlya kazhdogo
bloka vyyasnyaem, chto podano na ego vhody, i kakogo tipa etot signal:
  * vhodnaya peremennaya -- tip iz obyavleniya POU;
  * vyhod drugogo bloka -- tip schitaem po pravilam:
      - blok-konversiya X_TO_Y  -> Y;
      - SET/RESET i prochie s BOOL -> BOOL;
      - AND/OR/NOT/XOR/GT/LT/GE/LE/EQ/NE -> BOOL;
      - SEL/MUX -> tip vetki IN0, esli ee udalos opredelit;
      - ADD/SUB/SHL/SHR i prochie -- ANY, tip neizvesten (NE tronem).
Zatem sravnivaem s tem, chto zhdet poluchatel -- no poluchatelya tip my
znaem tolko dlya peremennyh (iz obyavleniya). Poetomu ishchem uzhe:
  1) BOOL podan v blok-konversiyu, kotoraya nachinaetsya s BYTE/WORD/DWORD
     (naprimer BYTE_TO_WORD) -- eto tochno oshibka;
  2) BYTE/WORD podan v BOOL_TO_*;
  3) BOOL podan v vyhodnuyu peremennuyu tipa BYTE ili WORD.

ZAPUSK: python generator\tools\find_type_mismatch.py
Kod vozvrata: 0 -- nichego ne najdeno, 1 -- est podozreniya.
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(ROOT, u"src")

NUM = (u"BYTE", u"WORD", u"DWORD", u"SINT", u"USINT", u"INT", u"UINT",
       u"DINT", u"UDINT", u"LINT", u"ULINT", u"REAL", u"LREAL")
BOOLISH = (u"AND", u"OR", u"XOR", u"NOT", u"GT", u"LT", u"GE", u"LE",
           u"EQ", u"NE", u"RS", u"SR")


def xml_unescape(t):
    return (t.replace(u"&#xA;", u"\n").replace(u"&quot;", u'"')
             .replace(u"&lt;", u"<").replace(u"&gt;", u">").replace(u"&amp;", u"&"))


def declarations(text):
    u"""Imya -> tip dlya vseh peremennyh POU."""
    out = {}
    for m in re.finditer(u'<variable name="(\\w+)">\\s*<type>\\s*<(\\w+)\\s*/>', text):
        out[m.group(1)] = m.group(2)
    for m in re.finditer(u'<variable name="(\\w+)">\\s*<type>\\s*'
                         u'<derived name="(\\w+)"', text):
        out[m.group(1)] = m.group(2)
    return out


def analyse(path, name):
    t = io.open(path, encoding=u"utf-8").read()
    decl = declarations(t)
    #  elementy: localId -> ('invar'|'outvar'|'block', znachenie)
    kind = {}
    for m in re.finditer(u'<inVariable localId="(\\d+)"[^>]*>(.*?)</inVariable>',
                         t, re.S):
        e = re.search(u"<expression>([^<]*)</expression>", m.group(2))
        kind[m.group(1)] = (u"invar", xml_unescape(e.group(1)) if e else u"")
    for m in re.finditer(u'<outVariable localId="(\\d+)"[^>]*>(.*?)</outVariable>',
                         t, re.S):
        e = re.search(u"<expression>([^<]*)</expression>", m.group(2))
        kind[m.group(1)] = (u"outvar", xml_unescape(e.group(1)) if e else u"")
    for m in re.finditer(u'<block localId="(\\d+)" typeName="(\\w+)"', t):
        kind[m.group(1)] = (u"block", m.group(2))

    def src_type(lid, depth=0):
        k = kind.get(lid)
        if k is None or depth > 6:
            return None
        what, val = k
        if what == u"invar":
            return decl.get(val)
        if what == u"outvar":
            return decl.get(val)
        #  blok
        if u"_TO_" in val:
            return val.split(u"_TO_")[-1]
        if val in BOOLISH:
            return u"BOOL"
        return None

    bad = []
    #  kazhdyj vhod kazhdogo bloka
    for m in re.finditer(u'<block localId="(\\d+)" typeName="(\\w+)"', t):
        bid, btyp = m.group(1), m.group(2)
        seg = t[m.end():m.end() + 4000]
        #  do nachala sleduyushchego bloka
        nxt = re.search(r'<block localId="', seg)
        if nxt:
            seg = seg[:nxt.start()]
        for pin in re.finditer(u'<variable formalParameter="([^"]*)">\\s*'
                               u'<connectionPointIn>(.*?)</connectionPointIn>',
                               seg, re.S):
            pname, body = pin.group(1), pin.group(2)
            ref = re.search(u'<connection refLocalId="(\\d+)"', body)
            if not ref:
                continue
            st = src_type(ref.group(1))
            if st is None:
                continue
            #  1) BOOL v chislovuyu konversiyu
            if u"_TO_" in btyp:
                a, b = btyp.split(u"_TO_")[0], btyp.split(u"_TO_")[-1]
                if st == u"BOOL" and a != u"BOOL":
                    bad.append(u"%s: blok %s (%s), vhod %s poluchaet BOOL, "
                               u"a nuzhen %s" % (name, btyp, bid, pname, a))
                if st != u"BOOL" and a == u"BOOL":
                    bad.append(u"%s: blok %s (%s), vhod %s poluchaet %s, "
                               u"a nuzhen BOOL" % (name, btyp, bid, pname, st))
            #  2) BOOL v blocheskuyu operaciyu -- normalno, propuskaem
        #  3) blok pitayot VYHODNUYu peremennuyu
        after = t[t.find(u'</block>', t.find(u'<block localId="%s"' % bid)):] if False else u""
    return bad


def outputs_check(path, name):
    u"""Vyhod bloka pitayot peremennuyu: sravnit tip bloka i peremennoj."""
    t = io.open(path, encoding=u"utf-8").read()
    decl = declarations(t)
    kind = {}
    for m in re.finditer(u'<outVariable localId="(\\d+)"[^>]*>(.*?)</outVariable>',
                         t, re.S):
        e = re.search(u"<expression>([^<]*)</expression>", m.group(2))
        kind[m.group(1)] = xml_unescape(e.group(1)) if e else u""
    bad = []
    for m in re.finditer(u'<outVariable localId="(\\d+)"[^>]*>(.*?)</outVariable>',
                         t, re.S):
        dst = kind.get(m.group(1))
        dt = decl.get(dst)
        if dt is None:
            continue
        body = m.group(2)
        ref = re.search(u'<connection refLocalId="(\\d+)"', body)
        if not ref:
            continue
        #  chto eto za istochnik
        src = re.search(u'<block localId="%s" typeName="(\\w+)"' % ref.group(1), t)
        if not src:
            continue
        btyp = src.group(1)
        st = None
        if u"_TO_" in btyp:
            st = btyp.split(u"_TO_")[-1]
        elif btyp in BOOLISH:
            st = u"BOOL"
        if st is None:
            continue
        if st != dt and dt in (u"BOOL", u"BYTE", u"WORD"):
            bad.append(u"%s: vyhod bloka %s -> peremennaya %s tipa %s"
                       % (name, btyp, dst, dt))
    return bad


def main():
    try:
        sys.stdout.reconfigure(encoding=u"utf-8", errors=u"replace")
    except Exception:                                          # noqa: BLE001
        pass
    sys.stdout.write(u"=== find_type_mismatch ===\n")
    total = 0
    for f in sorted(os.listdir(SRC)):
        if not f.endswith(u".plcopenxml"):
            continue
        p = os.path.join(SRC, f)
        nm = f[:-len(u".plcopenxml")]
        for b in analyse(p, nm) + outputs_check(p, nm):
            sys.stdout.write(u"  %s\n" % b)
            total += 1
    sys.stdout.write(u"podozrenij: %d\n" % total)
    return 1 if total else 0


if __name__ == u"__main__":
    sys.exit(main())
