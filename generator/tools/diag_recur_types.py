# -*- coding: utf-8 -*-
u"""R e K U R S I V N A Ya  karta tipov shemy: nahodit vse nesovpadeniya.

ZAPUSKAT SISTEMNYM PYTHON 3.
    python diag_recur_types.py PLC_PRG

ChEM OTLIChAETSYa ot diag_dst_types.py. Tot analizator znal tip istochnika
tolko dlya invar i dlya standartnyh blokov. Zdes tip schitaetsya REKURSIVNO:
dlya bloka smotrim ego vhody, dlya FB -- vyhod po imeni pina. Tak vidny
nesootvetstviya, kotorye pryachutsya za cepochkami SEL/ADD/OR.
"""
import io
import os
import re
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(ROOT, u"src")

STD_OUT = {
    u"SHL": u"USINT", u"SHR": u"USINT", u"ADD": u"NUM", u"SUB": u"NUM",
    u"MUL": u"NUM", u"AND": u"BITS", u"OR": u"BITS", u"XOR": u"BITS",
    u"NOT": u"BITS", u"EQ": u"BOOL", u"NE": u"BOOL", u"GE": u"BOOL",
    u"LE": u"BOOL", u"GT": u"BOOL", u"LT": u"BOOL", u"SEL": u"SELT",
}
CONV = re.compile(u"^(\\w+)_TO_(\\w+)$")


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
            return ch.get(u"name") if k == u"derived" else k
    return u"?"


class Model(object):
    def __init__(self):
        self.loc = {}      # POU -> {imya: tip}
        self.fb_out = {}   # POU -> [(imya, tip)]
        self.gvl = {}
        self.build()

    def build(self):
        for f in sorted(os.listdir(SRC)):
            if not f.endswith(u".plcopenxml"):
                continue
            root = ET.parse(os.path.join(SRC, f)).getroot()
            for pou in find_all(root, u"pou"):
                nm = pou.get(u"name")
                mine, outs = {}, []
                for iface in find_all(pou, u"interface"):
                    for node in iface:
                        tag = node.tag.split(u"}")[-1]
                        for v in find_all(node, u"variable"):
                            mine[v.get(u"name")] = var_type(v)
                            if tag == u"outputVars":
                                outs.append((v.get(u"name"), var_type(v)))
                self.loc[nm] = mine
                self.fb_out[nm] = outs
        for f in sorted(os.listdir(SRC)):
            if not f.endswith(u".gvl"):
                continue
            t = re.sub(u"\\(\\*.*?\\*\\)", u" ", io.open(os.path.join(SRC, f),
                                                        encoding=u"utf-8").read(), flags=re.S)
            for m in re.finditer(u"(?m)^\\s*(\\w+)\\s*:\\s*([A-Za-z0-9_]+)", t):
                self.gvl[m.group(1)] = m.group(2).upper()


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else u"PLC_PRG"
    M = Model()
    root = ET.parse(os.path.join(SRC, target + u".plcopenxml")).getroot()
    pou = list(find_all(root, u"pou"))[0]
    mine = M.loc[target]

    elems = {}
    for iv in find_all(pou, u"inVariable"):
        for e in find_all(iv, u"expression"):
            elems[iv.get(u"localId")] = (u"invar", u"".join(e.itertext()))
    for b in find_all(pou, u"block"):
        tn = b.get(u"typeName")
        inst = b.get(u"instanceName")
        # sootvetstvie "ekzemplyar -> tip FB"
        elems[b.get(u"localId")] = (u"block", tn, inst)

    # kakie vyhody FB chitayutsya: invar s "fbXXX.PIN"
    def inst_of(tag):
        return tag

    cache = {}

    def tp(eid, pin=None, depth=0):
        if depth > 8:
            return u"?"
        key = (eid, pin)
        if key in cache:
            return cache[key]
        cache[key] = u"?"          # zashchita ot ciklov
        res = u"?"
        k = elems.get(eid)
        if k:
            if k[0] == u"invar":
                val = k[1]
                if val in (u"TRUE", u"FALSE"):
                    res = u"BOOL"
                elif re.match(u"^[0-9]+$", val) or val.startswith(u"16#"):
                    res = u"NUM"
                elif val.startswith(u"u'") or val.startswith(u"'"):
                    res = u"NUM"
                elif u"." in val:
                    a, b = val.split(u".", 1)
                    if a.startswith(u"GVL_"):
                        res = M.gvl.get(b, u"?")
                    else:
                        # ssylka na vyhod ekzemplyara: ishem tip FB po imeni
                        fbname = None
                        for t2 in elems.values():
                            if t2[0] == u"block" and t2[2] == a:
                                fbname = t2[1]
                        if fbname:
                            for nm, t3 in M.fb_out.get(fbname, []):
                                if nm == b:
                                    res = t3
                                    break
                else:
                    res = mine.get(val, u"?")
            else:
                tn = k[1]
                if tn in STD_OUT:
                    res = STD_OUT[tn]
                else:
                    m = CONV.match(tn or u"")
                    if m:
                        res = m.group(2)
        cache[key] = res
        return res

    FITS = {u"BOOL": set([u"BOOL"]), u"BYTE": set([u"BYTE"]),
            u"WORD": set([u"WORD"]), u"INT": set([u"INT"])}
    sys.stdout.write(u"=== %s ===\n" % target)
    bad = 0
    for ov in find_all(pou, u"outVariable"):
        name = u""
        for e in find_all(ov, u"expression"):
            name = u"".join(e.itertext())
        ref = None
        for c in find_all(ov, u"connection"):
            ref = c.get(u"refLocalId")
        dst = M.gvl.get(name.split(u".")[1]) if u"." in name else mine.get(name)
        got = tp(ref)
        if dst in FITS and got in FITS and got not in FITS[dst]:
            sys.stdout.write(u"  %-26s (%s) <- %s   <<< NE SOVPADAET\n" % (name, dst, got))
            bad += 1
        elif dst in FITS and got in (u"NUM", u"BITS", u"SELT", u"ANY"):
            sys.stdout.write(u"  %-26s (%s) <- %s   (obobshchennyy tip)\n" % (name, dst, got))
            bad += 1
    sys.stdout.write(u"\npodozritelnyh svyazey: %d\n" % bad)


if __name__ == u"__main__":
    main()
