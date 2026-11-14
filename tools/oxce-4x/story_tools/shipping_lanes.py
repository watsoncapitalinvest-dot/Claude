"""Shipping lanes for the world-map civilian ships (SEA_BATTLES_DESIGN_v1 section 12; BUILD 13 Nov 19:05 item 10).
STORY data, 1980s traffic. Writes shipping_lanes.yml next to this script and checks every leg stays at sea
(great-circle sampled every ~2 km against global_land_mask), except legs marked canal.

Ports are an offshore point (the sea buoy), not the quay, so a ship never sits on land.
ships = how many of the ~40 world ships run this lane at once; cobra = the CEILING on the share that are Cobra's
when Cobra is well funded. The share actually sailing scales with Cobra's money and is zero when Cobra is broke
(SEA_BATTLES_DESIGN_v1 12h, John 13 Nov 20:59)
(Cobra's own lines and fronts). The world total of Cobra ships is about 1 in 10 (design 12b).
Lanes run both ways; BUILD reverses the waypoint list for the return trip.
Usage: python3 shipping_lanes.py [--check-only]"""
import math, sys, os, yaml

PORTS = {   # id: (name, lat, lon, country)
    'HOUSTON':       ('Houston',        29.25,  -94.55, 'USA'),
    'NEW_ORLEANS':   ('New Orleans',    28.80,  -89.40, 'USA'),
    'MIAMI':         ('Miami',          25.76,  -80.05, 'USA'),
    'NORFOLK':       ('Norfolk',        36.95,  -75.70, 'USA'),
    'NEW_YORK':      ('New York',       40.40,  -73.65, 'USA'),
    'LONG_BEACH':    ('Long Beach',     33.65,  -118.25, 'USA'),
    'SAN_FRANCISCO': ('San Francisco',  37.75,  -122.70, 'USA'),
    'VERACRUZ':      ('Veracruz',       19.25,  -95.95, 'Mexico'),
    'CARTAGENA':     ('Cartagena',      10.35,  -75.70, 'Colombia'),
    'KINGSTON':      ('Kingston',       17.85,  -76.75, 'Jamaica'),
    'COLON':         ('Colón (Panama Canal, Atlantic)', 9.45, -79.95, 'Panama'),
    'BALBOA':        ('Balboa (Panama Canal, Pacific)', 8.75, -79.50, 'Panama'),
    'RIO':           ('Rio de Janeiro', -23.05, -43.15, 'Brazil'),
    'LISBON':        ('Lisbon',         38.60,  -9.45, 'Portugal'),
    'ROTTERDAM':     ('Rotterdam',      52.00,  3.80, 'Netherlands'),
    'MARSEILLE':     ('Marseille',      43.20,  5.20, 'France'),
    'PIRAEUS':       ('Piraeus',        37.85,  23.55, 'Greece'),
    'PORT_SAID':     ('Port Said (Suez Canal, north)', 31.45, 32.35, 'Egypt'),
    'SUEZ':          ('Suez (Suez Canal, south)', 29.80, 32.58, 'Egypt'),
    'LAGOS':         ('Lagos',          6.20,   3.40, 'Nigeria'),
    'CAPE_TOWN':     ('Cape Town',      -33.85, 18.30, 'South Africa'),
    'BOMBAY':        ('Bombay',         18.85,  72.70, 'India'),
    'SINGAPORE':     ('Singapore',      1.14,   103.74, 'Singapore'),
    'HONG_KONG':     ('Hong Kong',      22.15,  114.30, 'Hong Kong'),
    'YOKOHAMA':      ('Yokohama',       35.15,  139.80, 'Japan'),
}

