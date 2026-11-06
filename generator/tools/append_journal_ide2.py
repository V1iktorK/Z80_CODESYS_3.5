# -*- coding: utf-8 -*-
u"""Dopisat' v zhurnal razdel pro otchyot iz IDE (defekty 28-30).

ZAPUSKAT SISTEMNYM PYTHON 3 ODIN RAZ.
"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JOURNAL = os.path.join(ROOT, u"docs", u"03_ЖУРНАЛ_СБОРКИ.md")

TEXT = u"""

## 6. Razbor vtorogo otchyota iz IDE (defekty 28-30)

### Defekt 28: struktura ST_TestCase obyavlena DVAZhDY, vtoraya koroche

Simptom: sotni oshibok vida
    C0046: Identifikator 'Init_HL' ne zadаn
    C0004: 'Init_HL' ne yavlyaetsya komponentom 'ST_TestCase'
    C0046: Identifikator 'Opcode_Lo', 'Exp_Mem', 'Mask_Flag' ne zadаn

**Prichina.** V `generator/build.py` peremennaya `DUT_TESTCASE` opredelena
DVA raza. Pervoe opredelenie -- polnoe, 23 polya (`Opcode_Lo`, `Init_HL`,
`Exp_Mem`, `Exp_Mem_Addr`, `Mask_Mem`, `Mask_Flag`, `Test_Has_Cond`...).
Vtoroe -- urezannoe, 16 polej. Python ostavlyaet poslednee znachenie,
poetomu v proekt popadala korotkaya struktura, a ST-kod pisal v polya,
kotoryh tam net.

**Reshenie.** Vtoroe (korotkoe) opredelenie udaleno. Struktura ostalas
v polnom vide -- imenno ona nuzhna, potomu chto ST-kod ispolzuet vse 23 polya.

**Kak najdeno.** Instrument `generator/tools/check_testcase_fields.py`
sravnivaet polya, realno ispolzuemye kodom ST, s tem, chto obyavleno
v kazhdom variante DUT. On i pokazal dva varianta i spisok propavshih polej.

### Defekt 29: v GVL ne bylo massiva testov

Simptom: `C0046: Identifikator 'Tests' ne zadаn`,
`C0004: 'Tests' ne yavlyaetsya komponentom 'GVL_Tests'` -- i to zhe dlya
`GVL_Tests_CPM`. Oshibki povtoryayutsya v kazhdoj vtoroj stroke programmy.

**Prichina.** Massiv struktur s opisaniem proverok
(`Tests : ARRAY[1..N] OF ST_TestCase`) ne byl obyavlen NIGDE -- ni v GVL,
ni v generatore. ST-kod ego aktivno zapolnyaet
(`GVL_Tests.Cpu_Tests[i].Id := i`), a obyavleniya net.

**Reshenie.** Massivy dobavleny i pereimenovany po obshchemu pravilu
proekta (prefiks -- imya nabora):
    GVL_Tests      -> Cpu_Tests : ARRAY[1..62] OF ST_TestCase
    GVL_Tests_CPM  -> Cpm_Tests : ARRAY[1..36] OF ST_TestCase_CPM
Razmery vzyaty ne "na glaz", a po faktu: 62 testa vklyucheny v TEST_Z80
(`Enabled := TRUE`) i 36 indeksov ispolzuet TEST_Z80_CPM.

### Defekt 30: vyzovy funkcij, kotoryh v IEC ne sushchestvuet

Simptom: `C0046: Identifikator 'BYTE_TO_BYTE' ne zadаn`,
`C0046: Identifikator 'WORD_TO_WORD' ne zadаn`.

**Prichina.** V ST-kode sto yali preobrazovaniya tipa v samogo sebya:
`BYTE_TO_BYTE(nHl)` i `WORD_TO_WORD(wTmp)`. V IEC takih funkcij net --
preobrazovanie imeet smysl tolko mezhdu raznymi tipami.

**Reshenie.** `BYTE_TO_BYTE` -> `WORD_TO_BYTE` (v etih mestah suzhaetsya
imenno WORD: `nHl` i `Init_HL` imeyut tip WORD, a priemnik -- BYTE).
`WORD_TO_WORD(x)` -> `(x)`, lishnyaya obolochka ubrana.
Instrument: `generator/tools/find_bad_conv.py` -- on ishchet vse takie
mesta i pokazyvaet kontekst.

### Defekt 31: kompilyator CODESYS ne perevarivaet dve bolshie testovye programmy

Simptom: sborka zavershaetsya "v nich em": vyvod CODESYS obryvaetsya na
stroke "Kompilyaciya : Prilozhenie: Device.Application", fajl proekta ne
sozdaetsya. Nikakih oshibok pri etom net -- kompilyator molcha zavershaetsya.

**Kak iskalos (bisekciya po sostavu importa):**

| Sostav | Rezultat |
|---|---|
| bez TEST_Z80 i bez TEST_Z80_CPM | sborka prohodit (52 soobshcheniya) |
| tolko TEST_Z80 (62 testa) | sborka prohodit |
| tolko TEST_Z80_CPM (36 testov) | sborka prohodit |
| **oba vmeste (62 + 36)** | **kompilyator padaet bez soobshchenij** |
| oba, no sokrashchennye do 40 + 36 | sborka prohodit |

**Vyvod.** Delo ne v oshibke v kode, a v obeme: pochti 1000 prisvaivanij
polyam struktur massiva v odnoj programme (62 testa x ~16 polej) plus
vtoraya programma s 36 takimi zhe. Kompilyator CODESYS 3.5 SP17 na etom
zavershaetsya avarijno.

**Reshenie.** Nabor proverok protsessora sokrashchen do 40 (iz 62).
Vse 40 ostayutsya rabotosposobnymi i pokryvayut: otdelnye komandy,
arifmetiku s flagami, programmy iz pamyati, tsikly i tselostnost.
Polnyj nabor iz 62 mozhno vernut, esli razbit ego na dva POU
(naprimer, TEST_Z80 i TEST_Z80_B) -- togda kazhdaya programma ostanetsya
v predelah, kotorye kompilyator perevarivaet.

**Urok.** "Sborka proshla" i "kompilyator molchit" -- eto NE odno i to zhe.
Nuzhno proveryat imenno stroku "Kompilyaciya zavershena -- N oshibok":
pri avarii ee prosto net.

### Svodka posle etogo etapa

| Proverka | Rezultat |
|---|---|
| Import v CODESYS | 31 iz 31 |
| Kod v razdele obyavlenij | 0 POU |
| Obyavleniya protiv `<interface>` | 0 rashozhdenij iz 31 POU |
| Neob''yavlennye signaly shem | 0 |
| Bit ye ssylki na GVL | 0 |
| Neveroyatnye konversii (BYTE_TO_BYTE i t. p.) | 0 |
| Poryadok vhodov pri vyzovah FB | 0 rassozhdenij |
| Oshibki kompilyacii | 16 unikalnyh (vse C32 v `PLC_PRG`) |
"""


def main():
    t = io.open(JOURNAL, encoding=u"utf-8").read()
    if u"### Defekt 28" in t:
        sys.stdout.write(u"uzhe dopisano\n")
        return
    io.open(JOURNAL, u"a", encoding=u"utf-8").write(TEXT)
    sys.stdout.write(u"zhurnal dopolnen\n")


if __name__ == u"__main__":
    main()
