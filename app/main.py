#!/usr/bin/python
# -*- coding: utf-8 -*-

from flask import Flask, request, render_template, send_from_directory
import time
import predict
from datetime import datetime
from dateutil import tz
import json
from gridtogps import GridToCoords


app = Flask(__name__)

def stamp_to_localtime(stamp):
    ts = datetime.utcfromtimestamp(stamp).replace(tzinfo=tz.tzutc())
    return ts.astimezone(tz.gettz('Europe/Warsaw')).strftime("%H:%M")


def perform_filtering(data, fs, only):
    filter_include = None
    filter_exclude = None

    if fs:
        fs = fs.upper()
        filter_include = [q for q in fs.split(',') if q[0] != '-']
        filter_exclude = [q[1:] for q in fs.split(',') if q[0] == '-']

    filtered = []

    for x in data:
        if only:
            if only == "SSB" and x[11] != 'SSB':
                continue

            if only == "FM" and x[11] != 'FM':
                continue

        if filter_exclude and any([fe in x[0] for fe in filter_exclude]):
            continue

        if filter_include:
            if any([fi in x[0] for fi in filter_include]):
                filtered.append(x)
            else:
                continue

        filtered.append(x)

    return filtered


def checkLocator(loc):
    gtc = GridToCoords()
    try:
        p = gtc.get(loc)
        if p != [0, 0]:
            return True
        else:
            return False
    except Exception:
        return False


def argtoggle(param, value):
    q = {}
    for k, v in request.args.items():
        q[k] = v

    q["only"] = value

    return '&'.join([f"{x}={q[x]}" for x in q])


@app.route('/')
@app.route('/<locator>')
def home(locator="JO82"):

    client_ip = request.headers.get('X-Forwarded-For')
    if client_ip:
        print(datetime.now().isoformat(), locator, client_ip, flush=True)

    pr = predict.Predictor()

    if not checkLocator(locator):
        return "<pre>Nieprawidłowy lokator.</pre>"

    data = pr.get_passes_for_locator(locator, 50)

    only = request.args.get("only")

    data = perform_filtering(data, request.args.get('f'), only)

    cnt = 0
    lines = []
    output = f"""<pre>Next passes [<i class="locator">{locator}</i>]:   """
    output = output + f"FM ONLY: <a href='{request.path}?{argtoggle('only', 'FM' if only!='FM' else '')}'>{'YES' if only == 'FM' else 'NO'}</a> | "
    output = output + f"SSB ONLY: <a href='{request.path}?{argtoggle('only', 'SSB' if only!='SSB' else '')}'>{'YES' if only == 'SSB' else 'NO'}</a>"

    output = output + "\n\n</pre>"

    for x in data:
        curTime = "    NOW!" if time.time() > x[1] else "in %02d:%02d" % ((int(x[1]-time.time())/3600), int((x[1]-time.time())/60) % 60)
        passDuration = int(x[5]-x[1])
        passLen = f"{int(passDuration/60):2}:{int(passDuration%60):02}"

        passDirection = '-'.join([f"{round(x[c]):03}" for c in [2, 10, 6]])

        # maplink = " <a href=\"#\" onClick=\"openmap('{:.0f},{:.0f},{:.0f},{:.0f}', {:d})\">MAP</a>".format(x[2], x[10], x[6], x[4], cnt)

        line = f"""<pre onclick="show({cnt});">[{x[11]:>3}] <b>{x[0]:14}</b>↑{stamp_to_localtime(x[1])} ↓{stamp_to_localtime(x[5])} ({passLen})"""
        line = line + f""" {curTime}   max el: <b>{x[4]:2}</b> az: {passDirection}"""
        line = line + f"""  <b class="details" sat="{x[0]}"></b></pre>\n"""
        line = line + f"""<div id="d{cnt}" style='display:none;'><pre class='sat_details'>"""
        line = line + f"""    Downlink: {x[8]} | Uplink: {x[7]}""" + (f""" | Beacon: {x[9]}""" if x[9] else "")
        line = line + """</pre></div>\n"""

        lines.append(line)

        cnt = cnt + 1

    # lines.append("<input type='text'></input>")

    output = output + ''.join(lines)

    return render_template('index.html', content=output)


@app.route('/map')
def map():
    path = request.args.get('path')
    return render_template('map.html', path=path)


def get_az_letter(az):
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    return directions[int(((az + 22.5) % 360)/45)]


def get_doppler_100m(v):
    return round(100e6 * (-v / 300e6))


@app.route('/current')
def current():
    pr = predict.Predictor()
    sats = json.loads(request.args.get('sats'))
    loc = request.args.get('loc')
    response = {}
    for sat in sats:
        data = pr.get_current_elaz(sat, loc)
        resp = f"↑{data['el']:4.1f}° ↔{data['az']:5.1f}° [{get_az_letter(data['az'])}]"
        response[sat] = resp if data['el'] > 0 else ""
    return json.dumps(response)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.ico', mimetype='image/vnd.microsoft.icon')


if __name__ == "__main__":
    app.config['DEBUG'] = True
    app.run()
