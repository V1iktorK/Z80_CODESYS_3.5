# -*- coding: utf-8 -*-
u"""Z A P U S K  E M U L Ya T O R A  V  S I M U L Ya Ts I I  I  Ch T E N I E  T E S T O V.

Z A Ch E M. Sborka dokazyvaet korrektnost tipov, no ne korrektnost emulyatsii.
Zdes my deystvitelno VYPOLNYAEM proekt i chitaem rezultaty vstroennyh testov:
    GVL_Tests.Cpu_Test_Total_Pass   dolzhno byt 62
    GVL_Tests.Cpu_Test_Fail_Count   dolzhno byt 0
    GVL_Tests_CPM.Cpm_Test_Total_Pass  dolzhno byt 30
    GVL_Tests_CPM.Cpm_Test_Fail_Count  dolzhno byt 0

K A K. ScriptEngine daet polnyj dostup k onlajnu: create_online_application,
login, start, read_value, set_prepared_value. Vklyuchaem rezhim simulyatsii
u ustrojstva, vhodim, zapuskaem, vyderzhivaem neskolko skanov i chitaem.

Rezultat pishetsya v log\sim_out.txt, a takzhe pechataetsya v stdout.

ZAPUSK: run_probe_fb.ps1 -Fbs none -Script tools\run_simulation.py
"""
import io
import os
import sys
import time

import scriptengine

ROOT = os.environ.get(u"Z80_ROOT")
if not ROOT:
    ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILD = os.path.join(ROOT, u"build")
LOG = os.path.join(ROOT, u"log")
PROJ = os.path.join(BUILD, u"Z80_EMU.project")
OUT = os.path.join(LOG, u"sim_out.txt")

LINES = []
FAIL = []


def log(m):
    LINES.append((u"%s" % (m,)))


def step(name):
    log(u"")
    log(u"--- %s ---" % name)


