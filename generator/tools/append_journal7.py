# -*- coding: utf-8 -*-
u"""Dopisat razdel 7 v zhurnal sborki.

Otdel nyj skript, a ne pravka rukami, potomu chto fajl bolshoy (1131 stroka)
i pravka cherez regulyarku po vsemu tekstu uzhe dva raza portila generator.
Zdes my tolko D O P I S Y V A E M tekst v konec -- eto bezopasno.

ZAPUSK: python generator\tools\append_journal7.py
"""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DOC = os.path.join(ROOT, u"docs", u"03_\u0416\u0423\u0420\u041d\u0410\u041b_"
                                 u"\u0421\u0411\u041e\u0420\u041a\u0418.md")

TEXT = u"""
---

## 7. Etap 6: razbor otchyota na 300+ oshibok (defekty 33-40)

Povod: sborka iz IDE davala bolee 300 oshibok. Nizhe -- chto okazalos
prichinoy, v poryadke vazhnosti. Samaya dorogaya nahodka -- pervaya: ona
chasa dva vyglyadela kak "kompilyator padaet na bolshih shemah".

### Defekt 33 (K L Yu Ch E V O J): posledovatelnost zvezdochka-skobka vnutri kommentariya

**Simptom.** Buket oshibok, kotorye ne ukazyvayut ni imya POU, ni nomer stroki:

    C9:   Obnaruzhen nedopustimyj simvol '-'
    C189: ';' trebuetsya vmesto '-'
    C8:   Nedopustimyj End-of-file: trebuetsya 'ELSIF', 'ELSE' ili 'END_IF'
    C77:  Neizvestnyj tip: 'vIsBDOS'

21 para C9/C189 za prohod, i ni odna iz nih ne svyazyvaetsya s soderzhimym:
poisk po vsem `src/` ne nahodil ni odnogo tire vne kommentariya.

**Prichina.** Vnutri kommentariya okazalas posledovatelnost iz zvezdochki
i zakryvayushchej skobki. Ona ZAKRYVAET kommentariy D O S R O Ch N O, i ves
ego hvost CODESYS chitaet kak KOD. V nashem proekte takih mest bylo dva:

    GVL_CPM.gvl      : "(Ctl_*)"  v kommentarii k peremennoy Bdos_Hit
    TEST_Z80         : "(F_*)"    v razdelitele "T31..T46: otdelnye flagi"

Vtoroe mesto obstoyatelnee: stroka nachinalas s `(* ----`, to est posle
dosrochnogo zakrytiya ostavalis tire, i imenno oni i davali "simvol '-'".

**Pochemu iskat bylo dolgo.** Ni imeni, ni nomera stroki v soobshchenii net;
tire v kommentariyah est po vsemu proektu, i vse oni zakonny. Pomoglo
programmnoe skanirovanie: projti po tekstu i najti posledovatelnost, pered
kotoroy stoit NE probel. Takaya proverka teper est:
`generator/tools/check_comments.py`.

**Urok.** Vnutri kommentariya nikogda ne dolzhno byt posledovatelnosti iz
zvezdochki i zakryvayushchej skobki -- dazhe kak chasti imeni ili shablona.
Pisat nado `Ctl_...` ili `Ctl_xx`.

### Defekt 34: zagolovok vida POU v InterfaceAsPlainText O B Ya Z A T E L E N

**Simptom.** Vse shest programm "ne najdeny":
`C46: Identifikator 'PRG_InitMemory' ne zadan`,
`C35: Vmesto 'PRG_InitMemory' trebuetsya imya programmy...`

**Prichina.** Atribut `pouType="program"` u elementa `<pou>` sam po sebe
vid POU N E  Z A D A Y O T. Vid opredelyaetsya po P E R V O M U  S L O V U
teksta v `InterfaceAsPlainText`. Bez zagolovka CODESYS schitaet obekt
funktsionalnym blokom.

**Kak ubedilis.** Otkryli sobrannyj proekt i prochitali `textual_declaration`
u kazhdogo POU (`generator/tools/diag_task.py`). U `FB_Memory64K` pervaya
stroka -- `FUNCTION_BLOCK FB_Memory64K`, i on rabotal. U `PRG_InitMemory`
pervaya stroka -- kommentar, i on ne rabotal.

**Vazhno: eto protivorechit bolee rannemu vyvodu v etom zhe zhurnale.**
Ranee bylo resheno, chto zagolovok vredен. Eto bylo neverno: togda odnovremenno
izmenilis dve veshchi, i vinovnika opredelili nepravilno. Sejchas zagolovok
stavitsya V S E G D A: `PROGRAM <imya>`, `FUNCTION_BLOCK <imya>`,
`FUNCTION <imya> : <tip>`.

### Defekt 35: perevody strok v InterfaceAsPlainText ne byli ekranirovany

**Simptom.** `C9: Obnaruzhen nedopustimyj simvol '&'`,
`C189: ';' trebuetsya vmesto '&'`, i tak zhe dlya `#`, `x`, `A`.

**Prichina.** V `<body>` perevody strok zamenyalis na `&#xA;`, a v
`InterfaceAsPlainText` ostavalis "zhivymi". CODESYS chitaet oba polya odnim
i tem zhe razborshchikom ST i v etom pole literal `&#xA;` ponimaet kak
T E K S T -- simvoly `&`, `#`, `x`, `A`.

**Pochemu eto kasalos tolko ST-POU.** U FBD-shem ekranirovanie bylo ispradu,
poetomu u nih oshibok ne bylo, a u kazhdoj ST-programmy -- po desyatke.

### Defekt 36: programmy ne byli zaregistrirovany v zadache (nepravilnyj API)

**Simptom.** Oshibki C9/C189/C8/C77 voobshche ne pojavlyalis, esli
konfiguraciya zadach byla pustoj, i pojavlyalis srazu, kak tolko v zadachu
popadala hot odna programma.

**Prichina i sledstvie.** Eto ne "oshibka ot zadachi", a osobennost:
CODESYS N E  K O M P I L I R U E T POU, ne svyazannyj s zadachej. Oshibki
byli v kode vsegda, i bez zadachi oni molchali.

Poputno vyясnilos, chto sposob registracii v `build.py` byl
nerabotosposobnym:

| Sposob | Rezultat |
|---|---|
| `task.pous.add(imya, imya)` | rabotaet |
| `task.pous[imya] = imya` | `object does not support item assignment` |
| `task.pous.append(imya)` | net takogo metoda |
| `task.pous.Add(imya)` | net takogo metoda |

U spiska programm zadachi est tolko `add`, `insert`, `remove`, `replace`.
V `build.py` pervyj sposob probovalsya, no ostavalsya i vtoroj kak
"rezervnyj", i imenno poetomu oshibka dolgo ostavalas neizvestnoj.

### Defekt 37: kirillica i bite simvoly vnutri ST-tekstov

**Simptom.** Vse te zhe C9/C189, no uzhe bez "vtorogo dnya poiska".

**Prichina.** V `gen_z80.py` vnutri strok, kotorye idut v ST, ostalis
kirillicheskie bukvy i bite simvoly (`o` s tildoj, `i` s udareniem) --
sledstvie proshlyh avtomaticheskih pravok fajla. Dlya CODESYS eto
nedopustimye simvoly.

**Reshenie.** `generator/tools/fix_nonascii.py` zamenyaet ih na translit.
Teper `src/` soderzhit tolko ASCII, i eto proveryaetsya.

### Defekt 38: odin nez akrytyj IF na 500 strok ST

**Simptom.** Tot zhe buket C9/C189/C8 -- i snova bez nomera stroki.

**Prichina.** V `TEST_Z80` chitalos `IF NOT bPrepared THEN` bez `END_IF`
pered `ELSIF GVL_Tests.Cpu_Test_Stage = 4 THEN`. Dalneyshij tekst parser
chital kak vlozhennoe telo usloviya i spotykalsya o pervyj zhe operator.

**Pochemu iskat bylo trudno.** POU soderzhal 528 strok ST: tablitsa iz 62
proverok i obrabotchik v odnom meste. Pomogla proverka balansa operatorov
stekom (`generator/tools/check_balance.py`), i ona zhe pokazala, chto
ostalnye pyat POU v poryadke.

**Sledstvie dlya struktury.** Tablitsa proverok vynesena v otdelnyj POU
`TEST_Z80_PREP` (338 strok), a v `TEST_Z80` ostalsya tolko obrabotchik
(198 strok). Priznak zapolneniya pereekhal iz lokalnoj peremennoj
`bFirstScan` v `GVL_InitState.TestTableDone`: lokalnaya peremennaya odnogo
POU nedostupna drugomu.

### Defekt 39: imena iz odnoj GVL chitalis cherez druguyu

**Simptom.** `C46: Identifikator 'File_Open' ne zadan`,
`C4: 'In_Cnt' ne yavlyaetsya komponentom 'GVL_CPM'`.

**Prichina.** Eti imena lezhali v `GVL_CPM_Extra`, i potomu byli vidny
B E Z kvalifikatora. No odna programma obrashchalas k nim s yavnym imenem
spiska -- `GVL_CPM.In_Cnt` -- i poluchala otkaz.

**Reshenie.** Imena (`File_Open`, `In_Cnt`, `Cpm_MsgLen`, `Out_Count`)
perenesены v `GVL_CPM`; `GVL_CPM_Extra` ostavlen pustym i podpisan, chtoby
nikto ne iskal tam imena snova.

### Defekt 40: DINT v INT, UDINT v WORD i sdvig na 8 po BYTE

Tri nezavisimye, no odnotipnye oshibki:

* `C32: Nevozmozhno konvertirovat tip 'DINT' v tip 'INT'` -- neyavnoe
  suzhenie v CODESYS zapreshcheno. Schetchiki ciklov v `PRG_InitMemory`,
  `PRG_LoadTestProgram` i `PRG_CPM_Boot` obyavleny kak `INT`;
* `C32: ... 'UDINT' v tip 'WORD'` -- v ST sobiralos
  `SHL(WORD_TO_DWORD(hi), 8) OR lo`, a eto UDINT. Poryadok obratnyj:
  snachala `BYTE_TO_WORD`, potom sdvig na 8 -- togda rezul tat WORD.
  Ispravleno v `FB_Memory64K` i v `TEST_Z80_CPM` (vetki 8 i 10);
* `C308: Sdvig na 8 prevyshaet razmer tipa BYTE` -- sledstvie togo zhe:
  suzhenie do BYTE delalos do sdviga.

### Sostoyanie posle etogo etapa

Bylo 300+ oshibok, stalo **17** (iz nih 8 unikalnyh po smyslu, ostalnye --
povtor vo vtorom prohode kompilyacii). Vse 17 -- odnogo vida: smeshannye
tipy v cepochkah `SEL`. Ni odnoj oshibki "identifikator ne zadan" bolshe net.

Statisticheskie proverki (bez CODESYS), vse zelenye:

| Proverka | Instrument | Rezultat |
|---|---|---|
| Kommentarii `(* ... *)` | `generator/tools/check_comments.py` | 55 tekstov, 0 narushenij |
| Balans IF/FOR/WHILE/CASE | `generator/tools/check_balance.py` | 8 ST-POU, 0 disbalansa |
| N e-ASCII v ST | `generator/tools/fix_nonascii.py` | 0 simvolov |
| Plana ispravlenij | `generator/tools/tests_plan.py` | 5 iz 7 |
| Sootvetstvie TZ | `generator/tools/check_tz.py` | 58 iz 58 |

### Chto ostalos: smeshannye tipy v cepochkah SEL

Ostalsya odin klass oshibok, i on zhe samyj trudnyj:

    C32: Nevozmozhno konvertirovat tip 'BOOL' v tip 'USINT'
    C32: Nevozmozhno konvertirovat tip 'USINT' v tip 'BOOL'
    C32: Nevozmozhno konvertirovat tip 'BOOL' v tip 'BYTE'
    C32: Nevozmozhno konvertirovat tip 'WORD' v tip 'BYTE'

Prichina: blok `SEL` obobshchennyj (ANY), ego tip vyvoditsya po vetkam.
Kogda v odnoj cepochke vstrechayutsya vetki raznogo tipa, CODESYS bere USINT
dlya vseh i potom ne mozhet ni prisvoit rezul tat v BYTE, ni soglasovat ego
s usloviem.

Tri podhoda U Zh E  P R O V E R E N Y  I  O T V E R G N U T Y:

1. Konversiya vida `BYTE_TO_BYTE` dlya vetok. V CODESYS takoy funkcii N E T:
   76 oshibok `C46: Identifikator 'BYTE_TO_BYTE' ne zadan`.
2. Promezhutochnye peremennye v T E L E seti. CODESYS schitaet ih "lazy"
   i otkazyvaetsya vyvodit tip:
   `Tip lazy peremennoj '__FB_IO_Ports__ImpVarN' ne mozhet byt razreshen`.
3. Promezhutochnye peremennye, obyavlennye v POU, so vsemi prisvoeniyami
   v odnoj seti. Kompilyator na etom Z A V I S A E T: CPU stoit, vyvod pust.
   Vosproizvedeno dvazhdy.

**Predlagaemoe reshenie -- sleduyushchij shag.** Otkazatsya ot cepochki `SEL`
v polzu `MUX`: u nego ODIN vyhod, ODIN tip i chislennyy vybor. Smeshivat tipy
prosto nechem. Eto trebuet peredelki treh setey:

* `FB_RegFileZ80` -- vyborka registra po `Sel_Src` (12 variantov);
* `FB_IO_Ports` -- chtenie porta po adresu (9 variantov);
* `FB_RegFileZ80` -- nachalnye znacheniya pri initsializatsii (12 variantov).

### Otkrytyj organizacionnyj vopros: zavisanie processa CODESYS

Dva raza za etap process `CODESYS.exe` zaversalsya tak, chto ostavalsya
nedejstvuyushchij process, kotorogo ne vidit `taskkill` (`There is no
running instance of the task`), no kotoryj derzhit monopolnyj mutex.
Posle etogo lyuboj novyj zapusk CODESYS molcha zhdET, i sborka stanovitsya
nevozmozhnoj do perezagruzki. Priznak: `codesys_out.txt` pust, CPU processa
ne rastet.

Poka eto ne ustraneno, poslednyuyu sborku (s ispravlennymi defektami 33-40)
proverit ne udalos. Nuzhna perezagruzka, zatem odin zapusk
`generator\\run_build_log.cmd`.
"""


def main():
    try:
        sys.stdout.reconfigure(encoding=u"utf-8", errors=u"replace")
    except Exception:                                          # noqa: BLE001
        pass
    if not os.path.exists(DOC):
        sys.stdout.write(u"NET FAJLA %s\n" % DOC)
        return 1
    t = io.open(DOC, encoding=u"utf-8").read()
    if u"## 7. Etap 6" in t:
        sys.stdout.write(u"razdel 7 uzhe dopisan -- propuskayu\n")
        return 0
    t = t.rstrip(u"\n") + u"\n" + TEXT
    io.open(DOC, u"w", encoding=u"utf-8").write(t)
    sys.stdout.write(u"zhurnal dopisan: %d strok\n" % t.count(u"\n"))
    return 0


if __name__ == u"__main__":
    sys.exit(main())
