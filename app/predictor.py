#!/usr/bin/python3
# -*- coding: utf-8 -*-

import predict
import requests
import time
import yaml
from datetime import datetime
from gridtogps import GridToCoords


class Predictor:
    def __init__(self):
        self.tle = []
        self.tle_urls = ["http://www.amsat.org/amsat/ftp/keps/current/nasabare.txt",
                         "http://celestrak.com/NORAD/elements/tle-new.txt"]
        self.tle_file = "tle.txt"
        self.tle_last_update = -1
        self.tle_max_age = 60*60*24     # 24 hours

        self.cache = {}
        self.cache_ages = {}
        self.cache_max_age = 60*60      # 1 hour

        with open("satellites.yaml", 'r') as f:
            self.sats = yaml.safe_load(f)

    def get_sats(self):
        return self.sats

    def get_current_el_az(self, sat_name, qth):
        qth = GridToCoords().get(qth)
        csd = predict.observe(self.get_tle(sat_name), qth)
        return [csd['elevation'], csd['azimuth']]

    def get_all_for_loc(self, qth, n):
        if qth in self.cache and qth in self.cache_ages and time.time() - self.cache_ages[qth] < self.cache_max_age:
            print("CACHE HIT!!!!")
            return [q for q in self.cache[qth] if q['end'] > time.time()]

        buf = []
        for sat in self.get_sats().keys():
            passes = self.get_next_passes(sat, qth, n)
            buf.extend(passes)

        buf = sorted(buf, key=lambda d: d['start'])

        self.cache[qth] = buf
        self.cache_ages[qth] = time.time()

        return buf

    def get_next_passes(self, sat_name, qth, n):
        qth = GridToCoords().get(qth)
        transits = predict.transits(self.get_tle(sat_name), qth)
        passes = []
        for _ in range(n):
            t = next(transits)
            tr = {}

            tr['name'] = sat_name
            tr['start'] = t.start
            tr['end'] = t.start + t.duration()
            tr['duration'] = t.duration()

            tr['start_str'] = datetime.fromtimestamp(tr['start']).strftime("%H:%M")
            tr['duration_str'] = datetime.fromtimestamp(tr['duration']).strftime("%M:%S")
            tr['end_str'] = datetime.fromtimestamp(tr['end']).strftime("%H:%M")

            tr['el_max'] = round(t.peak()['elevation'])
            tr['az_rise'] = round(t.at(t.start)['azimuth'])
            tr['az_peak'] = round(t.peak()['azimuth'])
            tr['az_set'] = round(t.at(t.start+t.duration())['azimuth'])
            passes.append(tr)

        return passes

    def update_tle(self):
        if time.time() - self.tle_last_update < self.tle_max_age:
            return

        self.tle = []

        for rt in [requests.get(url).content.decode() for url in self.tle_urls]:
            tle_lines = [line.strip() for line in rt.splitlines()]
            self.tle += tle_lines

        self.tle_last_update = time.time()

    def get_tle(self, sat_name):
        i = self.tle.index(sat_name)
        return self.tle[i:i+3]
