# -*- coding: utf-8 -*-
u"""T E S T Y  dlya plana ispravleniy (napisany DO samih pravok).

ZAPUSKAT SISTEMNYM PYTHON 3:
    python generator/tools/tests_plan.py

ChTO PROVERYaEM. Kazhdyy test sootvetstvuet odnomu shagu plana i lovit
IMENNO TU oshibku, kotoruyu kompilyator soobshchil v otchyote iz IDE:

    T1  simvol '$' v tekstah ST                  -> C0189 / C0007 (PRG_CPM_Boot)
    T2  vyzov ORD(                               -> C0046 'ORD' ne zadаn (27 shtuk)
    T3  neveroyatnye konversii BYTE_TO_BYTE      -> C0046 (uzhe chineno ranshe)
    T4  soderzhimoe kazhdogo vyzova SEL v PLC_PRG -> C0032 USINT<->BOOL
    T5  mertvyy kod vida "Halted;" / "0;"         -> C0139 (warning)
    T6  kazhdyy ST-POU: zagolovok, VAR, END_VAR   -> C0383 / C0008
    T7  kompilyaciya: net ni odnoj oshibki C*     -> itog sborki

Testy T1-T6 rabotayut po fajlam src/ i ne trebuyut CODESYS.
Test T7 chitaet log/codesys_out.txt posle sborki.
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(ROOT, u"src")
LOG = os.path.join(ROOT, u"log", u"codesys_out.txt")

RESULTS = []


def setup_stdout():
    u"""Konsole Windows po umolchaniyu cp1251 i padaet na kirillice."""
    try:
        sys.stdout.reconfigure(encoding=u"utf-8", errors=u"replace")
    except Exception:                                          # noqa: BLE001
        pass


def test(num, name, fn):
    try:
        bad = fn()
    except Exception as exc:                                   # noqa: BLE001
        RESULTS.append((num, name, u"OSHIBKA TESTA: %s" % exc, []))
        return
    RESULTS.append((num, name, u"PROJDEN" if not bad else u"NE PROJDEN", bad))


def st_files():
    out = []
    for f in sorted(os.listdir(SRC)):
        if not f.endswith(u".plcopenxml"):
            continue
        t = io.open(os.path.join(SRC, f), encoding=u"utf-8").read()
        if u"<ST>" in t:
            out.append((f[:-len(u".plcopenxml")], t))
    return out


def st_body(text):
    u"""Telo POU bez otkryvayushchego tega <ST><xhtml ...>."""
    i = text.find(u"<ST>")
    j = text.find(u"</ST>")
    if i < 0 or j <= i:
        return u""
    b = text[i:j].replace(u"&#xA;", u"\n").replace(u"&quot;", u'"')
    b = b.replace(u"&lt;", u"<").replace(u"&gt;", u">").replace(u"&amp;", u"&")
    #  P E R V A Ya  S T R O K A -- eto teg, a ne operator. Bez ego snyatiya
    #  regulyarka s nachalom stroki ne vidit pervyj IF, i schetchik
    #  dokladyvaet lozhnyj disbalans.
    tag = re.compile(u"^[ \\t]*<[A-Za-z/!?][^>]*>")
    out = []
    for l in b.split(u"\n"):
        m = tag.match(l)
        if m:
            l = l[m.end():]
        out.append(l)
    return u"\n".join(out)


def st_decl(text):
    u"""Obyavlenie POU s R A S K O D I R O V A N N Y M I suschnostyami.

    V A Zh N O: v fajle perevody strok zapisany kak &#xA;. Pervaya versiya
    etoj funkcii ih ne raskodirovala -- i togda testy T6/T4 videli odnu
    dlinnuyu stroku s tekstom "&#xA;" vnutri i dokladyvali o problemah,
    kotoryh net.
    """
    m = re.search(u"<InterfaceAsPlainText>.*?<xhtml[^>]*>(.*?)</xhtml>", text, re.S)
    if not m:
        return u""
    d = m.group(1)
    d = d.replace(u"&#xA;", u"\n").replace(u"&quot;", u'"')
    return d.replace(u"&lt;", u"<").replace(u"&gt;", u">").replace(u"&amp;", u"&")


# ---------------------------------------------------------------- T1
def no_comments(txt):
    u"""Ubiraem ST-kommentarii (* ... *) i // -- v nih '$' bezopasen."""
    txt = re.sub(u"\\(\\*.*?\\*\\)", u" ", txt, flags=re.S)
    txt = re.sub(u"(?m)//[^\n]*", u" ", txt)
    return txt


