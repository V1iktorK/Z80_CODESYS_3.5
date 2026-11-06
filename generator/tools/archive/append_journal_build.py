# -*- coding: utf-8 -*-
u"""Dopisat' v zhurnal rezul'taty proverki kataloga build.

ZAPUSKAT SISTEMNYM PYTHON 3 ODIN RAZ.
"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JOURNAL = os.path.join(ROOT, u"docs", u"03_ЖУРНАЛ_СБОРКИ.md")

TEXT = u"""

## 5. Poryadok v kataloge build i prodolzhenie poiska C32

### Chto bylo ne tak v kataloge build

Tam lezhali vosem fajlov, i dva iz nih byli lishnimi:

| Fajl | Otkuda vzyalsya | Pochemu lishnij |
|---|---|---|
| `Z80_EMU.project` | sborka | nuzhen |
| `Z80_EMU-AllUsers.opt`, `Z80_EMU-<polzovatel>.opt` | CODESYS | nuzhny, eto nastroyki okna |
| `Z80_EMU_project.precompilecache` | CODESYS | kes kompilyacii, sozdaetsya zanovo |
| `Z80_EMU_для_IDE.project` | moj `Copy-Item` | **lishnij**: eto kopiya, kotoruyu ya klal dlya peredachi, no po pravilam ee mesto v korne proekta |
| `Z80_EMU_для_IDE-AllUsers.opt`, `...-<polzovatel>.opt` | CODESYS | **lishnie**: oni ot kopii, kotoroj v build byt ne dolzhno |

Kopiya v `build` eshche i vvodila v zabluzhdenie: ona byla ot 5:29, to est
soderzhala STAROE sostoyanie proekta (s temi samymi oshibkami C0135/C0006,
o kotoryh soobshchil polzovatel), i pri otkrytii ej mozhno bylo poluchit
kartinu, ne otnosyashchuyusya k tekushchej sborke.

**Reshenie.** `build/` ochishchen i soderzhit tolko to, chto sozdaet sborka.
Kopiya dlya IDE delaetsya v koren proekta. Krome togo, ubrany ostatki ot
diagnosticheskih proektov (`iso_project`, `type_probe`) -- ih fajly `.opt`
i `.precompilecache` lezhali v korne i pomeshali by.

### Defekt 26: uslovie SEL -- rezul'tat obobshchennogo bloka OR

Eto okazalas samaya krupnaya chast ostavshihsya oshibok C32 (12 iz 17).

Simptom: `C32: Nevozmozhno konvertirovat tip 'USINT' v tip 'BOOL'`.

**Prichina.** V seti I/O-portov usloviem dlya `SEL` sluzhil rezul'tat bloka
`OR` nad dvumya znacheniyami `BOOL`:

```python
io_addr = b_sel(n16, ..., b_or(n16, ..., c_ioen, c_iowr), const("0"), c_n)
```

Blok `OR` v IEC obobshchennyy (`ANY_BIT`). CODESYS vyvodit ego tip kak `BYTE`
(USINT), a zatem trebuet na vhode `G` u `SEL` imenno `BOOL` -- i otvergaet
svoyu zhe vyvodku. Poluchaetsya zamknutyy krug, kotoryj kompilyator reshaet
oshibkoj.

**Reshenie.** Uslovie provoditsya cherez otdelnuyu peremennuyu `BOOL`:

```python
n16.outvar(u"vIOEn", b_or(n16, ..., c_ioen, c_iowr), ...)
io_addr = b_sel(n16, ..., n16.invar(u"vIOEn"), const("0"), c_n)
```

Prisvaivanie srazu zadaet tip, i obobshchennost bloka bolshe ne meshает.

**Kak najdeno.** Analizator tipov (`diag_types_real.py`) soobshchil
`SEL vhod 1 (BOOL) <- BITS`, a `find_bad_sel.py` pokazal konkretnye bloki
s usloviem ot `OR`. Do etogo tri popytki najti prichinu glazami i
avtomaticheskimi proverkami ne udalis: instrumenty ne zamechali, chto tip
usloviya vyveden iz obobshchennogo bloka.

### Defekt 27: vyhody FB chitalis napryamuyu

Simptom: `C32` pri generacii koda dlya tsiklicheskoj zadachi.

**Prichina.** V sheme ostavalis chteniya vida `n8.invar(u"fbALU.Y")` --
ssylka na vyhod ekzemplyara FB. Ih bylo 15 (`fbALU.*`, `fbRF.*`, `fbRFRd.*`,
`fbClock.*`, `fbIR.Q`, `fbPCLatch.Q`).

**Reshenie** (chastichno primenено). Kazhdyj takoy vyhod perevoditsya v
lokalnuyu peremennuyu: obyavlenie `p.var`, zapis v seti vyzova FB i chtenie
uzhe peremennoy. Instrument: `generator/tools/patch_fb_reads.py`.

**Vazhnyj urok pro avtomatizaciyu.** Pervaya popytka sdelat eto regulyarkoj po
vsemu tekstu ZATERLA HVOSTY mnogostrochnyh vyzovov i slomala generator
(`IndentationError`). Pravilnyj podhod -- menyat tolko imya vnutri `invar`,
po odnoj stroke. Eto stoit zapomnit: v etom generatore vyzovy chasto
mnogostrochnye, i lyubaya zamena po tekstu dolzhna byt postrochnoj.

### Sostoyanie posle etogo etapa

| Proverka | Rezultat |
|---|---|
| Import v CODESYS | 31 iz 31 |
| Kod v razdele obyavlenij | 0 POU |
| Obyavleniya protiv `<interface>` | 0 rashozhdenij iz 31 POU |
| Neob''yavlennye signaly shem | 0 |
| Bit ye ssylki na GVL | 0 |
| Poryadok vhodov pri vyzovah FB | 0 rassozhdenij |
| Oshibki kompilyacii | 17 unikalnyh (C32) + 10 par C46/C35 |
| Preduprezhdeniya | 2 (C139: kod bez dejstviya) |

**Chto dayut ostavshiesya C32.** Oni zhivut v odnoj sheme -- `PLC_PRG` -- i
poyavlyayutsya tolko pri kompilyacii dlya zadachi. Ih sledstvie -- pary
C46/C35: poka tipy ne shyutsya, ekzemplyary ST-programm ne sozdayutsya, i
zadacha ih "ne vidit". To est 20 iz 37 soobshchenij -- proizvodnye.

**Chto delat dalshe.** Ostavshiesya C32 -- eto konversii `USINT<->BOOL` i
`WORD->BYTE`. Instrument dlya poiska:
`generator/tools/diag_types_real.py PLC_PRG` (vyvod tipov po vhodam blokov)
i `find_bad_sel.py PLC_PRG` (usloviya `SEL` ne buleva tipa). Sleduyushchij
shag -- dobrat analogichnye mesta, gde obobshchennyy blok (`AND`, `OR`, `ADD`)
pitает vhod s strogo zadannym tipom.
"""


def main():
    t = io.open(JOURNAL, encoding=u"utf-8").read()
    if u"### Defekt 26" in t:
        sys.stdout.write(u"uzhe dopisano\n")
        return
    io.open(JOURNAL, u"a", encoding=u"utf-8").write(TEXT)
    sys.stdout.write(u"zhurnal dopolnen\n")


if __name__ == u"__main__":
    main()
