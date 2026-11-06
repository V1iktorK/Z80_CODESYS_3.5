# -*- coding: utf-8 -*-
u"""Diagnostika: vyvesti strukturnyj <interface> i tekst obyavleniya POU.

Zapuskat sistemnym Python 3:
    python generator/tools/dump_decl.py PRG_CPM_BDOS TEST_Z80_CPM
"""
import io
import os
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(os.path.dirname(HERE)), u"src")   # Z80_EMU/src

TC6 = u"http://www.plcopen.org/xml/tc6_0200"
NS_PLAIN = u"http://www.3s-software.com/plcopenxml/interfaceasplaintext"
XHTML = u"http://www.w3.org/1999/xhtml"

SEC = ((u"inputVars", u"VAR_INPUT"), (u"outputVars", u"VAR_OUTPUT"),
       (u"localVars", u"VAR"), (u"inOutVars", u"VAR_IN_OUT"),
       (u"externalVars", u"VAR_EXTERNAL"), (u"tempVars", u"VAR_TEMP"))


def dump(name):
    path = os.path.join(SRC, name + u".plcopenxml")
    root = ET.parse(path).getroot()
    pou = None
    for p in root.iter(u"{%s}pou" % TC6):
        pou = p
        break
    if pou is None:
        sys.stdout.write(u"%s: POU NE NAJDEN\n" % name)
        return
    sys.stdout.write(u"========== %s ==========\n" % name)
    iface = pou.find(u"{%s}interface" % TC6)
    if iface is None:
        sys.stdout.write(u"  <interface> OTSUTSTVUET\n")
    else:
        for tag, title in SEC:
            node = iface.find(u"{%s}%s" % (TC6, tag))
            if node is None:
                continue
            names = [v.get(u"name") for v in node.findall(u"{%s}variable" % TC6)]
            sys.stdout.write(u"  %-12s (%2d): %s\n" % (title, len(names), u", ".join(names)))
    for data in pou.iter(u"{%s}InterfaceAsPlainText" % NS_PLAIN):
        for x in data.iter(u"{%s}xhtml" % XHTML):
            txt = x.text or u""
            sys.stdout.write(u"  ---- tekst obyavleniya ----\n")
            for line in txt.split(u"\n"):
                sys.stdout.write(u"  | %s\n" % line)
    sys.stdout.write(u"\n")


if __name__ == u"__main__":
    args = sys.argv[1:]
    if not args:
        args = [u"PRG_CPM_BDOS", u"TEST_Z80_CPM", u"TEST_Z80", u"PRG_CPM_Boot",
                u"PRG_InitMemory", u"PRG_LoadTestProgram"]
    for a in args:
        dump(a)
