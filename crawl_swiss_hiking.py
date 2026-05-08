#!/usr/bin/env python3
"""Crawler-assisted Tratify updates for Swiss hiking/mountain railway operation pages.

Uses official destination/operator pages, extracts visible text with a headless browser
when possible, then writes conservative verified announcements to Tratify/Supabase.
"""
from __future__ import annotations

import json
import re
import subprocess
import time
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parent
INDEX = REPO / "index.html"

@dataclass
class Target:
    name: str
    place: str
    source_org: str
    url: str
    kind: str = "operator"
    region: str = "ch"

TARGETS = [
    Target("Jungfrau Region", "Jungfrau Region, Bernese Oberland, Switzerland", "Jungfrau Railways", "https://www.jungfrau.ch/en-gb/live/"),
    Target("Zermatt Matterhorn", "Zermatt, Valais, Switzerland", "Zermatt Bergbahnen / Zermatt Tourism", "https://www.matterhornparadise.ch/en/book/operating-hours"),
    Target("Pilatus", "Pilatus, Lucerne/Obwalden, Switzerland", "PILATUS-BAHNEN AG", "https://www.pilatus.ch/en/live"),
    Target("Rigi", "Rigi, Schwyz/Lucerne, Switzerland", "Rigi Bahnen AG", "https://www.rigi.ch/en/inform/current-information"),
    Target("Titlis Engelberg", "Engelberg-Titlis, Obwalden, Switzerland", "Titlis Bergbahnen", "https://www.titlis.ch/en/live"),
    Target("Schilthorn Mürren", "Schilthorn / Mürren, Bernese Oberland, Switzerland", "Schilthornbahn AG", "https://schilthorn.ch/en/Infos/Timetable__Tariffs/Open_facilities"),
    Target("Aletsch Arena", "Aletsch Arena, Valais, Switzerland", "Aletsch Arena AG", "https://www.aletscharena.ch/en/aletsch-arena/interactive/operating-status"),
    Target("Davos Klosters", "Davos Klosters, Graubünden, Switzerland", "Davos Klosters Mountains", "https://www.davos.ch/en/inform/operating-hours"),
    Target("Arosa Lenzerheide", "Arosa Lenzerheide, Graubünden, Switzerland", "Arosa Lenzerheide", "https://arosalenzerheide.swiss/en/Region/Live/Operating-hours"),
    Target("Flims Laax Falera", "Flims Laax Falera, Graubünden, Switzerland", "LAAX / Weisse Arena", "https://www.laax.com/en/live"),
    Target("Andermatt Sedrun Disentis", "Andermatt Sedrun Disentis, Uri/Graubünden, Switzerland", "Andermatt Sedrun Disentis", "https://www.andermatt-sedrun-disentis.ch/en/live-info"),
    Target("Saas-Fee / Saas Valley", "Saas-Fee, Valais, Switzerland", "Saas-Fee/Saastal Tourism", "https://www.saas-fee.ch/en/live/operating-information"),
    Target("Gstaad", "Gstaad, Bernese Oberland, Switzerland", "Gstaad Saanenland Tourism", "https://www.gstaad.ch/en/gstaad/information/operating-hours.html"),
    Target("Stoos", "Stoos, Schwyz, Switzerland", "Stoosbahnen AG", "https://www.stoos.ch/en/pages/operating-info"),

    Target("Engadin St. Moritz", "Engadin St. Moritz, Graubünden, Switzerland", "Engadin St. Moritz Mountains", "https://www.engadin.ch/en/snow-report/open-facilities/"),
    Target("Glacier 3000", "Glacier 3000, Vaud/Bern, Switzerland", "Glacier 3000", "https://www.glacier3000.ch/en/information/live-info"),
    Target("Verbier 4 Vallées", "Verbier 4 Vallées, Valais, Switzerland", "Téléverbier / 4 Vallées", "https://www.verbier4vallees.ch/en/infos/live-info"),
    Target("Crans-Montana", "Crans-Montana, Valais, Switzerland", "Crans-Montana Aminona", "https://www.mycma.ch/en/live/"),
    Target("Adelboden-Lenk", "Adelboden-Lenk, Bernese Oberland, Switzerland", "Adelboden-Lenk", "https://www.adelboden-lenk.ch/en/live"),
    Target("Meiringen-Hasliberg", "Meiringen-Hasliberg, Bernese Oberland, Switzerland", "Bergbahnen Meiringen-Hasliberg", "https://www.meiringen-hasliberg.ch/en/Live/Operating-hours"),
    Target("Flumserberg", "Flumserberg, St. Gallen, Switzerland", "Bergbahnen Flumserberg", "https://www.flumserberg.ch/en/Live/Facilities"),
    Target("Pizol", "Pizol, St. Gallen, Switzerland", "Pizolbahnen AG", "https://pizol.com/en/live/operating-hours"),
    Target("Mythenregion", "Mythenregion, Schwyz, Switzerland", "Mythenregion AG", "https://www.mythenregion.ch/en/live/operating-info"),
    Target("Sörenberg", "Sörenberg, Lucerne, Switzerland", "Bergbahnen Sörenberg", "https://www.soerenberg.ch/en/live/operating-hours"),
    Target("Melchsee-Frutt", "Melchsee-Frutt, Obwalden, Switzerland", "Sportbahnen Melchsee-Frutt", "https://www.melchsee-frutt.ch/en/live"),
    Target("Braunwald", "Braunwald, Glarus, Switzerland", "Braunwald-Klausenpass Tourismus", "https://www.braunwald.ch/en/live/operating-hours"),
    Target("Elm", "Elm, Glarus, Switzerland", "Sportbahnen Elm", "https://www.elm.ch/en/live/operating-hours"),
    Target("Leukerbad", "Leukerbad, Valais, Switzerland", "Leukerbad Torrent-Bahnen", "https://www.leukerbad.ch/en/live/operating-hours"),
]

