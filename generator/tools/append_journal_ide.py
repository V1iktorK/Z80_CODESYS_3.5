# -*- coding: utf-8 -*-
u"""Dopisat' v zhurnal razdel pro defekty 23-25 (po otchyotu polzovatelya).

ZAPUSKAT SISTEMNYM PYTHON 3 ODIN RAZ.
"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JOURNAL = os.path.join(ROOT, u"docs", u"03_ЖУРНАЛ_СБОРКИ.md")

TEXT = u"""

## 4. Razbor otchyota iz IDE (defekty 23-25)

Polzovatel otkryl `Z80_EMU_для_IDE.project` i prislal spisok oshibok. Imena
POU i nomera strok srazu pokazali tri prichiny, kotoryh moya proverka ne
videla.

### Defekt 23: v obyavlenie popadalo TELO programmy

Simptom: sotni oshibok vida
    TEST_Z80_CPM (Stroka 221 (Ob''yavl.)): C0006: ', AT ili :' trebuetsya vmesto '.'
    TEST_Z80_CPM (Stroka 238 (Ob''yavl.)): C0135: Takoj kod nedopustim v razdele obyavleniya
    TEST_Z80_CPM (Stroka 2 (Realiz.)):    C0046: Identifikator 'bFirst' ne zadan
    TEST_Z80_CPM (Stroka 6 (Realiz.)):    C0004: 'Tests' ne yavlyaetsya komponentom 'GVL_Tests_CPM'

**Prichina.** V PLCopenXML tekst obyavleniya peredaetsya v
`<InterfaceAsPlainText>`. Tuda uhodil POLNYY tekst POU -- i obyavlenie,
i telo. CODESYS chital telo kak obyavlenie: pervaya zhe stroka tela
(`GVL_Tests_CPM.Tests[i].Id := i;`) -- eto tochka tam, gde ozhidayutsya
zapyataya ili dvoetochie, otsyuda C0006. Posle C0135 ("kod nedopustim v
razdele obyavleniya") razdel obyavlenij okazyvalsya pustym, i vse lokalnye
peremennye stanovilis neizvestnymi -- otsyuda sotni C0046/C0004 v realizacii.

**Pochemu ne zametil ranshe.** Moya proverka `verify_decl.py` sravnivala
sekcii strukturnogo `<interface>` s TEKSTOM i nashla 0 rashozhdenij: tekst
soderzhal obyavlenie, prosto vmeste s lishnim. Setchik ne otvechal na vopros
"est li v tekste TO, CHEGO BYT NE DOLZhNO".

**Reshenie.** Dobavlen `TextPou._header_only()`: v `<InterfaceAsPlainText>`
idet tolko stroka zagolovka POU i bloki `VAR...END_VAR`. Dobavlena otdelnaya
proverka `generator/tools/check_decl_only.py`, kotoraya vyrezayet kommentarii
i znacheniya po umolchaniyu (oni zakonny) i ishchet v razdele obyavlenij
nastoyashchij kod. Rezultat: **0 POU s kodom v obyavlenii.**

### Defekt 24: signaly dekodera ne byli ni v GVL, ni v peremennyh POU

Simptom: `C4: 'Ctl_Is_Jr' ne yavlyaetsya komponentom 'GVL_Control'`,
`C46: Identifikator 'vCtl_IO_Rd' ne zadan`.

**Prichina.** Shema peredavala iz dekodera 16 signalov upravleniya, a v
`GVL_Control` byli ob''yavleny ne vse: `Ctl_Is_Jr`, `Ctl_IO_Rd`, `Ctl_IO_Wr`
propushcheny. Krome togo, vyhody ekzemplyara chitalis napryamuyu
(`n4.invar(u"fbDec.Ctl_Is_CALL")`) -- konstrukciya, kotoraya pri generacii
koda dlya tsiklicheskoj zadachi daet oshibki konversii tipov.

**Reshenie.** 1) Vse 20 signalov dekodera perechisleny v odnom meste
(`ctl_names`); 2) kazhdyj vyhod pishetsya snachala v lokalnuyu peremennuyu
`vCtl_*`, i tolko potom v GVL dlya drugih POU; 3) vnutri `PLC_PRG`
potrebiteli chitayut lokalnye peremennye, a ne GVL.

