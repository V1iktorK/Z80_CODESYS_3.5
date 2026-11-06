# -*- coding: utf-8 -*-
u"""Dopisat' v zhurnal rezul'taty revizii (defekty 19-22).

ZAPUSKAT SISTEMNYM PYTHON 3 ODIN RAZ.
"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JOURNAL = os.path.join(ROOT, u"docs", u"03_ЖУРНАЛ_СБОРКИ.md")

TEXT = u"""

## 3. Reviziya vsego proekta (defekty 19-22)

Polzovatel poprosil perebrat proekt celykom i ubrat oshibki. Reviziya
nachalas s togo, chto obyavleniya peremennyh okazalis v pole realizacii,
a zakonchilas nastoyashchej kompilyaciej, kotoraya vskryla eshche tri
sistemnyh defekta, nevidimyh ni pri importe, ni pri proverke struktury.

### Defekt 19: obyavleniya popali v pole realizacii

Zamecheno polzovatelem na skrinshote: v redaktore POU nizhnee pole
(realizaciya) soderzhalo obyavleniya, a verhnee (obyavleniya) bylo pustym.

**Prichina.** V klasse `TextPou` odin i tot zhe polnyj tekst POU otpravlyalsya
I v `<InterfaceAsPlainText>`, I v telo `<ST>`. CODESYS razrezal tekst po
`END_VAR`: zagolovok s `VAR` uezzhal v redaktor obyavlenij, a v realizacii
ostavalis oborvannye kommentarii. Plyus dubliruyushchie vyzovy `p.var(...)`
sozdavali peremennuyu i v strukturnom `<interface>`, i v tekste.

**Reshenie.** 1) `TextPou._cut_declaration()` -- v realizaciyu idet tolko
tekst POSLE poslednego `END_VAR`; 2) ubrany dubliruyushchie `p.var(...)`
dlya tekstovyh POU; 3) dobavlena proverka `generator/tools/verify_decl.py`,
kotoraya sravnivaet sekcii strukturnogo `<interface>` s tekstom obyavleniya.

**Skolko raz oshibalis v samoj proverke** (polezno kak preduprezhdenie):

* chitali telo ST vmesto obyavleniya i "nahodili" tam 50 lishnih peremennyh;
* iskali `<InterfaceAsPlainText>` po namespace `interfaceasplaintext`, a element
  zapisan BEZ prefiksa i nasleduet OSNOVNOJ namespace `tc6_0200` -- proverka
  "ne nahodila" obyavlenij vo vseh 31 fajlah srazu;
* regulyarka imeni trebovala minimum 2 simvola i molcha vybrasyvala
  odnonbukvennye `A`, `B`, `Y`, `Q`, `i`;
* `break` pri raspoznavanii zagolovka sekcii teryal PERVUYu peremennuyu
  kazhdoj sektsii (zagolovok i peremennaya chasto v odnom kuske posle `;`).

**Urok.** Instrument proverki nado proveryat: tri iz chetyreh "najdennyh"
defektov okazalis oshibkami samogo chekera.

### Defekt 20: odno imya -- neskolko GVL, i kompilyator molchit

Kompilyator CODESYS 3.5 SP17 **ne schitaet oshibkoj** odinakovye imena v raznyh
GVL. V proekte takih imen okazalos 10, v tom chisle `Test_Result` s razmerami
`[1..75]` i `[1..40]` v dvuh raznyh GVL, i `Bus_Addr`/`Bus_Data`, kotorye shema
pisala v GVL_PLCVisu, a HMI chital iz GVL_Bus.

**Reshenie: prefiks na kazhdyj GVL.** `GVL_Tests` -> `Cpu_Test_*`,
`GVL_Tests_CPM` -> `Cpm_Test_*`, `GVL_PLCVisu` -> `Visu_Test_*`. Realnye shiny
ostayutsya tolko v `GVL_Bus`, `Disk_DMA` -- tolko v `GVL_Disk`.
Proverka posle migracii: **169 globalnyh imen, 0 kollizij.**

