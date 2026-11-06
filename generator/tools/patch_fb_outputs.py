# -*- coding: utf-8 -*-
u"""Perevesti VSE vyhody FB v PLC_PRG na lokalnye peremennye.

ZAPUSKAT SISTEMNYM PYTHON 3 ODIN RAZ.

P R I Ch I N A. V sheme PLC_PRG vyhody ekzemplyarov chitalis' napryamuyu:
    n10.outvar(u"GVL_PLCVisu.A", n10.invar(u"fbRF.A", ...))
Takaya konstrukciya ("inVariable" so ssylkoj na vyhod FB) pri generacii koda
dlya tsiklicheskoj zadachi privodit k 17 oshibkam C32 (konverziya tipov).
Dokazano bisekciej: otklyuchenie seti s takimi ssylkami ubiraet vse C32.

R E Sh E N I E. Snachala pishem vyhod FB v lokalnuyu peremennuyu (obychnaya
outVariable s imenem), a potrebiteli chitayut uzhe peremennuyu. Tak svyaz'
stanovitsya obychnoj i odnoznachnoj dlya kompilyatora.

Skript nahodit vse mesta vida
    nXX.outvar(u"DEST", nXX.invar(u"fbYY.PIN", ...))
i prevrashchaet v
    nXX.outvar(u"vYY_PIN", nXX.invar(u"fbYY.PIN", ...))     # v peremennuyu
    nXX.outvar(u"DEST", nXX.invar(u"vYY_PIN", ...))          # iz peremennoy
a takzhe dobavlyaet obyavlenie p.var(u"vYY_PIN", ...) v nachalo mk_plc_prg.
Tip peremennoi opredelyaetsya po obyavleniyu vyhoda v sootvetstvuyushchem FB.
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEN = os.path.join(ROOT, u"generator", u"gen_z80.py")
SRC = os.path.join(ROOT, u"src")

MARK = u"# VYHODY FB CHEREZ LOKALNYE PEREMENNYE"


def out_types():
    u"""Tip kazhdogo vyhoda kazhdogo FB -- iz sgenerirovannyh shem."""
    res = {}
    for f in os.listdir(SRC):
        if not f.endswith(u".plcopenxml"):
            continue
        name = f[:-len(u".plcopenxml")]
        t = io.open(os.path.join(SRC, f), encoding=u"utf-8").read()
        m = re.search(u"<outputVars>(.*?)</outputVars>", t, re.S)
        if not m:
            continue
        d = {}
        for v in re.finditer(u'<variable name="(\\w+)"><type><(\\w+)\\s*/>', m.group(1)):
            d[v.group(1)] = v.group(2)
        for v in re.finditer(u'<variable name="(\\w+)"><type><derived name="(\\w+)"', m.group(1)):
            d[v.group(1)] = v.group(2)
        res[name] = d
    return res


def main():
    t = io.open(GEN, encoding=u"utf-8").read()
    if MARK in t:
        sys.stdout.write(u"uzhe primenено\n")
        return
    types = out_types()
    i = t.find(u"def mk_plc_prg():")
    j = t.find(u"\ndef ", i + 10)
    body = t[i:j]

    found = {}
    #  Lovim tolko "skelet" stroki, a hvost (x=..., y=...) ostavlyaem kak est:
    #  pervaya versiya zaterla koordinaty i isportila shemu.
    pat = re.compile(u'(?P<ind>[ \\t]*)(?P<net>n\\d+[a-z]*)\\.outvar\\(u"(?P<dest>[^"]+)",'
                     u'[^\\n]*?(?P=net)\\.invar\\(u"(?P<fb>fb\\w+)\\.(?P<pin>\\w+)"')

    def repl(m):
        net, dest = m.group(u"net"), m.group(u"dest")
        fb, pin = m.group(u"fb"), m.group(u"pin")
        var = u"v%s_%s" % (fb[2:], pin)
        found[var] = types.get(fb, {}).get(pin, u"BYTE")
        return (u'%(ind)s%(net)s.outvar(u"%(var)s", %(net)s.invar(u"%(fb)s.%(pin)s", y=30))\n'
                u'%(ind)s%(net)s.outvar(u"%(dest)s", %(net)s.invar(u"%(var)s", y=60)'
                % {u"ind": m.group(u"ind"), u"net": net, u"var": var,
                   u"fb": fb, u"pin": pin, u"dest": dest})

    body2 = pat.sub(repl, body)
    n = len(found)
    if n == 0:
        sys.stdout.write(u"ssylok na vyhody FB ne najdeno\n")
        return

    decl = [u"    " + MARK + u":",
            u"    #  Pochemu tak: ssylka vida fbXX.PIN v inVariable privodit k",
            u"    #  oshibkam C32 pri generacii koda dlya zadachi (naydeno bisekciej).",
            u"    #  Cherez peremennuyu svyaz' stanovitsya obychnoj."]
    for var in sorted(found):
        decl.append(u'    p.var(u"%s", u"%s", u"vyhod FB cherez peremennuyu")'
                    % (var, found[var]))
    decl.append(u"")

    # vstavlyaem obyavleniya srazu posle perechisleniya FB
    anchor = body2.find(u'    p.var(u"fbBIOS"')
    ins = body2.find(u"\n", anchor) + 1
    body2 = body2[:ins] + u"\n".join(decl) + u"\n" + body2[ins:]

    io.open(GEN, u"w", encoding=u"utf-8").write(t[:i] + body2 + t[j:])
    sys.stdout.write(u"pereneseno vyhodov FB v peremennye: %d\n" % n)
    for var in sorted(found):
        sys.stdout.write(u"    %-24s %s\n" % (var, found[var]))


if __name__ == u"__main__":
    main()
