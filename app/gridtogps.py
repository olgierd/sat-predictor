#!/usr/bin/python3

class GridToCoords:
    def get(self, grid):
        loc = grid.upper()

        if (
            loc[0] < 'A' or loc[0] > 'R' or loc[1] < 'A' or loc[1] > 'R' or
            loc[2] < '0' or loc[2] > '9' or loc[3] < '0' or loc[3] > '9'
        ):
            return [0, 0]

        if len(loc) == 6:
            if loc[4] < 'A' or loc[4] > 'X' or loc[5] < 'A' or loc[5] > 'X':
                return [0, 0]

        if len(loc) != 4 and len(loc) != 6:
            return [0, 0]

        lat = ((ord(loc[1])-ord('A'))*10) + (ord(loc[3])-ord('0'))
        lon = ((ord(loc[0])-ord('A'))*20) + (ord(loc[2])-ord('0'))*2

        if len(loc) == 6:
            lat = lat + ((ord(loc[5])-ord('A'))*2.5)/60.0 + 0.5*2.5/60.0
            lon = lon + (((ord(loc[4])-ord('A'))*5))/60.0 + 0.5*5/60.0

        if len(loc) == 4:
            lat = lat + 0.5
            lon = lon + 1

        lat = lat - 90
        lon = lon - 180

        return [lat, -lon, 100]
