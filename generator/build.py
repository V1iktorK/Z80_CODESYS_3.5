# -*- coding: utf-8 -*-
u"""build.py --  s b o r k a  p r o e k t a Z80_EMU  v n u t r i CODESYS (IronPython 2.7).

 ch t o  d e l a e t:
  1)  s o z d a e t  n o v y j  p r o e k t  s  u s t r o j s t v o m CODESYS Control Win V3 (385.17.30);
  2)  d o b a v l ya e t GVL  i DUT ( t i p ST_TestCase  i  sh i n y);
  3)  i m p o r t i r u e t  s g e n e r i r o v a n n y e FBD- s h e m y  i z src/*.plcopenxml  p o  o d n o j;
  4)  p r o v e r ya e t,  ch t o POU  d o e h a l i  i  s v ya z i  n e  p o t e r ya l i s ;
  5)  k o m p i l i r u e t  p r i l o zh e n i e  i  v y k l a d y v a e t  s o o b shch e n i ya  k o m p i l ya t o r a;
  6)  s o h r a n ya e t  p r o e k t  v build/.

 k o m p i l ya c i ya --  i  e s t   n a s t o ya shch a ya  p r o v e r k a  g e n e r a t o r a:  e s l i CODESYS  p r i n ya l
 n a sh i  s h e m y  i  s o b r a l  b e z  o sh i b o k,  z n a ch i t  g e n e r a c i ya FBD  r a b o t a e t.

 v n u t r i CODESYS  d o s t u p  k API  b e r e m  ch e r e z  m o d u l  scriptengine:  g l o b a l  n y e
objects (projects/system)  i n zh e k t i r u yu t s ya  t o l  k o  v namespace  g l a v n o g o  s k r i p t a,
 v  i m p o r t i r o v a n n o m  k o d e  i h  n a d o  z a p r a sh i v a t   u scriptengine.
"""

import io
import os
import sys
import traceback

import scriptengine

#  k o r e n   p r o e k t a  v y ch i s l ya e m  o t __file__ (generator/build.py -> Z80_EMU),
#  ch t o b y  n e  h a r d k o d i t   p u t   s  k i r i l l i c e j:  v IronPython 2  l i t e r a l ur"C:\..."  o p a s e n,
#  a \u041e  v n u t r i  o b y ch n o j  s t r o k i --  b e z o p a s e n.
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, u"src")
BUILD = os.path.join(ROOT, u"build")
LOG = os.path.join(ROOT, u"log", u"build.log")
OUT_PROJECT = os.path.join(BUILD, u"Z80_EMU.project")

DEVICE_TYPE = 4096
DEVICE_ID = u"0000 0001"
DEVICE_VERSION = u"3.5.17.30"

PT = scriptengine.PouType
DT = scriptengine.DutType


def log(m):
    # append+close  n a  k a zh d u yu  s t r o k u: flush()  v IronPython  n e  g a r a n t i r u e t  s b r o s
    #  n a  d i s k (.NET- b u f e r i z a c i ya),  i  p r i  s n ya t i i  p r o c e s s a  l o g  t e r ya e t s ya  c e l i k o m.
    f = io.open(LOG, "a", encoding="utf-8")
    f.write(u"%s\n" % (m,))
    f.close()


def _truncate():
    for d in (os.path.dirname(LOG), BUILD):
        if not os.path.isdir(d):
            os.makedirs(d)
    f = io.open(LOG, "w", encoding="utf-8")
    f.write(u"")
    f.close()


_truncate()

STEP = [0]


def head(t):
    STEP[0] += 1
    log(u"")
    log(u"################ [%02d] %s" % (STEP[0], t))


def err():
    log(u"!!! %s" % traceback.format_exc())


def nm(o):
    try:
        return o.get_name()
    except Exception:
        return u"?"


def walk(o, ind=0, depth=6, acc=None):
    if acc is None:
        acc = []
    try:
        acc.append((nm(o), o))
    except Exception:
        pass
    if ind >= depth:
        return acc
    try:
        kids = o.get_children()
    except Exception:
        kids = []
    for k in kids:
        walk(k, ind + 1, depth, acc)
    return acc


def find_deep(root, name):
    for n, o in walk(root, 0, 8, []):
        if n == name:
            return o
    return None


# ---------------------------------------------------------------------------
#   s o d e r zh i m o e GVL  i DUT
# ---------------------------------------------------------------------------