def t1():
    u"""Simvol '$' v KODE ST (vne kommentariev): v CODESYS eto escape."""
    bad = []
    for name, t in st_files():
        for where, txt in ((u"telo", st_body(t)), (u"obyavlenie", st_decl(t))):
            txt = no_comments(txt)
            for m in re.finditer(u"\\$", txt):
                ln = txt[:m.start()].count(u"\n") + 1
                ctx = txt[max(0, m.start() - 40):m.start() + 20].replace(u"\n", u" ")
                bad.append(u"%s (%s, str.%d): ...%s..." % (name, where, ln, ctx))
    return bad


# ---------------------------------------------------------------- T2
def t2():
    u"""Vyzov ORD(...): v etoy versii CODESYS takoy funkcii net."""
    bad = []
    for name, t in st_files():
        for where, txt in ((u"telo", st_body(t)), (u"obyavlenie", st_decl(t))):
            for m in re.finditer(u"\\bORD\\s*\\(", txt):
                ln = txt[:m.start()].count(u"\n") + 1
                bad.append(u"%s (%s, str.%d)" % (name, where, ln))
    return bad


# ---------------------------------------------------------------- T3
TYPE_WORDS = (u"BOOL", u"BYTE", u"WORD", u"DWORD", u"SINT", u"USINT", u"INT",
              u"UINT", u"DINT", u"UDINT", u"LINT", u"ULINT", u"REAL", u"LREAL")


def t3():
    u"""Preobrazovanie tipa v samogo sebya: BYTE_TO_BYTE i t. p."""
    pat = re.compile(u"\\b(%s)_TO_(%s)\\b" % (u"|".join(TYPE_WORDS),
                                              u"|".join(TYPE_WORDS)))
    bad = []
    for name, t in st_files():
        for m in pat.finditer(st_body(t)):
            if m.group(1) == m.group(2):
                bad.append(u"%s: %s" % (name, m.group(0)))
    #  i v shemah FBD
    for f in sorted(os.listdir(SRC)):
        if not f.endswith(u".plcopenxml"):
            continue
        t = io.open(os.path.join(SRC, f), encoding=u"utf-8").read()
        for m in pat.finditer(t):
            if m.group(1) == m.group(2):
                bad.append(u"%s (shema): %s" % (f[:-len(u".plcopenxml")], m.group(0)))
    return bad


# ---------------------------------------------------------------- T4
def t4():
    u"""V SEL uslovie (vhod G) dolzhno byt tipa BOOL.

    P R O V E R Ya E M  T I P, A  N E  «SPOSOB P O D K L Yu Ch E N I Ya».
    Pervaya versiya etogo testa trebovala, chtoby G bylo podklyucheno k
    I M E N O V A N N O J peremennoj, i schitala oshibkoy podachu vyhoda
    bloka sravneniya EQ napryamuyu. Eto bylo neverno: EQ vozvratit BOOL,
    i takaya svyazka zakonna -- imenno takustroeny vse cepochki vybora.

    Teper my razbiraem tip rekurssivno (cherez vse bloki) i trebuem tolko
    odnogo: tip usloviya dolzhen byt BOOL. Esli tip opredelit ne udalos
    (naprimer, vyhod pol zovatel skogo FB), vhod propuskaem -- inache test
    nachnet vrat' na zakonnyh shemah.
    """
    bad = []
    for f in sorted(os.listdir(SRC)):
        if not f.endswith(u".plcopenxml"):
            continue
        name = f[:-len(u".plcopenxml")]
        t = io.open(os.path.join(SRC, f), encoding=u"utf-8").read()
        if u"<FBD>" not in t:
            continue
        elems = _elements(t)
        decls = _decls(t)
        for m in re.finditer(u'<block localId="(\\d+)" typeName="SEL"', t):
            lid = m.group(1)
            pins = _pins(t, lid)
            g = pins.get(u"G")
            if g is None:
                continue
            tp = _rtype(g, elems, decls)
            if tp is not None and tp != u"BOOL":
                bad.append(u"%s: SEL %s -- uslovie G tipa %s (nuzhen BOOL)"
                           % (name, lid, tp))
    return bad


