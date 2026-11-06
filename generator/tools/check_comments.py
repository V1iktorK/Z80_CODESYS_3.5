# -*- coding: utf-8 -*-
u"""P R O V E R K A  K O M M E N T A R I E V  v ST-tekstah.

Ch T O  I Shch E M. Posledovatelnost iz zvezdochki i zakryvayushchej skobki
ZAKRYVAET kommentariy. Esli ona vstrechaetsya V N U T R I kommentariya --
kommentariy obryvaetsya dosrochno, i ves ego hvost CODESYS chitaet kak KOD.
Soobshcheniya pri etom takie:
    C9:   Obnaruzhen nedopustimyj simvol '-'
    C189: ';' trebuetsya vmesto '-'
Ni imeni POU, ni nomera stroki v nih NET. Imenno poetomu takaya opechatka
stoila chasov poiska: v nashem proekte ona soderzhalas v GVL_CPM
("(Ctl_*)") i v TEST_Z80 ("(F_*)").

P R A V I L O: vnutri kommentariya nikogda ne dolzhno byt etoy
posledovatelnosti -- dazhe kak chasti imeni ili shablona.
Pisat nado "(Ctl_...)" ili "Ctl_xx".

ZAPUSK: python generator\tools\check_comments.py
Kod vozvrata: 0 -- chisto, 1 -- najdeny obryvy.
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(ROOT, u"src")
OPEN_C = u"(*"
CLOSE_C = u"*)"


def scan(name, where, text):
    u"""Projti po tekstu i najti obryvayushchie posledovatelnosti."""
    bad = []
    depth = 0
    line = 1
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == u"\n":
            line += 1
        if text.startswith(OPEN_C, i):
            depth += 1
            i += 2
            continue
        if text.startswith(CLOSE_C, i):
            if depth == 0:
                bad.append(u"%s (%s): str.%d -- zakryvayushchaya skobka bez otkrytiya"
                           % (name, where, line))
            else:
                depth -= 1
                #  K L Yu Ch E V A Ya  P R O V E R K A: chto stoit pered nej.
                prev = text[i - 1] if i > 0 else u" "
                if prev not in u" \t\n\r":
                    bad.append(u"%s (%s): str.%d -- posledovatelnost zvezdochka-"
                               u"skobka stoit vplotnuyu k simvolu %r; kommentariy "
                               u"zakroyetsya zdes dosrochno"
                               % (name, where, line, prev))
            i += 2
            continue
        i += 1
    if depth != 0:
        bad.append(u"%s (%s): kommentariev otkryto bolshe, chem zakryto "
                   u"(raznica %d)" % (name, where, depth))
    return bad


def body_of(path):
    t = io.open(path, encoding=u"utf-8").read()
    i = t.find(u"<ST>")
    j = t.find(u"</ST>")
    if i < 0 or j <= i:
        return None
    b = t[i:j].replace(u"&#xA;", u"\n").replace(u"&quot;", u'"')
    return b.replace(u"&lt;", u"<").replace(u"&gt;", u">").replace(u"&amp;", u"&")


def decl_of(path):
    t = io.open(path, encoding=u"utf-8").read()
    m = re.search(u"<InterfaceAsPlainText>\\s*<xhtml[^>]*>(.*?)</xhtml>", t, re.S)
    if not m:
        return None
    d = m.group(1).replace(u"&#xA;", u"\n").replace(u"&quot;", u'"')
    return d.replace(u"&lt;", u"<").replace(u"&gt;", u">").replace(u"&amp;", u"&")


def main():
    try:
        sys.stdout.reconfigure(encoding=u"utf-8", errors=u"replace")
    except Exception:                                          # noqa: BLE001
        pass
    sys.stdout.write(u"=== check_comments ===\n")
    total = 0
    checked = 0
    for f in sorted(os.listdir(SRC)):
        p = os.path.join(SRC, f)
        if not os.path.isfile(p):
            continue
        if f.endswith(u".gvl"):
            t = io.open(p, encoding=u"utf-8").read()
            checked += 1
            for b in scan(f, u"gvl", t):
                sys.stdout.write(u"  %s\n" % b)
                total += 1
        elif f.endswith(u".plcopenxml"):
            d = decl_of(p)
            if d is not None:
                checked += 1
                for b in scan(f, u"obyavlenie", d):
                    sys.stdout.write(u"  %s\n" % b)
                    total += 1
            bd = body_of(p)
            if bd is not None:
                checked += 1
                for b in scan(f, u"telo", bd):
                    sys.stdout.write(u"  %s\n" % b)
                    total += 1
    sys.stdout.write(u"proverено tekstov: %d; narushenij: %d\n" % (checked, total))
    return 1 if total else 0


if __name__ == u"__main__":
    sys.exit(main())
