# -*- coding: utf-8 -*-
u"""P O I S K  b l o k o v  s  R A Z N Y M I  tipami operandov.

Z A Ch E M. Kompilyator daet pary
    C32: Nevozmozhno konvertirovat tip 'BOOL'  v tip 'USINT'
    C32: Nevozmozhno konvertirovat tip 'USINT' v tip 'BOOL'
    C32: Nevozmozhno konvertirovat tip 'BOOL'  v tip 'BYTE'
i ne ukazyvaet ni POU, ni seti. Bisekciej po ekzemplyaram ustanovleno, chto
vse otdel nye FB chisty -- znachit delo v setyah samogo PLC_PRG, gde bloki
svyazany mezhdu soboy.

Ch T O  I Shch E M. Dlya kazhdogo obobshchennogo bloka (AND, OR, XOR, NOT,
SEL, ADD, SUB, SHL, SHR) opredelyaem tip K A Zh D O G O vhoda, privodya tipy
rekursivno cherez vse bloki. Esli u odnogo bloka vhody raznogo tipa --
eto i est mesto oshibki.

P R I M E R nastoyashchey oshibki, najdennoj takim poiskom v FB_IO_Ports:
    Halt_Req := we20 AND b0
gde we20 -- BOOL, a b0 = AND(bajt, 16#01) -- BYTE. Raznye tipy v odnom AND.

ZAPUSK: python generator\tools\find_mixed_ops.py [POU ...]
Bez argumentov proveryaet vse POU.
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(ROOT, u"src")

BITWISE = (u"AND", u"OR", u"XOR")
COMPARE = (u"EQ", u"NE", u"GT", u"LT", u"GE", u"LE")
ARITH = (u"ADD", u"SUB", u"MUL", u"DIV", u"MOD")
SHIFT = (u"SHL", u"SHR", u"ROL", u"ROR")
SELECT = (u"SEL", u"MUX")
SINGLE = (u"NOT",)
NUM = (u"BYTE", u"WORD", u"DWORD", u"SINT", u"USINT", u"INT", u"UINT",
       u"DINT", u"UDINT", u"LINT", u"ULINT", u"REAL", u"LREAL")


def load_fb_outputs():
    u"""Imя FB -> {imya vyhoda: tip}. Nuzhno, chtoby ponimat `fbX.Pin`."""
    out = {}
    for f in os.listdir(SRC):
        if not f.endswith(u".plcopenxml"):
            continue
        name = f[:-len(u".plcopenxml")]
        t = io.open(os.path.join(SRC, f), encoding=u"utf-8").read()
        i = t.find(u"<outputVars>")
        j = t.find(u"</outputVars>")
        if i < 0 or j < 0:
            continue
        seg = t[i:j]
        d = {}
        for m in re.finditer(u'<variable name="(\\w+)">\\s*<type>\\s*'
                             u'(?:<(\\w+)\\s*/>|<derived name="(\\w+)")', seg):
            d[m.group(1)] = m.group(2) or m.group(3)
        out[name] = d
    return out


def load_fb_inputs():
    u"""Imя FB -> {imya vhoda: tip}.

    N U Zh N O  D L Ya  C196. Kogda vyhod odnogo FB (naprimer WORD) podayotsya
    na vhod drugogo FB, obyavlennyy kak INT, kompilyator delayot neyavnuyu
    konversiyu WORD -> INT: eto preduprezhdenie C196 bez ukazaniya mesta.
    Zdes my znaem obyavlennye tipy vhodov kazhdogo nashego FB i mozhem ih
    sravnit.
    """
    out = {}
    for f in os.listdir(SRC):
        if not f.endswith(u".plcopenxml"):
            continue
        name = f[:-len(u".plcopenxml")]
        t = io.open(os.path.join(SRC, f), encoding=u"utf-8").read()
        i = t.find(u"<inputVars>")
        j = t.find(u"</inputVars>")
        if i < 0 or j < 0:
            continue
        seg = t[i:j]
        d = {}
        for m in re.finditer(u'<variable name="(\\w+)">\\s*<type>\\s*'
                             u'(?:<(\\w+)\\s*/>|<derived name="(\\w+)")', seg):
            d[m.group(1)] = m.group(2) or m.group(3)
        out[name] = d
    return out


FB_OUT = load_fb_outputs()
FB_IN = load_fb_inputs()


def load_gvl_types():
    u"""Imya "GVL_X.Y" -> tip. GVL lezhat tekstom, razbor prostoj."""
    out = {}
    for f in os.listdir(SRC):
        if not f.endswith(u".gvl"):
            continue
        gvl = f[:-len(u".gvl")]
        txt = io.open(os.path.join(SRC, f), encoding=u"utf-8").read()
        txt = re.sub(u"\\(\\*.*?\\*\\)", u" ", txt, flags=re.S)
        for m in re.finditer(u"(\\w+)\\s*:\\s*(ARRAY\\s*\\[[^\\]]*\\]\\s*OF\\s+)?"
                             u"(\\w+)", txt):
            nm, arr, tp = m.group(1), m.group(2), m.group(3)
            out[u"%s.%s" % (gvl, nm)] = tp
    return out


GVL_TYPES = load_gvl_types()


def unesc(s):
    return (s.replace(u"&#xA;", u"\n").replace(u"&quot;", u'"')
             .replace(u"&lt;", u"<").replace(u"&gt;", u">").replace(u"&amp;", u"&"))


class Pou(object):
    def __init__(self, path, name):
        self.name = name
        self.text = io.open(path, encoding=u"utf-8").read()
        self.decls = {}
        for m in re.finditer(u'<variable name="(\\w+)">\\s*<type>\\s*<(\\w+)\\s*/>',
                             self.text):
            self.decls[m.group(1)] = m.group(2)
        for m in re.finditer(u'<variable name="(\\w+)">\\s*<type>\\s*'
                             u'<derived name="(\\w+)"', self.text):
            self.decls[m.group(1)] = m.group(2)
        self.elems = {}
        for m in re.finditer(u'<inVariable localId="(\\d+)"[^>]*>(.*?)</inVariable>',
                             self.text, re.S):
            x = re.search(u"<expression>([^<]*)</expression>", m.group(2))
            self.elems[m.group(1)] = (u"invar", unesc(x.group(1)) if x else u"")
        for m in re.finditer(u'<outVariable localId="(\\d+)"[^>]*>(.*?)</outVariable>',
                             self.text, re.S):
            x = re.search(u"<expression>([^<]*)</expression>", m.group(2))
            self.elems[m.group(1)] = (u"outvar", unesc(x.group(1)) if x else u"")
        for m in re.finditer(u'<block localId="(\\d+)" typeName="(\\w+)"', self.text):
            self.elems[m.group(1)] = (u"block", m.group(2))

    def pins(self, lid):
        i = self.text.find(u'<block localId="%s"' % lid)
        j = self.text.find(u"</block>", i)
        seg = self.text[i:j] if j > 0 else self.text[i:]
        out = {}
        for m in re.finditer(u'<variable formalParameter="([^"]*)">\\s*'
                             u'<connectionPointIn>(.*?)</connectionPointIn>',
                             seg, re.S):
            r = re.search(u'<connection refLocalId="(\\d+)"', m.group(2))
            if r:
                out[m.group(1)] = r.group(1)
        return out

    def rtype(self, lid, depth=0):
        u"""Tip signala. None -- opredelit ne udalos."""
        if depth > 10 or lid is None:
            return None
        e = self.elems.get(lid)
        if not e:
            return None
        kind, val = e
        if kind in (u"invar", u"outvar"):
            t = self.decls.get(val)
            if t:
                return t
            #  I M Ya  V I D A  "ekenziya.Vyhod".
            #  Tak v PLC_PRG chitayutsya vyhody ekzemplyarov FB. Bez etogo
            #  razbora takie ssylki schitalis "tip neizvesten", i poisk
            #  smeshannyh operandov ikh prosto propuskal.
            if u"." in val:
                inst, pin = val.split(u".", 1)
                fbt = self.decls.get(inst)
                if fbt:
                    tt = FB_OUT.get(fbt, {}).get(pin)
                    if tt:
                        return tt
                #  GVL: imya vida "GVL_X.Y" -- tip ishchem v fajle GVL
                gt = GVL_TYPES.get(val)
                if gt:
                    return gt
            #  vyhod ekzemplyara FB, peredannyj cherez vhod S E T I
            return None
        if u"_TO_" in val:
            return val.split(u"_TO_")[-1]
        if val in COMPARE:
            return u"BOOL"
        if val in BITWISE or val in ARITH or val in SHIFT or val in SINGLE:
            p = self.pins(lid)
            for pin in (u"IN1", u"IN"):
                if pin in p:
                    return self.rtype(p[pin], depth + 1)
            return None
        if val in SELECT:
            p = self.pins(lid)
            if u"IN0" in p:
                return self.rtype(p[u"IN0"], depth + 1)
            return None
        return None

    def check(self):
        bad = []
        for lid, (kind, val) in sorted(self.elems.items(), key=lambda x: int(x[0])):
            if kind != u"block":
                continue
            if val not in BITWISE + ARITH + SELECT:
                continue
            p = self.pins(lid)
            types = {}
            for pin in sorted(p):
                if pin in (u"G", u"K"):
                    continue
                t = self.rtype(p[pin])
                if t is not None:
                    types[pin] = t
            if len(types) < 2:
                continue
            uniq = sorted(set(types.values()))
            if len(uniq) > 1:
                bad.append(u"%s: blok %s (localId %s) -- vhody RAZNYH tipov: %s"
                           % (self.name, val, lid, types))
        return bad

    def check_assign(self):
        u"""Vtoroy prohod: vyhod bloka pitayot peremennuyu drugogo tipa."""
        bad = []
        for m in re.finditer(u'<outVariable localId="(\\d+)"[^>]*>(.*?)</outVariable>',
                             self.text, re.S):
            body = m.group(2)
            x = re.search(u"<expression>([^<]*)</expression>", body)
            if not x:
                continue
            dst = unesc(x.group(1))
            dts = self.decls.get(dst)
            if not dts:
                continue
            r = re.search(u'<connection refLocalId="(\\d+)"', body)
            if not r:
                continue
            st = self.rtype(r.group(1))
            if st is None or st == dts:
                continue
            #  chislovye tipy mezhdu soboy i BOOL -- eto uzhe podozritel no;
            #  REAL i prochie ekzoticheskie ne trogaem
            if st in NUM + (u"BOOL",) and dts in NUM + (u"BOOL",):
                bad.append(u"%s: %s (%s) := vyhod tipa %s"
                           % (self.name, dst, dts, st))
        return bad

    def check_literals(self):
        u"""Tretiy prohod: sravnenie/arifmetika WORD s B E Z T I P O V Y M literalom.

        P O Ch E M U  E T O  O T D E L N Y J  P R O H O D. Bezrisovyy literal
        (naprimer "1" ili "16#80") v etoy versii CODESYS vyvoditsya kak INT.
        Kogda vtoroy operand -- WORD, kompilyator delayot N E Ya V N U Yu
        konversiyu WORD -> INT i pechataet preduprezhdenie
            C196: Neyavnaya konversiya iz tipa bez znaka 'WORD' v tip
                  so znakom 'INT': vozmozhno izmenenie znaka
        Ni imeni POU, ni nomera seti v soobshchenii net.

        Lechenie: napisat literal s tipom -- WORD#1, BYTE#0, DWORD#16#FF.
        """
        bad = []
        for lid, (kind, val) in sorted(self.elems.items(), key=lambda x: int(x[0])):
            if kind != u"block":
                continue
            if val not in COMPARE + ARITH + BITWISE:
                continue
            p = self.pins(lid)
            typed = {}
            lits = {}
            for pin in sorted(p):
                ref = p[pin]
                e = self.elems.get(ref)
                if not e:
                    continue
                k, v = e
                if k in (u"invar", u"outvar") and u"." not in v \
                        and v not in self.decls and is_bare_literal(v):
                    lits[pin] = v
                else:
                    t = self.rtype(ref)
                    if t:
                        typed[pin] = t
            wide = [t for t in typed.values() if t in (u"WORD", u"DWORD", u"UDINT")]
            if wide and lits:
                bad.append(u"%s: blok %s (localId %s) -- %s vmeste s bezrisovym "
                           u"literalom %s (nuzhen tip, napr. WORD#...)"
                           % (self.name, val, lid, u"/".join(sorted(set(wide))),
                              u", ".join(u"%s=%s" % (k, v) for k, v in sorted(lits.items()))))
        return bad


def is_bare_literal(s):
    u"""Chislo bez tipa: 0, 255, 16#80."""
    return bool(re.match(u"^\\s*(?:\\d+|16#[0-9A-Fa-f]+|2#[01]+|8#[0-7]+)\\s*$", s))


