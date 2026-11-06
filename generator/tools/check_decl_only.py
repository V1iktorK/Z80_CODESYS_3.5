# -*- coding: utf-8 -*-
u"""Strogaya proverka: v <InterfaceAsPlainText> dolzhno byt TOLKO obyavlenie.

ZAPUSKAT SISTEMNYM PYTHON 3.

P O Ch E M U  E T O  V A Zh N O. Kogda v tekst obyavleniya popadaet telo POU,
CODESYS chitaet telo kak obyavlenie i sypal oshibkami vida
    C0135: Takoj kod nedopustim v razdele obyavleniya
    C0006: ', AT ili :' trebuetsya vmesto '.'
Pervaya zhe stroka tela ("GVL_Tests_CPM.Tests[i].Id := i;") daet imenno "."
tam, gde ozhidaetsya "," ili ":".

Proverka ustrojena tak, chtoby NE putat kommentarii i znacheniya po umolchaniyu
(`bFirst : BOOL := TRUE;` -- eto zakonno) s nastoyashchim kodom:
  * kommentarii (* ... *) i // vyrezayutsya;
  * stroka schitaetsya kodom, esli ona NE vnutri sekcii VAR i soderzhit
    prisvaivanie ili opertor IF/FOR/WHILE/CASE.
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(os.path.dirname(HERE)), u"src")


def strip_comments(text):
    text = re.sub(u"\\(\\*.*?\\*\\)", u" ", text, flags=re.S)
    out = []
    for line in text.split(u"\n"):
        k = line.find(u"//")
        out.append(line if k < 0 else line[:k])
    return u"\n".join(out)


def check(name, decl):
    body = strip_comments(decl)
    in_var = False
    problems = []
    for i, raw in enumerate(body.split(u"\n"), 1):
        s = raw.strip()
        if not s:
            continue
        if re.match(u"^(VAR|VAR_INPUT|VAR_OUTPUT|VAR_GLOBAL|VAR_IN_OUT|VAR_EXTERNAL|"
                    u"VAR_TEMP|VAR_STAT|VAR_INST|VAR_CONFIG)\\b", s):
            in_var = True
            continue
        if s.startswith(u"END_VAR"):
            in_var = False
            continue
        if in_var:
            continue
        if re.match(u"^(PROGRAM|FUNCTION_BLOCK|FUNCTION)\\b", s):
            continue
        # vse ostalnoe vne VAR -- eto telo
        problems.append((i, s))
    return problems


def main():
    bad = 0
    for f in sorted(os.listdir(SRC)):
        if not f.endswith(u".plcopenxml"):
            continue
        t = io.open(os.path.join(SRC, f), encoding=u"utf-8").read()
        m = re.search(u"<InterfaceAsPlainText>(.*?)</InterfaceAsPlainText>", t, re.S)
        if not m:
            continue
        x = re.search(u"<xhtml[^>]*>(.*?)</xhtml>", m.group(1), re.S)
        if not x:
            continue
        decl = x.group(1)
        name = f[:-len(u".plcopenxml")]
        probs = check(name, decl)
        if probs:
            bad += 1
            sys.stdout.write(u"!!! %s: kod v razdele obyavleniya (%d strok)\n"
                             % (name, len(probs)))
            for i, s in probs[:3]:
                sys.stdout.write(u"      str. %d: %s\n" % (i, s[:80]))
    sys.stdout.write(u"\nPOU s kodom v obyavlenii: %d\n" % bad)
    return 1 if bad else 0


if __name__ == u"__main__":
    sys.exit(main())
