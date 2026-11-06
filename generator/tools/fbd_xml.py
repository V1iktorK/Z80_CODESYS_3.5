# -*- coding: utf-8 -*-
u"""Генератор PLCopenXML для FBD-схем CODESYS 3.5 SP17.

ЭТО БИБЛИОТЕКА, её импортируют скрипты-сборщики (запускаются внутри CODESYS).

Правила диалекта — всё выяснено экспериментально, каждое правило оплачено
отладочным циклом (см. docs/03_ЖУРНАЛ_СБОРКИ.md):

  1. Тело FBD:  <body><FBD> ...элементы... </FBD></body>
     БЕЗ обёртки <network>. Сети в плоском списке разделяются только связями.

  2. localId должны быть УНИКАЛЬНЫ внутри всего POU, а не внутри сети.
     Иначе <connection refLocalId=N> попадает на чужой элемент и связи
     молча теряются (проверено: из 4 входов выживал 1).

  3. Порядок детей <block> строгий:
        position -> inputVariables -> inOutVariables -> outputVariables
     <inOutVariables/> ОБЯЗАТЕЛЕН, даже пустой. Иначе импорт падает:
     "Элемент block имеет недопустимый дочерний элемент outputVariables".

  4. <interface> НЕ МОЖЕТ быть пустым. Если объявить переменные только текстом
     в addData/InterfaceAsPlainText, CODESYS импорт "выполняет" без ошибки,
     но POU в проекте не появляется. Нужны и структурный <interface>,
     и текстовый дубль.

  5. Связь:  <connectionPointIn><connection refLocalId="N" /></connectionPointIn>
     formalParameter можно не указывать — CODESYS сопоставляет по позиции.
     Для блоков с несколькими выводами имя вывода обязательно.

  6. Координаты x/y CODESYS при импорте игнорирует и раскладывает схему сам
     (в экспорте все позиции обнуляются). Мы их всё равно задаём — XML
     остаётся читаемым и переносимым в другие инструменты.

Стиль схемы: сигналы строго слева направо. Колонки 40 / 200 / 360 / 520,
шаг по вертикали 30 px.
"""

import io
import re

XHTML = u'http://www.w3.org/1999/xhtml'
NS_PLAINTEXT = u'http://www.3s-software.com/plcopenxml/interfaceasplaintext'

COL_IN = 40        # колонка входных переменных
COL_BLK = 200      # колонка блоков
COL_BLK2 = 360     # колонка вторых блоков (каскады)
COL_OUT = 520      # колонка выходных переменных
ROW_H = 30         # шаг по вертикали
ROW0 = 40          # первая строка

ELEMENTARY = (u"BOOL", u"BYTE", u"WORD", u"DWORD", u"SINT", u"USINT", u"INT",
              u"UINT", u"DINT", u"UDINT", u"LINT", u"ULINT", u"REAL", u"LREAL",
              u"TIME", u"STRING", u"WSTRING")


# ---------------------------------------------------------------------------
# Слой совместимости Python 2 / Python 3.
# Библиотека запускается в ДВУХ окружениях:
#   * системный Python 3 -- генерация XML (файлы src/*.plcopenxml);
#   * IronPython 2.7 внутри CODESYS -- импорт схем (generator/build.py).
# В Python 3 нет встроенного unicode и иначе работает с текстом, поэтому
# определяем unicode сами и переводим esc() на безопасное приведение.
# ---------------------------------------------------------------------------
try:
    unicode
except NameError:                                   # Python 3
    unicode = str


def _u(s):
    u"""Привести значение к тексту (одинаково работает в Python 2 и 3)."""
    if isinstance(s, unicode):
        return s
    if isinstance(s, bytes):
        return s.decode(u"utf-8")
    return unicode(s)


def esc(s):
    u"""Экранирование XML."""
    return (_u(s).replace(u"&", u"&amp;").replace(u"<", u"&lt;")
            .replace(u">", u"&gt;").replace(u'"', u"&quot;"))


def type_xml(type_text):
    u"""IEC-тип -> XML-описание типа для PLCopenXML.

    Direktiva privyazki otbrasyvaetsya: stukturnyj <interface> opisyvaet TIP,
    a adres %IX0.0 -- otdel'naya informaciya, kotoruyu neset tekst obyavleniya.
    Bez etogo v XML popadalo <derived name="BOOL AT %IX0.0" />, i CODESYS
    schital eto neizvestnym tipom.
    """
    t = type_text.strip().upper()
    if u" AT " in t:
        t = t.split(u" AT ")[0].strip()
    if t.startswith(u"ARRAY[") and u" OF " in t:
        rng, base = t[6:].split(u"] OF ", 1)
        lo, hi = rng.split(u"..")
        return (u'<array><dimension lower="%s" upper="%s" />'
                u'<baseType>%s</baseType></array>' % (lo.strip(), hi.strip(), type_xml(base)))
    if t in ELEMENTARY:
        return u'<%s />' % t
    return u'<derived name="%s" />' % esc(type_text.strip())