LANES = [   # id, name, from, to, waypoints [(lat, lon)], ships, cobra share, canal
    # --- Gulf and Caribbean: Act 1's water. Cartel and Cobra traffic is heaviest here.
    ('GULF_COAST', 'Gulf coast', 'HOUSTON', 'NEW_ORLEANS', [(28.6, -92.0)], 3, 0.20, False),
    ('GULF_FLORIDA', 'Gulf to Florida', 'NEW_ORLEANS', 'MIAMI', [(26.5, -86.0), (24.25, -82.5), (24.35, -80.9), (24.4, -80.8), (24.85, -80.3), (25.35, -80.05)], 2, 0.20, False),
    ('MEXICO_GULF', 'Veracruz to Houston', 'VERACRUZ', 'HOUSTON', [(23.5, -95.6)], 2, 0.20, False),
    ('GULF_CANAL', 'Gulf to Panama', 'NEW_ORLEANS', 'COLON', [(25.0, -87.5), (21.6, -85.9), (18.0, -82.5), (12.0, -80.6)], 3, 0.15, False),
    ('COLOMBIA_GULF', 'Colombia to Houston', 'CARTAGENA', 'HOUSTON', [(15.0, -79.0), (19.0, -84.0), (21.6, -85.9), (25.0, -90.0)], 2, 0.50, False),
    ('COLOMBIA_FLORIDA', 'Colombia to Miami', 'CARTAGENA', 'MIAMI', [(15.0, -79.0), (19.0, -84.0), (21.6, -85.9), (23.5, -84.5), (24.25, -82.5), (24.35, -80.9), (24.4, -80.8), (24.85, -80.3), (25.35, -80.05)], 2, 0.50, False),
    ('JAMAICA_CANAL', 'Kingston to Panama', 'KINGSTON', 'COLON', [(14.0, -78.5)], 1, 0.0, False),
    ('JAMAICA_NEW_YORK', 'Kingston to New York', 'KINGSTON', 'NEW_YORK', [(17.6, -76.6), (17.7, -75.9), (18.6, -75.3), (20.0, -73.85), (20.3, -73.5), (20.6, -72.0), (21.5, -70.5), (23.5, -69.5), (32.0, -72.5)], 1, 0.0, False),
    ('EAST_COAST', 'East coast', 'MIAMI', 'NEW_YORK', [(27.5, -79.6), (31.5, -79.0), (35.0, -74.8), (36.9, -74.6)], 2, 0.0, False),
    ('PANAMA_CANAL', 'Panama Canal', 'COLON', 'BALBOA', [], 1, 0.0, True),
    # --- Pacific
    ('PACIFIC_CANAL', 'Long Beach to Panama', 'LONG_BEACH', 'BALBOA', [(30.0, -118.5), (22.2, -110.5), (18.5, -106.5), (15.5, -99.0), (12.5, -92.0), (10.5, -88.0), (7.5, -84.0), (6.8, -80.6), (7.5, -79.6)], 2, 0.0, False),
    ('CALIFORNIA_COAST', 'California coast', 'SAN_FRANCISCO', 'LONG_BEACH', [(35.0, -121.5), (34.2, -120.7), (33.6, -120.0), (33.6, -119.0)], 1, 0.0, False),
    ('TRANSPACIFIC', 'Transpacific', 'YOKOHAMA', 'LONG_BEACH', [(34.95, 139.75), (34.6, 139.9), (35.5, 142.0), (40.0, 150.0), (45.0, 170.0), (45.0, -170.0), (42.0, -145.0), (35.5, -125.0), (33.6, -120.0), (33.6, -119.0)], 3, 0.0, False),
    ('CHINA_JAPAN', 'Hong Kong to Yokohama', 'HONG_KONG', 'YOKOHAMA', [(21.4, 121.3), (26.0, 128.0), (31.0, 135.0), (34.3, 139.6)], 1, 0.0, False),
    ('SOUTH_CHINA_SEA', 'Singapore to Hong Kong', 'SINGAPORE', 'HONG_KONG', [(1.30, 104.35), (1.55, 104.7), (3.0, 105.5), (10.0, 110.0), (18.0, 113.5), (21.5, 114.6)], 1, 0.0, False),
    # --- Atlantic and Europe
    ('NORTH_ATLANTIC', 'New York to Rotterdam', 'NEW_YORK', 'ROTTERDAM', [(41.0, -60.0), (48.0, -30.0), (49.3, -6.0), (50.1, -1.5), (50.95, 1.45)], 3, 0.10, False),
    ('MID_ATLANTIC', 'Norfolk to Lisbon', 'NORFOLK', 'LISBON', [(37.0, -50.0), (38.5, -20.0)], 1, 0.0, False),
    ('GIBRALTAR', 'Lisbon to Marseille', 'LISBON', 'MARSEILLE', [(36.6, -9.0), (35.95, -6.0), (35.95, -5.4), (36.2, -2.0), (38.5, 3.0)], 2, 0.0, False),
    ('MEDITERRANEAN', 'Marseille to Piraeus', 'MARSEILLE', 'PIRAEUS', [(38.0, 8.9), (37.4, 11.8), (36.3, 15.5), (36.1, 21.0), (35.7, 23.0), (36.9, 23.6), (37.6, 23.75)], 2, 0.10, False),
    ('EAST_MED', 'Piraeus to Port Said', 'PIRAEUS', 'PORT_SAID', [(37.0, 24.6), (35.6, 26.0), (33.0, 30.0)], 1, 0.0, False),
    ('SUEZ_CANAL', 'Suez Canal', 'PORT_SAID', 'SUEZ', [], 1, 0.0, True),
    ('WEST_AFRICA', 'Lagos to Rotterdam', 'LAGOS', 'ROTTERDAM', [(4.5, -2.0), (3.5, -5.0), (4.0, -10.0), (7.0, -15.0), (15.0, -20.0), (28.0, -19.0), (36.0, -12.0), (43.5, -10.0), (48.6, -6.0), (50.1, -1.5), (50.95, 1.45)], 1, 0.0, False),
    # --- Southern and Indian Ocean
    ('BRAZIL_RUN', 'New York to Rio', 'NEW_YORK', 'RIO', [(30.0, -60.0), (10.0, -40.0), (0.0, -32.5), (-8.0, -33.5), (-15.0, -37.5), (-22.5, -41.0), (-23.3, -41.8)], 1, 0.0, False),
    ('SOUTH_ATLANTIC', 'Rio to Cape Town', 'RIO', 'CAPE_TOWN', [(-30.0, -20.0), (-33.0, 0.0), (-34.0, 15.0)], 1, 0.0, False),
    ('CAPE_ROUTE', 'Cape Town to Lagos', 'CAPE_TOWN', 'LAGOS', [(-30.0, 14.0), (-15.0, 9.0), (-3.0, 7.0), (3.5, 5.0)], 1, 0.0, False),
    ('RED_SEA', 'Suez to Bombay', 'SUEZ', 'BOMBAY', [(29.5, 32.65), (28.8, 33.0), (28.0, 33.55), (27.33, 34.2), (26.5, 34.6), (20.0, 38.5), (14.0, 42.2), (12.6, 43.35), (12.0, 46.0), (13.5, 52.0), (17.0, 65.0)], 1, 0.0, False),
    ('INDIAN_OCEAN', 'Bombay to Singapore', 'BOMBAY', 'SINGAPORE', [(17.5, 71.5), (12.0, 73.5), (8.0, 76.0), (5.6, 80.5), (6.2, 95.0), (5.9, 97.5), (4.5, 99.3), (2.6, 101.0), (1.6, 102.7), (1.2, 103.5)], 1, 0.0, False),
]