GVL_BUS = u"""VAR_GLOBAL
    (* OBShchIE ShINY: edinstvennaya svyaz' blokov.
       Provodami takuyu svyaz' tyanut' nel'zya -- poluchitsya nechitaemaya pautina. *)
    Bus_Data : BYTE;    (* 8-bitnaya shina dannyh *)
    Bus_Addr : WORD;    (* 16-bitnaya adresnaya shina *)
END_VAR
"""

GVL_CONTROL = u"""VAR_GLOBAL
    (* UPRAVLENIE EMULYaTOROM (knopki HMI) *)
    Emu_Run   : BOOL;
    Emu_Step  : BOOL;
    Emu_Reset : BOOL;

    (* SIGNALY DEKODERA, vyvedennye v GVL: chtoby na glavnoj sheme ostalis'
       tol'ko shiny dannyh i adresa *)
    Ctl_Sel_Dst   : BYTE;
    Ctl_Sel_Src   : BYTE;
    Ctl_ALU_Op    : BYTE;
    Ctl_Cond      : BYTE;
    Ctl_Wr_Enable : BOOL;
    Ctl_Mem_Rd    : BOOL;
    Ctl_Mem_Wr    : BOOL;
    Ctl_Is_CALL   : BOOL;
    Ctl_Is_RET    : BOOL;
    Ctl_Is_DJNZ   : BOOL;
    Ctl_Is_HALT   : BOOL;
    Ctl_Imm_Mode  : BOOL;
    Ctl_Is_Jump   : BOOL;
    Ctl_Is_Jr     : BOOL;
    Ctl_Flags_En  : BOOL;
    Ctl_IO_Rd     : BOOL;
    Ctl_IO_Wr     : BOOL;
END_VAR
"""

GVL_VISU = u"""VAR_GLOBAL
    (* ZERKALO DLYa VIZUALIZACII (tol'ko chtenie).
       HMI privyazyvaetsya TOL'KO k etomu GVL, chtoby vizualizaciya
       ne vliyala na ispolnenie. *)
    A  : BYTE;
    B  : BYTE;
    C  : BYTE;
    D  : BYTE;
    E  : BYTE;
    H  : BYTE;
    L  : BYTE;

    AltA : BYTE;
    AltB : BYTE;
    AltC : BYTE;
    AltD : BYTE;
    AltE : BYTE;
    AltH : BYTE;
    AltL : BYTE;

    F      : BYTE;
    PC     : WORD;
    SP     : WORD;
    IX     : WORD;
    IY     : WORD;
    I      : BYTE;
    R      : BYTE;
    IR     : BYTE;
    Halted : BOOL;
    C : BYTE;

    Bus_Addr : WORD;
    Bus_Data : BYTE;

    FlagS  : BOOL;
    FlagZ  : BOOL;
    FlagH  : BOOL;
    FlagPV : BOOL;
    FlagN  : BOOL;
    FlagC  : BOOL;
END_VAR
"""

DUT_TESTCASE = u"""TYPE ST_TestCase :
STRUCT
    (* OPISANIE ODNOGO TESTA. Chtoby dobavit test, dostatochno zapolnit
       ocherednuyu stroku massiva -- shema ne menyaetsya. *)
    Id           : INT;
    Stage        : INT;
    Opcode       : BYTE;
    Opcode_Lo    : BYTE;
    Init_A       : BYTE;
    Init_B       : BYTE;
    Init_F       : BYTE;
    Init_PC      : WORD;
    Init_SP      : WORD;
    Init_HL      : WORD;
    Exp_A        : BYTE;
    Exp_F        : BYTE;
    Exp_PC       : WORD;
    Exp_Mem      : BYTE;
    Exp_Mem_Addr : WORD;
    Exp_Cycles   : INT;
    Mask_A       : BOOL;
    Mask_F       : BOOL;
    Mask_PC      : BOOL;
    Mask_Mem     : BOOL;
    Mask_Flag    : BOOL;
    Test_Has_Cond : BOOL;
    Enabled      : BOOL;
END_STRUCT
END_TYPE
"""

#  p o r ya d o k  i m p o r t a =  p o r ya d o k  z a v i s i m o s t e j
# GVL sozdayutsya cherez API: import_xml ne prinimaet GVL ni s pouType,
# ni bez nego (oba varianta otvergnuty eksperimentom).


DUT_TESTCASE_CPM = u"""TYPE ST_TestCase_CPM :
STRUCT
    (* OPISANIE ODNOGO TESTA CP/M / I/O. Kind -- chto proveryaem. *)
    Id         : INT;
    Kind       : INT;
    Param      : INT;
    Exp_Byte   : BYTE;
    Exp_Word   : WORD;
    Mask_Byte  : BOOL;
    Mask_Word  : BOOL;
    Enabled    : BOOL;
END_STRUCT
END_TYPE
"""