class Var(object):
    u"""Объявляемая переменная: имя, IEC-тип, необязательный комментарий и адрес.

    address -- строка вида "%IX0.0" для прямой привязки к входу/выходу ПЛК.
    В IEC 61131-3 синтаксис объявления с адресом такой:
        PLC_DI_0 AT %IX0.0 : BOOL;
    то есть AT стоит МЕЖДУ именем и двоеточием. Поставить его в конец
    (после типа) нельзя -- компилятор ответит
        C6: ';, :=, REF=, ( или [' требуется вместо 'AT'.
    Поэтому адрес храним отдельным полем, а не подклеиваем к типу.
    """
    __slots__ = (u"name", u"type", u"comment", u"address")

    def __init__(self, name, type_text, comment=None, address=None):
        self.name = name
        self.type = type_text
        self.comment = comment
        self.address = address

    def plain(self):
        addr = (u" AT %s" % self.address) if self.address else u""
        if self.comment:
            return u'\t%s%s : %s; (* %s *)' % (self.name, addr, self.type,
                                               self.comment)
        return u'\t%s%s : %s;' % (self.name, addr, self.type)

    def xml(self):
        #  В структурном <interface> адрес НЕ указываем: CODESYS при импорте
        #  PLCopenXML отвергает <address> внутри переменной FBD-POU. Адрес
        #  живёт только в текстовом объявлении (InterfaceAsPlainText) --
        #  оттуда его и читает компилятор.
        return (u'            <variable name="%s"><type>%s</type></variable>'
                % (esc(self.name), type_xml(self.type)))

    def xml(self):
        return (u'            <variable name="%s"><type>%s</type></variable>'
                % (esc(self.name), type_xml(self.type)))


class Src(object):
    u"""Ссылка на выход элемента схемы: localId + (необязательно) имя вывода."""
    __slots__ = (u"eid", u"pin")

    def __init__(self, eid, pin=None):
        self.eid = eid
        self.pin = pin


class BlockRef(Src):
    u"""Ссылка на блок. Для блока с несколькими выводами имя вывода обязательно,
    поэтому берём его через .out(u"Sum")."""

    def __init__(self, eid, pins):
        Src.__init__(self, eid, pins[0] if len(pins) > 1 else None)
        self.pins = pins

    def out(self, pin):
        return Src(self.eid, pin)


