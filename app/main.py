#!/usr/bin/python3
# -*- coding: utf-8 -*-

from flask import Flask, request, render_template, send_from_directory
import time
import predict
from datetime import datetime
from dateutil import tz
import json
from gridtogps import GridToCoords

app = Flask(__name__)


@app.route('/')
@app.route('/<locator>')
def home(locator="JO82"):
    pr = predict.Predict(locator)
    pr.load_satellites('satellites.yaml')
    return "XD"


@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.ico', mimetype='image/vnd.microsoft.icon')


if __name__ == "__main__":
    app.config['DEBUG'] = True
    app.run()