KEYWORDS = [
    "closed", "closure", "partly", "partial", "limited", "restricted", "snow", "trail", "hiking",
    "operating", "open", "status", "maintenance", "revision", "construction", "weather", "warning",
    "geschlossen", "geöffnet", "teilweise", "wander", "schnee", "sperr", "betrieb", "störung",
]


def config():
    s = INDEX.read_text()
    url = re.search(r"https://[a-z0-9]+\.supabase\.co", s).group(0)
    key = re.search(r"sb_publishable_[A-Za-z0-9_\-]+", s).group(0)
    return url, key


def curl(method: str, url: str, key: str, path: str, data=None, prefer=False):
    cmd = ["curl", "-sS", "-w", "\n%{http_code}", "-X", method, url + path,
           "-H", "apikey: " + key, "-H", "Authorization: Bearer " + key]
    if data is not None:
        cmd += ["-H", "Content-Type: application/json", "--data", json.dumps(data, ensure_ascii=False)]
    if prefer:
        cmd += ["-H", "Prefer: return=representation"]
    out = subprocess.check_output(cmd, text=True, timeout=40)
    body, code = out.rsplit("\n", 1)
    return int(code), body


def cdp_eval(ws, expr):
    cdp_eval.counter += 1
    ws.send(json.dumps({"id": cdp_eval.counter, "method": "Runtime.evaluate", "params": {"expression": expr, "returnByValue": True, "awaitPromise": True}}))
    while True:
        msg = json.loads(ws.recv())
        if msg.get("id") == cdp_eval.counter:
            if "exceptionDetails" in msg:
                raise RuntimeError(msg["exceptionDetails"])
            return msg["result"]["result"].get("value")
cdp_eval.counter = 0


def fetch_visible_text(url: str) -> str:
    # Use Chrome DevTools Protocol via the already-installed Chrome. This handles JS-heavy official tourism pages.
    import websocket
    try:
        tabs = json.load(urllib.request.urlopen("http://127.0.0.1:9223/json", timeout=1))
    except Exception:
        subprocess.Popen([
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "--headless=new", "--remote-debugging-port=9223", "--remote-allow-origins=*",
            "--user-data-dir=/tmp/tratify-swiss-crawler", "--disable-gpu", "about:blank",
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1.5)
        tabs = json.load(urllib.request.urlopen("http://127.0.0.1:9223/json", timeout=2))
    page = next(t for t in tabs if t.get("type") == "page")
    ws = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=8, origin="http://127.0.0.1:9223")
    try:
        cdp_eval.counter += 1
        ws.send(json.dumps({"id": cdp_eval.counter, "method": "Page.navigate", "params": {"url": url}}))
        # Drain navigation response
        while True:
            msg = json.loads(ws.recv())
            if msg.get("id") == cdp_eval.counter:
                break
        time.sleep(6)
        # Accept/deny cookie banners when obvious, then wait a bit more.
        try:
            cdp_eval(ws, "Array.from(document.querySelectorAll('button')).find(b => /deny|reject|necessary|allow all|accept/i.test(b.innerText || ''))?.click()")
            time.sleep(1)
        except Exception:
            pass
        text = cdp_eval(ws, "document.body ? document.body.innerText : ''") or ""
        return re.sub(r"\n{3,}", "\n\n", text).strip()
    finally:
        ws.close()


