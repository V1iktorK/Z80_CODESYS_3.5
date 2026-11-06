# -*- coding: utf-8 -*-
u"""P R A V K A  sel_chain: yavnaya tipizaciya vetok + b_sel s tipom.

P O Ch E M U  O T D E L N Y J  S K R I P T. Fajl gen_z80.py bolshoj, i
pravka cherez regulyarku po vsemu tekstu uzhe dva raza portila ego hvosty
mnogostrochnyh vyzovov. Zdes my menyaem STROKI PO NOMERAM i tolko v
predelah odnoj funkcii, a potom proveryaem sintaksis.

Ch T O  M E N Ya E M:
  1) telo sel_chain -- vmesto prostoj cepochki stavim cepochku s
     n.typed() dlya kazhdoj vetki i dlya IN0;
  2) b_sel -- dobavlyaem neobyazatelnyy parametr tip i primenyaem typed().
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GEN = os.path.join(ROOT, u"generator", u"gen_z80.py")

NEW_TAIL = [
    u'    tip = (tip or u"BYTE").upper()',
    u'    #  T I P I Z A C I Ya  V E T O K -- sm. Network.typed() v fbd_xml.py.',
    u'    #  U kazhdoj vetki tip zadayotsya Y A V N O (BYTE#16#00 vmesto 16#00),',
    u'    #  poetomu obobshchennyj SEL poluchaet odnoznachnyj tip i pary oshibok',
    u'    #  "C32: BOOL <-> USINT" ischezayut.',
    u'    #',
    u'    #  Chto bylo pereprobovano ranee i N E  P O D O Sh L O (chtoby ne',
    u'    #  povtoryat):',
    u'    #   1) konversiya "BYTE_TO_BYTE" dlya vetok -- v CODESYS takoy funkcii',
    u'    #      NET: 76 oshibok "C46: Identifikator \'BYTE_TO_BYTE\' ne zadan";',
    u'    #   2) promezhutochnye peremennye v T E L E seti -- CODESYS obyavlyaet',
    u'    #      ih "lazy" i ne vyvodit tip;',
    u'    #   3) promezhutochnye peremennye v obyavlenii POU so vsemi',
    u'    #      prisvoeniyami v odnoj seti -- kompilyator na etom ZAVISAET.',
    u'    #  Rabotaet imenno yavnaya tipizaciya literala: vybora u kompilyatora',
    u'    #  ne ostayotsya.',
    u'    in0 = n.typed(in0, tip)',
    u'    cases = [(cond, n.typed(val, tip)) for cond, val in cases]',
    u'    cur = in0',
    u'    y = y0',
    u'    for cond, val in cases:',
    u'        d = n.block(u"SEL", [(u"G", cond), (u"IN0", cur), (u"IN1", val)], [POUT],',
    u'                    x=x, y=y)',
    u'        cur = d',
    u'        y += ystep',
    u'    return cur',
]


def main():
    try:
        sys.stdout.reconfigure(encoding=u"utf-8", errors=u"replace")
    except Exception:                                          # noqa: BLE001
        pass
    lines = io.open(GEN, encoding=u"utf-8").read().split(u"\n")

    # --- 1. najti nachalo tela sel_chain: stroka "    tip = (tip or"
    i_tip = None
    for n, l in enumerate(lines):
        if l.strip().startswith(u"tip = (tip or"):
            i_tip = n
            break
    if i_tip is None:
        sys.stdout.write(u"NE NAJDENA stroka 'tip = (tip or'\n")
        return 1
    #  konec tela -- stroka "    return cur" posle nee
    i_ret = None
    for n in range(i_tip, min(i_tip + 60, len(lines))):
        if lines[n].strip() == u"return cur":
            i_ret = n
            break
    if i_ret is None:
        sys.stdout.write(u"NE NAJDEN 'return cur' posle sel_chain\n")
        return 1
    sys.stdout.write(u"sel_chain: telo so stroki %d po %d (%d strok) -> %d\n"
                     % (i_tip + 1, i_ret + 1, i_ret - i_tip + 1, len(NEW_TAIL)))
    lines[i_tip:i_ret + 1] = NEW_TAIL

    # --- 2. b_sel: dobavit parametr tip i primenit typed
    out = []
    done_b_sel = 0
    skip = 0
    for n, l in enumerate(lines):
        if skip > 0:
            skip -= 1
            continue
        if l.startswith(u'def b_sel(n, x, y, g, in0, in1):'):
            out.append(u'def b_sel(n, x, y, g, in0, in1, tip=None):')
            out.append(u'    u"""Vybor iz dvuh: G=0 -> in0, G=1 -> in1.')
            out.append(u'')
            out.append(u'    tip -- tip rezul tata (naprimer u"BYTE"). Nuzhen potomu,')
            out.append(u'    chto blok SEL obobshchennyj: bez nego literaly v vetkah')
            out.append(u'    poluchayut tip po usmotreniyu kompilyatora, i v cepochke')
            out.append(u'    iz neskolkih SEL eto daet "C32: BOOL <-> USINT".')
            out.append(u'    """')
            out.append(u'    if tip:')
            out.append(u'        in0 = n.typed(in0, tip)')
            out.append(u'        in1 = n.typed(in1, tip)')
            out.append(u'    return n.block(u"SEL", [(u"G", g), (u"IN0", in0), (u"IN1", in1)],')
            out.append(u'                    [POUT], x=x, y=y)')
            #  propustit DVE stroki starogo return (vydacha i prodolzhenie)
            skip = 2
            done_b_sel += 1
            continue
        out.append(l)
    lines = out

    io.open(GEN, u"w", encoding=u"utf-8").write(u"\n".join(lines))
    sys.stdout.write(u"b_sel perepisan: %d\n" % done_b_sel)
    return 0


if __name__ == u"__main__":
    sys.exit(main())
