# -*- coding: utf-8 -*-
u"""patch_textpou_iface.py -- TextPou dolzhen sam razbirat svoj interfejs.

PROBLEMA (najdena po skrinshotu polzovatelya):
    U 6 POU (TEST_Z80, TEST_Z80_CPM, PRG_InitMemory, PRG_LoadTestProgram,
    PRG_CPM_Boot, PRG_CPM_BDOS) obyavleniya popadali v POLE REALIZACII,
    a v strukturnyy <interface> -- lish chastichno ili voobshche nichego.

    Prichiny bylo dve:
      1. TextPou otpravlyal ODIN i tot zhe tekst i v interfeys, i v telo;
         CODESYS razrezal ego po END_VAR -- zagolovok s VAR uezhal v
         redaktor obyavleniy, a v realizacii ostalis oborvannye kommentarii.
         (uzhe ispravleno v fbd_xml.py: dobavlen body_text)
      2. Razbor interfejsa (_parse_interface) byl tolko u klassa TextFb.
         U obychnyh TextPou spiski inputs/outputs/locals ostavalis pustymi.

Reshenie: perenesti razbor interfejsa v bazovyy klass Pou i vyzyvat ego
dlya lyubogo POU, u kotorogo obyavlenie zadano tekstom.
"""

import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
LIB = os.path.join(ROOT, "generator", "tools", "fbd_xml.py")

t = io.open(LIB, "r", encoding="utf-8").read()

# --- 1. perenesti _parse_interface v klass Pou ---------------------------------
# vyrezaem ego iz TextFb
old_fb = u'''    def _parse_interface(self):
        u"""Разобрать текст объявления и заполнить inputs/outputs/locals.

        Нужно потому, что <interface> не может быть пустым: без структурного
        описания переменных CODESYS молча пропускает объект.
        """
        section = None
        for raw in self._decl.split(u"\\n"):
            line = raw.strip()
            if line.startswith(u"VAR_INPUT"):
                section = self.inputs
                continue
            if line.startswith(u"VAR_OUTPUT"):
                section = self.outputs
                continue
            if line == u"VAR":
                section = self.locals
                continue
            if line.startswith(u"END_VAR"):
                section = None
                continue
            if section is None or not line or line.startswith(u"(*"):
                continue
            if u":" not in line:
                continue
            name, typ = line.split(u":", 1)
            name = name.strip().rstrip(u";").strip()
            typ = typ.split(u";")[0].split(u"(*")[0].strip()
            if name and typ:
                section.append(Var(name, typ))

'''
assert old_fb in t, u"ne najden _parse_interface v TextFb"
t = t.replace(old_fb, u"", 1)

# --- 2. dobavit ego v klass Pou ------------------------------------------------
anchor = u'''    def declaration(self):
        u"""Текстовое объявление (то же, что уходит в InterfaceAsPlainText)."""'''
assert anchor in t, u"ne najden declaration v Pou"
PARSE = u'''    def parse_interface_from_text(self, text):
        u"""Разобрать текст объявления и заполнить inputs/outputs/locals.

        Нужно потому, что <interface> не может быть пустым: без структурного
        описания переменных CODESYS молча пропускает объект при импорте.
        Поддерживаются VAR_INPUT / VAR_OUTPUT / VAR, комментарии (* ... *)
        и инициализация через ":=".
        """
        section = None
        for raw in text.split(u"\\n"):
            line = raw.strip()
            if line.startswith(u"VAR_INPUT"):
                section = self.inputs
                continue
            if line.startswith(u"VAR_OUTPUT"):
                section = self.outputs
                continue
            if line.startswith(u"VAR_EXTERNAL"):
                section = None
                continue
            if line.startswith(u"VAR_IN_OUT"):
                section = self.inputs
                continue
            if line == u"VAR" or line.startswith(u"VAR "):
                section = self.locals
                continue
            if line.startswith(u"END_VAR"):
                section = None
                continue
            if section is None or not line:
                continue
            if line.startswith(u"(*") and line.endswith(u"*)"):
                continue
            if u":" not in line:
                continue
            name, typ = line.split(u":", 1)
            name = name.strip().rstrip(u";").strip()
            typ = typ.split(u";")[0].split(u"(*")[0].strip()
            # ubrat inicializaciyu: BOOL := TRUE -> BOOL
            if u":=" in typ:
                typ = typ.split(u":=")[0].strip()
            # ubrat vlozhennye kommentarii v konce
            if typ.endswith(u"*)"):
                typ = typ[:typ.rfind(u"(*")].strip() if u"(*" in typ else typ
            if name and typ:
                section.append(Var(name, typ))

'''
t = t.replace(anchor, PARSE + anchor, 1)

# --- 3. vyzvat razbor vo vseh tekstovyh klassah --------------------------------
old_tp = u'''        Pou.__init__(self, name, pou_type, doc)
        self.st_text = st_text
        if body_text is None:
            body_text = self._cut_declaration(st_text)
        self.body_text = body_text'''
new_tp = u'''        Pou.__init__(self, name, pou_type, doc)
        self.st_text = st_text
        self.parse_interface_from_text(st_text)
        if body_text is None:
            body_text = self._cut_declaration(st_text)
        self.body_text = body_text'''
assert old_tp in t, u"ne najden __init__ TextPou"
t = t.replace(old_tp, new_tp, 1)

old_fb2 = u'''        TextPou.__init__(self, name, st_text, u"functionBlock", doc)
        self._decl = decl_text
        self._parse_interface()'''
new_fb2 = u'''        TextPou.__init__(self, name, st_text, u"functionBlock", doc)
        self._decl = decl_text
        # interfejs stroim iz otdel'nogo teksta obyavleniya
        self.inputs = []
        self.outputs = []
        self.locals = []
        self.parse_interface_from_text(decl_text)'''
assert old_fb2 in t, u"ne najden __init__ TextFb"
t = t.replace(old_fb2, new_fb2, 1)

io.open(LIB, "w", encoding="utf-8").write(t)
print(u"PATCH TEXTPOU_IFACE OK")
