# -*- coding: utf-8 -*-
u"""Dopisat v docs/04_СХЕМЫ.md razdel pro yavnuyu tipizaciyu vetok SEL.

Z A Ch E M. Shemy izmenilis: ucepochki vybora teper tipiziruyut literaly
yavno, a BOOL_TO_BYTE ne ispolzuetsya. Dokumentaciya shem dolzhna eto
otrazhat, inache chitayushchij ne pojmet, pochemu v shemah stoit "BYTE#0".

ZAPUSK: python generator\tools\append_schemes_sel.py
"""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DOCS = os.path.join(ROOT, u"docs")
DOC = None
for f in os.listdir(DOCS):
    if f.startswith(u"04_"):
        DOC = os.path.join(DOCS, f)
        break

TEXT = u"""
## Правило типизации цепочек выбора (SEL)

Цепочка `SEL` — основной способ сделать выбор «одно из многих» в FBD:
каждый блок берёт очередное значение, если сработало его условие, иначе
пропускает дальше предыдущий результат. Так собраны выборка регистра чтения,
чтение I/O-порта и начальные значения регистров.

**Правило: каждая ветвь такой цепочки должна иметь тип, известный
компилятору заранее.**

Почему это важно. `SEL` — обобщённый блок (IEC `ANY`): его тип CODESYS
выводит по ветвям `IN0`/`IN1`. Если одна ветвь — переменная типа `BYTE`,
а другая — «голый» литерал `0` или `16#00`, компилятор **сам выбирает тип
литерала**. В цепочке из десятка блоков он выбирает `USINT` для всех,
и дальше сборка падает сообщениями без имени POU и номера сети:

```
C32: Невозможно конвертировать тип 'BOOL'  в тип 'USINT'
C32: Невозможно конвертировать тип 'USINT' в тип 'BOOL'
C32: Невозможно конвертировать тип 'BOOL'  в тип 'BYTE'
C32: Невозможно конвертировать тип 'WORD'  в тип 'BYTE'
```

Поэтому в схемах:

| В ветви `SEL` | Как записано |
|---|---|
| константа-байт | `BYTE#0`, `BYTE#16#00`, `BYTE#16#FF` |
| константа-слово | `WORD#16#FA23` и т. п. |
| строб «есть/нет» | `SEL(G, BYTE#0, BYTE#1)` — см. ниже |
| переменная POU | как есть: тип задан объявлением |
| выход конверсии | как есть: тип задан самой конверсией |

Две вещи, которых в схемах **сознательно нет**:

1. **`BOOL_TO_BYTE`.** В CODESYS эта конверсия даёт `USINT`, а не `BYTE`
   (для `BYTE` — битовой строки — обобщённые блоки выводят `USINT`).
   Такой выход, попав в цепочку `BYTE`, ломает её тип. Поэтому строб
   «есть символ / нет символа» собирается блоком `SEL` с двумя явными
   литералами `BYTE#0` и `BYTE#1` — тип результата однозначен.
2. **`BYTE_TO_BYTE`.** В CODESYS такой функции не существует; попытка
   «привести ветвь к тому же типу» ею даёт 76 ошибок
   `C46: Идентификатор 'BYTE_TO_BYTE' не задан`. Приводить ветви не нужно —
   достаточно явно записать литерал.

Проверка автоматическая: `tools/find_sel_types.py` рекурсивно выводит типы
ветвей каждого `SEL` во всех схемах и сообщает, где они разные. Тест плана
**T8** держит это закрытым.

Пример из `FB_IO_Ports` (чтение порта `10h`, статус консоли):

```
        ┌─────────────┐
Con_Rdy─┤G            │
 BYTE#0─┤IN0   SEL   OUT├──► ветвь цепочки (BYTE)
 BYTE#1─┤IN1          │
        └─────────────┘
```

Обе ветви — `BYTE`, условие — `BOOL`, результат — `BYTE`.
"""


def main():
    try:
        sys.stdout.reconfigure(encoding=u"utf-8", errors=u"replace")
    except Exception:                                          # noqa: BLE001
        pass
    if DOC is None:
        sys.stdout.write(u"NE NAJDEN 04_*.md\n")
        return 1
    t = io.open(DOC, encoding=u"utf-8").read()
    if u"## Правило типизации цепочек выбора" in t:
        sys.stdout.write(u"razdel uzhe est -- propuskayu\n")
        return 0
    t = t.rstrip(u"\n") + u"\n" + TEXT
    io.open(DOC, u"w", encoding=u"utf-8").write(t)
    sys.stdout.write(u"04_СХЕМЫ.md dopolnен: %d strok\n" % (t.count(u"\n") + 1))
    return 0


if __name__ == u"__main__":
    sys.exit(main())
