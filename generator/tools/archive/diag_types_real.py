# -*- coding: utf-8 -*-
u"""N a S T O Ya Shch I J  vyvod tipov po sheme: vse vhody vseh blokov.

ZAPUSKAT SISTEMNYM PYTHON 3.
    python diag_types_real.py PLC_PRG

ChEM LUChShE predydushchih popytok. Ranshe tip istochnika opredelyalsya
grubo (i dlya GE/LT vozvrashchalsya "BITS", hotya eto BOOL) -- otsyuda byli
lozhnye srabatyvaniya. Zdes:
  * vhodnye tipy standartnyh blokov vzyaty iz spetsifikacii IEC (GE/LT/NE --
    BOOL, AND/OR/XOR -- po vhodam, SHL/SHR -- USINT i t.d.);
  * tip vyhoda FB beretsya iz ego <outputVars> po imeni pina;
  * posle sbora tipov proveryaem, chto na KAZhDOM vhode KAZhDOGO bloka tip
    sovmestim so ozhidaemym, i chto u vseh vhodov odnogo bloka tipy soglasovany.
"""
import io
import os
import re
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(ROOT, u"src")

#  (vyhod, [tipy vhodov])
STD = {
    u"SHL": (u"USINT", [u"USINT", u"USINT"]),
    u"SHR": (u"USINT", [u"USINT", u"USINT"]),
    u"ADD": (u"NUM", [u"NUM", u"NUM"]),
    u"SUB": (u"NUM", [u"NUM", u"NUM"]),
    u"MUL": (u"NUM", [u"NUM", u"NUM"]),
    u"DIV": (u"NUM", [u"NUM", u"NUM"]),
    u"AND": (u"BITS", [u"BITS", u"BITS"]),
    u"OR": (u"BITS", [u"BITS", u"BITS"]),
    u"XOR": (u"BITS", [u"BITS", u"BITS"]),
    u"NOT": (u"BITS", [u"BITS"]),
    u"EQ": (u"BOOL", [u"ANY", u"ANY"]),
    u"NE": (u"BOOL", [u"ANY", u"ANY"]),
    u"GE": (u"BOOL", [u"ANY", u"ANY"]),
    u"LE": (u"BOOL", [u"ANY", u"ANY"]),
    u"GT": (u"BOOL", [u"ANY", u"ANY"]),
    u"LT": (u"BOOL", [u"ANY", u"ANY"]),
    u"SEL": (u"SELT", [u"BOOL", u"ANY", u"ANY"]),
    u"MOVE": (u"ANY", [u"ANY"]),
}
CONV = re.compile(u"^(\\w+)_TO_(\\w+)$")
NUMT = set([u"BYTE", u"USINT", u"WORD", u"UINT", u"DWORD", u"UDINT",
            u"SINT", u"INT", u"DINT", u"REAL", u"LREAL"])


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


