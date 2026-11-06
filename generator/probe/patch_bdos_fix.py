# -*- coding: utf-8 -*-
u"""patch_bdos_fix.py -- ubiraet iz FB_CPM_BDOS obrashchenie k massivu.

PRICHINA PADENIYA KOMPILYATORA (izolirovano eksperimentom):
    v FB_CPM_BDOS byla stroka
        mem_ch = n1.invar(u"Z80_Mem[DE_Reg]", y=240)
    to est indeksatsiya massiva v FBD. Kompilyator CODESYS na etom padaet
    (ta zhe prichina, chto i s MEM_READ/MEM_WRITE ranee).

PRAVILO PROEKTA (okonchatel noe):
    v FBD nelzya ni indeksirovat massiv, ni shagat po nemu. Poetomu
    FB_CPM_BDOS rabotaet tolko so SKALYaRAMI (registr C, slovo DE, bufery
    konsoli), a operatsii s pamyat yu (vyvod stroki do $, vvod stroki,
    katalog diska) vypolnyaet ST-drajver PRG_CPM_BDOS -- eto razreshennaya
    zadaniem tochka primeneniya ST dlya raboty s massivami.

Chto menyaetsya:
  1) iz FB_CPM_BDOS udalyayutsya seti s obrashcheniem k massivu;
  2) dobavlyaetsya vyhod Out_Mode: 0 = net vyvoda, 1 = vyvesti odin simvol
     (funktsiya 2), 2 = vyvesti stroku do $ (funktsiya 9) -- stroku obrabatyvaet ST.
"""

import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GEN = os.path.join(ROOT, "generator", "gen_z80.py")

t = io.open(GEN, "r", encoding="utf-8").read()

# --- 1. udalit obrashchenie k massivu i peredelat vybor simvola ---------------
old = u'''    # vybor simvola dlya vyvoda: dlya 2 -- mladshij bajt DE, dlya 9 -- iz pamyati
    e_lo = b_w2b(n1, F.COL_BLK2 + 160, 60, c_de)
    mem_ch = n1.invar(u"Z80_Mem[DE_Reg]", y=240)
    ch_sel = b_sel(n1, F.COL_BLK2 + 320, 120, f9, e_lo, mem_ch)
    # vyvod est dlya 2 i 9
    wr_any = b_or(n1, F.COL_BLK2 + 320, 60, f2, f9)
    n1.outvar(u"Con_Out", ch_sel, x=F.COL_OUT + 300, y=120)
    n1.outvar(u"Con_Wr", b_and(n1, F.COL_BLK2 + 480, 60, wr_any, c_en),
              x=F.COL_OUT + 300, y=60)'''
new = u'''    # Simvol dlya vyvoda beretsya iz mladshego bajta DE (funktsiya 2).
    # Dlya funktsii 9 stroku chitaet ST-drajver: v FBD nelzya shagat po massivu.
    e_lo = b_w2b(n1, F.COL_BLK2 + 160, 60, c_de)
    n1.outvar(u"Con_Out", e_lo, x=F.COL_OUT + 300, y=120)
    n1.outvar(u"Con_Wr", b_and(n1, F.COL_BLK2 + 320, 60, f2, c_en),
              x=F.COL_OUT + 300, y=60)
    # Rezhim vyvoda dlya ST-drajvera: 2 -> odin simvol, 9 -> stroka do $
    mode2 = b_sel(n1, F.COL_BLK2 + 320, 190, f9,
                  n1.const(u"2", y=204), n1.const(u"0", y=234))
    mode_all = b_sel(n1, F.COL_BLK2 + 480, 190, f2,
                     n1.const(u"1", y=204), mode2)
    n1.outvar(u"Out_Mode", mode_all, x=F.COL_OUT + 300, y=190)'''
assert old in t, u"ne najden blok vyvoda simvola v FB_CPM_BDOS"
t = t.replace(old, new, 1)

# --- 2. dobavit vyhod Out_Mode v obyavlenie -----------------------------------
old2 = u'''    p.var_out(u"Err", u"BYTE", u"kod oshibki")'''
new2 = u'''    p.var_out(u"Err", u"BYTE", u"kod oshibki")
    p.var_out(u"Out_Mode", u"BYTE",
              u"rezhim vyvoda: 0 net, 1 odin simvol, 2 stroka do $")'''
assert old2 in t, u"ne najden vyhod Err"
t = t.replace(old2, new2, 1)

io.open(GEN, "w", encoding="utf-8").write(t)
print(u"PATCH BDOS_FIX OK")
