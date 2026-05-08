#!/usr/bin/env python3
from crawl_swiss_hiking import Target, fetch_visible_text, summarize, config, curl
import json, urllib.parse
from pathlib import Path
REPO = Path(__file__).resolve().parent
TARGETS = [
    Target("Savognin", "Savognin, Graubünden, Switzerland", "Savognin Bergbahnen", "https://www.valsurses.ch/en/live"),
    Target("Obersaxen Mundaun", "Obersaxen Mundaun, Graubünden, Switzerland", "Bergbahnen Obersaxen Mundaun", "https://www.obersaxen-mundaun.ch/en/live"),
    Target("Brigels Waltensburg Andiast", "Brigels Waltensburg Andiast, Graubünden, Switzerland", "Bergbahnen Brigels", "https://www.brigels-bergbahnen.ch/en/live"),
    Target("Scuol Motta Naluns", "Scuol / Motta Naluns, Graubünden, Switzerland", "Bergbahnen Scuol", "https://www.scuol-bergbahnen.ch/en/live"),
    Target("Samnaun", "Samnaun, Graubünden, Switzerland", "Bergbahnen Samnaun", "https://www.samnaun.ch/en/Service/Live"),
    Target("Airolo Pesciüm", "Airolo Pesciüm, Ticino, Switzerland", "Airolo Pesciüm", "https://www.airolo.ch/en/live"),
    Target("Bosco Gurin", "Bosco Gurin, Ticino, Switzerland", "Grossalp SA Bosco Gurin", "https://www.bosco-gurin.ch/en/live"),
    Target("Nara", "Nara / Leontica, Ticino, Switzerland", "Impianti turistici Nara", "https://www.nara.ch/en/live"),
    Target("Carì", "Carì, Ticino, Switzerland", "Funivia Carì", "https://www.cari.swiss/en/live"),
    Target("Weissenstein", "Weissenstein, Solothurn, Switzerland", "Seilbahn Weissenstein AG", "https://www.seilbahn-weissenstein.ch/en/live"),
    Target("Balmberg", "Balmberg, Solothurn, Switzerland", "Balmberg Tourismus", "https://www.balmberg.ch/"),
    Target("Toggenburg Alt St. Johann", "Alt St. Johann / Toggenburg, St. Gallen, Switzerland", "Toggenburg Bergbahnen AG", "https://www.toggenburg.swiss/en/live"),
]

def main():
    supa_url,key=config(); rows=[]; reports=[]
    for t in TARGETS:
        print(f"FETCH {t.name}: {t.url}", flush=True)
        try:
            text=fetch_visible_text(t.url)
            status,title,body=summarize(t,text)
            reports.append({"target":t.name,"status":status,"title":title,"text_len":len(text),"url":t.url})
            rows.append({"orig_title":title,"orig_body":body,"place":t.place,"region":t.region,"status":status,"type":t.kind,"orig_lang":"en","source_org":t.source_org,"contact_email":None,"verified":True})
        except Exception as e:
            reports.append({"target":t.name,"error":str(e),"url":t.url})
    for t in TARGETS:
        q=urllib.parse.quote(f"*{t.place.split(',')[0]}*",safe="*")
        code,body=curl("GET",supa_url,key,f"/rest/v1/announcements?place=ilike.{q}&select=id")
        if code==200 and body:
            for item in json.loads(body): curl("DELETE",supa_url,key,f"/rest/v1/announcements?id=eq.{item['id']}")
    if rows:
        code,body=curl("POST",supa_url,key,"/rest/v1/announcements",rows,True)
        print("INSERT",code,body[:1000])
    out={"inserted":len(rows),"reports":reports}
    (REPO/"swiss-hiking-crawl-report-batch5.json").write_text(json.dumps(out,ensure_ascii=False,indent=2))
    print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__ == "__main__": main()
