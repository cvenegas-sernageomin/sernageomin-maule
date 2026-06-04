"""
Scrapea los últimos sismos del CSN (sismologia.cl) -> KMZ.
Solo librería estándar (corre en GitHub Actions sin instalar nada).
Salida relativa al repo: capas/sismos/ultimos_sismos_csn.kmz
"""
import urllib.request, re, os, zipfile, datetime

BASE = "https://www.sismologia.cl"
AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.path.normpath(os.path.join(AQUI, "..", "capas", "sismos", "ultimos_sismos_csn.kmz"))


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=40).read().decode("utf-8", errors="replace")


def estilo_mag(mag):
    if mag >= 7:   return "ff0000cc", 1.8
    if mag >= 6:   return "ff0033ff", 1.3
    if mag >= 5:   return "ff0080ff", 1.0
    if mag >= 4:   return "ff00d7ff", 0.7
    if mag >= 3:   return "ff00ffbf", 0.5
    return "ff66ff66", 0.4


def main():
    home = get(BASE + "/")
    eventos = []
    for f in re.findall(r'(?s)<tr>(.*?)</tr>', home):
        if "<td" not in f:
            continue
        href = re.search(r'href="([^"]+\.html)"', f)
        if not href:
            continue
        celdas = re.findall(r'(?s)<td.*?>(.*?)</td>', f)
        texto = [re.sub(r'<[^>]+>', ' ', c).strip() for c in celdas]
        eventos.append({"href": href.group(1), "raw": texto})

    placemarks = []
    for ev in eventos:
        url = ev["href"] if ev["href"].startswith("http") else BASE + ev["href"]
        try:
            ficha = get(url)
        except Exception:
            continue
        txt = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', ficha))
        mlat = re.search(r'Latitud\s+(-?\d+\.\d+)', txt)
        mlon = re.search(r'Longitud\s+(-?\d+\.\d+)', txt)
        mprof = re.search(r'Profundidad\s+(\d+)\s*km', txt)
        mmag = re.search(r'Magnitud\s+([\d.]+)', txt)
        mfecha = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', txt)
        mlugar = re.search(r'\d+\s*km al [NSEO]+ de [^0-9]+', " ".join(ev["raw"]))
        if not (mlat and mlon and mmag):
            continue
        lat = float(mlat.group(1)); lon = float(mlon.group(1)); mag = float(mmag.group(1))
        prof = mprof.group(1) if mprof else "?"
        fecha = mfecha.group(1) if mfecha else (ev["raw"][0] if ev["raw"] else "")
        lugar = mlugar.group(0).strip() if mlugar else ""
        color, escala = estilo_mag(mag)
        placemarks.append(f"""
  <Placemark>
    <name>M {mag:.1f}</name>
    <description><![CDATA[
      <div style="font-family:Arial;font-size:12px;width:240px;">
        <div style="background:#b71c1c;color:white;padding:5px 8px;font-weight:bold;">Sismo reciente M {mag:.1f}</div>
        <table style="font-size:12px;margin:6px;">
          <tr><td><b>Fecha local</b></td><td>{fecha}</td></tr>
          <tr><td><b>Magnitud</b></td><td>{mag:.1f}</td></tr>
          <tr><td><b>Profundidad</b></td><td>{prof} km</td></tr>
          <tr><td><b>Lugar</b></td><td>{lugar}</td></tr>
          <tr><td><b>Lat, Lon</b></td><td>{lat:.2f}, {lon:.2f}</td></tr>
          <tr><td><b>Fuente</b></td><td><a href="{url}">CSN — Universidad de Chile</a></td></tr>
        </table>
      </div>]]></description>
    <Style>
      <IconStyle><color>{color}</color><scale>{escala:.1f}</scale>
        <Icon><href>http://maps.google.com/mapfiles/kml/shapes/shaded_dot.png</href></Icon></IconStyle>
      <LabelStyle><scale>0</scale></LabelStyle>
    </Style>
    <Point><coordinates>{lon},{lat},0</coordinates></Point>
  </Placemark>""")

    ahora = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    kml = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
  <name>Últimos sismos (CSN) — actualizado {ahora}</name>
  <description>Últimos sismos del Centro Sismológico Nacional (sismologia.cl). Actualización automática semanal.</description>
  {''.join(placemarks)}
</Document>
</kml>"""
    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    with zipfile.ZipFile(SALIDA, "w", zipfile.ZIP_DEFLATED) as kmz:
        kmz.writestr("doc.kml", kml.encode("utf-8"))
    print(f"OK: {SALIDA} ({len(placemarks)} sismos)")


if __name__ == "__main__":
    main()
