# -*- coding: utf-8 -*-
u"""Dopisat' v zhurnal defekt 32 (ostavshijsya process CODESYS) i itogi.

ZAPUSKAT SISTEMNYM PYTHON 3 ODIN RAZ.
"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JOURNAL = os.path.join(ROOT, u"docs", u"03_ЖУРНАЛ_СБОРКИ.md")

TEXT = u"""

### Defekt 32: sborka "padala" iz-za ostavshegosya processa CODESYS

Samyj dorogoj po vremeni defekt. Posle vklyucheniya massivov testov sborka
stala zavershatsya "v nich em": vyvod CODESYS pustoj, `build.log` obryvaetsya
na sekcii KOMPILYACIYA, fajl proekta ne sozdaetsya. Vyglyadelo kak avariya
kompilyatora na bolshih testovyh programmah.

**Chto ya uspel perebrat, poka ne ponyal prichinu** (i chto okazalos
naprasnym): razmer massiva 75 -> 62 -> 40 -> 30, razbienie podgotovki testov
na porcii po 8 cherez `CASE`, isklyuchenie TEST_Z80 i TEST_Z80_CPM po
ocheredi... Rezultat byl NEPREDSKAZUEMYM: odna i ta zhe konfiguraciya to
sobiralas, to net. Eto i dolzhno bylo nastorozhit: nastoyashchaya oshibka
v kode daet stabilnyj rezultat.

**Nastoyashchaya prichina.** CODESYS -- ODNOEKZEMPLYaRNOE prilozhenie. Kogda
predydushchij progon ubivaetsya po timeoutu (a on u menya ubivalsya
neskolko raz), process CODESYS ostaetsya zhit. Novyj zapusk pri etom
NE nachinaet rabotu: on molcha zhdet uzhe rabotayushchij ekzemplyar.
Otsyuda pustoj vyvod i obryv loga.

**Dokazatelstvo.** Posle togo kak ya v cikle ubil vse processy CODESYS
do nulya i podozhdal, ta zhe samaya sborka (40 testov CPU + 36 CP/M)
proshla s PERVOGO raza: 31 iz 31 importirovano, proekt sozdan, 52
soobshcheniya kompilyatora.

**Reshenie.** V `generator/run_build_log.cmd` dobavleny dva bloka:
pered zapuskom -- cikl `taskkill` s proverkoj `tasklist`, poka process
ne ischeznet, plus udalenie `*.~u`; posle zapuska -- tot zhe `taskkill`,
chtoby sleduyushchaya sborka ne zavisla. Teper sborka vosproizvodima.

**Urok.** Esli rezultat nestabilen -- ishchi ne oshibku v kode, a problemu
okruzheniya. Stabilnyj defekt vosproizvoditsya vsegda; "to da, to net" --
priznak vneshnego faktora. I eshche: ubivaya process po timeoutu, nado
ubeditsya, chto on deystvitelno umer.

### Itog proverki kataloga build

V kataloge lezhali lishnie fajly: kopiya proekta `Z80_EMU_для_IDE.project`
ot bolee rannego progonu (ona pokazyvala USTAREVShee sostoyanie i
pugala oshibkami, kotoryh v tekushchej sborke net), ee fajly `.opt`
i `precompilecache` ot proshlyh zapuskov, a takzhe ostatki ot
diagnosticheskih proektov (`iso`, `type_probe`). Vse ubrano.

Sejchas v `build` tolko to, chto sozdaet sborka:

| Fajl | Zachem |
|---|---|
| `Z80_EMU.project` | sam proekt |
| `Z80_EMU-AllUsers.opt`, `Z80_EMU-<polzovatel>.opt` | nastroyki okna CODESYS |
| `Z80_EMU_project.precompilecache` | kes kompilyacii, peresozdaetsya |

Kopiya dlya otkrytiya v IDE delaetsya v koren proekta.

### Sverka s tehnicheskim zadaniem

Instrument `generator/tools/check_tz.py` proveryaet 58 punktov TZ:
komandy, registry, flagi, pamyat, porty, sinhronizaciyu i ogranicheniya
na ST. Rezultat: **58 iz 58**.

| Razdel TZ | Chto provereno |
|---|---|
| Komandy | vse 16 iz zadaniya: LD r,r'; LD r,n; LD r,(HL); LD (HL),r; ADD A,r; SUB r; INC r; DEC r; JP nn; JP Z; JP NZ; CALL nn; RET; HALT; DJNZ; IN A,(n); OUT (n),A |
| Registry | A F B C D E H L, alternativnye Sa..Sf, IX, IY, SP, PC, I, R |
| Flagi | S Z H P/V N C, plyus F5 i F3 (hranyatsya) |
| Pamyat' | `Z80_Mem : ARRAY[0..65535] OF BYTE` |
| Porty | 256 portov, shiny `Bus_IO_Addr` / `Bus_IO_Data` |
| Sinhronizaciya | dvuhfaznyy takt, vhod `Scan` |
| ST | tolko v razreshennyh POU (7 shtuk), osnovnaya logika -- v 24 shemah FBD |

**Zamechanie po punktu "chislo instrukcij za skan".** V TZ dopuskaetsya
nastraivaemoe chislo N. V proekte realizovan rezhim "1 skan = 1 komanda"
(kak trebuet osnovnoy variant), a takt sdelan dvuhfaznym -- eto i est
tochka rasshireniya: chtoby puskat N komand za skan, dostatochno dobavit
schetchik povtorov fazy ispolneniya, peredelki shemy ne potrebuetsya.

### Chto ostalos

16 unikalnyh oshibok C32 (konversiya tipov) v sheme `PLC_PRG`. Oni
vosproizvodyatsya stabilno. Pary C46/C35 -- ih sledstvie: poka tipy ne
shyutsya, ekzemplyary ST-programm ne sozdayutsya, i zadacha ih "ne vidit".

Instrumenty dlya prodolzheniya:
  * `generator/tools/diag_types_real.py PLC_PRG` -- tipy po vhodam blokov;
  * `generator/tools/find_bad_sel.py PLC_PRG` -- usloviya `SEL` ne buleva tipa;
  * `generator/tools/hide_net.py off "SET N"` -- bisekciya setey;
  * `generator/run_build_log.cmd` -- sborka (sam ubivaet ostavshiesya
    processy CODESYS, poetomu rezultat vosproizvodim).
"""


def main():
    t = io.open(JOURNAL, encoding=u"utf-8").read()
    if u"### Defekt 32" in t:
        sys.stdout.write(u"uzhe dopisano\n")
        return
    io.open(JOURNAL, u"a", encoding=u"utf-8").write(TEXT)
    sys.stdout.write(u"zhurnal dopolnen\n")


if __name__ == u"__main__":
    main()
