#!/usr/bin/python3

import sqlite3
import sys


data = open(sys.argv[1]).read().splitlines()

conn = sqlite3.connect('predict.db')
cur = conn.cursor()
try:
    cur.execute("drop table satellites")
except Exception:
    print("Table was not removed")

print(f"create table satellites ({data[0]})")
cur.execute(f"create table satellites ({data[0]})")

for x in data[1:]:
    q = x.split(',')
    print(q)
    print("insert into satellites values (" + ','.join(['?']*len(q)) + ");", q)
    cur.execute(f"insert into satellites values ({','.join(['?']*len(q))});", q)
conn.commit()

try:
    cur.execute("drop table passes")
except Exception:
    print("Table was not removed")


passes_header = ['sat', 'loc', 'gen_time', 'aos_time', 'aos_az', 'peak_time', 'peak_el',
                 'los_time', 'los_az', 'peak_az']

cur.execute(f"create table passes ({','.join(passes_header)})")
conn.commit()
