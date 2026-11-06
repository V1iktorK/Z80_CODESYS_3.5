# -*- coding: utf-8 -*-
u"""Diagnostika XML: pokazat' derevo tegov i najti InterfaceAsPlainText."""
import os
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(os.path.dirname(HERE)), u"src")

path = os.path.join(SRC, u"TEST_Z80.plcopenxml")
sys.stdout.write(u"fajl: %s (%d bajt)\n" % (path, os.path.getsize(path)))
root = ET.parse(path).getroot()
sys.stdout.write(u"root tag: %r\n" % root.tag)


def walk(node, depth=0):
    sys.stdout.write(u"%s%r\n" % (u"  " * depth, node.tag))
    for ch in list(node):
        walk(ch, depth + 1)


walk(root)

raw = open(path, "rb").read().decode(u"utf-8")
i = raw.find(u"InterfaceAsPlainText")
sys.stdout.write(u"\npervoe vhozhdenie 'InterfaceAsPlainText' v tekste: %d\n" % i)
if i > 0:
    sys.stdout.write(raw[max(0, i - 260):i + 60].replace(u"\n", u"\\n") + u"\n")
