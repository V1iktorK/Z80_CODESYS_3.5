# -*- coding: utf-8 -*-
u"""Vremenno ubrat' set' 'SET 15' iz PLC_PRG i posmotret na schetchik oshibok.

ZAPUSKAT SISTEMNYM PYTHON 3.
    python hide_net.py off "SET 15"   -- skryt' set'
    python hide_net.py on             -- vernut'
    python hide_net.py list           -- pokazat' seti

Pravim SGENERIROVANNYJ PLC_PRG.plcopenxml: udalyaem vse elementy, kotorye
prinadlezhat seti, i svyazi na nih. Eto bystree i nadezhnee, chem perebirat'
generator.
"""
import io
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
XML = os.path.join(ROOT, u"src", u"PLC_PRG.plcopenxml")
BAK = XML + u".bak"


def split_body(text):
    u"""Vernut' (do_tela, telo, posle_tela)."""
    i = text.find(u"<FBD>")
    j = text.find(u"</FBD>")
    return text[:i], text[i:j], text[j:]


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else u"list"
    if mode == u"on":
        if os.path.exists(BAK):
            shutil.copyfile(BAK, XML)
            os.remove(BAK)
            sys.stdout.write(u"PLC_PRG vosstanovlen\n")
        else:
            sys.stdout.write(u"rezerva net\n")
        return

    t = io.open(XML, encoding=u"utf-8").read()
    if mode == u"list":
        for m in re.finditer(u"<!-- (SET [^>]*?) -->", t):
            sys.stdout.write(u"  %s\n" % m.group(1))
        return

    if mode != u"off":
        return
    tag = sys.argv[2] if len(sys.argv) > 2 else u"SET 15"
    if not os.path.exists(BAK):
        shutil.copyfile(XML, BAK)
        t = io.open(XML, encoding=u"utf-8").read()
    else:
        t = io.open(BAK, encoding=u"utf-8").read()

    head, body, tail = split_body(t)
    i = body.find(u"<!-- %s" % tag)
    if i < 0:
        sys.stdout.write(u"set' '%s' ne najdena\n" % tag)
        return
    # sleduyushchaya set' ili konec
    nxt = body.find(u"<!-- ", i + 10)
    seg = body[i:nxt if nxt > 0 else len(body)]
    body = body[:i] + body[nxt if nxt > 0 else len(body):]
    io.open(XML, u"w", encoding=u"utf-8").write(head + body + tail)
    sys.stdout.write(u"set' '%s' skryta (%d simvolov)\n" % (tag, len(seg)))


if __name__ == u"__main__":
    main()