GVL_ORDER = [u"GVL_Bus", u"GVL_Memory", u"GVL_Control", u"GVL_InitState",
             u"GVL_PLCVisu", u"GVL_Tests", u"GVL_InitRegs",
             u"GVL_HW_IO", u"GVL_HW_Buffer", u"GVL_IO", u"GVL_CPM",
             u"GVL_Disk", u"GVL_CPM_Extra", u"GVL_BootFlags", u"GVL_Tests_CPM"]
# Poryadok importa = poryadok zavisimostej: snachala primitivy, zatem bloki.
IMPORT_ORDER = [
    u"FB_Reg8", u"FB_Reg16", u"FB_RTrig", u"FB_FTrig", u"FB_RS", u"FB_Reg8Latch",
    u"FB_BitUnpack8", u"FB_ADDER8",
    u"FB_RegFileZ80", u"FB_ALU_Z80", u"FB_FlagsRegZ80", u"FB_DecoderZ80",
    u"FB_Memory64K", u"FB_PC_Z80", u"FB_SP_StackZ80", u"FB_ControlUnit",
    u"FB_Clock", u"FB_TestCase",
    u"FB_AlwaysTrue", u"FB_HW_IO_PLC", u"FB_IO_Ports",
    u"FB_CPM_Disk", u"FB_CPM_BDOS", u"FB_CPM_BIOS",
    u"PLC_PRG",
    u"PRG_InitMemory", u"PRG_LoadTestProgram", u"PRG_CPM_Boot",
    u"PRG_CPM_BDOS", u"TEST_Z80_PREP", u"TEST_Z80", u"TEST_Z80_CPM",
]


