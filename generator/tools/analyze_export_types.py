# -*- coding: utf-8 -*-
u"""R A Z B O R  vygruzhennogo POU: kakie tipy CODESYS vyvel dlya blokov SEL.

Chto smotrim. V vygruzhennom PLCopenXML u kazhdogo vyzova bloka est addData
s razdelami inputparamtypes / outputparamtypes. Tam zapisany tipy, kotorye
CODESYS V Y V E L  S A M. Esli u bloka SEL vhod IN0 poluchil tip USINT,
a vyhod ego pitayot peremennaya BYTE ili BOOL, -- vot ona, oshibka C32,
s tochnym localId. Nikakoj bisekcii po setyam bolshe ne nuzhno.

ZAPUSK: python generator\tools\analyze_export_types.py
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
LOG = os.path.join(ROOT, u"log")

WC = (u"BOOL", u"BYTE", u"WORD", u"DWORD")


def load(name):
    p = os.path.join(LOG, u"diag_types_%s.xml" % name)
    if not os.path.exists(p):
        return None
    return io.open(p, encoding=u"utf-8").read()


def param_types(seg):
    u"""Dostat spisok tipov iz inputparamtypes / outputparamtypes."""
    m = re.search(u'name="[^"]*/(input|output)paramtypes"[^>]*>(.*?)</data>',
                  seg, re.S)
    if not m:
        return []
    body = m.group(2)
    body = body.replace(u"&quot;", u'"').replace(u"&#xA;", u" ")
    #  tipy perechisleny cherez zapyatuyu vnutri <xhtml>...</xhtml>
    x = re.search(u"<xhtml[^>]*>(.*?)</xhtml>", body, re.S)
    if not x:
        return []
    txt = re.sub(u"<[^>]+>", u" ", x.group(1))
    out = [t.strip() for t in re.split(u"[,;]", txt) if t.strip()]
    return out


def analyse(name):
    t = load(name)
    if t is None:
        sys.stdout.write(u"  %s: net vygruzki\n" % name)
        return []
    #  karty: localId -> imya peremennoj (iz outVariable)
    dst = {}
    for m in re.finditer(u'<outVariable localId="(\\d+)"[^>]*>(.*?)</outVariable>',
                         t, re.S):
        e = re.search(u"<expression>([^<]*)</expression>", m.group(2))
        if e:
            dst[m.group(1)] = e.group(1)
    #  tipy obyavlennyh peremennyh
    decl = {}
    for m in re.finditer(u'<variable name="(\\w+)">\\s*<type>\\s*<(\\w+)\\s*/>', t):
        decl[m.group(1)] = m.group(2)

    bad = []
    #  razbor kazhdogo bloka
    blocks = list(re.finditer(u'<block localId="(\\d+)" typeName="([\\w]+)"', t))
    for idx, m in enumerate(blocks):
        bid, btyp = m.group(1), m.group(2)
        end = blocks[idx + 1].start() if idx + 1 < len(blocks) else len(t)
        seg = t[m.start():end]
        outs = param_types(seg)
        if not outs:
            continue
        typ = outs[0] if outs else None
        if btyp == u"SEL":
            #  vyhod SEL: kuda on idet
            tgt = t.find(u'refLocalId="%s"' % bid)
            if tgt < 0:
                continue
            #  najti outVariable, gde est ssylka na etot localId
            for om in re.finditer(u'<outVariable localId="(\\d+)"[^>]*>(.*?)'
                                  u'</outVariable>', t, re.S):
                if (u'refLocalId="%s"' % bid) in om.group(2):
                    tn = dst.get(om.group(1), u"?")
                    tt = decl.get(tn)
                    if tt and typ and typ != tt:
                        bad.append(u"%s: SEL %s vyvod %s -> peremennaya %s (%s)"
                                   % (name, bid, typ, tn, tt))
                    break
    return bad


def main():
    try:
        sys.stdout.reconfigure(encoding=u"utf-8", errors=u"replace")
    except Exception:                                          # noqa: BLE001
        pass
    sys.stdout.write(u"=== analyze_export_types ===\n")
    total = 0
    for nm in (u"FB_IO_Ports", u"FB_RegFileZ80", u"PLC_PRG",
               u"FB_DecoderZ80", u"FB_ALU_Z80"):
        for b in analyse(nm):
            sys.stdout.write(u"  %s\n" % b)
            total += 1
    sys.stdout.write(u"nesootvetstvij: %d\n" % total)
    return 0


if __name__ == u"__main__":
    sys.exit(main())