def main():
    log(u"=== ZAPUSK V SIMULYATSII ===")
    if not os.path.exists(PROJ):
        log(u"NET PROEKTA: %s" % PROJ)
        FAIL.append(u"net sobrannogo proekta")
        return

    log(u"proekt: %s" % PROJ)
    proj = scriptengine.projects.open(PROJ)
    app = proj.active_application
    log(u"prilozhenie: %s" % app)

    # 1. perekompilirovat, chtoby proekt byl aktualen
    step(u"1. sborka")
    try:
        app.build()
        log(u"build() -- OK")
    except Exception as exc:                                   # noqa: BLE001
        log(u"build() OSHIBKA: %s" % exc)

    # 2. ustrojstvo, shlyuz i adres
    step(u"2. podklyuchenie")
    dev = None
    try:
        found = list(proj.find(u"Device"))
        log(u"  proj.find('Device'): %d sht" % len(found))
        if found:
            dev = found[0]
            log(u"  ustrojstvo: %s" % ((u"%s" % dev)[:120]))
    except Exception as exc:                                   # noqa: BLE001
        log(u"  proj.find OSHIBKA: %s" % exc)

    if dev is not None:
        for meth in (u"set_simulation_mode", u"get_simulation_mode",
                     u"set_gateway_and_address", u"is_simulation_mode"):
            try:
                log(u"  dev.%s EST (%s)" % (meth, getattr(dev, meth)))
            except Exception as exc:                           # noqa: BLE001
                log(u"  dev.%s net: %s" % (meth, (u"%s" % exc)[:60]))

        #  snachala probuem rezhim simulyatsii -- on ne trebuet shlyuza
        sim_ok = False
        try:
            dev.set_simulation_mode(True)
            sim_ok = True
            log(u"  set_simulation_mode(True) -- OK")
        except Exception as exc:                               # noqa: BLE001
            log(u"  set_simulation_mode OSHIBKA: %s" % exc)

        #  esli simulyatsiya ne vklyuchaetsya -- podklyuchaemsya cherez shlyuz
        if not sim_ok:
            gw_name = None
            try:
                gws = list(scriptengine.online.gateways)
                log(u"  shlyuzov: %d" % len(gws))
                for g in gws:
                    log(u"    %s" % g)
                if gws:
                    for attr in (u"name", u"gateway_name", u"GatewayName"):
                        try:
                            gw_name = getattr(gws[0], attr)
                            break
                        except Exception:                      # noqa: BLE001
                            continue
            except Exception as exc:                           # noqa: BLE001
                log(u"  gateways OSHIBKA: %s" % exc)
            log(u"  imya shlyuza: %s" % gw_name)
            for gw in (gw_name, u"Gateway-1", u"Gateway"):
                if not gw:
                    continue
                try:
                    dev.set_gateway_and_address(gw, u"localhost")
                    log(u"  set_gateway_and_address(%s, localhost) -- OK" % gw)
                    break
                except Exception as exc:                       # noqa: BLE001
                    log(u"  set_gateway_and_address(%s) OSHIBKA: %s"
                        % (gw, (u"%s" % exc)[:80]))

    # 3. onlajn-prisposoblenie
    step(u"3. create_online_application")
    onl = None
    try:
        onl = scriptengine.online.create_online_application(app)
        log(u"  sozdano: %s" % onl)
    except Exception as exc:                                   # noqa: BLE001
        log(u"  OSHIBKA: %s" % exc)
        FAIL.append(u"net online-prilozheniya")
        return

    # 4. login
    step(u"4. login")
    try:
        opt = scriptengine.OnlineChangeOption.Try
        onl.login(opt, True)
        log(u"  login -- OK, is_logged_in=%s" % onl.is_logged_in)
    except Exception as exc:                                   # noqa: BLE001
        log(u"  login OSHIBKA: %s" % exc)
        FAIL.append(u"login ne udalsya: %s" % exc)
        try:
            onl.logout()
        except Exception:                                      # noqa: BLE001
            pass
        return

    # 5. start
    step(u"5. start")
    try:
        onl.start()
        log(u"  start -- OK, state=%s" % onl.application_state)
    except Exception as exc:                                   # noqa: BLE001
        log(u"  start OSHIBKA: %s" % exc)

    # 6. zapustit testy
    step(u"6. puskaem testy")
    for name, val in ((u"GVL_Tests.Cpu_Test_Run", u"TRUE"),
                      (u"GVL_Tests_CPM.Cpm_Test_Run", u"TRUE")):
        try:
            onl.set_prepared_value(name, val)
            onl.write_prepared_values()
            log(u"  %s := %s -- OK" % (name, val))
        except Exception as exc:                               # noqa: BLE001
            log(u"  %s OSHIBKA: %s" % (name, exc))

    # 7. zhdat, poka projdut testy
    step(u"7. ozhidanie i chtenie")
    names = [u"GVL_Tests.Cpu_Test_Total_Pass",
             u"GVL_Tests.Cpu_Test_Fail_Count",
             u"GVL_Tests.Cpu_Test_Run",
             u"GVL_Tests_CPM.Cpm_Test_Total_Pass",
             u"GVL_Tests_CPM.Cpm_Test_Fail_Count",
             u"GVL_Tests_CPM.Cpm_Test_Run"]
    last = None
    for attempt in range(30):
        time.sleep(1)
        try:
            vals = list(onl.read_values(names))
        except Exception as exc:                               # noqa: BLE001
            log(u"  popytka %d: read_values OSHIBKA: %s" % (attempt + 1, exc))
            continue
        d = dict(zip(names, vals))
        log(u"  popytka %2d: %s" % (attempt + 1,
            u", ".join([u"%s=%s" % (k.split(u".")[-1], v) for k, v in d.items()])))
        last = d
        if u"FALSE" in (u"%s" % d.get(u"GVL_Tests.Cpu_Test_Run")) \
                and u"FALSE" in (u"%s" % d.get(u"GVL_Tests_CPM.Cpm_Test_Run")):
            log(u"  oba testa zavershilis")
            break

    # 8. itog
    step(u"8. ITOG")
    try:
        vals = dict(zip(names, list(onl.read_values(names))))
        log(u"  %s" % vals)
        cpu_pass = vals.get(u"GVL_Tests.Cpu_Test_Total_Pass")
        cpu_fail = vals.get(u"GVL_Tests.Cpu_Test_Fail_Count")
        cpm_pass = vals.get(u"GVL_Tests_CPM.Cpm_Test_Total_Pass")
        cpm_fail = vals.get(u"GVL_Tests_CPM.Cpm_Test_Fail_Count")
        log(u"  CPU: projdeno %s, provaleno %s (ozhidaetsya 62 / 0)"
            % (cpu_pass, cpu_fail))
        log(u"  CPM: projdeno %s, provaleno %s (ozhidaetsya 30 / 0)"
            % (cpm_pass, cpm_fail))
        if not (u"%s" % cpu_pass).endswith(u"62"):
            FAIL.append(u"CPU: projdeno %s vmesto 62" % cpu_pass)
        if not (u"%s" % cpu_fail).endswith(u"0"):
            FAIL.append(u"CPU: provaleno %s vmesto 0" % cpu_fail)
        if not (u"%s" % cpm_pass).endswith(u"30"):
            FAIL.append(u"CPM: projdeno %s vmesto 30" % cpm_pass)
        if not (u"%s" % cpm_fail).endswith(u"0"):
            FAIL.append(u"CPM: provaleno %s vmesto 0" % cpm_fail)
    except Exception as exc:                                   # noqa: BLE001
        log(u"  chtenie OSHIBKA: %s" % exc)
        FAIL.append(u"ne udalos prochitat rezultaty")

    # 9. vyhod
    step(u"9. logout")
    try:
        onl.stop()
        log(u"  stop -- OK")
    except Exception as exc:                                   # noqa: BLE001
        log(u"  stop: %s" % exc)
    try:
        onl.logout()
        log(u"  logout -- OK")
    except Exception as exc:                                   # noqa: BLE001
        log(u"  logout: %s" % exc)
    try:
        proj.close()
    except Exception:                                          # noqa: BLE001
        pass

    log(u"")
    if FAIL:
        log(u"REZULTAT: NE UDALOS")
        for f in FAIL:
            log(u"  * " + f)
    else:
        log(u"REZULTAT: VSE TESTY PROJDENY (62/0 i 30/0)")
    log(u"=== KONEC ===")


try:
    main()
except Exception, exc:                                          # noqa: E999
    log(u"AVARIYA: " + (u"%s" % exc))
    import traceback
    log(traceback.format_exc())
    FAIL.append(u"avariya skripta")

if not os.path.isdir(LOG):
    os.makedirs(LOG)
f = open(OUT, u"w")
f.write(u"\n".join(LINES).encode(u"utf-8"))
f.close()
sys.stdout.write(u"run_simulation: %d strok, provalov %d\n" % (len(LINES), len(FAIL)))
if FAIL:
    for x in FAIL:
        sys.stdout.write(u"  * " + x + u"\n")