Otdelno vsplylo: `GVL_PLCVisu.Visu_Test_Active` pisalsya programmoj, no NE byl
nikde ob''yavlen -- kompilyator molchal, potomu chto korotkoe imya `Test_Active`
nashlos v DRUGOM GVL. Kollizii ne tolko zatrudnyayut chtenie, oni PRYaChUT
realnye oshibki.

### Defekt 21: `app.build()` NE kompiliruet kod

Samyj vazhnyj defekt metodiki. Schetchik `OSHIBOK: 0` v `build.log` ne znachit
nichego: `app.build()` sobiraet prilozhenie, no ne kompiliruet POU, i vozvashchaet
pustoj spisok soobshchenij dazhe togda, kogda v programme yavnaya oshibka.

**Kak dokazano.** V `PRG_InitMemory` vstavlena stroka
`ETO @@@ sindaksicheskaya oshibka;`. `app.build()` otvetil "soobshcheniy: 0".
Togda zhe v toj zhe sessii CODESYS soobshchil v svoj vyvod: "Kompilyaciya
zavershena -- 39 oshibok". T.e. kompilyaciya idet, no ne tam, gde my ee zh dali,
i soobshcheniya v API ne popadayut.

**Reshenie.** Nastoyashchaya kompilyaciya -- `app.generate_code()`. Soobshcheniya
cherez API poluchit ne udalos (pust i posle nee, i posle `system.delay`), poetomu
itog chitaetsya iz VYVODA CODESYS. Dlya etogo dobavlen
`generator/run_build_log.cmd`: on perenapravlyaet vyvod v `log/codesys_out.txt`,
gde stroka "Kompilyaciya zavershena -- N oshibok" vidna cherez
`Select-String`/`read`.

Poboe sledstvie: pri sborke cherez PowerShell soobshcheniya DVUH zapuskov
smeshivayutsya, i oshibki proshlogo progona vyglyadyat kak aktualnye.
Chtoby etogo ne bylo, vyvod pishetsya v fajl.

### Defekt 22: chto imenno nashla kompilyaciya

Kogda kompilyaciya nakonect-to zarabotala, nashlos 146 oshibok -- i ni odna
iz nih ne byla vidna ni pri importe, ni pri proverke struktury. Etapy:

| Chto nashlos | Kak proyavlyalos | Kak ispravleno |
|---|---|---|
| 7 neob''yavlennyh ekzemplyarov FB (`fbAO0Lo`, `trDecode`, `fbStopped` i dr.) | `C177: 'X' ne yavlyaetsya ekzemplyarom 'FB_Reg16'` | dobavleny `p.var(...)` |
| 46 neob''yavlennyh signalov shem (`WE_0..15`, `Add_Lo`, `Sel_Op0..5`, `vSetDMA`...) | `C77: Neizvestnyy tip: 'Add_Lo'` | ob''yavleny kak lokalnye peremennye POU |
| 19 bit yh ssylok na GVL (`GVL_Control.Ctl_*`, `GVL_Bus.Bus_Addr_HL`) | `C4: 'Ctl_Is_CALL' ne yavlyaetsya komponentom 'GVL_Control'` | imeny dobavleny v GVL |
| 40 oshibok ot `AT %IX0.0` v GVL | `C6: ';, :=, REF=, ( ili [' trebuetsya vmesto 'AT'` | privyazka snyata; GVL_HW_IO -- testovye znacheniya, privyazka -- ruchnoj shag |
| `FB_AlwaysTrue` ob''yavlen kak `function`, a vyzyvaetsya s ekzemplyarom | `C177: imeet tip FUNCTION i ne mozhet imet ekzemplyary` | tip ispravlen na `functionBlock` |
| `SEL` poluchal BYTE `vImm` tam, gde nuzhen BOOL | `C32: 'BOOL' v 'USINT'` | podan `GVL_Control.Ctl_Imm_Mode` |
| `SHR` po WORD so sdvigom 8 i obratnyj poryadok suzheniya | `C308: Sdvig na 8 prevyshaet razmer tipa BYTE` | snachala sdvig po WORD, zatem `WORD_TO_BYTE` |
| `vSpRd` ob''yavlen BYTE, a prinimaet WORD | `C32: 'WORD' v 'BYTE'` | tip ispravlen na WORD |
| `FB_SP_StackZ80.Mem_Rd` ob''yavlen BYTE, a prinimaet WORD | `C32: 'WORD' v 'BYTE'` | tip ispravlen na WORD |
| `GVL_PLCVisu.R_Next` ne sushchestvoval | `C4: 'R' ne yavlyaetsya komponentom 'GVL_PLCVisu'` | schetchik R teper' schitaet `R+1` cherez `ADD`/`BYTE_TO_WORD` |
| `app.pou_call(imya)` -- takogo metoda net | `Fatal error. Internal CLR error. (0x80131506)` | metod ubran; ostavleny tolko bezopasnye sposoby |