class Network(object):
    u"""Одна сеть FBD.

    Номера элементов берутся у POU-владельца (сквозная нумерация, см. п.2 выше).
    """

    def __init__(self, number, title=u"", owner=None):
        self.number = number
        self.title = title
        self._owner = owner
        self._items = []
        self._auto_y = ROW0
        self._inst = {}        # localId -> имя экземпляра FB (для вызовов FB)

    def _nid(self):
        return self._owner._nid()

    def _y(self, y):
        if y is not None:
            return y
        v = self._auto_y
        self._auto_y += ROW_H
        return v

    # ---------- элементы ----------
    def invar(self, expr, x=COL_IN, y=None):
        u"""Входная переменная (источник сигнала)."""
        i = self._nid()
        self._items.append((u"invar", i, expr, x, self._y(y)))
        return Src(i)

    def const(self, literal, x=COL_IN, y=None):
        u"""Константа — тоже inputVariable, но с литералом вместо имени."""
        return self.invar(literal, x, y)

    def outvar(self, expr, src, x=COL_OUT, y=None):
        u"""Выходная переменная (приёмник)."""
        i = self._nid()
        self._items.append((u"outvar", i, expr, _src(src), x, self._y(y)))
        return Src(i)

    def typed(self, src, tip):
        u"""Сделать ЛИТЕРАЛ в ветви явно типизированным: 16#00 -> BYTE#16#00.

        П О Ч Е М У  Э Т О  Н У Ж Н О. Блок SEL обобщённый: его тип выводится
        по ветвям IN0/IN1. Если одна ветвь -- переменная BYTE, а другая --
        «голый» литерал 16#00, компилятор вынужден сам выбирать тип литерала
        и в цепочке из десятка SEL ошибается: берёт USINT, и тогда
        присвоение результата в BYTE даёт
            C32: Невозможно конвертировать тип 'USINT' в тип 'BOOL'.
        Явная запись BYTE#16#00 снимает выбор: тип ветви задан текстом.

        Работает только с литералами. Переменные и выходы блоков не трогаем:
        у них тип уже есть (или его задаёт сам блок).

        В А Ж Н О: функция возвращает ТОТ ЖЕ Src, поэтому встраивается
        в существующие вызовы без переделки схем.
        """
        if src is None or tip is None:
            return src
        #  V N I M A N I E: _src() vozvrashchaet O B E K T Src, a ne nomer.
        #  Pervaya versiya sravnivala it[1] (chislo) s etim obektom, sravnenie
        #  nikogda ne sovpadalo, i tipizaciya molcha ne srabatyvala -- vneshne
        #  oshibki ostavalis, hotya kod vyglyadel pravilno.
        eid = _src(src).eid
        for idx, it in enumerate(self._items):
            if it[1] != eid:
                continue
            if it[0] != u"invar":
                return src          # eto blok ili vyhod -- ne tronem
            expr = it[2]
            s = (u"%s" % expr).strip()
            #  U Zh E  T I P I Z I R O V A N: nachinaetsya s imeni tipa pered "#".
            #  V A Zh N O  N E  S P U T A T' s osnovaniem sistemy schisleniya:
            #  "16#00" nachinaetsya s C I F R, a "BYTE#16#00" -- s imeni.
            if re.match(u"^[A-Za-z][A-Za-z0-9_]*#", s):
                return src
            if not (re.match(u"^\\d+$", s) or re.match(u"^\\d+#", s)):
                return src          # ne literal
            self._items[idx] = (it[0], it[1], u"%s#%s" % (tip.upper(), s),
                                it[3], it[4])
            return src
        return src

    def block(self, type_name, inputs, outputs, x=COL_BLK, y=None, instance=None):
        u"""Блок. inputs — [(pin, Src)]. outputs — [имя вывода].

        instance — имя экземпляра для вызова пользовательского FB
        (при этом сам экземпляр должен быть объявлен в VAR POU).

        Возвращает BlockRef. Для блока с несколькими выводами имя вывода
        берётся через .out(u"Sum").
        """
        i = self._nid()
        yv = self._y(y)
        self._items.append((u"block", i, type_name, inputs, outputs, x, yv))
        if instance:
            self._inst[i] = instance
        return BlockRef(i, outputs)

    # ---------- отрисовка ----------
    def _expand_fanout(self):
        u"""Размножить источники, у которых больше одной исходящей связи.

        Причина: CODESYS 3.5 SP17 молча выбрасывает POU целиком, если ЛЮБОЙ выход
        (входная переменная ИЛИ выход блока) питает более одного входа.
        Проверено бисекцией: POU с fan-out теряется, а межсетевые ссылки работают.

        Как лечим: схему-граф разворачиваем в дерево. Первое использование
        элемента оставляем как есть, для каждого следующего создаём КОПИЮ
        элемента (со всей его входной ветвью) непосредственно перед
        потребителем — ссылка всегда идёт «назад», как того требует импортёр.

        Исключение: вызов пользовательского FB размножать нельзя (экземпляр
        один). Такой случай — ошибка проектирования схемы: сигнал надо провести
        через переменную.
        """
        items = self._items
        by_id = dict([(it[1], it) for it in items])

        def sources(it):
            if it[0] == u"invar":
                return []
            if it[0] == u"outvar":
                return [_src(it[3])]
            return [_src(s) for _, s in it[3]]

        uses = {}
        for it in items:
            for s in sources(it):
                uses[s.eid] = uses.get(s.eid, 0) + 1
        if not uses or max(uses.values()) <= 1:
            return

        taken = {}
        pending = []

        def clone(it):
            if it[0] == u"invar":
                cand = (u"invar", self._nid(), it[2], it[3], it[4] + 12)
            elif it[0] == u"block":
                inst = self._inst.get(it[1])
                if inst:
                    raise ValueError(
                        u"Выход вызова FB '%s' (%s) разветвляется на несколько входов. "
                        u"Экземпляр FB дублировать нельзя - проведите сигнал через "
                        u"локальную переменную POU." % (it[2], inst))
                ins = [(pin, alloc(s)) for pin, s in it[3]]
                cand = (u"block", self._nid(), it[2], ins, it[4], it[5], it[6] + 10)
            else:
                raise ValueError(u"outVariable нельзя использовать как источник сигнала")
            by_id[cand[1]] = cand
            pending.append(cand)
            return cand

        def alloc(s):
            s = _src(s)
            k = taken.get(s.eid, 0)
            taken[s.eid] = k + 1
            it = by_id.get(s.eid)
            if it is None or k == 0:
                return Src(s.eid, s.pin)
            new = clone(it)
            return Src(new[1], s.pin)

        final = []
        for it in items:
            if it[0] == u"invar":
                final.append(it)
                continue
            if it[0] == u"outvar":
                built = (u"outvar", it[1], it[2], alloc(it[3]), it[4], it[5])
            else:
                built = (u"block", it[1], it[2],
                         [(pin, alloc(s)) for pin, s in it[3]], it[4], it[5], it[6])
            if pending:
                final.extend(pending)
                pending = []
            final.append(built)
        if pending:
            final.extend(pending)
        self._items = final

    def used_ids(self):
        u"""localId всех источников сигналов в этой сети (для чистки по POU)."""
        used = set()
        for it in self._items:
            if it[0] == u"outvar":
                s = _src(it[3])
                if s is not None:
                    used.add(s.eid)
            elif it[0] == u"block":
                for _pin, s in it[3]:
                    ss = _src(s)
                    if ss is not None:
                        used.add(ss.eid)
        return used

    def prune_unused_inputs(self, used):
        u"""Убрать входные переменные, на которые никто не ссылается.

        P O Ch E M U  E T O  N U Zh N O. Неиспользуемый <inVariable> CODESYS
        превращает в оператор без действия и выдаёт предупреждение
            C139: Код 'Con_Lin;' не имеет действия. Это сделано намеренно?
        без имени POU и номера сети. Именно так в проекте появлялись
        предупреждения про `Con_Lin`, `Halted` и `0` — это были висячие
        входные переменные, созданные генератором и не подключённые.

        В A Zh N O: used приходит С В Е Р Х У и учитывает ссылки из ВСЕХ сетей
        POU. Если считать только по своей сети, можно удалить вход, нужный
        соседней сети, и CODESYS ответит
            C9: Обнаружен недопустимый символ '?'
        (проверено — именно так и случилось с localId 418 и 420 в PLC_PRG).
        """
        import os as _os
        drop = [it for it in self._items
                if it[0] == u"invar" and it[1] not in used]
        if drop and _os.environ.get(u"Z80_PRUNE_DEBUG"):
            import sys as _sys
            _sys.stderr.write(u"PRUNE net=%s ids=%s\n" % (
                self.title, u",".join([u"%s" % d[1] for d in drop])))
        self._items = [it for it in self._items
                       if not (it[0] == u"invar" and it[1] not in used)]

    def render(self, prepared=False):
        if not prepared:
            self._expand_fanout()
            self.prune_unused_inputs(self.used_ids())
        out = []
        if self.title:
            out.append(u'            <!-- %s -->' % esc(self.title))
        for it in self._items:
            kind = it[0]
            if kind == u"invar":
                _, i, expr, x, y = it
                w = 20 + 9 * len(_u(expr))
                out.append(u'            <inVariable localId="%d" height="10" width="%d">' % (i, w))
                out.append(u'              <position x="%d" y="%d" />' % (x, y))
                out.append(u'              <connectionPointOut><relPosition x="%d" y="5" /></connectionPointOut>' % w)
                out.append(u'              <expression>%s</expression>' % esc(expr))
                out.append(u'            </inVariable>')
            elif kind == u"outvar":
                _, i, expr, src, x, y = it
                w = 20 + 9 * len(_u(expr))
                out.append(u'            <outVariable localId="%d" height="10" width="%d">' % (i, w))
                out.append(u'              <position x="%d" y="%d" />' % (x, y))
                out.append(u'              <connectionPointIn>')
                out.append(u'                <relPosition x="0" y="5" />')
                out.append(_conn(src, indent=u'                '))
                out.append(u'              </connectionPointIn>')
                out.append(u'              <expression>%s</expression>' % esc(expr))
                out.append(u'            </outVariable>')
            else:
                _, i, tname, inputs, outputs, x, y = it
                w = 40 + 12 * max(len(inputs), len(outputs))
                inst = self._inst.get(i)
                inst_attr = u' instanceName="%s"' % esc(inst) if inst else u''
                out.append(u'            <block localId="%d" typeName="%s"%s height="%d" width="%d">'
                           % (i, esc(tname), inst_attr, 10 + 10 * max(len(inputs), 1), w))
                out.append(u'              <position x="%d" y="%d" />' % (x, y))
                out.append(u'              <inputVariables>')
                for k, (pin, src) in enumerate(inputs):
                    if pin:
                        out.append(u'                <variable formalParameter="%s">' % esc(pin))
                    else:
                        out.append(u'                <variable>')
                    out.append(u'                  <connectionPointIn>')
                    out.append(u'                    <relPosition x="0" y="%d" />' % (5 + 10 * k))
                    out.append(_conn(src, indent=u'                    '))
                    out.append(u'                  </connectionPointIn>')
                    out.append(u'                </variable>')
                out.append(u'              </inputVariables>')
                out.append(u'              <inOutVariables />')
                out.append(u'              <outputVariables>')
                for k, pin in enumerate(outputs):
                    out.append(u'                <variable formalParameter="%s">' % esc(pin))
                    out.append(u'                  <connectionPointOut>')
                    out.append(u'                    <relPosition x="%d" y="%d" />' % (w, 5 + 10 * k))
                    out.append(u'                  </connectionPointOut>')
                    out.append(u'                </variable>')
                out.append(u'              </outputVariables>')
                out.append(u'            </block>')
        return u"\n".join(out)