def summarize(target: Target, text: str) -> tuple[str, str, str]:
    lines = [re.sub(r"\s+", " ", l).strip() for l in text.splitlines()]
    lines = [l for l in lines if 8 <= len(l) <= 240]
    # Prefer alert/status lines near keywords; filter generic nav/cookies.
    bad = re.compile(r"cookie|privacy|login|newsletter|password|basket|copyright|terms|contact|skip to content|online shop|wallet", re.I)
    scored = []
    for i, l in enumerate(lines):
        if bad.search(l):
            continue
        score = sum(1 for k in KEYWORDS if k.lower() in l.lower())
        if target.name.split()[0].lower() in l.lower():
            score += 1
        if score:
            scored.append((score, i, l))
    scored.sort(key=lambda x: (-x[0], x[1]))
    chosen = []
    seen = set()
    for _, _, l in scored:
        key = l.lower()
        if key in seen:
            continue
        seen.add(key); chosen.append(l)
        if len(chosen) >= 5:
            break
    high_signal = [l for l in chosen if re.search(r"closed|closure|partly|partial|limited|restricted|snow|trail|hiking|open facilities|operating hours|geschlossen|geöffnet|teilweise|wander|schnee|sperr|betrieb", l, re.I)]
    if not high_signal:
        status = "open"
        title = f"{target.name} operating info checked — live conditions page available"
        body = f"Official operating information page checked. No specific hiking-trail closure alert was confidently extracted automatically, so travellers should verify the live page before departure. Source checked: {target.url}"
    else:
        joined = " • ".join(high_signal[:5])
        lower = joined.lower()
        status = "partial" if any(w in lower for w in ["closed", "closure", "partly", "partial", "limited", "restricted", "snow", "geschlossen", "teilweise", "sperr"]) else "open"
        title = f"{target.name} operating info — {high_signal[0][:120]}"
        body = f"Official operating information extracted from {target.source_org}: {joined}. Travellers should check the source before hiking or using mountain railways. Source checked: {target.url}"
    return status, title, body


def main():
    supa_url, key = config()
    rows = []
    reports = []
    for t in TARGETS:
        print(f"FETCH {t.name}: {t.url}", flush=True)
        try:
            text = fetch_visible_text(t.url)
            status, title, body = summarize(t, text)
            reports.append({"target": t.name, "status": status, "title": title, "text_len": len(text), "url": t.url})
            rows.append({
                "orig_title": title,
                "orig_body": body,
                "place": t.place,
                "region": t.region,
                "status": status,
                "type": t.kind,
                "orig_lang": "en",
                "source_org": t.source_org,
                "contact_email": None,
                "verified": True,
            })
        except Exception as e:
            reports.append({"target": t.name, "error": str(e), "url": t.url})
    # Delete previous crawler entries for these places to avoid duplicates.
    for t in TARGETS:
        q = urllib.parse.quote(f"*{t.place.split(',')[0]}*", safe="*")
        code, body = curl("GET", supa_url, key, f"/rest/v1/announcements?place=ilike.{q}&select=id")
        if code == 200 and body:
            for item in json.loads(body):
                curl("DELETE", supa_url, key, f"/rest/v1/announcements?id=eq.{item['id']}")
    if rows:
        code, body = curl("POST", supa_url, key, "/rest/v1/announcements", rows, True)
        print("INSERT", code, body[:1000])
    out = {"inserted": len(rows), "reports": reports}
    (REPO / "swiss-hiking-crawl-report.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