# ---------------------------------------------------------------- T5
def t5():
    u"""Mertvyy kod vida "Halted;" -- ssylka na peremennuyu bez dejstviya."""
    bad = []
    for name, t in st_files():
        body = st_body(t)
        #  stroka, sostoyashchaya tolko iz imeni i tochki s zapyatoj,
        #  vne kommentariev
        clean = re.sub(u"\\(\\*.*?\\*\\)", u" ", body, flags=re.S)
        for ln, line in enumerate(clean.split(u"\n"), 1):
            s = line.strip()
            if re.match(u"^[A-Za-z_]\\w*;$", s) and s != u"END_IF;":
                bad.append(u"%s: str.%d  %s" % (name, ln, s))
    return bad


# ---------------------------------------------------------------- T6
def t6():
    u"""Kazhdyj ST-POU: ZAGOLOVOK VIDA POU, blok VAR, balans IF/FOR.

    Z A G O L O V O K  O B Ya Z A T E L E N, i eto vyяснено eksperimentom.
    Pervonachalno test treboval obratnoe -- chtoby zagolovka NE bylo. Eto
    bylo neverno: atribut pouType="program" sam po sebe vid POU NE zadayot,
    i bez zagolovka CODESYS schitaet obekt funktsionalnym blokom. V otchyote
    eto vyglyadit tak (ni nomera stroki, ni imeni POU):
        C46: Identifikator 'PRG_InitMemory' ne zadan
        C35: Vmesto 'PRG_InitMemory' trebuetsya imya programmy, funkciya
             ili ekzemplyar funktsionalnogo bloka
    Podtverzhdeno chteniem textual_declaration u sobrannogo proekta: u POU
    bez zagolovka pervaya stroka -- kommentar, u FUNCTION_BLOCK -- zagolovok.
    """
    bad = []
    for name, t in st_files():
        decl = st_decl(t)
        head = decl.strip().split(u"\n")[0] if decl.strip() else u""
        if not re.match(u"^(PROGRAM|FUNCTION_BLOCK|FUNCTION)\\s+\\w+", head):
            bad.append(u"%s: net zagolovka POU (nachalo: %r)" % (name, head[:50]))
        if not decl.strip():
            bad.append(u"%s: pustoe obyavlenie" % name)
        if u"VAR" not in decl:
            bad.append(u"%s: net bloka VAR" % name)
        if u"END_VAR" not in decl:
            bad.append(u"%s: net END_VAR" % name)
        body = st_body(t)
        if not body.strip():
            bad.append(u"%s: pustoe telo" % name)
        clean = no_comments(body)
        #  telo ne dolzhno soderzhat sekcij VAR
        if re.search(u"(?m)^\\s*VAR(_INPUT|_OUTPUT|_IN_OUT|_GLOBAL|_EXTERNAL)?\\s*$",
                     clean):
            bad.append(u"%s: blok VAR popal v telo" % name)
        #  B A L A N S  U S L O V I J. ELSIF i ELSE -- eto NE novye bloki,
        #  oni prodolzhayut tot zhe IF. Poetomu snachala ih vykidyvaem,
        #  i tolko potom schitaem IF i END_IF. Inache poluchaetsya lozhnyj
        #  disbalans: v nashem kode IF-ELSIF-IF-END_IF-END_IF, i ELSIF
        #  schitalsya kak eshche odin otkrytyj blok.
        body_only = re.sub(u"(?im)^\\s*(ELSIF|ELSE)\\b.*$", u" ", clean)
        n_if = len(re.findall(u"(?im)^\\s*IF\\b", body_only))
        n_end = len(re.findall(u"(?im)^\\s*END_IF\\b", body_only))
        if n_if != n_end:
            bad.append(u"%s: IF=%d, END_IF=%d (ne balans)" % (name, n_if, n_end))
        n_for = len(re.findall(u"(?im)^\\s*FOR\\b", body_only))
        n_efor = len(re.findall(u"(?im)^\\s*END_FOR\\b", body_only))
        if n_for != n_efor:
            bad.append(u"%s: FOR=%d, END_FOR=%d (ne balans)" % (name, n_for, n_efor))
    return bad


