# -*- coding: utf-8 -*-
"""Otkryvaem sobrannyy proekt i pokazyvaem, CHTO v nem est grafika."""
import io, os, re, traceback
import scriptengine

HERE = r"C:\Users\Ольга\OneDrive\Рабочий стол\CODESYS\Z80_EMU"
BUILD = os.path.join(HERE, "build")
LOG = os.path.join(HERE, "log", "probe_show_graphics.log")
PROJ = os.path.join(BUILD, "Z80_EMU.project")

def log(m):
    f = io.open(LOG, "a", encoding="utf-8"); f.write(u"%s\n" % (m,)); f.close()

f = io.open(LOG, "w", encoding="utf-8"); f.write(u""); f.close()
log(u"=== PROVERKA GRAFIKI V PROEKTE ===")

for p in list(scriptengine.projects.all):
    try: p.close()
    except Exception: pass

proj = scriptengine.projects.open(PROJ)
app = proj.active_application
log(u"proekt otkryt")

def walk(o, ind=0, depth=4, acc=None):
    if acc is None: acc = []
    try: acc.append((o.get_name(), o))
    except Exception: pass
    if ind >= depth: return acc
    try: kids = o.get_children()
    except Exception: kids = []
    for k in kids: walk(k, ind+1, depth, acc)
    return acc

objs = walk(app, 0, 4, [])
log(u"obektov v Application: %d" % len(objs))
for n, _ in objs:
    log(u"   %s" % n)

# Vygruzhaem neskolko POU i schitaem GRAPHICheskie elementy
CHECK = [u"PLC_PRG", u"FB_ALU_Z80", u"FB_RegFileZ80", u"FB_IO_Ports",
         u"FB_CPM_BDOS", u"FB_DecoderZ80"]
out = os.path.join(BUILD, "check_graphics.xml")
sel = [o for n, o in objs if n in CHECK]
try:
    proj.export_xml(sel, path=out, declarations_as_plaintext=True)
    scriptengine.system.delay(1500)
    import shutil
    cp = out + ".copy"
    shutil.copyfile(out, cp)
    t = io.open(cp, "r", encoding="utf-8").read()
    log(u"")
    log(u"=== GRAFIKA V VYGRUZENNYH POU ===")
    for m in re.finditer(r'<pou name="([^"]+)"', t):
        name = m.group(1)
        j = t.find("</pou>", m.start())
        seg = t[m.start():j]
        blocks = len(re.findall(r"<block ", seg))
        invars = len(re.findall(r"<inVariable ", seg))
        outvars = len(re.findall(r"<outVariable ", seg))
        conns = len(re.findall(r"<connection ", seg))
        positions = len(re.findall(r"<position ", seg))
        log(u"  %-16s blokov=%-4d vhodov=%-4d vyhodov=%-3d provodov=%-4d poziciy=%d"
            % (name, blocks, invars, outvars, conns, positions))
except Exception:
    log(u"export FAIL:\n%s" % traceback.format_exc())

try: proj.close()
except Exception: pass
log(u"=== KONEC ===")
