#!/usr/bin/python3
# -*- coding: utf-8 -*-

import predict
import requests
import time
import yaml
from bs4 import BeautifulSoup
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

        self.amsat_status_cache = {}
        self.amsat_status_last_update = -1
        self.amsat_status_max_age = 60*60*6     # 6 hours

        with open("satellites.yaml", 'r') as f:
            self.sats = yaml.safe_load(f)

    def get_current_el_az(self, sat_name, qth):
        qth = GridToCoords().get(qth)
        csd = predict.observe(self.get_tle(sat_name), qth)
        return [csd['elevation'], csd['azimuth']]

    def get_all_for_loc(self, qth, n):
        self.update_tle()
        self.update_amsat_status()

        if qth in self.cache and qth in self.cache_ages and time.time() - self.cache_ages[qth] < self.cache_max_age:
            # cache hit, return from buffer
            buf = [q for q in self.cache[qth] if q['end'] > time.time()]

        else:   # not in cache
            print(f"Generating predictions for {qth}")
            buf = []
            for sat in self.sats.keys():
                passes = self.get_next_passes(sat, qth, n)
                buf.extend(passes)

            buf = sorted(buf, key=lambda d: d['start'])

            # add to cache
            self.cache[qth] = buf
            self.cache_ages[qth] = time.time()

        for sat_pass in buf:
            sat_pass['remaining'] = sat_pass['start']-time.time()
            if sat_pass['remaining'] > 0:
                sat_pass['remaining_str'] = datetime.utcfromtimestamp(sat_pass['remaining']).strftime("%H:%M")
            else:
                sat_pass['remaining_str'] = "NOW!"

            if sat_pass['start'] < time.time() and time.time() < sat_pass['end']:
                sat_pass['el_now'], sat_pass['az_now'] = self.get_current_el_az(sat_pass['name'], qth)

        return buf

    def get_next_passes(self, sat_name, qth, n):
        qth = GridToCoords().get(qth)
        transits = predict.transits(self.get_tle(sat_name), qth)
        passes = []
        for _ in range(n):
            t = next(transits)
            tr = {}

            tr['name'] = sat_name
            tr['mode'] = self.sats[sat_name]['mode']
            tr['uplink'] = self.sats[sat_name]['uplink']
            tr['downlink'] = self.sats[sat_name]['downlink']
            tr['beacon'] = self.sats[sat_name]['beacon']

            tr['start'] = t.start
            tr['end'] = t.start + t.duration()
            tr['duration'] = t.duration()

            tr['start_str'] = datetime.fromtimestamp(tr['start']).strftime("%H:%M")
            tr['duration_str'] = datetime.utcfromtimestamp(tr['duration']).strftime("%-M:%S")
            tr['end_str'] = datetime.fromtimestamp(tr['end']).strftime("%H:%M")

            tr['el_max'] = round(t.peak()['elevation'])
            tr['az_rise'] = round(t.at(t.start)['azimuth'])
            tr['az_peak'] = round(t.peak()['azimuth'])
            tr['az_set'] = round(t.at(t.start+t.duration())['azimuth'])

            # status_string, perc = self.get_amsat_status(sat_name)
            tr['status'] = self.get_amsat_status(sat_name)

            passes.append(tr)

        return passes

    def get_above_horizon_el_az(self, qth):

        self.update_tle()

        qth = GridToCoords().get(qth)

        o = {}
        for sat in self.sats.keys():
            info = predict.observe(self.get_tle(sat), qth)
            if info['elevation'] >= 0:
                o[sat] = [round(info['elevation'], 1), round(info['azimuth'], 1)]
        return o

    def update_tle(self):
        if time.time() - self.tle_last_update < self.tle_max_age:
            return

        print("Updating TLE")
        self.tle = []

        for rt in [requests.get(url).content.decode() for url in self.tle_urls]:
            tle_lines = [line.strip() for line in rt.splitlines()]
            self.tle += tle_lines

        self.tle_last_update = time.time()

    def get_tle(self, sat_name):
        i = self.tle.index(sat_name)
        return self.tle[i:i+3]

    def get_amsat_status(self, sat):
        if 'amsat_name' in self.sats[sat]:
            sat = self.sats[sat]['amsat_name']

        if sat in self.amsat_status_cache:
            return self.amsat_status_cache[sat]
        else:
            return [5, 5, 5]

    def update_amsat_status(self):
        if time.time() - self.amsat_status_last_update < self.amsat_status_max_age:
            return

        print("Updating Amsat")

        self.amsat_status_cache = {}
        self.amsat_status_last_update = time.time()

        symbols = {'#4169E1': '0', 'yellow': '1', 'red': '2', 'orange': '3', '#9900FF': '4', 'C0C0C0': '5'}

        page_src = requests.get('https://amsat.org/status/').content
        sat_rows = BeautifulSoup(page_src, 'html.parser').find_all('table')[2].find_all('tr')[1:]

        for row in sat_rows:
            filtered_cells = [c for c in row.find_all('td') if c.has_attr('bgcolor')]
            colors = [cell.attrs['bgcolor'] for cell in filtered_cells]
            satellite_name = row.find_all('td')[0].text
            status_string = [symbols[x] for x in colors]

            self.amsat_status_cache[satellite_name] = status_string
