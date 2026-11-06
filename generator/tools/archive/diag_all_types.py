# -*- coding: utf-8 -*-
u"""Diagnostika: sverit tipy vseh vhodov blokov s obyavleniyami POU/FB.

ZAPUSKAT SISTEMNYM PYTHON 3.

ZADAChA. Kompilyator daet 36 oshibok C32 (konverziya tipov), no ponyat, gde
imenno, po soobshcheniyu nel'zya -- nomera strok ne ukazany. Zdes my sami
schitaem: dlya kazhdogo bloka v kazhdoj sheme sravnivaem tip kazhdogo vhoda
s tem, chto k nemu podklyucheno.

Tip vhoda FB berem iz ego zhe strukturnogo <interface> (inputVars po poryadku).
Tip istochnika -- iz obyavlenij POU, dlya blokov -- po tipu bloka.
"""
import io
import os
import re
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(os.path.dirname(HERE)), u"src")

# vhody standartnyh blokov IEC
STD = {
    u"SHL": [u"USINT", u"USINT"], u"SHR": [u"USINT", u"USINT"],
    u"ADD": [u"ANY_NUM", u"ANY_NUM"], u"SUB": [u"ANY_NUM", u"ANY_NUM"],
    u"MUL": [u"ANY_NUM", u"ANY_NUM"], u"DIV": [u"ANY_NUM", u"ANY_NUM"],
    u"AND": [u"ANY_BIT", u"ANY_BIT"], u"OR": [u"ANY_BIT", u"ANY_BIT"],
    u"XOR": [u"ANY_BIT", u"ANY_BIT"], u"NOT": [u"ANY_BIT"],
    u"EQ": [u"ANY", u"ANY"], u"NE": [u"ANY", u"ANY"],
    u"GE": [u"ANY", u"ANY"], u"LE": [u"ANY", u"ANY"],
    u"GT": [u"ANY", u"ANY"], u"LT": [u"ANY", u"ANY"],
    u"SEL": [u"BOOL", u"ANY", u"ANY"],
    u"MOVE": [u"ANY"],
}
CONV = re.compile(u"^(\\w+)_TO_(\\w+)$")

BITS = set([u"BOOL", u"BYTE", u"WORD", u"DWORD", u"USINT", u"UINT", u"UDINT",
            u"SINT", u"INT", u"DINT", u"LWORD", u"LINT", u"ULINT"])
NUM = set([u"BYTE", u"WORD", u"DWORD", u"USINT", u"UINT", u"UDINT", u"SINT",
           u"INT", u"DINT", u"REAL", u"LREAL"])
BOOLISH = set([u"BOOL"])


def find_all(node, local):
    out = []
    for ch in node.iter():
        if isinstance(ch.tag, str) and (ch.tag == local or ch.tag.endswith(u"}" + local)):
            out.append(ch)
    return out


def pou_input_types(pou):
    out = []
    for iface in find_all(pou, u"interface"):
        for node in iface:
            if node.tag.split(u"}")[-1] != u"inputVars":
                continue
            for v in find_all(node, u"variable"):
                tp = None
                for t in find_all(v, u"type"):
                    for ch in list(t):
                        tag = ch.tag.split(u"}")[-1]
                        tp = ch.get(u"name") if tag == u"derived" else (
                            u"ARRAY" if tag == u"array" else tag)
                    break
                out.append((v.get(u"name"), tp))
    return out


def main():
    # tipy vseh POU: imya -> spisok vhodov
    lib = {}
    allpou = {}
    for f in sorted(os.listdir(SRC)):
        if not f.endswith(u".plcopenxml"):
            continue
        root = ET.parse(os.path.join(SRC, f)).getroot()
        for pou in find_all(root, u"pou"):
            nm = pou.get(u"name")
            allpou[nm] = pou
            lib[nm] = [t for _, t in pou_input_types(pou)]

    total = 0
    for nm, pou in sorted(allpou.items()):
        loc = {}
        for iface in find_all(pou, u"interface"):
            for v in find_all(iface, u"variable"):
                tp = None
                for t in find_all(v, u"type"):
                    for ch in list(t):
                        tag = ch.tag.split(u"}")[-1]
                        tp = ch.get(u"name") if tag == u"derived" else (
                            u"ARRAY" if tag == u"array" else tag)
                    break
                loc[v.get(u"name")] = tp

        elems = {}
        for iv in find_all(pou, u"inVariable"):
            for e in find_all(iv, u"expression"):
                elems[iv.get(u"localId")] = (u"invar", u"".join(e.itertext()))
        for b in find_all(pou, u"block"):
            elems[b.get(u"localId")] = (u"block", b.get(u"typeName"))

        def tp_of(eid):
            k = elems.get(eid)
            if not k:
                return u"?"
            kind, val = k
            if kind == u"block":
                return u"<%s>" % val
            if u"." in val:
                return u"?gvl"
            if val in (u"TRUE", u"FALSE"):
                return u"BOOL"
            if re.match(u"^[0-9]+$", val):
                return u"#num"
            if val.startswith(u"16#"):
                return u"#num"
            if val.startswith(u"'") and val.endswith(u"'"):
                return u"#char"
            return loc.get(val, u"?")

        probs = []
        for b in find_all(pou, u"block"):
            tn = b.get(u"typeName")
            if tn in lib and tn != nm:
                want = lib[tn]
            elif tn in STD:
                want = STD[tn]
            else:
                m = CONV.match(tn or u"")
                want = [m.group(1)] if m else None
            if not want:
                continue
            for i, var in enumerate(find_all(b, u"variable")):
                if i >= len(want):
                    break
                ref = None
                for c in find_all(var, u"connection"):
                    ref = c.get(u"refLocalId")
                if not ref:
                    continue
                got = tp_of(ref)
                exp = want[i]
                if got in (u"?", u"?gvl", u"#num", u"#char", u""):
                    continue
                if exp in (u"ANY", u"ANY_NUM", u"ANY_BIT"):
                    if exp == u"ANY_NUM" and got not in NUM and got not in BITS:
                        probs.append((tn, i + 1, exp, got, elems.get(ref, (u"", u""))[1]))
                    continue
                if exp == u"USINT" and got == u"BOOL":
                    probs.append((tn, i + 1, exp, got, elems.get(ref, (u"", u""))[1]))
                if exp == u"BOOL" and got in (u"USINT", u"BYTE", u"UINT", u"WORD",
                                              u"INT", u"DINT", u"UDINT"):
                    probs.append((tn, i + 1, exp, got, elems.get(ref, (u"", u""))[1]))
                if exp in (u"BYTE", u"WORD", u"USINT") and got in BITS and got != exp:
                    probs.append((tn, i + 1, exp, got, elems.get(ref, (u"", u""))[1]))
        if probs:
            sys.stdout.write(u"=== %s ===\n" % nm)
            for tn, pin, exp, got, src in probs:
                total += 1
                sys.stdout.write(u"   %-16s vhod %-2d zhdet %-7s poluchaet %-7s ot %s\n"
                                 % (tn, pin, exp, got, src))
    sys.stdout.write(u"\nVSEGO nedopustimyh svyazey: %d\n" % total)


if __name__ == u"__main__":
    main()
