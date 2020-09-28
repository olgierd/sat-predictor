#!/usr/bin/python
# -*- coding: utf-8 -*-

from flask import Flask, request, render_template, send_from_directory
import time
import predict
from datetime import datetime
from dateutil import tz
import os

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


@app.route('/')
@app.route('/<locator>')
def home(locator="JO82"):

    if locator not in locators:
        return "<pre>Nieprawidłowy lokator.</pre>"

    pr = predict.Predictor()

    output = u"<pre>Następne przeloty [" + locator + "]:\n\n</pre>"

    data = pr.get_passes_for_locator(locator, 50)
    cnt = 0
    lines = []

    for x in data:
        curTime = "    NOW!" if time.time() > x[1] else "za %02d:%02d" % ((int(x[1]-time.time())/3600), int((x[1]-time.time())/60) % 60)
        passDuration = int(x[5]-x[1])
        passLen = f"{int(passDuration/60):2}:{int(passDuration%60):02}"

        passDirection = '-'.join([f"{round(x[c]):03}" for c in [2, 10, 6]])

        # maplink = " <a href=\"#\" onClick=\"openmap('{:.0f},{:.0f},{:.0f},{:.0f}', {:d})\">MAP</a>".format(x[2], x[10], x[6], x[4], cnt)

        line = f"""<pre onclick="show({cnt});"><b>{x[0]:14}</b>↑{stamp_to_localtime(x[1])} ↓{stamp_to_localtime(x[5])} ({passLen}) {curTime}"""
        line = line + f"""   max el: <b>{x[4]:2}</b> az: {passDirection}</pre>"""
        line = line + f"""<div id="d{cnt}" style='display:none;'><pre class='details'>"""
        line = line + f"""    Downlink: {x[8]} | Uplink: {x[7]} | Beacon: {x[9]}</pre></div>"""
        # line = line + f"""    Downlink: {x[8]} | Uplink: {x[7]} | Beacon: {x[9]} {maplink} </pre></div>"""

        lines.append(line)

        cnt = cnt + 1

    output = output + ''.join(lines)

    return render_template('index.html', content=output)


@app.route('/map')
def map():
    path = request.args.get('path')
    return render_template('map.html', path=path)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory('', 'favicon.ico', mimetype='image/vnd.microsoft.icon')


if __name__ == "__main__":
    app.run()
