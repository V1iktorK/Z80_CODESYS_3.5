# -*- coding: utf-8 -*-
u"""D i A G N O S T I K A: sverit tip kazhdogo priemnika v PLC_PRG s tem, chto prishlo.

ZAPUSKAT SISTEMNYM PYTHON 3.

ZADAChA. Ostaetsya 17 oshibok C32 v PLC_PRG, i nikak ne udastsya ih najti
glazami. Zdes schitaem vse svyazi "outVariable <- istochnik" i dlya kazhdoj
opredelyaem:
  * tip PRIEMNIKA (iz obyavlenij POU ili GVL);
  * tip ISTOCHNIKA (iz obyavlenij, iz tipa bloka ili iz tipa vyhoda FB).
I vyvodim tolko te, gde tipy yavno nesovmestimy.
"""
import io
import os
import re
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(ROOT, u"src")

STD = {
    u"SHL": u"USINT", u"SHR": u"USINT", u"ADD": u"ANY", u"SUB": u"ANY",
    u"MUL": u"ANY", u"AND": u"ANY_BIT", u"OR": u"ANY_BIT", u"XOR": u"ANY_BIT",
    u"NOT": u"ANY_BIT", u"EQ": u"BOOL", u"NE": u"BOOL", u"GE": u"BOOL",
    u"LE": u"BOOL", u"GT": u"BOOL", u"LT": u"BOOL", u"SEL": u"ANY",
    u"BYTE_TO_WORD": u"WORD", u"WORD_TO_BYTE": u"BYTE", u"INT_TO_WORD": u"WORD",
    u"WORD_TO_INT": u"INT", u"BOOL_TO_BYTE": u"BYTE", u"BYTE_TO_BOOL": u"BOOL",
    u"BYTE_TO_DWORD": u"DWORD", u"DWORD_TO_WORD": u"WORD",
    u"BYTE_TO_INT": u"INT", u"INT_TO_BYTE": u"BYTE", u"WORD_TO_DWORD": u"DWORD",
    u"BYTE_TO_USINT": u"USINT", u"USINT_TO_BYTE": u"BYTE",
}
FITS = {
    u"BOOL": set([u"BOOL"]),
    u"BYTE": set([u"BYTE"]),
    u"WORD": set([u"WORD"]),
    u"INT": set([u"INT"]),
    u"USINT": set([u"BYTE"]),
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
            return ch.get(u"name") if k == u"derived" else k
    return u"?"


def main():
    # 1) tipy vseh peremennyh vseh POU i vseh GVL
    loc, gvl = {}, {}
    fbins, fbouts = {}, {}
    for f in sorted(os.listdir(SRC)):
        if not f.endswith(u".plcopenxml"):
            continue
        root = ET.parse(os.path.join(SRC, f)).getroot()
        for pou in find_all(root, u"pou"):
            nm = pou.get(u"name")
            ins, outs, mine = [], [], {}
            for iface in find_all(pou, u"interface"):
                for node in iface:
                    tag = node.tag.split(u"}")[-1]
                    for v in find_all(node, u"variable"):
                        key = v.get(u"name")
                        mine[key] = var_type(v)
                        if tag == u"inputVars":
                            ins.append((key, var_type(v)))
                        elif tag == u"outputVars":
                            outs.append((key, var_type(v)))
            loc[nm] = mine
            fbins[nm] = ins
            fbouts[nm] = outs
        else:
            continue
    for f in sorted(os.listdir(SRC)):
        if not f.endswith(u".gvl"):
            continue
        t = re.sub(u"\\(\\*.*?\\*\\)", u" ", io.open(os.path.join(SRC, f),
                                                    encoding=u"utf-8").read(), flags=re.S)
        for m in re.finditer(u"(?m)^\\s*(\\w+)\\s*:\\s*([A-Za-z0-9_]+)", t):
            gvl[m.group(1)] = m.group(2).upper()

    target = sys.argv[1] if len(sys.argv) > 1 else u"PLC_PRG"
    root = ET.parse(os.path.join(SRC, target + u".plcopenxml")).getroot()
    pou = list(find_all(root, u"pou"))[0]
    mine = loc[target]

    elements = {}
    for iv in find_all(pou, u"inVariable"):
        for e in find_all(iv, u"expression"):
            elements[iv.get(u"localId")] = (u"invar", u"".join(e.itertext()))
    for b in find_all(pou, u"block"):
        inst = b.get(u"instanceName")
        elements[b.get(u"localId")] = (u"block", b.get(u"typeName"),
                                       u"fb_" + inst if inst else None)

    def src_type(eid):
        k = elements.get(eid)
        if not k:
            return u"?"
        if k[0] == u"invar":
            val = k[1]
            if val in (u"TRUE", u"FALSE"):
                return u"BOOL"
            if re.match(u"^[0-9]+$", val) or val.startswith(u"16#"):
                return u"#num"
            if val.startswith(u"u'"):
                return u"#num"
            if u"." in val:
                parts = val.split(u".")
                if len(parts) == 2 and parts[0].startswith(u"GVL_"):
                    return gvl.get(parts[1], u"?")
                return u"?"
            return mine.get(val, u"?")
        tn, inst = k[1], k[2]
        if tn in STD:
            return STD[tn]
        if tn in fbouts:
            # dlya FB nuzhen imenovanny vyhod -- ego ne znayem, no tip odin
            return u"<%s>" % tn
        return u"<%s>" % tn

    sys.stdout.write(u"=== %s: podozritelnye svyazi ===\n" % target)
    bad = 0
    for ov in find_all(pou, u"outVariable"):
        name = None
        for e in find_all(ov, u"expression"):
            name = u"".join(e.itertext())
        ref = None
        for c in find_all(ov, u"connection"):
            ref = c.get(u"refLocalId")
        if u"." in name:
            dst_t = gvl.get(name.split(u".")[1], u"?")
        else:
            dst_t = mine.get(name, u"?")
        got = src_type(ref)
        known = set(STD.values()) | set([u"BOOL", u"BYTE", u"WORD", u"INT", u"USINT"])
        if dst_t in FITS and got in known:
            if got not in FITS.get(dst_t, set()):
                sys.stdout.write(u"  %-28s (%s)  <-  %s   <<< NE SOVPADAET\n"
                                 % (name, dst_t, got))
                bad += 1
    sys.stdout.write(u"\nyavnyh nesootvetstvij: %d\n" % bad)


if __name__ == u"__main__":
    main()
