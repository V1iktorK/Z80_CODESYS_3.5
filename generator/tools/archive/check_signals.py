# -*- coding: utf-8 -*-
u"""Proverka: vse li signaly shem ob''yavleny v interfejse POU.

ZAPUSKAT SISTEMNYM PYTHON 3 (ne IronPython).

ZADAChA. Kompilyator daet "C77: Neizvestnyy tip: 'Add_Lo'" i t.p. Prichina:
v FBD-sheme est outVariable s imenem vnutrennego signala, no etogo imeni net
ni v VAR_INPUT, ni v VAR_OUTPUT, ni v VAR. Dlya CODESYS takoj "signal" --
prosto neizvestnoe imya, i on schitaet ego tipom.

Eto tot zhe klass oshibki, chto i neobyavlennye ekzemplyary FB: shema
ssylaetsya na imya, kotorogo v obyavleniyah net. Poetomu proverka nuzhna
avtomaticheskaya, a ne po soobshcheniyam kompilyatora.

PRAVILA PROVERKI:
  * berem vse <expression>NAME</expression> iz tela POU;
  * propuskaem literaly (FALSE, TRUE, chisla), vyrazheniya s tochkami i
    operatorami, i imena s prefiksom GVL_ (globalnye peremennye);
  * vse ostalnoe dolzhno byt obyavleno v interfejse POU.

Kod vozvratа: 0 -- chisto, 1 -- est nedoopredelennye signaly.
"""
import os
import re
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(os.path.dirname(HERE)), u"src")

IDENT = re.compile(u"^[A-Za-z_][A-Za-z0-9_]*$")
SKIP = set([u"TRUE", u"FALSE", u"NULL"])


def find_all(node, local):
    out = []
    for ch in node.iter():
        if isinstance(ch.tag, str) and (ch.tag == local or ch.tag.endswith(u"}" + local)):
            out.append(ch)
    return out


def check_pou(pou, gvls):
    name = pou.get(u"name")
    ifaces = find_all(pou, u"interface")
    declared = set()
    if ifaces:
        for v in find_all(ifaces[0], u"variable"):
            declared.add(v.get(u"name"))
    # lokalnye FB-ekzemplyary tozhe obyavleny -- ih uzhe proveryaet
    # check_fb_instances.py, zdes nas interesuyut imena-signaly
    used = []
    for x in find_all(pou, u"expression"):
        txt = (x.text or u"").strip()
        if not IDENT.match(txt):
            continue
        if txt in SKIP or txt.startswith(u"GVL_"):
            continue
        used.append(txt)
    undeclared = []
    for u_ in used:
        if u_ not in declared and u_ not in undeclared:
            undeclared.append(u_)
    return name, undeclared


def main():
    # imena vseh globalnyh peremennyh
    gvls = set()
    for f in os.listdir(SRC):
        if f.endswith(u".gvl"):
            t = open(os.path.join(SRC, f), encoding=u"utf-8").read()
            for m in re.finditer(u"(?m)^\\s*(\\w+)\\s*:", t):
                gvls.add(m.group(1))
    bad = 0
    total = 0
    for f in sorted(os.listdir(SRC)):
        if not f.endswith(u".plcopenxml"):
            continue
        root = ET.parse(os.path.join(SRC, f)).getroot()
        for pou in find_all(root, u"pou"):
            total += 1
            name, und = check_pou(pou, gvls)
            if und:
                bad += 1
                sys.stdout.write(u"%-20s NE OB''YaVLENY: %s\n" % (name, u", ".join(und)))
    sys.stdout.write(u"\nPOU vsego: %d, s nedoopredelennymi signalami: %d\n" % (total, bad))
    return 1 if bad else 0


if __name__ == u"__main__":
    sys.exit(main())
