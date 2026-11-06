# -*- coding: utf-8 -*-
u"""V Y Ch I S T I T  nedopustimye simvoly iz generatora.

P O Ch E M U. V tekste gen_z80.py ostalis kirillicheskie bukvy i bite
simvoly (o', i', e) VNUTRI strok, kotorye idut v ST-tekst dlya CODESYS.
Dlya nih eto nedopustimye simvoly, i kompilyator syplet:
    C9:   Obnaruzhen nedopustimyj simvol '-'
    C189: ';' trebuetsya vmesto '-'
Bite simvoly -- sledstvie proshlyh avtomaticheskih praavok fajla:
kirillica popala v angloyazychnyj ST, a 'o s tildoj' -- ostatok ot
perekodirovki.

Ch T O  D E L A E M. Zamenyaem tolko te simvoly, chto FAKTIChesKI popali
v src/ (spisok sostavlen po fajlam src/, a ne na glaz). Kirillica
zamenyaetsya na translit, bite latinskie -- na chistye latinskie.

ZAPUSK: python generator\tools\fix_nonascii.py
"""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GEN = os.path.join(ROOT, u"generator", u"gen_z80.py")
SRC = os.path.join(ROOT, u"src")

#  Kirillica -> translit. Tolko te bukvy, chto najdeny v src/.
CYR = {
    u"\u0430": u"a", u"\u0431": u"b", u"\u0432": u"v", u"\u0433": u"g",
    u"\u0434": u"d", u"\u0435": u"e", u"\u0451": u"e", u"\u0436": u"zh",
    u"\u0437": u"z", u"\u0438": u"i", u"\u0439": u"j", u"\u043a": u"k",
    u"\u043b": u"l", u"\u043c": u"m", u"\u043d": u"n", u"\u043e": u"o",
    u"\u043f": u"p", u"\u0440": u"r", u"\u0441": u"s", u"\u0442": u"t",
    u"\u0443": u"u", u"\u0444": u"f", u"\u0445": u"h", u"\u0446": u"c",
    u"\u0447": u"ch", u"\u0448": u"sh", u"\u0449": u"shch", u"\u044a": u"",
    u"\u044b": u"y", u"\u044c": u"", u"\u044d": u"e", u"\u044e": u"yu",
    u"\u044f": u"ya",
    u"\u0410": u"A", u"\u0411": u"B", u"\u0412": u"V", u"\u0413": u"G",
    u"\u0414": u"D", u"\u0415": u"E", u"\u0416": u"ZH", u"\u0417": u"Z",
    u"\u0418": u"I", u"\u0419": u"J", u"\u041a": u"K", u"\u041b": u"L",
    u"\u041c": u"M", u"\u041d": u"N", u"\u041e": u"O", u"\u041f": u"P",
    u"\u0420": u"R", u"\u0421": u"S", u"\u0422": u"T", u"\u0423": u"U",
    u"\u0424": u"F", u"\u0425": u"H", u"\u0426": u"C", u"\u0427": u"CH",
    u"\u0428": u"SH", u"\u0429": u"SHCH", u"\u042b": u"Y", u"\u042d": u"E",
    u"\u042e": u"YU", u"\u042f": u"YA",
    #  bite latinskie bukvy s diakritikoj
    u"\u00f3": u"o", u"\u00ed": u"i", u"\u00e9": u"e", u"\u00e1": u"a",
    u"\u00fa": u"u", u"\u00e8": u"e", u"\u00ea": u"e", u"\u00e7": u"c",
    u"\u00f1": u"n",
    #  tipografika
    u"\u2013": u"-", u"\u2014": u"-", u"\u2018": u"'", u"\u2019": u"'",
    u"\u201c": u'"', u"\u201d": u'"', u"\u00ab": u'"', u"\u00bb": u'"',
    u"\u00a0": u" ",
}


def clean(text):
    out = []
    for ch in text:
        if ord(ch) < 128:
            out.append(ch)
        elif ch in CYR:
            out.append(CYR[ch])
        else:
            out.append(u"")
    return u"".join(out)


def report(title, path):
    t = io.open(path, encoding=u"utf-8").read()
    bad = {}
    for n, l in enumerate(t.split(u"\n"), 1):
        for ch in l:
            if ord(ch) > 127:
                bad.setdefault(ch, []).append(n)
    if not bad:
        sys.stdout.write(u"  %-28s chisto\n" % title)
        return 0
    for ch, lns in sorted(bad.items()):
        sys.stdout.write(u"  %-28s U+%04X %r stroki: %s\n"
                         % (title, ord(ch), ch, lns[:8]))
    return len(bad)


def main():
    try:
        sys.stdout.reconfigure(encoding=u"utf-8", errors=u"replace")
    except Exception:                                          # noqa: BLE001
        pass
    sys.stdout.write(u"=== fix_nonascii ===\n")
    sys.stdout.write(u"DO pravki:\n")
    report(u"generator/gen_z80.py", GEN)
    n = 0
    for f in sorted(os.listdir(SRC)):
        if f.endswith(u".plcopenxml") or f.endswith(u".gvl"):
            n += report(u"src/" + f, os.path.join(SRC, f))
    sys.stdout.write(u"  (vsego problemnyh simvolov v src/: %d)\n" % n)

    src = io.open(GEN, encoding=u"utf-8").read()
    fixed = clean(src)
    if fixed != src:
        bak = GEN + u".bak_step3"
        io.open(bak, u"w", encoding=u"utf-8").write(src)
        io.open(GEN, u"w", encoding=u"utf-8").write(fixed)
        sys.stdout.write(u"gen_z80.py ochishchen, kopiya: %s\n" % bak)
    else:
        sys.stdout.write(u"gen_z80.py uzhe chist\n")
    sys.stdout.write(u"=== gotovo ===\n")


if __name__ == u"__main__":
    main()
