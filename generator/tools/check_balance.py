# -*- coding: utf-8 -*-
u"""P R O V E R K A  B A L A N S A  operatorov v ST-telah.

Z A Ch E M. Kompilyator soobshchaet buket oshibok
    C9   : Obnaruzhen nedopustimyj simvol '-'
    C189 : ';' trebuetsya vmesto '-'
    C8   : Nedopustimyj End-of-file: trebuetsya 'ELSIF', 'ELSE' ili 'END_IF'
i ni odna iz nih ne ukazyvaet na nastoyashchee mesto. Na samom dele eto
posledstvie O D N O J  nezakrytoj konstrukcii: dalshe parser idet po
tekstu kak po vlozhennom tele usloviya i spotykaetsya o pervyj zhe operator.

N A S T O Ya Shch A Ya  P R I Ch I N A  takogo povedeniya v nashem proekte
uzhe najdena odin raz: v TEST_Z80 chitalos "IF NOT bPrepared THEN" bez
"END_IF" pered "ELSIF GVL_Tests.Cpu_Test_Stage = 4 THEN".

Ch T O  D E L A E M. Idem po strogam kak stek: kazhdoe IF/ELSIF/FOR/WHILE/CASE
polozhit chto-to, kazhdoe END_* snimaet. Kommentari (* ... *) vykidyvaem
D O podscheta: v nih slovom vstrechaetsya i "IF", i "END_IF", i eto
uzhe odin raz privelo k lozhnym vyvodam.

V A Zh N O: bez etoj proverki nelzya, potomu chto CODESYS NE KOMPILIRUET
POU, ne svyazannyj s zadachej, -- oshibka molchit do teh por, poka
programma ne popadet v spisok zapuska.

ZAPUSK: python generator\tools\check_balance.py
Kod vozvrata: 0 -- vse balansy verny, 1 -- est disbalans.
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(ROOT, u"src")

#  Chto otkryvaet blok i chem zakryvaetsya.
OPENER = re.compile(u"^[ \\t]*(IF|FOR|WHILE|CASE|REPEAT)\\b", re.I)
MIDDLE = re.compile(u"^[ \\t]*(ELSIF|ELSE)\\b", re.I)
CLOSER = re.compile(u"^[ \\t]*END_(IF|FOR|WHILE|CASE|REPEAT)\\b", re.I)
PAIR = {u"IF": u"IF", u"FOR": u"FOR", u"WHILE": u"WHILE",
        u"CASE": u"CASE", u"REPEAT": u"REPEAT"}


def strip_comments(text):
    u"""Ubrat (* ... *) -- oni mogut byt mnogostrochnymi."""
    return re.sub(u"\\(\\*.*?\\*\\)", u" ", text, flags=re.S)


def body_of(path):
    t = io.open(path, encoding=u"utf-8").read()
    i = t.find(u"<ST>")
    j = t.find(u"</ST>")
    if i < 0 or j <= i:
        return None
    b = t[i:j].replace(u"&#xA;", u"\n").replace(u"&quot;", u'"')
    b = b.replace(u"&lt;", u"<").replace(u"&gt;", u">").replace(u"&amp;", u"&")
    return b


def clean_lines(body):
    u"""Vernut stroki tela bez kommentariev i bez nachalnogo XML-tega.

    P O Ch E M U  S N I M A E M  T E G. Pervaya stroka tela nachinaetsya
    otkryvayushchim tegom: "            <xhtml xmlns=...>IF (NOT x) THEN".
    Bez ego snimaй regulyarka s nachalom stroki operatora ne vidit.

    V A Zh N O: teg ishchem po V I D U "<s imya", a ne po pervoj pare "<...>".
    Pervaya versiya etoj funkcii iskala ">" i otbrasyvala nachalo do nego --
    i na stroke s OPERATOROM NERAVENSTVA "<>" otrezala sam operator:
        "IF Masк_Mem AND (z80Mem <> Exp_Mem) THEN"  prevrashchalos v
        " Exp_Mem) THEN"
    i validnyj IF ischezal iz proverki, a END_IF vyglyadel kak lishnij.
    """
    clean = strip_comments(body)
    tag = re.compile(u"^[ \\t]*<[A-Za-z/!?][^>]*>")
    out = []
    for l in clean.split(u"\n"):
        m = tag.match(l)
        if m:
            l = l[m.end():]
        out.append(l)
    return out


def check(name, body):
    u"""Vernut spisok problem dlya odnogo POU."""
    stack = []
    bad = []
    for n, line in enumerate(clean_lines(body), 1):
        m = OPENER.match(line)
        if m:
            stack.append((m.group(1).upper(), n))
            continue
        c = CLOSER.match(line)
        if c:
            want = PAIR.get(c.group(1).upper())
            if not stack:
                bad.append(u"str.%d: END_%s bez otkryvayushchego" % (n, want))
                continue
            got, ln = stack.pop()
            if got != want:
                bad.append(u"str.%d: END_%s zakryvaet %s so str.%d"
                           % (n, want, got, ln))
            continue
    for got, ln in stack:
        bad.append(u"str.%d: %s NE ZAKRYT" % (ln, got))
    return bad


def main():
    try:
        sys.stdout.reconfigure(encoding=u"utf-8", errors=u"replace")
    except Exception:                                          # noqa: BLE001
        pass
    sys.stdout.write(u"=== check_balance: balans operatorov v ST-telah ===\n")
    total_files = 0
    total_bad = 0
    for f in sorted(os.listdir(SRC)):
        if not f.endswith(u".plcopenxml"):
            continue
        body = body_of(os.path.join(SRC, f))
        if body is None:
            continue
        total_files += 1
        bad = check(f[:-len(u".plcopenxml")], body)
        if bad:
            total_bad += 1
            sys.stdout.write(u"  %s\n" % f[:-len(u".plcopenxml")])
            for b in bad:
                sys.stdout.write(u"      %s\n" % b)
    sys.stdout.write(u"proverено ST-POU: %d; s disbalansom: %d\n"
                     % (total_files, total_bad))
    return 1 if total_bad else 0


if __name__ == u"__main__":
    sys.exit(main())
