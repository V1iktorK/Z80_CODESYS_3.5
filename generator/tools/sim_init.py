# -*- coding: utf-8 -*-
u"""SIM INIT -- nablyudaem za pereborom registrov vo vremya initsializatsii."""
import io, os, sys, time
import scriptengine

ROOT = os.environ.get(u"Z80_ROOT")
PROJ = os.path.join(ROOT, u"build", u"Z80_EMU.project")
OUT = os.path.join(ROOT, u"log", u"sim_init.txt")
L = []


def log(m):
    L.append(u"%s" % (m,))


def rd(oapp, e, d=u"-"):
    try:
        return u"%s" % oapp.read_value(e)
    except Exception:
        return d


def wr(oapp, pairs):
    for e, v in pairs:
        try:
            oapp.set_prepared_value(e, u"%s" % v)
        except Exception:
            pass
    try:
        oapp.write_prepared_values()
    except Exception:
        pass


def main():
    proj = scriptengine.projects.open(PROJ)
    app = proj.active_application
    app.build()
    list(proj.find(u"Device"))[0].set_simulation_mode(True)
    oapp = scriptengine.online.create_online_application(app)
    oapp.login(scriptengine.OnlineChangeOption.Try, False)
    oapp.start()
    time.sleep(1.2)

    log(u"=== SIM INIT ===")
    log(u"do podgotovki: A=%s F=%s Init_Sel_Dst=%s Init_Busy=%s"
        % (rd(oapp, u"GVL_PLCVisu.A"), rd(oapp, u"GVL_PLCVisu.F"),
           rd(oapp, u"GVL_InitRegs.Init_Sel_Dst"), rd(oapp, u"GVL_InitRegs.Init_Busy")))

    #  ostavim tolko test 13 i zagruzim ego Init_Vals vruchnuyu
    pairs = [(u"GVL_Tests.Cpu_Tests[%d].Enabled" % i, u"TRUE" if i == 13 else u"FALSE")
             for i in range(1, 41)]
    pairs += [(u"GVL_InitRegs.Init_Vals[0]", u"16#0F"),
              (u"GVL_InitRegs.Init_Vals[1]", u"16#00"),
              (u"GVL_InitRegs.Init_Vals[7]", u"16#01"),
              (u"GVL_InitRegs.Init_En", u"TRUE")]
    wr(oapp, pairs)
    log(u"Init_En := TRUE, Init_Vals[0] := 0Fh")
    for k in range(24):
        time.sleep(0.12)
        log(u"  t=%4.1f  A=%-9s F=%-9s Sel_Dst=%-9s Busy=%-6s En=%-6s cnt=%s"
            % (k * 0.12, rd(oapp, u"GVL_PLCVisu.A"), rd(oapp, u"GVL_PLCVisu.F"),
               rd(oapp, u"GVL_InitRegs.Init_Sel_Dst"),
               rd(oapp, u"GVL_InitRegs.Init_Busy"),
               rd(oapp, u"GVL_InitRegs.Init_En"),
               rd(oapp, u"PLC_PRG.vInitCnt")))
    wr(oapp, [(u"GVL_InitRegs.Init_En", u"FALSE")])
    time.sleep(0.3)
    log(u"posle snyatiya Init_En: A=%s F=%s" % (rd(oapp, u"GVL_PLCVisu.A"),
                                                rd(oapp, u"GVL_PLCVisu.F")))
    try:
        oapp.stop(); oapp.logout()
    except Exception:
        pass
    proj.close()


try:
    main()
except Exception, exc:
    log(u"AVARIYA: %s" % exc)
    import traceback
    log(traceback.format_exc())

f = open(OUT, u"w")
f.write(u"\n".join(L).encode(u"utf-8"))
f.close()
sys.stdout.write(u"sim_init: %d strok\n" % len(L))