def _src(src):
    if isinstance(src, Src):
        return src
    return Src(int(src))


def _conn(src, indent=u'                  '):
    src = _src(src)
    if src.pin:
        return (u'%s<connection refLocalId="%d" formalParameter="%s" />'
                % (indent, src.eid, esc(src.pin)))
    return u'%s<connection refLocalId="%d" />' % (indent, src.eid)


def strip_comments(text):
    u"""Убрать комментарии IEC: (* ... *) (в том числе многострочные) и // ..."""
    text = re.sub(u"\\(\\*.*?\\*\\)", u" ", text, flags=re.S)
    out = []
    for line in text.split(u"\n"):
        k = line.find(u"//")
        out.append(line if k < 0 else line[:k])
    return u"\n".join(out)


# Заголовки секций объявлений -> ключ словаря секций.
# ВАЖНО: словарь именно словарём, а не if/elif — иначе "VAR CONSTANT"
# перехватывался бы проверкой префикса "VAR " и уезжал в локальные.
VAR_SECTIONS = {
    u"VAR_INPUT": u"in",
    u"VAR_OUTPUT": u"out",
    u"VAR_IN_OUT": u"inout",
    u"VAR_EXTERNAL": u"ext",
    u"VAR_GLOBAL": u"ext",
    u"VAR_TEMP": u"local",
    u"VAR_STAT": u"local",
    u"VAR_INST": u"local",
    u"VAR_CONFIG": u"config",
    u"VAR": u"local",
}