def slerp(a, b, t):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    p1 = (math.cos(la1) * math.cos(lo1), math.cos(la1) * math.sin(lo1), math.sin(la1))
    p2 = (math.cos(la2) * math.cos(lo2), math.cos(la2) * math.sin(lo2), math.sin(la2))
    d = math.acos(max(-1, min(1, sum(x * y for x, y in zip(p1, p2)))))
    if d < 1e-9: return a
    s1, s2 = math.sin((1 - t) * d) / math.sin(d), math.sin(t * d) / math.sin(d)
    x, y, z = (s1 * u + s2 * v for u, v in zip(p1, p2))
    return math.degrees(math.atan2(z, math.hypot(x, y))), math.degrees(math.atan2(y, x)), d * 6371


def check():
    from global_land_mask import globe
    bad = []
    for pid, (n, la, lo, c) in PORTS.items():
        if globe.is_land(la, lo): bad.append(f'port {pid} on land at {la},{lo}')
    for lid, name, f, t, wps, ships, cob, canal in LANES:
        pts = [PORTS[f][1:3]] + list(wps) + [PORTS[t][1:3]]
        if canal: continue
        for i, (a, b) in enumerate(zip(pts, pts[1:])):
            dist = slerp(a, b, 1)[2]
            n = max(2, int(dist / 2))
            for k in range(n + 1):
                la, lo, _ = slerp(a, b, k / n)
                lo = (lo + 180) % 360 - 180
                if globe.is_land(la, lo):
                    bad.append(f'lane {lid} leg {i} ({a} -> {b}) crosses land near {la:.2f},{lo:.2f}'); break
    return bad


if __name__ == '__main__':
    bad = check()
    for b in bad: print('LAND:', b)
    total = sum(l[5] for l in LANES); cobra = sum(l[5] * l[6] for l in LANES)
    print(f'{len(PORTS)} ports, {len(LANES)} lanes, {total} ships, about {cobra:.1f} Cobra ({100*cobra/total:.0f}%)')
    if '--check-only' in sys.argv or bad: sys.exit(1 if bad else 0)
    out = {'ports': [{'id': k, 'name': v[0], 'lat': v[1], 'lon': v[2], 'country': v[3]} for k, v in PORTS.items()],
           'lanes': [{'id': l[0], 'name': l[1], 'from': l[2], 'to': l[3], 'waypoints': [list(w) for w in l[4]],
                      'ships': l[5], 'cobraShare': l[6], **({'canal': True} if l[7] else {})} for l in LANES]}
    hdr = ('# Shipping lanes for the world-map civilian ships (STORY). Generated by shipping_lanes.py: edit the script, not this file.\n'
           '# Every leg except canals checked at sea. Ports are offshore points. Lanes run both ways.\n'
           '# cobraShare is a ceiling: the Cobra ships actually sailing scale with Cobra\'s funds, zero when broke (SEA_BATTLES_DESIGN_v1 12h).\n')
    open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shipping_lanes.yml'), 'w').write(hdr + yaml.dump(out, sort_keys=False, width=200))
    print('wrote shipping_lanes.yml')
