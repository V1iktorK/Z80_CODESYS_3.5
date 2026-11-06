# -*- coding: utf-8 -*-
u"""Perevesti VSE chteniya vyhodov FB v PLC_PRG na lokalnye peremennye.

ZAPUSKAT SISTEMNYM PYTHON 3 ODIN RAZ.

Z A D A Ch A. V sheme PLC_PRG vyhody ekzemplyarov chitayutsya napryamuyu:
    n8.invar(u"fbALU.Y"), n9.invar(u"fbALU.Flag_S"), n10.invar(u"fbRF.B") ...
Takaya konstrukciya privodit k oshibkam C32 pri generacii koda dlya zadachi.
Uzhe ispravlennye vyhody (fbMem, fbCtl, fbPC, fbRFRd.Addr_HL i dr.) pokazali,
chto cherez peremennuyu vse rabotaet.

P O Ch E M U  POSTROChNO, A NE SHABLONOM. Pervaya popytka ispolzovala regulyarku
po vsemu tekstu i zaterla hvosty mnogostrochnyh vyzovov -- prishlos vosstanavlivat
vruchnuyu. Zdes my menyaem tolko IMYa VNUTRI invar (odna zamena na stroku),
poetomu struktura koda ne menyaetsya.

Chto delaem dlya kazhdogo najdennogo "fbXX.PIN":
  1) obyavlyaem p.var(u"vXX_PIN", <tip vyhoda>) -- tip berem iz <outputVars>;
  2) v seti, gde stoit vyzov etogo FB, dobavlyaem stroku zapisi vyhoda
     v etu peremennuyu;
  3) v meste chteniya podstavlyaem imya peremennoy.
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEN = os.path.join(ROOT, u"generator", u"gen_z80.py")
SRC = os.path.join(ROOT, u"src")

MARK = u"# VYhODY FB -> LOKALNYE PEREMENNYE"

#  kakoy ekzemplyar kakomu FB sootvetstvuet i v kakoy seti on vyzyvaetsya
INSTANCES = {
    u"fbClock": (u"FB_Clock", None),
    u"fbPCLatch": (u"FB_Reg16", u"n13"),
    u"fbIR": (u"FB_Reg8Latch", u"n3"),
    u"fbDec": (u"FB_DecoderZ80", u"n4"),
    u"fbRFRd": (u"FB_RegFileZ80", u"n5"),
    u"fbMem": (u"FB_Memory64K", u"n7"),
    u"fbALU": (u"FB_ALU_Z80", u"n8"),
    u"fbFlags": (u"FB_FlagsRegZ80", u"n9"),
    u"fbRF": (u"FB_RegFileZ80", u"n10"),
    u"fbSP": (u"FB_SP_StackZ80", u"n11"),
    u"fbCtl": (u"FB_ControlUnit", u"n12"),
    u"fbPC": (u"FB_PC_Z80", u"n13"),
    u"fbIO": (u"FB_IO_Ports", u"n16"),
    u"fbBIOS": (u"FB_CPM_BIOS", u"n17"),
    u"fbHW": (u"FB_HW_IO_PLC", u"n15"),
    u"fbR": (u"FB_Reg8", u"n14"),
    u"fbAlways": (u"FB_AlwaysTrue", u"n1"),
}


def out_types():
    res = {}
    for f in os.listdir(SRC):
        if not f.endswith(u".plcopenxml"):
            continue
        name = f[:-len(u".plcopenxml")]
        t = io.open(os.path.join(SRC, f), encoding=u"utf-8").read()
        m = re.search(u"<outputVars>(.*?)</outputVars>", t, re.S)
        if not m:
            res[name] = {}
            continue
        d = {}
        for v in re.finditer(u'<variable name="(\\w+)"><type>(?:<(\\w+)\\s*/>'
                             u'|<derived name="(\\w+)")', m.group(1)):
            d[v.group(1)] = v.group(2) or v.group(3)
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
    lines = body.split(u"\n")

    ref = re.compile(u'invar\\(u"(fb\\w+)\\.(\\w+)"')
    reads = {}
    for idx, ln in enumerate(lines):
        for m in ref.finditer(ln):
            fb, pin = m.group(1), m.group(2)
            if fb not in INSTANCES:
                continue
            var = u"v%s_%s" % (fb[2:], pin)
            #  esli peremennaya UZhE obyavlena (eto delali predydushchie pravki) --
            #  ne trogaem: inache poluchim dvojnuyu zapis' vyhoda.
            if u'p.var(u"%s"' % var in body:
                lines[idx] = ref.sub(
                    lambda mm: u'invar(u"v%s_%s"' % (mm.group(1)[2:], mm.group(2)),
                    ln, count=1)
                while ref.search(lines[idx]):
                    lines[idx] = ref.sub(
                        lambda mm: u'invar(u"v%s_%s"' % (mm.group(1)[2:], mm.group(2)),
                        lines[idx], count=1)
                continue
            reads.setdefault(var, (fb, pin, idx))
            lines[idx] = ref.sub(
                lambda mm: u'invar(u"v%s_%s"' % (mm.group(1)[2:], mm.group(2)), ln, count=1)
            while ref.search(lines[idx]):
                lines[idx] = ref.sub(
                    lambda mm: u'invar(u"v%s_%s"' % (mm.group(1)[2:], mm.group(2)),
                    lines[idx], count=1)

    if not reads:
        sys.stdout.write(u"chtenij vyhodov FB ne najdeno\n")
        return

    # 1) obyavleniya
    decl = [u"    " + MARK + u":",
            u"    #  Pochemu tak: pryamaya ssylka invar(u\"fbXX.PIN\") privodit",
            u"    #  k oshibkam C32 pri generacii koda dlya zadachi (naydeno bisekciej).",
            u"    #  Cherez peremennuyu svyaz' stanovitsya obychnoj."]
    for var in sorted(reads):
        fb, pin, _ = reads[var]
        fbn = INSTANCES[fb][0]
        tp = types.get(fbn, {}).get(pin, u"BYTE")
        decl.append(u'    p.var(u"%s", u"%s", u"%s.%s")' % (var, tp, fb, pin))
    decl.append(u"")
    anchor = None
    for idx, ln in enumerate(lines):
        if u'p.var(u"fbBIOS"' in ln:
            anchor = idx
            break
    if anchor is None:
        sys.stdout.write(u"anker ne najden\n")
        return
    lines = lines[:anchor + 1] + decl + lines[anchor + 1:]

    # 2) zapis vyhodov v peremennye -- v seti vyzova sootvetstvuyushchego FB
    body = u"\n".join(lines)
    for var in sorted(reads):
        fb, pin, _ = reads[var]
        net = INSTANCES[fb][1]
        if not net:
            continue
        #  ishem stroku s vyzovom etogo FB v seti net
        i2 = body.find(u"%s.block(u\"%s\"" % (net, INSTANCES[fb][0]))
        if i2 < 0:
            i2 = body.find(u"%s.block(u\"%s\"" % (net, INSTANCES[fb][0]))
        if i2 < 0:
            sys.stdout.write(u"  vyzov %s v seti %s ne najden\n" % (fb, net))
            continue
        #  konec vyzova -- pervyy ") na nachale sleduyushchey stroki
        e = body.find(u"\n", body.find(u"instance=u\"%s\")" % fb, i2))
        if e < 0:
            sys.stdout.write(u"  konec vyzova %s ne najden\n" % fb)
            continue
        ins = (u'\n    %s.outvar(u"%s", %s.invar(u"%s.%s", y=30))'
               % (net, var, net, fb, pin))
        body = body[:e] + ins + body[e:]

    io.open(GEN, u"w", encoding=u"utf-8").write(t[:i] + body + t[j:])
    sys.stdout.write(u"pereneseno chteniy: %d\n" % len(reads))
    for var in sorted(reads):
        fb, pin, _ = reads[var]
        sys.stdout.write(u"    %-24s %s.%s\n" % (var, fb, pin))


if __name__ == u"__main__":
    main()