def var_section_of(line):
    u"""Определить секцию по строке-заголовку. None, если это не заголовок.

    Разбираем первое слово, поэтому "VAR CONSTANT", "VAR RETAIN",
    "VAR_INPUT CONSTANT", "VAR_GLOBAL PERSISTENT" распознаются правильно.
    """
    word = line.split(u" ")[0].split(u"\t")[0]
    return VAR_SECTIONS.get(word)


def parse_declaration_text(text):
    u"""Разобрать текст объявления POU в словарь секций {in/out/inout/ext/local: [Var]}.

    ПОЧЕМУ ТАК. Первая версия этого разбора шла построчно и искала ":" в строке.
    Из-за этого комментарии вида "(* Podderzhany: ... *)" превращались в
    переменные с именем "(* Podderzhany" и типом "*)", а такие стандартные
    секции, как VAR CONSTANT, вообще не распознавались. Структурный <interface>
    строится ИЗ ЭТОГО ЖЕ РАЗБОРА, поэтому ошибка разбора означала, что
    объявление и схема расходятся -- ровно то, на что указал пользователь.

    Теперь: сначала снимаем комментарии, затем режем по ";", а не по строкам,
    -- так корректно обрабатываются многострочные объявления и массивы.
    """
    res = {}
    section = None
    for chunk in strip_comments(text).split(u";"):
        for line in chunk.split(u"\n"):
            s = line.strip()
            if not s:
                continue
            if s.startswith(u"END_VAR"):
                section = None
                continue
            key = var_section_of(s)
            if key is not None:
                section = res.setdefault(key, [])
                # IMEJNO continue, a NE break! Zagolovok sektsii i pervaya
                # peremennaya chasto popadayut v ODIN kusok posle deleniya po
                # ";" ("VAR_INPUT\n A : BYTE"), i break teryal imenno pervuyu
                # peremennuyu kazhdoj sektsii.
                continue
            if section is None or u":" not in s:
                continue
            left, right = s.split(u":", 1)
            if right.lstrip().startswith(u"="):
                right = right.lstrip()[1:]
            if u":=" in right:
                right = right.split(u":=")[0]
            typ = right.strip().rstrip(u";").strip()
            if not typ:
                continue
            for nm in left.split(u","):
                nm = nm.strip()
                # ODNOBUKVENNYE imena (A, B, Y, Q, i) -- zakonnye!
                # Pervaya versiya regulyarki trebovala >=2 simvolov i molcha
                # vybrasyvala imenno ih: strukturnyj <interface> i tekst
                # rashodilis, hotya v fajle vse bylo verno.
                if nm and re.match(u"^[A-Za-z_][A-Za-z0-9_]*$", nm):
                    section.append(Var(nm, typ))
    return res