def main():
    log(u"=== BUILD START ===")
    log(u"root: %s" % ROOT)
    log(u"cwd : %s" % os.getcwd())
    log(u"python: %s" % sys.version)

    # ----------------------------------------------------------  p r o e k t
    head(u"sozdanie proekta s ustrojstvom")
    proj = None
    app = None
    try:
        for p in list(scriptengine.projects.all):
            try:
                p.close()
            except Exception:
                pass
        #  p o d ch i s t i t   p r o sh l y e  a r t e f a k t y,  i n a ch e CODESYS  n e  o t k r o e t  f a j l
        for junk in os.listdir(BUILD):
            if junk.startswith(u"Z80_EMU.project") or junk.endswith(u".precompilecache"):
                try:
                    os.remove(os.path.join(BUILD, junk))
                except Exception:
                    pass
        proj = scriptengine.projects.create(OUT_PROJECT)
        log(u"projects.create OK -> %s" % OUT_PROJECT)
        proj.add(name=u"Device", type=DEVICE_TYPE, id=DEVICE_ID,
                 version=DEVICE_VERSION)
        log(u"ustrojstvo dobavleno: type=%d id=%s version=%s"
            % (DEVICE_TYPE, DEVICE_ID, DEVICE_VERSION))
        app = proj.active_application
        log(u"active_application = %r" % (app,))
    except Exception:
        err()

    if app is None:
        log(u" k r i t i ch n o:  n e t Application --  s b o r k a  n e v o z m o zh n a")
        return

    # ---------------------------------------------------------- GVL
    # ---------------------------------------------------------- GVL
    # GVL sozdaem cherez API: import_xml ih ne prinimaet (sm. kommentarij u
    # GVL_ORDER). Tekst obyyavleniya berem iz src/<imya>.gvl.
    head(u"sozdanie DUT")
    try:
        d = app.create_dut(u"ST_TestCase", type=DT.Structure)
        d.textual_declaration.replace(DUT_TESTCASE)
        log(u"  DUT ST_TestCase -- OK")
    except Exception:
        log(u"  DUT ST_TestCase -- OSHIBKA")
        err()
    try:
        d2 = app.create_dut(u"ST_TestCase_CPM", type=DT.Structure)
        d2.textual_declaration.replace(DUT_TESTCASE_CPM)
        log(u"  DUT ST_TestCase_CPM -- OK")
    except Exception:
        log(u"  DUT ST_TestCase_CPM -- OSHIBKA")
        err()

    head(u"sozdanie GVL iz src/*.gvl")
    for name in GVL_ORDER:
        gp = os.path.join(SRC, u"%s.gvl" % name)
        if not os.path.exists(gp):
            log(u"  NET FAJLA: %s" % gp)
            continue
        try:
            gf = io.open(gp, u"r", encoding=u"utf-8")
            gtext = gf.read()
            gf.close()
            g = app.create_gvl(name)
            g.textual_declaration.replace(gtext)
            log(u"  GVL %-14s -- OK (%d simvolov)" % (name, len(gtext)))
        except Exception:
            log(u"  GVL %s -- OSHIBKA" % name)
            err()

    # ----------------------------------------------------------  i m p o r t FBD
    head(u"import FBD-shem iz src/")
    imported = []
    for name in IMPORT_ORDER:
        path = os.path.join(SRC, u"%s.plcopenxml" % name)
        if not os.path.exists(path):
            log(u"  NET FajLA: %s" % path)
            continue
        try:
            app.import_xml(path)
            imported.append(name)
            log(u"  importirovan: %s" % name)
        except Exception:
            log(u"  OSHIBKA importa: %s" % name)
            err()
    log(u"itogo importirovano: %d iz %d" % (len(imported), len(IMPORT_ORDER)))

    # ----------------------------------------------------------  p r o v e r k a  s o s t a v a
    head(u"proverka sostava proekta")
    for name in IMPORT_ORDER:
        try:
            o = find_deep(app, name)
            if o is None:
                o = find_deep(proj, name)
            log(u"  %-12s -> %s" % (name, u"NAJDEN" if o is not None else u"NET!!!"))
        except Exception:
            err()

    # ---------------------------------------------------------- zadacha
    # Bez registratsii v zadache programmy ne vypolnyayutsya v simulyatsii.
    # Poryadok: snachala initsializatsiya, zatem zagruzka testov, zatem sam
    # emulyator. Vse tri -- v odnoj tsiklicheskoj zadache; odnorazovost
    # initsializatsii obespechivayut flagi InitDone/TestLoaded v GVL_InitState.
    #
    #  P O Ch E M U  ZADAChA SOZDAETSYa DO KOMPILYACII.
    #  app.generate_code() pri otsutstvii zadach zavershaetsya oshibkoj
    #  "V prilozhenii ne zadano zadach. I/O-obnovlenie nevozmozhno."
    #  Poetomu konfiguratsiya zadach idet PERVOJ, a kompilyaciya -- posle nee.
    head(u"nastroyka zadachi")
    try:
        tc = find_deep(app, u"Taskkonfiguration")
        if tc is None:
            tc = find_deep(app, u"Task Configuration")
        if tc is None:
            tc = app.create_task_configuration()
            log(u"  konfiguratsiya zadach sozdana")
        else:
            log(u"  konfiguratsiya zadach najdena")
        task = find_deep(tc, u"MainTask")
        if task is None:
            task = tc.create_task(u"MainTask")
            log(u"  MainTask sozdana")
        else:
            log(u"  MainTask najdena")
        try:
            task.priority = u"1"
            task.interval = u"T#10ms"
            log(u"  MainTask: prioritet 1, interval T#10ms")
        except Exception:
            log(u"  parametry MainTask zadat ne udalos")
            err()
        #  Spisok programm v zadache mozhno pereopredelit cherez
        #  peremennuyu okruzheniya Z80_TASK_POUS (imena cherez zapyatuyu).
        #  Eto nuzhno dlya diagnostiki: ustanovleno, chto imenno
        #  registraciya programm v zadache porozhdaet oshibki C32.
        _env = os.environ.get(u"Z80_TASK_POUS")
        if _env:
            _pous = [x.strip() for x in _env.split(u",") if x.strip()]
            log(u"  spisok zadach iz Z80_TASK_POUS: %s" % _pous)
        else:
            _pous = [u"PRG_InitMemory", u"TEST_Z80_PREP", u"PRG_CPM_Boot",
                     u"TEST_Z80", u"PRG_CPM_BDOS", u"TEST_Z80_CPM", u"PLC_PRG"]
        for prg in _pous:
            #  P R A V I L N Y J  S P O S O B  T O L K O  O D I N: add(imya, imya).
            #  Vyяснeno otdelnym opytom (generator/tools/probe_task.py):
            #    task.pous.add(imya, imya) -- rabotaet, element popadaet v spisok;
            #    task.pous[imya] = imya   -- "object does not support item
            #                                assignment", NE rabotaet;
            #    task.pous.append(imya)   -- net takogo metoda;
            #    task.pous.Add(imya)      -- net takogo metoda.
            #  U spiska programm zadachi est tolko: add, insert, remove, replace.
            #
            #  P O Ch E M U  E T O  V A Zh N O. Bez registracii v zadache
            #  CODESYS NE KOMPILIRUET programmu -- ona molchit, i oshibki
            #  v nej ne vsplyvayut. Imenno poetomu sborka "vse POU, no bez
            #  zadachi" davala "0 oshibok", a ta zhe sborka s zadachej --
            #  buket oshibok v TEST_Z80.
            try:
                task.pous.add(prg, prg)
                ok = True
            except Exception as e:
                log(u"    add(%s, %s) ne podoshel: %s" % (prg, prg, e))
                ok = False
            if not ok:
                log(u"  NE UDALOS dobavit v zadachu: %s" % prg)
                err()
        #  Ch T O   R E A L N O   Z A R E G I S T R I R O V A N O.
        #  Bez etoj proverki my ne vidim raznicy mezhdu "add() ne brosil
        #  isklyuchenie" i "programma deystvitel'no v zadache".
        try:
            lst = list(task.pous)
            log(u"  v zadache chisel: %d" % len(lst))
            for it in lst:
                log(u"    urovень: %r" % (it,))
        except Exception as e:
            log(u"  spisok urovney zadachi prochitat ne udalos: %s" % e)
    except Exception:
        log(u"  OSHIBKA nastroyki zadachi")
        err()

    # ----------------------------------------------------------  k o m p i l ya c i ya
    head(u"KOMPILYACIYA")
    #  V A Zh N O.  app.build() SOBIRAET prilozhenie, no NE kompiliruet kod:
    #  on vozvashchaet pustoj spisok soobshcheniy dazhe kogda v POU lezhit
    #  yavnaya oshibka. Proverено eksperimentom: v PRG_InitMemory byl vstavlen
    #  musor, i app.build() soobshchil "soobshcheniy: 0".
    #  Realnaya kompilyaciya -- app.generate_code(). Poluchit konkretnye oshibki
    #  cherez API ne udalos (get_messages pust i posle nee), no CODESYS pechataet
    #  itog v svoj vyvod, i run_codesys.ps1 ego sohranyaet. Poetomu:
    #    1) vyzyvaem build() i generate_code();
    #    2) v log idet napominanie, chto chitat nado vyvod CODESYS.
    # clear_messages v etom build zhdet Guid, a ne bool -- poetomu probuem
    # neskol'ko variantov. Ochistka soobshchenij vspomogatel'naya i ne dolzhna
    # lomat' sborku, po etomu lyubaya neudacha prosto propuskaetsya.
    for title, fn in ((u"clear_messages(None)", lambda: system.clear_messages(None)),
                      (u"clear_messages()", lambda: system.clear_messages())):
        try:
            fn()
            log(u"  %s -- OK" % title)
            break
        except Exception:
            log(u"  %s -- ne podoshel" % title)
    try:
        app.build()
        log(u">>> app.build() -- bez isklyucheniya (sborka prilozheniya)")
    except Exception:
        log(u">>> app.build() -- ISKLYuChENIE")
        err()
    try:
        app.generate_code()
        log(u">>> app.generate_code() -- bez isklyucheniya (N A S T O Ya Shch A Ya kompilyaciya)")
        log(u"    itog sm. v vyvode CODESYS: stroka 'Kompilyaciya zavershena -- N oshibok'")
    except Exception:
        log(u">>> app.generate_code() -- ISKLYuChENIE")
        err()

    log(u"---------- soobshcheniya kompilyatora ----------")
    n_err = 0
    try:
        msgs = system.get_messages()
        log(u"vsego: %d" % len(msgs))
        for m in msgs:
            parts = []
            for attr in (u"severity", u"text"):
                try:
                    parts.append(u"%s=%s" % (attr, getattr(m, attr)))
                except Exception:
                    pass
            line = u"  " + (u" | ".join(parts) if parts else repr(m))
            if u"Error" in line or u"error" in line:
                n_err += 1
            log(line)
    except Exception:
        err()
    log(u"OSHIBOK: %d" % n_err)

    # ----------------------------------------------------------  s o h r a n e n i e
    head(u"sohranenie")
    try:
        proj.save()
        log(u"sohran e n o: %s" % OUT_PROJECT)
    except Exception:
        err()
    try:
        proj.close()
        log(u"proj.close() OK")
    except Exception:
        err()

    log(u"")
    log(u"=== BUILD END (oshibok: %d) ===" % n_err)
    return n_err


try:
    _rc = main()
except Exception:
    log(u"FATAL:\n%s" % traceback.format_exc())
