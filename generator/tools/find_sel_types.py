# -*- coding: utf-8 -*-
u"""P O I S K  s m e sh a n n y h  t i p o v  v  c e p o ch k a h  SEL.

Z A Ch E M. CODESYS soobshchaet pary
    C32: Nevozmozhno konvertirovat tip 'BOOL' v tip 'USINT'
    C32: Nevozmozhno konvertirovat tip 'USINT' v tip 'BOOL'
bez imeni POU i nomera seti. Prichina -- obobshchennyj blok SEL: ego tip
vyvoditsya po vetkam IN0/IN1, i esli v odnoj cepochke okazhutsya BYTE
i USINT (naprimer, posle BOOL_TO_BYTE) ili BYTE i neyavnyj literal,
CODESYS ne mozhet ih soglasovat.

Ch T O  D E L A E M. Po sgenerirovannomu XML kazhdogo POU:
  * dlya kazhdogo bloka SEL nahodim istochniki vhodov In2 (IN0) i In3 (IN1);
  * opredelyaem ih tip:
      - peremennaya POU / vyrazhenie GVL -- tip iz obyavleniya;
      - literal -- esli tip yavno ukazan (BYTE#...), berem ego; esli net,
        stavim "?" -- eto i est potencialnaya problema;
      - blok-konversiya X_TO_Y -- tip Y;
      - AND/OR/XOR/NOT/GT/LT/GE/LE/EQ/NE -- BOOL;
      - SHL/SHR/ADD/SUB/MUL/DIV -- "?" (obobshchennye, tip ne opredelit);
      - SEL -- "?" (sama cepochka);
  * sravnivaem tipy vetok odnogo SEL i tip peremennoy, kotoruyu on pitayet.

V Y V O D: spisok SEL, gde tipy vetok ne sovpadayut ili ne opredeleny.

ZAPUSK: python generator\tools\find_sel_types.py
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(ROOT, u"src")

CONV = re.compile(u"^([A-Z][A-Z0-9]*)_TO_([A-Z][A-Z0-9]*)$")
BOOLBLK = (u"AND", u"OR", u"XOR", u"NOT", u"GT", u"LT", u"GE", u"LE",
           u"EQ", u"NE")
GENERIC = (u"SHL", u"SHR", u"ADD", u"SUB", u"MUL", u"DIV", u"MOD", u"SEL",
           u"MUX", u"LIMIT", u"MAX", u"MIN", u"ABS", u"TRUNC")


def unesc(t):
    return (t.replace(u"&#xA;", u"\n").replace(u"&quot;", u'"')
             .replace(u"&lt;", u"<").replace(u"&gt;", u">").replace(u"&amp;", u"&"))


def literals_type(expr):
    u"""Tip yavno tipizirovannogo literala: BYTE#16#00 -> BYTE."""
    m = re.match(u"^([A-Z][A-Z0-9]*)#", expr.strip())
    return m.group(1) if m else None


def collect(text):
    u"""Sobrat: obyavleniya, istochniki, bloki."""
    decl = {}
    for m in re.finditer(u'<variable name="(\\w+)">\\s*<type>\\s*<(\\w+)\\s*/>', text):
        decl[m.group(1)] = m.group(2)
    for m in re.finditer(u'<variable name="(\\w+)">\\s*<type>\\s*'
                         u'<derived name="(\\w+)"', text):
        decl[m.group(1)] = m.group(2)
    src = {}
    for m in re.finditer(u'<inVariable localId="(\\d+)"[^>]*>(.*?)</inVariable>',
                         text, re.S):
        e = re.search(u"<expression>([^<]*)</expression>", m.group(2))
        src[m.group(1)] = (u"in", unesc(e.group(1)) if e else u"")
    for m in re.finditer(u'<outVariable localId="(\\d+)"[^>]*>(.*?)</outVariable>',
                         text, re.S):
        e = re.search(u"<expression>([^<]*)</expression>", m.group(2))
        src[m.group(1)] = (u"out", unesc(e.group(1)) if e else u"")
    for m in re.finditer(u'<block localId="(\\d+)" typeName="(\\w+)"', text):
        src[m.group(1)] = (u"blk", m.group(2))
    return decl, src


