# -*- coding: utf-8 -*-
u"""Sverka: strukturnyj <interface> protiv tekstovogo obyavleniya POU.

ZAPUSKAT SISTEMNYM PYTHON 3 (ne IronPython):
    python generator/tools/verify_decl.py            # vse fajly iz src/
    python generator/tools/verify_decl.py TEST_Z80   # konkretnye POU

ChTO PROVERYaET I POChEMU ETO VAZhNO.
U PLCopenXML dva nezavisimyh mesta, gde perechisleny peremennye POU:
  1) strukturnyj <interface> -- ego chitaet import CODESYS;
  2) <InterfaceAsPlainText> -- tekst, kotoryj vidit polzovatel v redaktore
     obyavlenij.
Esli oni rashodyatsya, polzovatel vidit odno, a kompiliruetsya drugoe --
imenno na eto ukazal polzovatel, kogda obyavleniya okazalis v pole
realizacii. Ran'she sverki ne bylo voobshche, poetomu rashozhdenie
(nepravil'nyj razbor kommentariev s dvoetochiem) zhilo v proekte.

VNIMANIE K NAMESPACE. Element <InterfaceAsPlainText> zapisan BEZ prefiksa,
poetomu on nasleduet OSNOVNOJ namespace tc6_0200, a ne
interfaceasplaintext (tot namespace stoit tolko v attribute name="..."). Pervaya
versiya proverki iskala ego po namespace interfaceasplaintext i poetomu
"ne nahodila" obyavlenij vo vseh 31 fajlah -- lozhnyj minus. poetomu zdes
sravnenie po lokal'nomu imeni tega.

Kod vozvratа: 0 -- vse chisto, 1 -- est' rashozhdeniya.
"""
import os
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(os.path.dirname(HERE)), u"src")
sys.path.insert(0, HERE)

import fbd_xml as F                                            # noqa: E402

TC6 = u"{http://www.plcopen.org/xml/tc6_0200}"

# klyuch sektsii -> (teg v <interface>, zagolovok v tekste)
SECTIONS = ((u"in", u"inputVars", u"VAR_INPUT"),
            (u"out", u"outputVars", u"VAR_OUTPUT"),
            (u"inout", u"inOutVars", u"VAR_IN_OUT"),
            (u"ext", u"externalVars", u"VAR_EXTERNAL"),
            (u"local", u"localVars", u"VAR"))


def find_all(node, local_name):
    u"""Najti vse potomki s dannym lokal'nym imenem tega (ljuboj namespace)."""
    res = []
    for ch in node.iter():
        if ch.tag == local_name or (isinstance(ch.tag, str) and ch.tag.endswith(u"}" + local_name)):
            res.append(ch)
    return res


def check_pou(pou):
    u"""Vernut' (imya, spisok problem) dlya odnogo elementa <pou>."""
    name = pou.get(u"name") or u"<bez imeni>"
    problems = []
    ifaces = find_all(pou, u"interface")
    if not ifaces:
        return name, [u"<interface> otsutstvuet"]
    iface = ifaces[0]

    decl_text = None
    for d in find_all(pou, u"InterfaceAsPlainText"):
        for x in find_all(d, u"xhtml"):
            decl_text = u"".join(x.itertext())
    if decl_text is None:
        problems.append(u"<InterfaceAsPlainText> otsutstvuet -- polzovatel ne uvidit obyavlenij")
        return name, problems

    struct = {}
    for key, tag, title in SECTIONS:
        nodes = [n for n in iface if n.tag == TC6 + tag]
        struct[key] = [] if not nodes else [v.get(u"name") for v in nodes[0]
                                            if v.tag == TC6 + u"variable"]

    parsed = F.parse_declaration_text(decl_text)
    text = dict([(k, [v.name for v in parsed.get(k, [])]) for k, _, _ in SECTIONS])

    for key, tag, title in SECTIONS:
        s, t = struct[key], text[key]
        only_s = [x for x in s if x not in t]
        only_t = [x for x in t if x not in s]
        if only_s:
            problems.append(u"%s: est' v <interface>, net v tekste: %s" % (title, u", ".join(only_s)))
        if only_t:
            problems.append(u"%s: est' v tekste, net v <interface>: %s" % (title, u", ".join(only_t)))
        if len(s) != len(t):
            problems.append(u"%s: raznoe chislo: <interface>=%d tekst=%d" % (title, len(s), len(t)))

    allnames = []
    for key, _, _ in SECTIONS:
        allnames.extend(struct[key])
    dup = sorted(set([n for n in allnames if allnames.count(n) > 1]))
    if dup:
        problems.append(u"dubli imen v obyavleniyah: %s" % u", ".join(dup))
    return name, problems


def check_file(path):
    u"""Proverit' VSE POU v fajle (v odnom XML ih mozhet byt' neskol'ko)."""
    root = ET.parse(path).getroot()
    pous = find_all(root, u"pou")
    if not pous:
        return [(os.path.splitext(os.path.basename(path))[0], [u"net elementa <pou>"])]
    return [check_pou(p) for p in pous]


def main(argv):
    names = argv[1:]
    if names:
        files = [os.path.join(SRC, n + u".plcopenxml") for n in names]
    else:
        files = sorted([os.path.join(SRC, f) for f in os.listdir(SRC)
                        if f.endswith(u".plcopenxml")])
    total = 0
    bad = 0
    sys.stdout.write(u"%-22s %-6s %s\n" % (u"POU", u"status", u"problemy"))
    sys.stdout.write(u"-" * 78 + u"\n")
    for f in files:
        for name, problems in check_file(f):
            total += 1
            if problems:
                bad += 1
                sys.stdout.write(u"%-22s %-6s %s\n" % (name, u"PLOHO", problems[0]))
                for p in problems[1:]:
                    sys.stdout.write(u"%-22s %-6s %s\n" % (u"", u"", p))
            else:
                sys.stdout.write(u"%-22s %-6s\n" % (name, u"OK"))
    sys.stdout.write(u"\n%s: %d iz %d\n" % (u"RASHOZhDENIJ", bad, total))
    return 1 if bad else 0


if __name__ == u"__main__":
    try:
        sys.exit(main(sys.argv))
    except Exception as exc:                                   # noqa: BLE001
        sys.stdout.write(u"OSHIBKA proverki: %s\n" % exc)
        sys.exit(2)
