#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Generate SNAPPED walking routes via OpenRouteService (foot-walking).
# Requires env var ORS_API_KEY
# Outputs: GPX + KML + prints summary distance/duration.

import json, os, sys, requests

ORS = os.environ.get("ORS_URL","https://api.openrouteservice.org/v2/directions/foot-walking")
KEY = os.environ.get("ORS_API_KEY")
INFILE = sys.argv[1] if len(sys.argv)>1 else "waypoints_ghent.json"

def route_ors(coords):
    if not KEY:
        raise SystemExit("Brak ORS_API_KEY w zmiennej środowiskowej.")
    headers = {"Authorization": KEY, "Content-Type":"application/json"}
    body = {"coordinates":[ [lon,lat] for (lon,lat,_) in coords ], "instructions": False}
    r = requests.post(ORS, json=body, headers=headers, timeout=40); r.raise_for_status()
    data = r.json()
    line = data["features"][0]["geometry"]["coordinates"]   # [lon,lat]
    summary = data["features"][0]["properties"]["summary"]  # distance (m), duration (s)
    return line, summary

def write_gpx(name, coords_line, waypoints):
    out = ['<?xml version="1.0" encoding="UTF-8"?>','<gpx version="1.1" creator="ghent_ors_snap" xmlns="http://www.topografix.com/GPX/1/1">']
    for (lon,lat,label) in waypoints:
        out.append(f'  <wpt lat="{lat:.6f}" lon="{lon:.6f}"><name>{label}</name></wpt>')
    out.append(f'  <trk><name>{name}</name><trkseg>')
    for (lon,lat) in coords_line:
        out.append(f'    <trkpt lat="{lat:.6f}" lon="{lon:.6f}"></trkpt>')
    out.append('  </trkseg></trk></gpx>')
    return "\n".join(out)

def write_kml(name, coords_line, waypoints):
    out = ['<?xml version="1.0" encoding="UTF-8"?>','<kml xmlns="http://www.opengis.net/kml/2.2">','<Document>', f'  <name>{name}</name>']
    for i in range(1,41):
        out.append(f'  <Style id="n{i}"><IconStyle><Icon><href>http://maps.google.com/mapfiles/kml/paddle/{i}.png</href></Icon></IconStyle></Style>')
    for i,(lon,lat,label) in enumerate(waypoints, start=1):
        sid = f"#n{i if i<=40 else 1}"
        out.append(f'  <Placemark><name>{label}</name><styleUrl>{sid}</styleUrl><Point><coordinates>{lon:.6f},{lat:.6f},0</coordinates></Point></Placemark>')
    out.append('  <Style id="line"><LineStyle><width>4</width></LineStyle></Style>')
    coords = " ".join([f"{lon:.6f},{lat:.6f},0" for (lon,lat) in coords_line])
    out.append(f'  <Placemark><name>{name}</name><styleUrl>#line</styleUrl><LineString><tessellate>1</tessellate><coordinates>{coords}</coordinates></LineString></Placemark>')
    out.append('</Document></kml>')
    return "\n".join(out)

def main():
    with open(INFILE,"r",encoding="utf-8") as f:
        wp = json.load(f)
    for key in ["short","grand"]:
        coords = wp[key]
        line, summary = route_ors(coords)
        name = f"Ghent — { 'Pętla CENTRUM' if key=='short' else 'Pętla ROZSZERZONA' } (ORS snapped)"
        gpx = write_gpx(name, line, coords)
        kml = write_kml(name, line, coords)
        with open(f\"{key}_ORS_snapped.gpx\",\"w\",encoding=\"utf-8\") as fo: fo.write(gpx)
        with open(f\"{key}_ORS_snapped.kml\",\"w\",encoding=\"utf-8\") as fo: fo.write(kml)
        dist_km = summary['distance']/1000.0; dur_min = summary['duration']/60.0
        print(f\"✓ {key}: {dist_km:.2f} km, ~{dur_min:.0f} min  → {key}_ORS_snapped.gpx, {key}_ORS_snapped.kml\")
    print(\"Gotowe.\")

if __name__=='__main__':
    main()