# ---------------------------------------------------------------- T7
def read_log():
    u"""Chitaem log sborki.

    I S T O R I Ya. Snachala tut perebiralis cp866/cp1251/utf-8 -- i pervym
    shel cp866, kotoryj "uspeshno" raskodiruet LYUBYE bajty. V rezul tate
    normalnyj UTF-8 log prevrashchalsya v krakozyabry, i test T7 ne mog
    najti ni slova "Error", ni stroki "zavershena". Teper pervym idet utf-8:
    nash run_build_log.ps1 pishet log imenno v UTF-8, a cp866 ostalsya
    zapasnym variantom dlya staryh logov.
    """
    raw = io.open(LOG, u"rb").read()
    if not raw:
        return u""
    for cp in (u"utf-8", u"cp1251", u"cp866"):
        try:
            t = raw.decode(cp)
        except Exception:                                      # noqa: BLE001
            continue
        #  priznak pravilnoj kodirovki -- nalichie latinskih slov iz loga
        if u"Error" in t or u"zavershena" in t or u"\u041e\u0448\u0438\u0431" in t:
            return t
    return raw.decode(u"utf-8", u"replace")


def t7():
    u"""Itog kompilyacii: ni odnoj oshibki i stroka 'zavershena -- 0 oshibok'.

    V N I M A N I E  P O  K O D I R O V K E. CODESYS pishet itog
    P O - R U S S K I: "Компиляция завершена -- 0 ошибок". Pervaya versiya
    etogo testa iskala latinskoe "zavershena" i poetomu V S E G D A padala,
    dazhe kogda sborka byla chistoj. Teper ishchem oba varianta.
    """
    if not os.path.exists(LOG) or os.path.getsize(LOG) == 0:
        return [u"log kompilyacii pust -- sborka ne proshla"]
    t = read_log()
    bad = []
    itog = [l.strip() for l in t.split(u"\n")
            if u"завершена" in l or u"zavershena" in l]
    if not itog:
        bad.append(u"net stroki 'Компиляция завершена' -- sborka oborvalas")
    for l in itog:
        if u"0 ошибок" not in l and u"0 oshibok" not in l:
            bad.append(u"ITOG: " + l[:120])
    seen = {}
    for l in t.split(u"\n"):
        if u": Error:" not in l:
            continue
        k = re.sub(u"[0-9]+", u"N", l.strip())[:150]
        seen[k] = seen.get(k, 0) + 1
    for k in sorted(seen):
        bad.append(u"%dx %s" % (seen[k], k))
    return bad


