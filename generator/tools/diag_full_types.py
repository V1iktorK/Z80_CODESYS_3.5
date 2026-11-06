# -*- coding: utf-8 -*-
u"""Polnaya karta tipov svyazej v PLC_PRG: kto na chto podklyuchen.

ZAPUSKAT SISTEMNYM PYTHON 3.

ZADAChA. 18 oshibok C32 imenno v PLC_PRG. Nuzhno uvidet KAZhDUYU svyaz s
ee tipom, chtoby glazami najti nesootvetstvie, kotoroe avtomaticheskij
analiz propuskaet.
"""
import os
import re
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(ROOT, u"src")

# tipy vyhodov standartnyh blokov (po vhodam)
STD_OUT = {
    u"SHL": u"USINT", u"SHR": u"USINT", u"ADD": u"ANY", u"SUB": u"ANY",
    u"MUL": u"ANY", u"AND": u"ANY_BIT", u"OR": u"ANY_BIT", u"XOR": u"ANY_BIT",
    u"NOT": u"ANY_BIT", u"EQ": u"BOOL", u"NE": u"BOOL", u"GE": u"BOOL",
    u"LE": u"BOOL", u"GT": u"BOOL", u"LT": u"BOOL", u"SEL": u"ANY",
    u"BYTE_TO_WORD": u"WORD", u"WORD_TO_BYTE": u"BYTE", u"INT_TO_WORD": u"WORD",
    u"WORD_TO_INT": u"INT", u"BOOL_TO_BYTE": u"BYTE", u"BYTE_TO_BOOL": u"BOOL",
    u"BYTE_TO_DWORD": u"DWORD", u"DWORD_TO_WORD": u"WORD",
}


def find_all(node, local):
    out = []
    for ch in node.iter():
        if isinstance(ch.tag, str) and (ch.tag == local or ch.tag.endswith(u"}" + local)):
            out.append(ch)
    return out


def var_type(v):
    for t in find_all(v, u"type"):
        for ch in list(t):
            k = ch.tag.split(u"}")[-1]
            if k == u"derived":
                return ch.get(u"name")
            if k == u"array":
                return u"ARRAY"
            return k
    return u"?"


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else u"PLC_PRG"
    path = os.path.join(SRC, target + u".plcopenxml")
    root = ET.parse(path).getroot()
    pou = None
    for p in find_all(root, u"pou"):
        pou = p
    loc = {}
    for iface in find_all(pou, u"interface"):
        for v in find_all(iface, u"variable"):
            loc[v.get(u"name")] = var_type(v)

    # tela vseh POU -- dlya tipov vhodov nashih FB
    fb_in = {}
    fb_out = {}
    for f in os.listdir(SRC):
        if not f.endswith(u".plcopenxml"):
            continue
        r2 = ET.parse(os.path.join(SRC, f)).getroot()
        for p2 in find_all(r2, u"pou"):
            nm = p2.get(u"name")
            ins, outs = [], []
            for iface in find_all(p2, u"interface"):
                for node in iface:
                    tag = node.tag.split(u"}")[-1]
                    for v in find_all(node, u"variable"):
                        if tag == u"inputVars":
                            ins.append((v.get(u"name"), var_type(v)))
                        elif tag == u"outputVars":
                            outs.append((v.get(u"name"), var_type(v)))
            fb_in[nm] = ins
            fb_out[nm] = outs

    elems = {}
    for iv in find_all(pou, u"inVariable"):
        for e in find_all(iv, u"expression"):
            elems[iv.get(u"localId")] = (u"invar", u"".join(e.itertext()))
    for b in find_all(pou, u"block"):
        elems[b.get(u"localId")] = (u"block", b.get(u"typeName") + (
            u"/" + b.get(u"instanceName") if b.get(u"instanceName") else u""))

    def tp(eid, pin=None):
        k = elems.get(eid)
        if not k:
            return u"?"
        kind, val = k
        if kind == u"invar":
            if u"." in val:
                parts = val.split(u".")
                if parts[0] in (u"fbRFRd", u"fbMem", u"fbRF", u"fbALU", u"fbPC"):
                    return u"?"                       # chlen ekzemplyara
                return u"?gvl"
            if val in (u"TRUE", u"FALSE"):
                return u"BOOL"
            if re.match(u"^[0-9]+$", val) or val.startswith(u"16#"):
                return u"#num"
            return loc.get(val, u"?")
        tn, inst = val.split(u"/")[0], val.split(u"/")[-1]
        if tn in STD_OUT:
            return STD_OUT[tn]
        if tn in fb_out:
            for n2, t2 in fb_out[tn]:
                if pin and n2 == pin:
                    return t2
            return u"<%s>" % tn
        return u"<%s>" % tn

    sys.stdout.write(u"=== %s: vse vyhody (outVariable) ===\n" % target)
    for ov in find_all(pou, u"outVariable"):
        for e in find_all(ov, u"expression"):
            name = u"".join(e.itertext())
        ref = None
        for c in find_all(ov, u"connection"):
            ref = c.get(u"refLocalId")
        dst = loc.get(name, u"?gvl" if u"." in name else u"?")
        sys.stdout.write(u"  %-28s (%s)  <-  %s\n" % (name, dst, tp(ref)))

    sys.stdout.write(u"\n=== %s: vhody blokov ===\n" % target)
    for b in find_all(pou, u"block"):
        tn = b.get(u"typeName")
        want = fb_in.get(tn)
        cnt = 0
        for var in find_all(b, u"variable"):
            pin = var.get(u"formalParameter")
            ref = None
            for c in find_all(var, u"connection"):
                ref = c.get(u"refLocalId")
            exp = u"?"
            if want and cnt < len(want):
                exp = want[cnt][1]
            sys.stdout.write(u"  %-16s %-12s (%s) <- %s\n" % (tn, pin, exp, tp(ref, pin)))
            cnt += 1


if __name__ == u"__main__":
    main()
