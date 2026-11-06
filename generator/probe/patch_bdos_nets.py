# -*- coding: utf-8 -*-
u"""patch_bdos_nets.py -- raznosit vyhody FB_CPM_BDOS po setyam.

PRICHINA POTERI 12 BLOKOV (najdena sravneniem do/posle importa):
    v seti 4 chitalis CHEtyRE vyhoda odnogo ekzempl yara FB_CPM_BDOS
    (Set_DMA, F_Size, Ret_Mode, Ret_Val). Po pravilu proekta, kotoroe my
    vyyasnili na FB_HW_IO_PLC, eto vyglyadit kak fan-out: biblioteka schitaet
    ssylki na localId BLOKA, i pri >1 ssylke v odnoy seti pytaetsya klonirovat
    vyzov FB.

    Pri etom import NE padal i NE soobshchal oshibku -- CODESYS molcha otbrosil
    chast seti. Imenno po etomu schetchik verify i poyavilsya: 720 -> 708.

REShenie: kazhdyy vyhod -- v SVOEY seti.
"""

import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GEN = os.path.join(ROOT, "generator", "gen_z80.py")

t = io.open(GEN, "r", encoding="utf-8").read()

old = u'''    n4.outvar(u"Set_DMA", f26, x=F.COL_OUT, y=30)
    n4.outvar(u"F_Size", f35, x=F.COL_OUT, y=190)'''
new = u'''    n4.outvar(u"Set_DMA", f26, x=F.COL_OUT, y=30)'''
assert old in t, u"ne najdeny vyhody Set_DMA/F_Size"
t = t.replace(old, new, 1)

old2 = u'''    rm4 = b_or(n4, F.COL_BLK2 + 480, 390, rm3, f27m)
    n4.outvar(u"Ret_Mode", rm4, x=F.COL_OUT + 300, y=390)

    # --- 32 F_USERNUM: otvet 0 (polzovatel 0) ---
    f32v = b_and(n4, F.COL_BLK2 + 160, 430, f32, n4.const(u"0", y=444))
    f32w = b_b2w(n4, F.COL_BLK2 + 320, 430, f32v)
    n4.outvar(u"Ret_Val", f32w, x=F.COL_OUT + 300, y=430)'''
new2 = u'''    rm4 = b_or(n4, F.COL_BLK2 + 480, 390, rm3, f27m)
    n4.outvar(u"Ret_Mode", rm4, x=F.COL_OUT + 300, y=390)

    # --- 32 F_USERNUM: otvet 0 (polzovatel 0) ---
    f32v = b_and(n4, F.COL_BLK2 + 160, 430, f32, n4.const(u"0", y=444))
    f32w = b_b2w(n4, F.COL_BLK2 + 320, 430, f32v)
    n4.outvar(u"Ret_Val", f32w, x=F.COL_OUT + 300, y=430)

    # ================= SET 6: OTDEL NYE SETI DLYa KAZhDOGO VYHODA =========
    # KAZhDYY vyhod FB_CPM_BDOS chitaetsya v SVOEY seti: inache biblioteka
    # vidit fan-out i CODESYS molcha otbrasyvaet chast seti (proverено:
    # 12 blokov iz 40 ne doehali). Set_DMA i F_Size uzhe vyvedeny v seti 4,
    # poetomu zdes tolko te, chto chitayutsya otdel no.
    n6 = p.network(u"SET 6: vyhody BDOS: priznaki dlya ST-drajvera")
    n6.outvar(u"vBdosSetDMA", n6.invar(u"fbBdos.Set_DMA", y=30),
              x=F.COL_OUT, y=30)

    n7 = p.network(u"SET 7: vyhody BDOS: razmer fajla")
    n7.outvar(u"vBdosFSize", n7.invar(u"fbBdos.F_Size", y=30),
              x=F.COL_OUT, y=30)

    n8 = p.network(u"SET 8: vyhody BDOS: rezhim raboty s pamyat yu")
    n8.outvar(u"vBdosRetMode", n8.invar(u"fbBdos.Ret_Mode", y=30),
              x=F.COL_OUT, y=30)

    n9 = p.network(u"SET 9: vyhody BDOS: gotovyy otvet")
    n9.outvar(u"vBdosRetVal", n9.invar(u"fbBdos.Ret_Val", y=30),
              x=F.COL_OUT, y=30)

    n10b = p.network(u"SET 10b: vyhody BDOS: rezhim vyvoda")
    n10b.outvar(u"vBdosOutMode", n10b.invar(u"fbBdos.Out_Mode", y=30),
                x=F.COL_OUT, y=30)'''
assert old2 in t, u"ne najden blok Ret_Val"
t = t.replace(old2, new2, 1)

io.open(GEN, "w", encoding="utf-8").write(t)
print(u"PATCH BDOS_NETS OK")