def compatible(expect, got):
    if got in (u"?", u"", u"#num"):
        return True
    if expect == u"ANY":
        return True
    if expect == u"NUM":
        return got in NUMT or got == u"NUM"
    if expect in (u"BITS", u"ANY_BIT"):
        return got in NUMT or got in (u"BITS", u"BOOL")
    if expect == u"BOOL":
        return got == u"BOOL" or got == u"SELT"
    if expect == u"SELT":
        return True
    if expect == u"USINT":
        return got in (u"USINT", u"BYTE", u"NUM", u"SELT", u"BITS")
    return got in (expect, u"NUM", u"ANY", u"SELT", u"BITS")


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else u"PLC_PRG"
    loc, fb_out, gvl = {}, {}, {}
    for f in sorted(os.listdir(SRC)):
        if not f.endswith(u".plcopenxml"):
            continue
        root = ET.parse(os.path.join(SRC, f)).getroot()
        for pou in find_all(root, u"pou"):
            nm = pou.get(u"name")
            mine, outs, ins = {}, [], []
            for iface in find_all(pou, u"interface"):
                for node in iface:
                    tag = node.tag.split(u"}")[-1]
                    for v in find_all(node, u"variable"):
                        mine[v.get(u"name")] = var_type(v)
                        if tag == u"outputVars":
                            outs.append((v.get(u"name"), var_type(v)))
                        if tag == u"inputVars":
                            ins.append((v.get(u"name"), var_type(v)))
            loc[nm] = mine
            fb_out[nm] = outs
            loc[nm + u":in"] = ins
    for f in sorted(os.listdir(SRC)):
        if not f.endswith(u".gvl"):
            continue
        t = re.sub(u"\\(\\*.*?\\*\\)", u" ", io.open(os.path.join(SRC, f),
                                                    encoding=u"utf-8").read(), flags=re.S)
        for m in re.finditer(u"(?m)^\\s*(\\w+)\\s*:\\s*([A-Za-z0-9_]+)", t):
            gvl[m.group(1)] = m.group(2).upper()

    root = ET.parse(os.path.join(SRC, target + u".plcopenxml")).getroot()
    pou = list(find_all(root, u"pou"))[0]
    mine = loc[target]

    elems = {}
    for iv in find_all(pou, u"inVariable"):
        for e in find_all(iv, u"expression"):
            elems[iv.get(u"localId")] = (u"invar", u"".join(e.itertext()))
    for b in find_all(pou, u"block"):
        elems[b.get(u"localId")] = (u"block", b.get(u"typeName"), b.get(u"instanceName"))

    def inst_type(inst):
        for k in elems.values():
            if k[0] == u"block" and k[2] == inst:
                return k[1]
        return None

    def tp(eid):
        k = elems.get(eid)
        if not k:
            return u"?"
        if k[0] == u"invar":
            val = k[1]
            if val in (u"TRUE", u"FALSE"):
                return u"BOOL"
            if re.match(u"^[0-9]+$", val) or val.startswith(u"16#"):
                return u"#num"
            if u"." in val:
                a, b = val.split(u".", 1)
                if a.startswith(u"GVL_"):
                    return gvl.get(b, u"?")
                tn = inst_type(a)
                if tn:
                    for nm, t2 in fb_out.get(tn, []):
                        if nm == b:
                            return t2
                return u"?"
            return mine.get(val, u"?")
        tn = k[1]
        if tn in STD:
            return STD[tn][0]
        m = CONV.match(tn or u"")
        if m:
            return m.group(2)
        return u"<FB>"

    sys.stdout.write(u"=== %s: proverka vhodov blokov ===\n" % target)
    bad = 0
    for b in find_all(pou, u"block"):
        tn = b.get(u"typeName")
        inst = b.get(u"instanceName")
        if tn in loc.get(tn + u":in", []) or True:
            pass
        if inst:
            want = [t for _, t in loc.get(tn + u":in", [])]
        elif tn in STD:
            want = STD[tn][1]
        else:
            m = CONV.match(tn or u"")
            want = [m.group(1)] if m else []
        got = []
        for var in find_all(b, u"variable"):
            ref = None
            for c in find_all(var, u"connection"):
                ref = c.get(u"refLocalId")
            got.append(tp(ref))
        for i in range(min(len(want), len(got))):
            if not compatible(want[i], got[i]):
                sys.stdout.write(u"  %-16s vhod %-2d (%s) <- %s   <<< NE SOVPADAET\n"
                                 % (tn, i + 1, want[i], got[i]))
                bad += 1
        # soglasovannost tipov mezhdu vhodami odnogo bloka
        types = set([g for g in got if g not in (u"?", u"#num")])
        if len(types) > 1 and not (tn in STD and tn in (u"SEL",)):
            sys.stdout.write(u"  %-16s vhody raznogo tipa: %s\n" % (tn, sorted(types)))
            bad += 1
    sys.stdout.write(u"\nnajdeno problem: %d\n" % bad)


if __name__ == u"__main__":
    main()