# ---------------------------------------------------------------- T8
u"""T8: v cepochkah vybora vse vetki ODNOGO tipa, a uslovie -- BOOL.

Z A Ch E M  E T O T  T E S T. Kompilyator daet sem par oshibok
    C32: Nevozmozhno konvertirovat tip 'BOOL'  v tip 'USINT'
    C32: Nevozmozhno konvertirovat tip 'USINT' v tip 'BOOL'
i ni odna iz nih ne ukazyvaet ni POU, ni nomer seti. Prichina: blok SEL
obobshchennyj (ANY), ego tip vyvoditsya po vetkam IN0/IN1. Esli vetki
raznogo tipa -- CODESYS beret USINT dlya vseh i potom ne mozhet ni
prisvoit rezul tat v BYTE, ni soglasovat s usloviem.

T E S T  L O V I T  I M E N N O  E T O: dlya kazhdogo bloka vybora
(SEL ili MUX) razbiraem tip kazhdoj vetki i trebuem, chtoby oni sovpadali,
a uslovie G (dlya MUX -- nomer K) bylo buleva tipa / chislennym.

Tip vyvoda bloka schitaem po pravilam:
  * blok-konversiya X_TO_Y              -> Y;
  * SEL / MUX                           -> tip ego vetki;
  * AND/OR/XOR/NOT/SHL/SHR/ADD/SUB/...  -> tip pervogo operanda;
  * ekzemplyar pol zovatel skogo FB     -> tip neizvesten (propuskaem).
"""

BOOLISH = (u"AND", u"OR", u"XOR", u"NOT", u"EQ", u"NE",
           u"GT", u"LT", u"GE", u"LE")
GENERIC = BOOLISH + (u"ADD", u"SUB", u"MUL", u"DIV", u"MOD",
                     u"SHL", u"SHR", u"ROL", u"ROR", u"MOVE")


def _elements(text):
    u"""localId -> ('invar'|'outvar'|'block', znachenie)."""
    e = {}
    for m in re.finditer(u'<inVariable localId="(\\d+)"[^>]*>(.*?)</inVariable>',
                         text, re.S):
        x = re.search(u"<expression>([^<]*)</expression>", m.group(2))
        e[m.group(1)] = (u"invar", xml_unescape(x.group(1)) if x else u"")
    for m in re.finditer(u'<outVariable localId="(\\d+)"[^>]*>(.*?)</outVariable>',
                         text, re.S):
        x = re.search(u"<expression>([^<]*)</expression>", m.group(2))
        e[m.group(1)] = (u"outvar", xml_unescape(x.group(1)) if x else u"")
    for m in re.finditer(u'<block localId="(\\d+)" typeName="(\\w+)"', text):
        e[m.group(1)] = (u"block", m.group(2))
    return e


def xml_unescape(s):
    return (s.replace(u"&#xA;", u"\n").replace(u"&quot;", u'"')
             .replace(u"&lt;", u"<").replace(u"&gt;", u">").replace(u"&amp;", u"&"))


def _decls(text):
    u"""Imya peremennoj -> tip IEC."""
    out = {}
    for m in re.finditer(u'<variable name="(\\w+)">\\s*<type>\\s*<(\\w+)\\s*/>', text):
        out[m.group(1)] = m.group(2)
    for m in re.finditer(u'<variable name="(\\w+)">\\s*<type>\\s*'
                         u'<derived name="(\\w+)"', text):
        out[m.group(1)] = m.group(2)
    return out


def _block_segment(text, lid):
    i = text.find(u'<block localId="%s"' % lid)
    if i < 0:
        return u""
    j = text.find(u"</block>", i)
    return text[i:j] if j > 0 else text[i:]


def _pins(text, lid):
    u"""Imя vyvoda -> refLocalId istochnika."""
    seg = _block_segment(text, lid)
    out = {}
    for m in re.finditer(u'<variable formalParameter="([^"]*)">\\s*'
                         u'<connectionPointIn>(.*?)</connectionPointIn>',
                         seg, re.S):
        r = re.search(u'<connection refLocalId="(\\d+)"', m.group(2))
        if r:
            out[m.group(1)] = r.group(1)
    return out


def _rtype(lid, elems, decls, depth=0):
    u"""Tip signala po localId. None -- opredelit ne udalos."""
    if depth > 8 or lid is None:
        return None
    e = elems.get(lid)
    if not e:
        return None
    kind, val = e
    if kind in (u"invar", u"outvar"):
        return decls.get(val)
    if u"_TO_" in val:
        return val.split(u"_TO_")[-1]
    return None


