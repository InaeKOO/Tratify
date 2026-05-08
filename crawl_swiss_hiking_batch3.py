#!/usr/bin/env python3
from crawl_swiss_hiking import Target, fetch_visible_text, summarize, config, curl
import json, urllib.parse
from pathlib import Path
REPO = Path(__file__).resolve().parent
TARGETS = [
    Target("Männlichen", "Männlichen / Grindelwald-Wengen, Bernese Oberland, Switzerland", "Gondelbahn Grindelwald-Männlichen AG", "https://www.maennlichen.ch/en/live.html"),
    Target("Stockhorn", "Stockhorn, Bernese Oberland, Switzerland", "Stockhornbahn AG", "https://stockhorn.ch/en/live/"),
    Target("Wiriehorn", "Wiriehorn / Diemtigtal, Bernese Oberland, Switzerland", "Wiriehornbahnen AG", "https://www.wiriehorn.ch/en/live"),
    Target("Klewenalp-Stockhütte", "Klewenalp-Stockhütte, Nidwalden, Switzerland", "Bergbahnen Beckenried-Emmetten AG", "https://www.klewenalp.ch/en/live/operating-hours"),
    Target("Bannalp", "Bannalp, Nidwalden, Switzerland", "Luftseilbahnen Bannalp", "https://www.bannalp.ch/en/live/"),
    Target("Sattel-Hochstuckli", "Sattel-Hochstuckli, Schwyz, Switzerland", "Sattel-Hochstuckli AG", "https://www.sattel-hochstuckli.ch/en/live"),
    Target("Hoch-Ybrig", "Hoch-Ybrig, Schwyz, Switzerland", "Hoch-Ybrig AG", "https://www.hoch-ybrig.ch/en/live"),
    Target("Atzmännig", "Atzmännig, St. Gallen, Switzerland", "Atzmännig AG", "https://www.atzmaennig.ch/en/live"),
    Target("Chäserrugg Toggenburg", "Chäserrugg / Toggenburg, St. Gallen, Switzerland", "Toggenburg Bergbahnen AG", "https://chäserrugg.ch/en/live/"),
    Target("Wildhaus", "Wildhaus, St. Gallen, Switzerland", "Bergbahnen Wildhaus AG", "https://www.wildhaus.ch/en/live"),
    Target("Belalp", "Belalp, Valais, Switzerland", "Belalp Bahnen AG", "https://www.belalp.ch/en/live/operating-hours"),
    Target("Grächen", "Grächen, Valais, Switzerland", "Touristische Unternehmung Grächen AG", "https://www.graechen.ch/en/live/operating-hours"),
    Target("Nendaz", "Nendaz, Valais, Switzerland", "Nendaz Tourisme", "https://www.nendaz.ch/en/P87367/opening-status"),
    Target("Anzère", "Anzère, Valais, Switzerland", "Anzère Tourisme", "https://www.anzere.ch/en/live/"),
    Target("Leysin", "Leysin, Vaud, Switzerland", "Leysin Téléleysin", "https://www.alpesvaudoises.ch/en/stories/live-info"),
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
    (REPO/"swiss-hiking-crawl-report-batch3.json").write_text(json.dumps(out,ensure_ascii=False,indent=2))
    print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__ == "__main__": main()