### Defekt 25: tipy peremennyh, vvedennyh avtomaticheski

Simptom: posle perenosa vyhodov FB v peremennye dobavilos 26 novyh oshibok
`C32: Nevozmozhno konvertirovat tip ...`.

**Prichina.** Skript-perenos prisvoil VSEM novym peremennym tip `BYTE`.
A realnye tipy vyhodov raznye: `PC_New` i `SP` -- `WORD`, `Halted` i
`PC_Load` -- `BOOL`, i tolko `Y`, `F`, `Inc_By`, `Q` -- `BYTE`.

**Reshenie.** Tipy vzyaty ne na glaz, a iz strukturnogo `<interface>`
sotvetstvuyushchih FB (`generator/tools/fix_fb_var_types.py`). Pravka
primenena dlya vseh 14 peremennoy.

### Chto eshhe najdeno poputno

* Mertvaya ssylka `vCtl_Cond` tipa `BYTE` v seti upravleniya potokom: ona
  ni v chem ne uchastvovala (uslovie perehoda schitaetsya iz bita 6 registra F),
  no imenno ona davala `C32: USINT v BOOL`. Udalena.
* Dve seti (`SET 15`, `SET 16`) pri bisekcii ostavlyali "visit" svyazi i
  davali C7/C9 -- eto artefakt instrumenta `hide_net.py`, a ne proekta.
* `app.pou_call(imya)` -- takogo metoda net, i popytka ego vyzvat valit CLR
  tselikom: "Fatal error. Internal CLR error. (0x80131506)". Metod ubran.

### Chto ostalos

17 oshibok `C32` (konversiya tipov) v sheme `PLC_PRG`. Oni vosproizvodyatsya
usto chivo i lokalizovany: poyavlyayutsya tolko togda, kogda `PLC_PRG`
zaregistrirovan v zadache (bez zadachi -- 0 oshibok). Bisekciej po setyam
vyyasneno, chto kazhdaya iz nih po otdelnosti ne vinovata: udalenie lyuboj
odnoj (krome `SET 6`, kotoraya daet -1) ne menyaet schetchik. Eto znachit,
chto prichina -- vo vzaimodejstvii setey, i iskat nado ne "plohuyu set'', a
neskolko svyazannyh.

Instrumenty dlya prodolzheniya gotovy:
  * `generator/tools/diag_dst_types.py PLC_PRG` -- tip kazhdogo priemnika
    protiv tipa istochnika;
  * `generator/tools/diag_full_types.py PLC_PRG` -- polnaya karta svyazey;
  * `generator/tools/hide_net.py off "SET N"` -- bisekciya setey;
  * `generator/run_build_log.cmd` -- sborka s zapis'yu vyvoda CODESYS.

### Svodka po itogam dvuh etapov revizii

| Proverka | Rezultat |
|---|---|
| Kod v razdele obyavlenij | 0 POU |
| Obyavleniya protiv `<interface>` | 0 rashozhdenij iz 31 POU |
| Neob''yavlennye signaly shem | 0 |
| Bit ye ssylki na GVL | 0 iz 118 |
| Kollizii imen mezhdu GVL | 0 iz 169 |
| Obyavleniya v pole realizacii | 0 |
| Oshibki kompilyacii | 146 -> 17 (vse C32 v odnoj sheme) |
"""


def main():
    t = io.open(JOURNAL, encoding=u"utf-8").read()
    if u"### Defekt 23" in t:
        sys.stdout.write(u"uzhe dopisano\n")
        return
    io.open(JOURNAL, u"a", encoding=u"utf-8").write(TEXT)
    sys.stdout.write(u"zhurnal dopolnen\n")


if __name__ == u"__main__":
    main()
