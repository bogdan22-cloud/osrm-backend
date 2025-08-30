#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Generate SNAPPED walking routes via OSRM (public demo server).
# Outputs: GPX + KML with line snapped to foot network + numbered waypoints.

import json, sys, os, requests

OSRM = os.environ.get("OSRM_URL","https://router.project-osrm.org")
INFILE = sys.argv[1] if len(sys.argv)>1 else "waypoints_ghent.json"

def route_osrm(coords):
    # coords: list of (lon,lat,label)
    coord_str = ";".join([f"{lon:.6f},{lat:.6f}" for (lon,lat,_) in coords])
    url = f"{OSRM}/route/v1/foot/{coord_str}?overview=full&geometries=geojson&steps=false&annotations=false"
    r = requests.get(url, timeout=30); r.raise_for_status()
    data = r.json()
    return data["routes"][0]["geometry"]["coordinates"]  # list [lon,lat]

def write_gpx(name, coords_line, waypoints):
    out = []
    out.append('<?xml version="1.0" encoding="UTF-8"?>')
    out.append('<gpx version="1.1" creator="ghent_osrm_snap" xmlns="http://www.topografix.com/GPX/1/1">')
    for (lon,lat,label) in waypoints:
        out.append(f'  <wpt lat="{lat:.6f}" lon="{lon:.6f}"><name>{label}</name></wpt>')
    out.append(f'  <trk><name>{name}</name><trkseg>')
    for (lon,lat) in coords_line:
        out.append(f'    <trkpt lat="{lat:.6f}" lon="{lon:.6f}"></trkpt>')
    out.append('  </trkseg></trk>')
    out.append('</gpx>')
    return "\n".join(out)

def write_kml(name, coords_line, waypoints):
    out = []
    out.append('<?xml version="1.0" encoding="UTF-8"?>')
    out.append('<kml xmlns="http://www.opengis.net/kml/2.2">')
    out.append('<Document>')
    out.append(f'  <name>{name}</name>')
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
        line = route_osrm(coords)
        name = f"Ghent — { 'Pętla CENTRUM' if key=='short' else 'Pętla ROZSZERZONA' } (OSRM snapped)"
        gpx = write_gpx(name, line, coords)
        kml = write_kml(name, line, coords)
        with open(f"{key}_OSRM_snapped.gpx","w",encoding="utf-8") as fo: fo.write(gpx)
        with open(f"{key}_OSRM_snapped.kml","w",encoding="utf-8") as fo: fo.write(kml)
        print(f"✓ Wygenerowano: {key}_OSRM_snapped.gpx, {key}_OSRM_snapped.kml")
    print("Gotowe.")

if __name__=="__main__":
    main()