def check_fb_calls(pou):
    u"""Chetvertyy prohod: vyhod pitayot vhod D R U G O G O  FB ne togo tipa.

    Primer nastyashchey oshibki iz zhurnala: vhod `Index` u FB_CPM_Disk
    obyavlen kak INT, a na nego podayotsya WORD. Kompilyator delayot
    neyavnuyu konversiyu i pechataet C196 bez imeni POU i nomera seti.
    """
    bad = []
    for lid, (kind, val) in sorted(pou.elems.items(), key=lambda x: int(x[0])):
        if kind != u"block":
            continue
        declared = FB_IN.get(val)
        if not declared:
            continue
        pins = pou.pins(lid)
        for pin, ref in sorted(pins.items()):
            want = declared.get(pin)
            if not want or want not in NUM:
                continue
            have = pou.rtype(ref)
            if have is None or have == want:
                continue
            if have in NUM:
                bad.append(u"%s: vyzov %s (localId %s) -- vhod %s obyavlen kak "
                           u"%s, a podayotsya %s"
                           % (pou.name, val, lid, pin, want, have))
    return bad


def main():
    try:
        sys.stdout.reconfigure(encoding=u"utf-8", errors=u"replace")
    except Exception:                                          # noqa: BLE001
        pass
    only = [x.upper() for x in sys.argv[1:]]
    sys.stdout.write(u"=== find_mixed_ops ===\n")
    total = 0
    for f in sorted(os.listdir(SRC)):
        if not f.endswith(u".plcopenxml"):
            continue
        name = f[:-len(u".plcopenxml")]
        if only and name.upper() not in only:
            continue
        p = Pou(os.path.join(SRC, f), name)
        if u"<FBD>" not in p.text:
            continue
        for b in p.check() + p.check_assign() + p.check_literals() + check_fb_calls(p):
            sys.stdout.write(u"  %s\n" % b)
            total += 1
    sys.stdout.write(u"najdeno: %d\n" % total)
    return 1 if total else 0


if __name__ == u"__main__":
    sys.exit(main())