class Pou(object):
    u"""POU с телом FBD: структурный <interface> + текстовый дубль объявления.

    name        — имя (IEC-идентификатор)
    pou_type    — 'functionBlock' | 'function' | 'program'
    doc         — текст в шапке объявления (комментарий (* ... *))
    """

    def __init__(self, name, pou_type=u"functionBlock", doc=u"", ret_type=u""):
        self.name = name
        self.pou_type = pou_type
        self.doc = doc
        #  T I P  V O Z V R A T A  dlya FUNCTION. V ST on stoit v zagolovke:
        #  "FUNCTION FB_ADDER8 : WORD". Dlya FB i PROGRAM -- pustaya stroka.
        self.ret_type = ret_type
        self.inputs = []
        self.outputs = []
        self.inouts = []
        self.externals = []
        self.locals = []
        self.networks = []
        self._next = 0

    # ---------- объявления ----------
    def var_in(self, name, type_text, comment=None):
        self.inputs.append(Var(name, type_text, comment))
        return name

    def var_out(self, name, type_text, comment=None):
        self.outputs.append(Var(name, type_text, comment))
        return name

    def var_inout(self, name, type_text, comment=None):
        self.inouts.append(Var(name, type_text, comment))
        return name

    def var_external(self, name, type_text, comment=None):
        u"""VAR_EXTERNAL -- берётся из GVL, но объявляется явно в POU."""
        self.externals.append(Var(name, type_text, comment))
        return name

    def var(self, name, type_text, comment=None, address=None):
        u"""Локальная переменная POU.

        address -- необязательная привязка вида "%IX0.0": в объявлении
        получится "имя AT %IX0.0 : ТИП;". Подробности -- в классе Var.
        """
        self.locals.append(Var(name, type_text, comment, address))
        return name

    # ---------- схема ----------
    def _nid(self):
        self._next += 1
        return self._next

    def network(self, title=u""):
        n = Network(len(self.networks) + 1, title, owner=self)
        self.networks.append(n)
        return n

    # ---------- отрисовка ----------
    def parse_interface_from_text(self, text):
        u"""Заполнить inputs/outputs/inouts/externals/locals из текста объявления.

        Нужно потому, что <interface> НЕ МОЖЕТ быть пустым: без структурного
        описания переменных CODESYS молча пропускает объект при импорте
        (оплачено отладочным циклом, см. docs/03_ЖУРНАЛ_СБОРКИ.md).
        Сам разбор -- в parse_declaration_text(), см. её докстроку.
        """
        sec = parse_declaration_text(text)
        self.inputs = sec.get(u"in", [])
        self.outputs = sec.get(u"out", [])
        self.inouts = sec.get(u"inout", [])
        self.externals = sec.get(u"ext", [])
        self.locals = sec.get(u"local", [])

    def var_stats(self):
        u"""Сколько переменных в каждой секции -- для протокола сборки."""
        return ((u"VAR_INPUT", len(self.inputs)), (u"VAR_OUTPUT", len(self.outputs)),
                (u"VAR_IN_OUT", len(self.inouts)), (u"VAR_EXTERNAL", len(self.externals)),
                (u"VAR", len(self.locals)))

    def declaration(self, with_header=True):
        u"""Текстовое объявление (то же, что уходит в InterfaceAsPlainText).

        Z A G O L O V O K  O B Ya Z A T E L E N. Eksperiment pokazal: atribut
        pouType="program" sam po sebe vid POU NE ZADAYOT. Esli zagolovka net,
        CODESYS schitaet obekt funktsionalnym blokom, i sborka padaet s
            C46: Identifikator 'PRG_InitMemory' ne zadan
            C35: Vmesto 'PRG_InitMemory' trebuetsya imya programmy, funkciya
                 ili ekzemplyar funktsionalnogo bloka
        Proverено chteniem textual_declaration u sobrannogo proekta: u POU
        bez zagolovka pervaya stroka -- kommentar, u FUNCTION_BLOCK --
        "FUNCTION_BLOCK FB_Memory64K", i tolko on i rabotal kak nado.
        """
        head = {u"functionBlock": u"FUNCTION_BLOCK",
                u"function": u"FUNCTION",
                u"program": u"PROGRAM"}[self.pou_type]
        first = u"%s %s" % (head, self.name)
        if self.pou_type == u"function" and self.ret_type:
            first = u"%s : %s" % (first, self.ret_type)
        parts = [first] if with_header else []
        if self.doc:
            parts.append(u"(* %s *)" % self.doc)
        for title, vars_ in ((u"VAR_INPUT", self.inputs),
                             (u"VAR_OUTPUT", self.outputs),
                             (u"VAR_IN_OUT", self.inouts),
                             (u"VAR_EXTERNAL", self.externals),
                             (u"VAR", self.locals)):
            if not vars_:
                continue
            parts.append(title)
            for v in vars_:
                parts.append(v.plain())
            parts.append(u"END_VAR")
        parts.append(u"")
        return u"\n".join(parts)

    def interface_xml(self):
        if not (self.inputs or self.outputs or self.inouts or self.externals or self.locals):
            raise ValueError(u"POU %s: пустой <interface> — CODESYS молча пропустит объект" % self.name)
        out = [u'        <interface>']
        for tag, vars_ in ((u"inputVars", self.inputs),
                           (u"outputVars", self.outputs),
                           (u"inOutVars", self.inouts),
                           (u"externalVars", self.externals),
                           (u"localVars", self.locals)):
            if not vars_:
                continue
            out.append(u'          <%s>' % tag)
            for v in vars_:
                out.append(v.xml())
            out.append(u'          </%s>' % tag)
        out.append(u'        </interface>')
        return u"\n".join(out)

    def render(self):
        #  R A Z V E R T Y V A N I E  I  Ch I S T K A  --  N A  У R O V N E  P O U.
        #  localId в PLCopenXML считaются В ПРЕДЕЛАХ ВСЕГО POU, а не сети:
        #  генератор местами создаёт вход в одной сети, а ссылается на него
        #  из другой. Поэтому и разворачивать ветви, и выкидывать висячие
        #  входы нужно по всему POU сразу — иначе чистка удалит вход, который
        #  нужен соседней сети, и получится «Вместо '?' требуется выражение».
        for n in self.networks:
            n._expand_fanout()
        used = set()
        for n in self.networks:
            used |= n.used_ids()
        for n in self.networks:
            n.prune_unused_inputs(used)
        body = u"\n".join([n.render(prepared=True) for n in self.networks])
        return u"""      <pou name="%(name)s" pouType="%(type)s">
%(iface)s
        <body>
          <FBD>
%(body)s
          </FBD>
        </body>
        <addData>
          <data name="%(ns)s" handleUnknown="implementation">
            <InterfaceAsPlainText>
              <xhtml xmlns="%(xhtml)s">%(decl)s</xhtml>
            </InterfaceAsPlainText>
          </data>
        </addData>
      </pou>""" % {
            u"name": esc(self.name),
            u"type": esc(self.pou_type),
            u"iface": self.interface_xml(),
            u"body": body,
            u"ns": NS_PLAINTEXT,
            u"xhtml": XHTML,
            u"decl": esc(self.declaration()).replace(u"\n", u"&#xA;"),
        }