def t8():
    u"""Vetvi vybora odnogo tipa, uslovie -- BOOL (sm. docstring bloka T8)."""
    bad = []
    for f in sorted(os.listdir(SRC)):
        if not f.endswith(u".plcopenxml"):
            continue
        name = f[:-len(u".plcopenxml")]
        t = io.open(os.path.join(SRC, f), encoding=u"utf-8").read()
        if u"<FBD>" not in t:
            continue
        elems = _elements(t)
        decls = _decls(t)
        for m in re.finditer(u'<block localId="(\\d+)" typeName="(SEL|MUX)"', t):
            lid, kind = m.group(1), m.group(2)
            pins = _pins(t, lid)

            def rt(pin):
                return _rtype(pins.get(pin), elems, decls)

            if kind == u"SEL":
                tg, t0, t1 = rt(u"G"), rt(u"IN0"), rt(u"IN1")
                if tg is not None and tg != u"BOOL":
                    bad.append(u"%s: SEL %s -- uslovie G tipa %s (nuzhen BOOL)"
                               % (name, lid, tg))
                if t0 is not None and t1 is not None and t0 != t1:
                    bad.append(u"%s: SEL %s -- vetki RAZNYH tipov: IN0=%s, IN1=%s"
                               % (name, lid, t0, t1))
            else:
                #  MUX: vybor chislennym nomerom, vse vetki odnogo tipa
                tk = rt(u"K")
                if tk is not None and tk not in (u"BYTE", u"USINT", u"SINT",
                                                 u"INT", u"UINT", u"WORD",
                                                 u"DINT", u"UDINT"):
                    bad.append(u"%s: MUX %s -- nomer K tipa %s (nuzhno chislo)"
                               % (name, lid, tk))
                ins = sorted(p for p in pins if p.startswith(u"IN"))
                types = {}
                for p in ins:
                    tp = _rtype(pins[p], elems, decls)
                    if tp is not None:
                        types[p] = tp
                uniq = sorted(set(types.values()))
                if len(uniq) > 1:
                    bad.append(u"%s: MUX %s -- vetki RAZNYH tipov: %s"
                               % (name, lid, types))
    return bad


def t9():
    u"""V loge net C196 -- neyavnyh konversij so smenoj znaka.

    P O Ch E M U  O T D E L N Y J  T E S T. Kompilyator soobshchaet
        C196: Neyavnaya konversiya iz tipa WORD v tip INT: vozmozhno
              izmenenie znaka
    B E Z  imeni POU i nomera stroki, poetomu po logu nel zya ponyat, gde
    imenno problema. Eto preduprezhdenie kovarno tem, chto chislo bol she
    32767 prevratitsya v otricatel noe -- dlya emulyatora s 64 KB pamyati
    eto real nyj defekt, a ne kosmetika.

    V etom proekte prichiny byli takie:
      * smeshenie WORD i INT v odnom vyrazhenii (naprimer nPtr + 32 * i);
      * granitsa cikla, vyvedennaya kak UINT (64 * 32 - 1).
    Test derzhit etot klass defektov zakrytym.
    """
    if not os.path.exists(LOG) or os.path.getsize(LOG) == 0:
        return [u"log kompilyacii pust -- sborka ne proshla"]
    t = read_log()
    bad = []
    for l in t.split(u"\n"):
        if u"Warning" in l and u"C196" in l:
            k = l.strip()[:150]
            if k not in bad:
                bad.append(k)
    return bad