**Chto eshche ostalos.** 18 oshibok C32 vida "USINT v BOOL" / "BOOL v USINT"
v sheme `PLC_PRG`. Ih istochnik lokalizovan tochno: oni poyavlyayutsya togda i
tolko togda, kogda `PLC_PRG` zaregistrirovan v zadache (bez zadachi -- 0 oshibok,
s odnim `PLC_PRG` v zadache -- 18). Znachit pri generacii koda dlya tsiklicheskoj
zadachi kompilyator primenyaet bolee strogie pravila proverki tipov.
Instrumenty dlya dalneyshego poiska gotovy:
`generator/tools/diag_full_types.py` (polnaya karta tipov vseh svyazej),
`generator/tools/diag_all_types.py`, `generator/tools/find_st_type_bugs.py`.

### Chto dobavleno v instrumentarij

| Fajl | Zachem |
|---|---|
| `generator/tools/verify_decl.py` | sverka strukturnogo `<interface>` s tekstom obyavleniya |
| `generator/tools/check_signals.py` | pois k signalov shem, kotoryh net v obyavleniyah |
| `generator/tools/check_gvl_refs.py` | pois bit yh ssylok `GVL_x.y` |
| `generator/tools/diag_pin_order.py` | sverka poryadka i imen vhodov pri vyzovah FB |
| `generator/tools/diag_all_types.py`, `diag_full_types.py` | karta tipov svyazej |
| `generator/tools/dump_decl.py`, `dump_tree.py` | chto v kakom pole POU |
| `generator/inspect_project.py` | chto real'no lezhit v SOBRANNOM proekte |
| `generator/run_build_log.cmd` | sborka s zapis'yu vyvoda CODESYS v fajl |

### Itog revizii

| Proverka | Rezultat |
|---|---|
| Sgenerirovano | 31 POU + 15 GVL |
| Import v CODESYS | 31 iz 31 |
| Obyavleniya vs `<interface>` | 0 rashozhdenij iz 31 POU |
| Neob''yavlennye signaly shem | 0 |
| Bit ye ssylki na GVL | 0 iz 114 |
| Kollizii imen mezhdu GVL | 0 iz 169 |
| Poryadok vhodov pri vyzovah FB | 0 rassozhdenij |
| Obyavleniya v pole realizacii | 0 |
| Oshibki kompilyacii | bylo 146 -> stalo 18 (vse C32 v `PLC_PRG`) |

**Glavnyy vyvod.** Tri instrumenta, kotorye schitalis dokazatelstvom
korrektnosti -- uspeshnyj import, `app.build()` i sverka chislа blokov -- ne
lovyat ni odnoj iz etih oshibok. Edinstvennaya nastoyashchaya proverka --
`app.generate_code()` s chteniem vyvoda CODESYS.
"""


def main():
    t = io.open(JOURNAL, encoding=u"utf-8").read()
    if u"### Defekt 21" in t:
        sys.stdout.write(u"uzhe dopisano\n")
        return
    io.open(JOURNAL, u"a", encoding=u"utf-8").write(TEXT)
    sys.stdout.write(u"zhurnal dopolnen (%d simvolov)\n" % len(TEXT))


if __name__ == u"__main__":
    main()
