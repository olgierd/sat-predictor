#!/usr/bin/python
# -*- coding: utf-8 -*-

from flask import Flask, request, render_template, send_from_directory
import time
import predict
from datetime import datetime
from dateutil import tz


app = Flask(__name__)
app.config['DEBUG'] = True

locators = ["JO74", "JO84", "JO94", "KO04", "KO14",
            "JO73", "JO83", "JO93", "KO03", "KO13",
            "JO72", "JO82", "JO92", "KO02", "KO12",
            "JO71", "JO81", "JO91", "KO01", "KO11",
            "JO70", "JO80", "JO90", "KO00", "KO10",
            "JN79", "JN89", "JN99", "KN09", "KN19",
            "JO59"]


def stamp_to_localtime(stamp):
    ts = datetime.utcfromtimestamp(stamp).replace(tzinfo=tz.tzutc())
    return ts.astimezone(tz.gettz('Europe/Warsaw')).strftime("%H:%M")


def perform_filtering(data, fs, ssb_only, fm_only):
    filter_include = None
    filter_exclude = None

    if fs:
        filter_include = [q for q in fs.split(',') if q[0] != '-']
        filter_exclude = [q[1:] for q in fs.split(',') if q[0] == '-']

    filtered = []

    for x in data:
        if ssb_only and ssb_only == '1' and x[12] != '1':
            continue

        if fm_only and fm_only == '1' and x[11] != '1':
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


@app.route('/')
@app.route('/<locator>')
def home(locator="JO82"):

    if locator not in locators:
        return "<pre>Nieprawidłowy lokator.</pre>"

    pr = predict.Predictor()
    data = pr.get_passes_for_locator(locator, 50)

    data = perform_filtering(data, request.args.get('f'), request.args.get("ssb_only"), request.args.get("fm_only"))

    cnt = 0
    lines = []
    output = f"""<pre>Next passes [<i class="locator">{locator}</i>]:\n\n"""
    output = output + "</pre>"

    for x in data:
        curTime = "    NOW!" if time.time() > x[1] else "in %02d:%02d" % ((int(x[1]-time.time())/3600), int((x[1]-time.time())/60) % 60)
        passDuration = int(x[5]-x[1])
        passLen = f"{int(passDuration/60):2}:{int(passDuration%60):02}"

        passDirection = '-'.join([f"{round(x[c]):03}" for c in [2, 10, 6]])

        # maplink = " <a href=\"#\" onClick=\"openmap('{:.0f},{:.0f},{:.0f},{:.0f}', {:d})\">MAP</a>".format(x[2], x[10], x[6], x[4], cnt)

        line = f"""<pre onclick="show({cnt});"><b>{x[0]:14}</b>↑{stamp_to_localtime(x[1])} ↓{stamp_to_localtime(x[5])} ({passLen}) {curTime}"""
        line = line + f"""   max el: <b>{x[4]:2}</b> az: {passDirection}"""
        line = line + f"""  <b class="details" sat="{x[0]}"></b></pre>\n"""
        line = line + f"""<div id="d{cnt}" style='display:none;'><pre class='details'>"""
        line = line + f"""    Downlink: {x[8]} | Uplink: {x[7]}""" + (f""" | Beacon: {x[9]}""" if x[9] else "")
        line = line + """</pre></div>\n"""

        lines.append(line)

        cnt = cnt + 1

    output = output + ''.join(lines)

    return render_template('index.html', content=output)


@app.route('/map')
def map():
    path = request.args.get('path')
    return render_template('map.html', path=path)


@app.route('/current')
def current():
    pr = predict.Predictor()
    sat = request.args.get('sat')
    loc = request.args.get('loc')
    return pr.get_current_elaz(sat, loc)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory('', 'favicon.ico', mimetype='image/vnd.microsoft.icon')


if __name__ == "__main__":
    app.run()