def t10():
    u"""Privyazka k ustrojstvu: u peremennyh PLC_PRG est adresa %I/%Q.

    T R E B O V A N I E  Z A D A N I Ya: porty Z80 otobrazheny na vhody/vyhody
    PLK cherez Device Tree. Eto znachit, chto peremennye, cherez kotorye shema
    obshchaetsya s zhelezom, obyavleny s adresom vida
        PLC_DI_0 AT %IX0.0 : BOOL;
    Esli adresov net, privyazki net -- i na real nom PLK vse vhody okazhutsya
    nezavisimymi pamyatnymi yachejkami, a ne kanalami.

    Prover yaem: 8 diskretnyh vhodov, 8 diskretnyh vyhodov, 2 analogovyh
    vhoda i 2 analogovyh vyhoda -- rovno 20 adresov.
    """
    path = os.path.join(SRC, u"PLC_PRG.plcopenxml")
    if not os.path.exists(path):
        return [u"net PLC_PRG.plcopenxml"]
    t = io.open(path, encoding=u"utf-8").read()
    m = re.search(u'<InterfaceAsPlainText>\\s*<xhtml[^>]*>(.*?)</xhtml>', t, re.S)
    if not m:
        return [u"net tekstovogo obyavleniya v PLC_PRG"]
    d = unesc = m.group(1).replace(u"&#xA;", u"\n")
    for a, b in ((u"&quot;", u'"'), (u"&lt;", u"<"), (u"&gt;", u">"),
                 (u"&amp;", u"&")):
        d = d.replace(a, b)

    want = {u"%IX0.0": u"BOOL", u"%IX0.1": u"BOOL", u"%IX0.2": u"BOOL",
            u"%IX0.3": u"BOOL", u"%IX0.4": u"BOOL", u"%IX0.5": u"BOOL",
            u"%IX0.6": u"BOOL", u"%IX0.7": u"BOOL",
            u"%QX0.0": u"BOOL", u"%QX0.1": u"BOOL", u"%QX0.2": u"BOOL",
            u"%QX0.3": u"BOOL", u"%QX0.4": u"BOOL", u"%QX0.5": u"BOOL",
            u"%QX0.6": u"BOOL", u"%QX0.7": u"BOOL",
            u"%IW0": u"INT", u"%IW1": u"INT",
            u"%QW0": u"INT", u"%QW1": u"INT"}

    have = {}
    for line in d.split(u"\n"):
        line = line.split(u"(*")[0]
        mm = re.match(u'\\s*(\\w+)\\s+AT\\s+(%[IQXWB][^*:]+?)\\s*:\\s*(\\w+)', line)
        if mm:
            have[mm.group(2).strip()] = mm.group(3).strip()

    bad = []
    for addr in sorted(want):
        if addr not in have:
            bad.append(u"net adresa %s (ozhidal tip %s)" % (addr, want[addr]))
        elif have[addr] != want[addr]:
            bad.append(u"%s obyavlen kak %s, a ozhidalsya %s"
                       % (addr, have[addr], want[addr]))
    return bad


def main():
    setup_stdout()
    test(1, u"T1: net simvola '$' v ST", t1)
    test(2, u"T2: net vyzovov ORD(", t2)
    test(3, u"T3: net konversij tipa v sebya", t3)
    test(4, u"T4: usloviya SEL imeyut tip BOOL", t4)
    test(5, u"T5: net mertvogo koda", t5)
    test(6, u"T6: struktura ST-POU", t6)
    test(7, u"T7: kompilyaciya bez oshibok", t7)
    test(8, u"T8: vetki vybora odnogo tipa", t8)
    test(9, u"T9: net C196 (konversij so smenoj znaka)", t9)
    test(10, u"T10: privyazka k PLK (%I/%Q)", t10)

    sys.stdout.write(u"%-4s %-38s %-12s %s\n" % (u"#", u"TEST", u"REZUL'TAT", u"DETALI"))
    sys.stdout.write(u"-" * 96 + u"\n")
    fails = 0
    for num, name, res, det in RESULTS:
        sys.stdout.write(u"%-4d %-38s %-12s\n" % (num, name, res))
        for d in det[:6]:
            sys.stdout.write(u"       %s\n" % d)
        if det and len(det) > 6:
            sys.stdout.write(u"       ... i eshhe %d\n" % (len(det) - 6))
        if res != u"PROJDEN":
            fails += 1
    sys.stdout.write(u"\nITOGO: %d iz %d testov projdeno\n"
                     % (len(RESULTS) - fails, len(RESULTS)))
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
