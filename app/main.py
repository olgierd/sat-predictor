#!/usr/bin/python3
# -*- coding: utf-8 -*-

from flask import Flask, request, render_template, send_from_directory
import json
import predictor

app = Flask(__name__)

pr = predictor.Predictor()


@app.route('/')
@app.route('/<locator>')
def home(locator="JO82"):
    return render_template("index.html", locator=locator)


@app.route('/predictions')
def satellites():
    locator = request.args.get("loc")
    return json.dumps(pr.get_all_for_loc(locator, 5))

@app.route('/positions')
def positions():
    locator = request.args.get("loc")
    return json.dumps(pr.get_above_horizon_el_az(locator))

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.ico', mimetype='image/vnd.microsoft.icon')


if __name__ == "__main__":
    app.config['DEBUG'] = True
    app.run(host='0.0.0.0')