class Gvl(object):
    u"""Global Variable List, сохраняемая как ТЕКСТОВЫЙ файл (.gvl).

    ПОЧЕМУ НЕ XML. Оба очевидных варианта отвергнуты экспериментом:
      * pouType="globalVarList" -> «значение недействительно (Сбой ограничения
        Enumeration)»: такого члена нет в схеме tc6_0200;
      * без pouType вовсе -> «Отсутствует обязательный атрибут pouType».
    Поэтому GVL создаются штатным API (app.create_gvl) в build.py, а этот
    класс лишь пишет файл объявления, который build.py читает.
    """

    def __init__(self, name, decl_text):
        self.name = name
        self.decl_text = decl_text

    def render(self):
        return self.decl_text


class TextPou(Pou):
    u"""POU с ТЕКСТОВЫМ телом (ST) в PLCopenXML.

    Нужен для программ инициализации: по заданию ST разрешён ровно для
    инициализации массива памяти и генерации тестовых данных, поэтому такие
    POU идут отдельным, явно помеченным классом, а не смешиваются со схемами.
    """

    def __init__(self, name, st_text, pou_type=u"program", doc=u"",
                 body_text=None):
        u"""st_text -- ПОЛНЫЙ текст POU (с заголовком и VAR); он идёт в интерфейс.
        body_text -- ТОЛЬКО операторы; он идёт в поле реализации.

        Если body_text не задан, он вычисляется отрезанием всего до END_VAR.
        Иначе получалась бы грубая ошибка: одни и те же объявления попадали и
        в интерфейс, и в тело, и CODESYS разрезал текст по END_VAR --
        заголовок с VAR уезжал в редактор объявлений, а в реализации
        оставались оборванные комментарии.
        """
        Pou.__init__(self, name, pou_type, doc)
        self.st_text = st_text
        self.parse_interface_from_text(st_text)
        if body_text is None:
            body_text = self._cut_declaration(st_text)
        self.body_text = body_text

    @staticmethod
    def _cut_declaration(text):
        u"""Отрезать заголовок POU и все блоки VAR: оставить только операторы."""
        lines = text.split(u"\n")
        last_end = -1
        for i, raw in enumerate(lines):
            if raw.strip().startswith(u"END_VAR"):
                last_end = i
        if last_end >= 0:
            return u"\n".join(lines[last_end + 1:]).lstrip(u"\n")
        # net VAR -- uberaem tolko stroku s zagolovkom
        out = []
        for raw in lines:
            s = raw.strip()
            if re.match(u"^(PROGRAM|FUNCTION_BLOCK|FUNCTION)\\s+\\w+", s):
                continue
            out.append(raw)
        return u"\n".join(out).lstrip(u"\n")

    @staticmethod
    def _header_only(text):
        u"""Ostavit tolko obyavlenie: bloki VAR...END_VAR, BEZ tela i BEZ zagolovka.

        P O Ch E M U  B E Z  T E L A. V <InterfaceAsPlainText> dolzhno lezhat
        TOLKO obyavlenie. Kogda tuda popadal ves tekst POU vmeste s telom,
        CODESYS chital telo kak obyavlenie i sypal oshibkami:
            C0135: Takoj kod nedopustim v razdele obyavleniya
            C0006: ', AT ili :' trebuetsya vmesto '.'
        (pervaya zhe stroka tela -- primer s tochkoy, naprimer
        GVL_Tests_CPM.Tests[i].Id := i;).

        P O Ch E M U  B E Z  Z A G O L O V K A. Stroka "PROGRAM <imya>" /
        "FUNCTION_BLOCK <imya>" zastavlyaet CODESYS schitat vid POU po etomu
        tekstu i pereopredelit ego. Programmy prevrashchalis v funktsionalnye
        bloki, i sborka padala s
            C0034: Programma 'PRG_InitMemory' trebuetsya dlya programmy,
                   funkciya dlya vozvratnogo znacheniya funk. bloka
            C0035: Identifikator 'PRG_InitMemory' ne naiden
        Vid POU zadayot atribut pouType u elementa <pou>, i etogo dostatochno.
        """
        lines = text.split(u"\n")
        last_end = -1
        for i, raw in enumerate(lines):
            if raw.strip().startswith(u"END_VAR"):
                last_end = i
        if last_end >= 0:
            lines = lines[:last_end + 1]
        out = []
        for raw in lines:
            if re.match(u"^(PROGRAM|FUNCTION_BLOCK|FUNCTION)\\s+\\w+", raw.strip()):
                continue
            out.append(raw)
        return u"\n".join(out).strip(u"\n")

    def declaration(self):
        u"""Tekstovoe obyavlenie: zagolovok POU + bloki VAR...END_VAR, bez tela.

        Dva trebovaniya, i oba oplacheny otladkoj:

        1) BEZ tela. Inache CODESYS schitaet stroki tela obyavleniyami
           i vydayot C0135/C0006.

        2) S ZAGOLOVKOM "PROGRAM <imya>" / "FUNCTION_BLOCK <imya>".
           Imenno zagolovok (a ne atribut pouType) zadayot vid POU:
           bez nego programmy stanovilis funktsionalnymi blokami, i sborka
           padala s C46/C35 "trebuetsya imya programmy".
        """
        head = {u"functionBlock": u"FUNCTION_BLOCK",
                u"function": u"FUNCTION",
                u"program": u"PROGRAM"}[self.pou_type]
        first = u"%s %s" % (head, self.name)
        if self.pou_type == u"function" and self.ret_type:
            first = u"%s : %s" % (first, self.ret_type)
        decl = self._header_only(self.st_text)
        return (first + u"\n" + decl) if decl else first

    def render(self):
        decl = self.declaration()
        body = esc(self.body_text).replace(u"\n", u"&#xA;")
        #  P O Ch E M U  esc()  I  Z D E S. V <body> perevody strok uzhe
        #  zameneny na &#xA;, a v InterfaceAsPlainText ostavalis "zhivymi".
        #  CODESYS chitaet oba polya odnim i tem zhe razborshchikom ST i
        #  v etom pole literal "&#xA;" ponimaet kak T E K S T -- simvoly
        #  &, #, x, A. Otsyuda vot etot buket, kotoryj nikak ne svyazyvalsya
        #  s soderzhimym POU:
        #      C9:   Obnaruzhen nedopustimyj simvol '&'
        #      C189: ';' trebuetsya vmesto '&'      (i tak zhe dlya #, x, A)
        #  Imenno poetomu u FBD-shem, gde ekranirovanie bylo, oshibok ne bylo,
        #  a u kazhdoj ST-programmy -- po desyatke.
        decl_x = esc(decl).replace(u"\n", u"&#xA;")
        return u"""      <pou name="%(name)s" pouType="%(type)s">
%(iface)s
        <body>
          <ST>
            <xhtml xmlns="%(xhtml)s">%(body)s</xhtml>
          </ST>
        </body>
        <addData>
          <data name="%(ns)s" handleUnknown="implementation">
            <InterfaceAsPlainText>
              <xhtml xmlns="%(xhtml)s">%(decl)s</xhtml>
            </InterfaceAsPlainText>
          </data>
        </addData>
      </pou>""" % {
            u"name": esc(self.name),
            u"type": esc(self.pou_type),
            u"iface": self.interface_xml(),
            u"body": body,
            u"ns": NS_PLAINTEXT,
            u"xhtml": XHTML,
            u"decl": decl_x,
        }


