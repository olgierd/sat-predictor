#!/usr/bin/python
# -*- coding: utf-8 -*-

from gridtogps import GridToCoords
import ephem
import os
import time
import requests
import sqlite3
import calendar


class Predictor:
    def __init__(self):
        self.TLEFILE = './tle.txt'
        self.DBFILE = './predict.db'
        self.update_tle()
        self.all_tle = open(self.TLEFILE, 'r').read().splitlines()
        self.refreshlimit = 60*60
        self.conn = sqlite3.connect(self.DBFILE)

    def update_tle(self):
        if not os.path.isfile(self.TLEFILE) or (time.time()-os.path.getctime(self.TLEFILE)) > 60*60*24*3:
            print("Fetching new TLE")
            f = open(self.TLEFILE, "w")
            f.write(requests.get("http://www.amsat.org/amsat/ftp/keps/current/nasabare.txt").text+"\n")
            f.write(requests.get("http://celestrak.com/NORAD/elements/tle-new.txt").text)
            f.close()
            self.all_tle = open(self.TLEFILE, 'r').read().splitlines()

    def middle_point(self, a, b):
        c = [a, b]
        c.sort()
        res = (c[1]-c[0], 1) if c[1]-c[0] < 180 else ((c[0]-c[1]) % 360, -1)
        return (c[0]+(res[0]/2)*res[1]) % 360

    def get_tle(self, sat_name):
        for line_n in range(len(self.all_tle)):
            if self.all_tle[line_n].upper() == sat_name.upper():
                return self.all_tle[line_n:line_n+3]
        raise Exception(f"Whoa, no satellite found! {sat_name}")

    def get_current_elaz(self, satellite, locator):
        beg = time.time()
        lat, lon = GridToCoords().get(locator)
        obs = ephem.Observer()
        obs.lat, obs.lon = lat * ephem.degree, lon * ephem.degree
        obs.elevation = 100
        raw_tle = self.get_tle(satellite)
        satellite = ephem.readtle(raw_tle[0], raw_tle[1], raw_tle[2])
        satellite.compute(obs)

        return str([satellite.alt/ephem.degree, satellite.az/ephem.degree, time.time()-beg])

    def get_current_elaz_many(self, satellites, locator):
        lat, lon = GridToCoords().get(locator)
        obs = ephem.Observer()
        obs.lat, obs.lon = lat * ephem.degree, lon * ephem.degree
        obs.elevation = 100
        d = {}
        for satellite in satellites:
            raw_tle = self.get_tle(satellite)
            sat = ephem.readtle(raw_tle[0], raw_tle[1], raw_tle[2])
            sat.compute(obs)
            d[satellite] = [sat.alt/ephem.degree, sat.az/ephem.degree]

        return d

    def get_passes(self, satellite, locator):
        raw_tle = self.get_tle(satellite)
        lat, lon = GridToCoords().get(locator)

        obs = ephem.Observer()
        obs.lat, obs.lon = lat * ephem.degree, lon * ephem.degree
        obs.elevation = 100
        satellite = ephem.readtle(raw_tle[0], raw_tle[1], raw_tle[2])

        obs.date = obs.date - 5*ephem.minute
        passes = []
        for x in range(15):
            cur_pass = obs.next_pass(satellite)
            new_pass = []
            for x in range(0, 6, 2):
                new_pass.append(calendar.timegm(cur_pass[x].datetime().timetuple()))
                new_pass.append(int(cur_pass[x+1]/ephem.degree+0.5))
            new_pass.append(self.middle_point(new_pass[1], new_pass[5]))
            passes.append(new_pass)
            obs.date = cur_pass[4] + ephem.minute*5

        return passes

    def update_locator(self, locator):

        self.update_tle()
        satellites = [x[0] for x in self.conn.execute('select name from satellites')]

        self.conn.execute("delete from passes where loc='" + locator + "'")

        for sat in satellites:
            for sat_pass in self.get_passes(sat, locator):
                data = [sat, locator, time.time()] + sat_pass
                self.conn.execute('insert into passes values(' + ','.join(['?']*len(data)) + ')', data)

        self.conn.commit()

    def get_passes_for_locator(self, locator, limit):

        oldestrecord = self.conn.execute("select gen_time from passes \
            where loc = ?\
            order by gen_time asc limit 1", [locator]).fetchone()

        if oldestrecord is None or time.time()-oldestrecord[0] > self.refreshlimit:
            start = time.time()
            self.update_locator(locator)
            print("Regenerating for", locator, "Elapsed [ms]:", round((time.time()-start)*1000))

        data = self.conn.execute("select sat, aos_time, aos_az, peak_time, peak_el, los_time, los_az, uplink, downlink, beacon, peak_az, fm, linear \
                         from passes p left join satellites s \
                         on p.sat = s.name \
                         where loc = ? and los_time > ?\
                         order by aos_time limit ?", [locator, int(time.time()), limit])

        return data

    def get_ssb_sats(self):
        data = self.conn.execute("select name from satellites where linear = '1'").fetchall()
        return [x[0] for x in data]

    def get_fm_sats(self):
        data = self.conn.execute("select name from satellites where fm = '1'").fetchall()
        return [x[0] for x in data]
