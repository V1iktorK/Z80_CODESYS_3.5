# -*- coding: utf-8 -*-
u"""Diagnostika: sverit POZICII i TIPY vhodov u vyzovov nashih FB.

ZAPUSKAT SISTEMNYM PYTHON 3.

ZADAChA. Kompilyator daet 36 oshibok C32 (konverziya tipov) bez nomerov
strok, i moy prosmotr svyazey ih ne nahodit. Prichina mozhet byt v tom, chto
pri vyzove FB poryadok vhodov v sheme NE SOVPADAET s poryadkom obyavleniya
VAR_INPUT: CODESYS sopostavlyaet po pozicii (tak rabotaet import PLCopenXML),
i znacheniya popadayut ne na svoi mesta -- naprimer WORD okazyvaetsya tam,
gde ozhidaetsya BOOL.

Zdes my dlya kazhdogo bloka s typeName iz nashego proekta sravnivaem:
  * spisok vhodov v sheme (po poryadku),
  * spisok VAR_INPUT v obyavlenii etogo FB (po poryadku),
i soobshchaem o rassozhdenii.
"""
import os
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(os.path.dirname(HERE)), u"src")


def find_all(node, local):
    out = []
    for ch in node.iter():
        if isinstance(ch.tag, str) and (ch.tag == local or ch.tag.endswith(u"}" + local)):
            out.append(ch)
    return out


def iface_vars(pou, tag):
    res = []
    for iface in find_all(pou, u"interface"):
        for node in iface:
            if node.tag.split(u"}")[-1] != tag:
                continue
            for v in find_all(node, u"variable"):
                tp = None
                for t in find_all(v, u"type"):
                    for ch in list(t):
                        k = ch.tag.split(u"}")[-1]
                        tp = ch.get(u"name") if k == u"derived" else (
                            u"ARRAY" if k == u"array" else k)
                    break
                res.append((v.get(u"name"), tp))
    return res


def main():
    pous = {}
    for f in sorted(os.listdir(SRC)):
        if not f.endswith(u".plcopenxml"):
            continue
        root = ET.parse(os.path.join(SRC, f)).getroot()
        for pou in find_all(root, u"pou"):
            pous[pou.get(u"name")] = pou

    total = 0
    for nm, pou in sorted(pous.items()):
        loc = dict(iface_vars(pou, u"localVars") + iface_vars(pou, u"inputVars")
                   + iface_vars(pou, u"outputVars"))
        elems = {}
        for iv in find_all(pou, u"inVariable"):
            for e in find_all(iv, u"expression"):
                elems[iv.get(u"localId")] = u"".join(e.itertext())
        for b in find_all(pou, u"block"):
            elems[b.get(u"localId")] = u"<" + (b.get(u"typeName") or u"") + u">"

        for b in find_all(pou, u"block"):
            tn = b.get(u"typeName")
            if tn not in pous or tn == nm:
                continue
            want = iface_vars(pous[tn], u"inputVars")
            got = []
            for var in find_all(b, u"variable"):
                pin = var.get(u"formalParameter")
                ref = None
                for c in find_all(var, u"connection"):
                    ref = c.get(u"refLocalId")
                got.append((pin, elems.get(ref, u"?")))
            if len(want) != len(got):
                sys.stdout.write(u"!!! %s: vyzov %s -- vhodov v sheme %d, "
                                 u"v obyavlenii %d\n" % (nm, tn, len(got), len(want)))
            for i in range(min(len(want), len(got))):
                wn, wt = want[i]
                gp, gs = got[i]
                if wn != gp:
                    total += 1
                    sys.stdout.write(u"%-20s %-16s poziciya %2d: v sheme '%s' (%s), "
                                     u"v obyavlenii '%s' (%s)\n"
                                     % (nm, tn, i + 1, gp, gs, wn, wt))
    sys.stdout.write(u"\nVSEGO rassozhdenij poziciy: %d\n" % total)


if __name__ == u"__main__":
    main()