class TextFb(TextPou):
    u"""FUNCTION_BLOCK с ТЕКСТОВЫМ телом (ST).

    Единственное применение -- FB_Memory64K: в FBD нет оператора индексации
    массива, а псевдоэлементы MEM_READ/MEM_WRITE, которыми я пробовал его
    заменить, роняют компилятор CODESYS (проверено экспериментом). Поэтому
    доступ к массиву Z80_Mem написан на ST, а вся остальная логика -- в FBD.
    """

    def __init__(self, name, decl_text, st_text, doc=u""):
        TextPou.__init__(self, name, st_text, u"functionBlock", doc)
        self._decl = decl_text
        # interfejs stroim iz OTDEL'NOGO teksta obyavleniya:
        # u FB_Memory64K st_text -- eto tol'ko telo, bez VAR.
        self.inputs = []
        self.outputs = []
        self.inouts = []
        self.externals = []
        self.locals = []
        self.parse_interface_from_text(decl_text)

    def declaration(self):
        return self._decl


HEADER = u"""<?xml version="1.0" encoding="utf-8"?>
<project xmlns="http://www.plcopen.org/xml/tc6_0200">
  <fileHeader companyName="" productName="CODESYS" productVersion="CODESYS V3.5 SP17 Patch 3" creationDateTime="2026-01-01T00:00:00" />  <contentHeader name="%(content)s">
    <coordinateInfo>
      <fbd><scaling x="1" y="1" /></fbd>
      <ld><scaling x="1" y="1" /></ld>
      <sfc><scaling x="1" y="1" /></sfc>
    </coordinateInfo>
  </contentHeader>
  <types>
    <dataTypes />
    <pous>
"""

FOOTER = u"""    </pous>
  </types>
  <instances>
    <configurations />
  </instances>
</project>
"""


def write_project(path, pous, content_name=u"EMU8080"):
    u"""Записать PLCopenXML со списком POU (тело FBD). Возвращает длину текста."""
    parts = [HEADER % {u"content": esc(content_name)}]
    for p in pous:
        parts.append(p.render())
        parts.append(u"\n")
    parts.append(FOOTER)
    text = u"".join(parts)
    f = io.open(path, "w", encoding="utf-8")
    f.write(text)
    f.close()
    return len(text)


def count_elements(path):
    u"""Статистика XML: (блоков, входных перем., выходных перем., связей, пустых входов)."""
    t = io.open(path, "r", encoding="utf-8").read()
    return (t.count(u"<block "), t.count(u"<inVariable "), t.count(u"<outVariable "),
            t.count(u"<connection "), t.count(u"<connectionPointIn />"))
