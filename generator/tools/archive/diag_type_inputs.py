# -*- coding: utf-8 -*-
u"""Diagnostika: nayti v shemah vhody BOOL tam, gde nuzhen BYTE/USINT.

ZAPUSKAT SISTEMNYM PYTHON 3.

ZADAChA. 16 oshibok "Nevozmozhno konvertirovat tip 'BOOL' v tip 'USINT'".
Nuzhno najti konkretnye mesta: kakoy blok zhdet USINT i chto v nego podayut.
Tip opredelyaem po obyavleniyam POU (VAR_INPUT/VAR_OUTPUT) i po tipam
standardnyh blokov.
"""
import io
import os
import re
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(os.path.dirname(HERE)), u"src")

# tipy vhodov standartnyh blokov IEC, kotorye my ispolzuem
KNOWN = {
    u"SHL": (u"USINT", u"USINT"),      # IN, N
    u"SHR": (u"USINT", u"USINT"),
    u"ADD": (u"ANY_NUM", u"ANY_NUM"),
    u"SUB": (u"ANY_NUM", u"ANY_NUM"),
    u"MUL": (u"ANY_NUM", u"ANY_NUM"),
    u"AND": (u"ANY_BIT", u"ANY_BIT"),
    u"OR": (u"ANY_BIT", u"ANY_BIT"),
    u"XOR": (u"ANY_BIT", u"ANY_BIT"),
    u"NOT": (u"ANY_BIT",),
    u"EQ": (u"ANY", u"ANY"),
    u"NE": (u"ANY", u"ANY"),
    u"GE": (u"ANY", u"ANY"),
    u"LE": (u"ANY", u"ANY"),
    u"GT": (u"ANY", u"ANY"),
    u"LT": (u"ANY", u"ANY"),
    u"SEL": (u"BOOL", u"ANY", u"ANY"),
}


def find_all(node, local):
    out = []
    for ch in node.iter():
        if isinstance(ch.tag, str) and (ch.tag == local or ch.tag.endswith(u"}" + local)):
            out.append(ch)
    return out


def pou_types(pou):
    u"""Imena -> tip dlya vseh obyavlennyh peremennyh POU."""
    out = {}
    for iface in find_all(pou, u"interface"):
        for v in find_all(iface, u"variable"):
            nm = v.get(u"name")
            tp = None
            for t in find_all(v, u"type"):
                for ch in list(t):
                    tag = ch.tag.split(u"}")[-1]
                    if tag == u"derived":
                        tp = ch.get(u"name")
                    elif tag == u"array":
                        tp = u"ARRAY"
                    else:
                        tp = tag
                break
            out[nm] = tp
    return out


def main():
    for f in sorted(os.listdir(SRC)):
        if not f.endswith(u".plcopenxml"):
            continue
        root = ET.parse(os.path.join(SRC, f)).getroot()
        for pou in find_all(root, u"pou"):
            name = pou.get(u"name")
            types = pou_types(pou)
            # sobiraem vse elementy tela: localId -> (vid, imya/tip)
            elems = {}
            for iv in find_all(pou, u"inVariable"):
                e = find_all(iv, u"expression")
                elems[iv.get(u"localId")] = (u"invar", u"".join(e[0].itertext()) if e else u"?")
            for ov in find_all(pou, u"outVariable"):
                e = find_all(ov, u"expression")
                elems[ov.get(u"localId")] = (u"outvar", u"".join(e[0].itertext()) if e else u"?")
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
                    return u"?"
                return types.get(val, u"?")

            bad = []
            for b in find_all(pou, u"block"):
                tn = b.get(u"typeName")
                want = KNOWN.get(tn)
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
                    if got in (u"?", u"") or exp in (u"ANY", u"ANY_BIT"):
                        continue
                    if exp == u"ANY_NUM" and got in (u"USINT", u"UINT", u"UDINT", u"BYTE",
                                                     u"WORD", u"DWORD", u"INT", u"SINT",
                                                     u"DINT", u"REAL", u"LREAL"):
                        continue
                    if exp == u"USINT" and got in (u"BOOL", u"INT", u"WORD", u"DINT", u"UDINT"):
                        bad.append((tn, exp, got, elems.get(ref, (u"?", u"?"))[1]))
                    if exp == u"BOOL" and got in (u"USINT", u"BYTE", u"UINT", u"WORD",
                                                  u"INT", u"DINT"):
                        bad.append((tn, exp, got, elems.get(ref, (u"?", u"?"))[1]))
            if bad:
                sys.stdout.write(u"=== %s ===\n" % name)
                for tn, exp, got, src in bad:
                    sys.stdout.write(u"   %-6s zhdet %-7s poluchaet %-7s ot %s\n"
                                     % (tn, exp, got, src))
    sys.stdout.write(u"gotovo\n")


if __name__ == u"__main__":
    main()