def type_of(lid, decl, src, depth=0):
    if depth > 8:
        return u"?"
    k = src.get(lid)
    if k is None:
        return u"?"
    what, val = k
    if what in (u"in", u"out"):
        v = val.strip()
        lit = literals_type(v)
        if lit:
            return lit
        #  pryamoj tip iz obyavleniya
        if v in decl:
            return decl[v]
        #  GVL.imya -- tip uznaem tolko esli imya obyavleno (chasto net)
        m = re.match(u"^([A-Z][A-Z0-9_]*)\\.(\\w+)(?:\\[.*\\])?$", v)
        if m:
            return u"GVL"
        if re.match(u"^\\d+$", v) or v.startswith(u"16#"):
            return u"?LIT"
        if v in (u"TRUE", u"FALSE"):
            return u"BOOL"
        return u"?"
    #  blok
    c = CONV.match(val)
    if c:
        return c.group(2)
    if val in BOOLBLK:
        return u"BOOL"
    return u"?"


def analyse(name, text):
    decl, src = collect(text)
    blocks = list(re.finditer(u'<block localId="(\\d+)" typeName="(\\w+)"', text))
    problems = []
    for idx, m in enumerate(blocks):
        if m.group(2) != u"SEL":
            continue
        bid = m.group(1)
        end = blocks[idx + 1].start() if idx + 1 < len(blocks) else len(text)
        seg = text[m.start():end]
        pins = {}
        for pm in re.finditer(u'<variable formalParameter="([^"]*)">\\s*'
                              u'<connectionPointIn>(.*?)</connectionPointIn>',
                              seg, re.S):
            ref = re.search(u'<connection refLocalId="(\\d+)"', pm.group(2))
            if ref:
                pins[pm.group(1).upper()] = ref.group(1)
        #  u CODESYS vhody nazyvayutsya In1(In0=G), In2, In3; u nas -- G/IN0/IN1
        g = pins.get(u"G") or pins.get(u"IN1")
        i0 = pins.get(u"IN0") or pins.get(u"IN2")
        i1 = pins.get(u"IN1") if pins.get(u"IN0") else pins.get(u"IN3")
        tg = type_of(g, decl, src) if g else u"?"
        t0 = type_of(i0, decl, src) if i0 else u"?"
        t1 = type_of(i1, decl, src) if i1 else u"?"
        #  kuda idet vyhod
        tgt = u"?"
        for om in re.finditer(u'<outVariable localId="(\\d+)"[^>]*>(.*?)'
                              u'</outVariable>', text, re.S):
            if (u'refLocalId="%s"' % bid) in om.group(2):
                e = re.search(u"<expression>([^<]*)</expression>", om.group(2))
                if e:
                    tgt = unesc(e.group(1))
                break
        tt = decl.get(tgt, u"?")
        #  ocenka
        notes = []
        if tg not in (u"BOOL", u"?"):
            notes.append(u"uslovie tipa %s" % tg)
        for nm, tv in ((u"IN0", t0), (u"IN1", t1)):
            if tv == u"?LIT":
                notes.append(u"%s -- literal bez tipa" % nm)
        known = [x for x in (t0, t1) if x not in (u"?", u"GVL", u"?LIT")]
        if len(set(known)) > 1:
            notes.append(u"vetki raznogo tipa: %s" % known)
        if notes:
            problems.append(u"%s: SEL %s -> %s (%s) : %s"
                            % (name, bid, tgt, tt, u"; ".join(notes)))
    return problems


def main():
    try:
        sys.stdout.reconfigure(encoding=u"utf-8", errors=u"replace")
    except Exception:                                          # noqa: BLE001
        pass
    sys.stdout.write(u"=== find_sel_types ===\n")
    total = 0
    for f in sorted(os.listdir(SRC)):
        if not f.endswith(u".plcopenxml"):
            continue
        text = io.open(os.path.join(SRC, f), encoding=u"utf-8").read()
        if u"<FBD>" not in text:
            continue
        probs = analyse(f[:-len(u".plcopenxml")], text)
        for p in probs:
            sys.stdout.write(u"  %s\n" % p)
        total += len(probs)
    sys.stdout.write(u"problemnyh SEL: %d\n" % total)
    return 1 if total else 0


if __name__ == u"__main__":
    sys.exit(main())
