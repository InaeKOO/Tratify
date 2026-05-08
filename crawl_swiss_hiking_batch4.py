#!/usr/bin/env python3
from crawl_swiss_hiking import Target, fetch_visible_text, summarize, config, curl
import json, urllib.parse
from pathlib import Path
REPO = Path(__file__).resolve().parent
TARGETS = [
    Target("Kronberg", "Kronberg / Appenzell, Switzerland", "Luftseilbahn Jakobsbad-Kronberg AG", "https://www.kronberg.ch/en/live"),
    Target("Flumserberg Prodalp", "Flumserberg / Prodalp, St. Gallen, Switzerland", "Bergbahnen Flumserberg", "https://www.flumserberg.ch/en/Live/Facilities"),
    Target("Moleson", "Moléson, Fribourg, Switzerland", "Moléson - La Gruyère", "https://www.moleson.ch/en/live"),
    Target("Charmey", "Charmey, Fribourg, Switzerland", "TéléCharmey SA", "https://www.charmey.ch/en/live"),
    Target("Les Diablerets", "Les Diablerets, Vaud, Switzerland", "Alpes Vaudoises", "https://www.alpesvaudoises.ch/en/stories/live-info"),
    Target("Villars-Gryon", "Villars-Gryon, Vaud, Switzerland", "Villars-Gryon-Diablerets", "https://www.alpesvaudoises.ch/en/stories/live-info"),
    Target("Sainte-Croix Les Rasses", "Sainte-Croix / Les Rasses, Vaud, Switzerland", "Yverdon-les-Bains Région", "https://www.yverdonlesbainsregion.ch/en/Z13117/live-info"),
    Target("Sattel Mostelberg", "Mostelberg / Sattel, Schwyz, Switzerland", "Sattel-Hochstuckli AG", "https://www.sattel-hochstuckli.ch/en/live"),
    Target("Marbachegg", "Marbachegg, Lucerne, Switzerland", "Sportbahnen Marbachegg AG", "https://www.marbachegg.ch/en/live"),
    Target("Wirzweli", "Wirzweli, Nidwalden, Switzerland", "Luftseilbahn Dallenwil-Wirzweli AG", "https://www.wirzweli.ch/en/live"),
    Target("Rosswald", "Rosswald, Valais, Switzerland", "Rosswald Bahnen AG", "https://www.rosswald.ch/en/live"),
    Target("Bettmeralp", "Bettmeralp / Aletsch Arena, Valais, Switzerland", "Aletsch Arena AG", "https://www.aletscharena.ch/en/aletsch-arena/interactive/operating-status"),
    Target("Riederalp", "Riederalp / Aletsch Arena, Valais, Switzerland", "Aletsch Arena AG", "https://www.aletscharena.ch/en/aletsch-arena/interactive/operating-status"),
    Target("Sörenberg Brienzer Rothorn", "Sörenberg / Brienzer Rothorn, Lucerne, Switzerland", "Bergbahnen Sörenberg", "https://www.soerenberg.ch/en/live/operating-hours"),
    Target("Kandersteg Sunnbüel", "Sunnbüel / Kandersteg, Bernese Oberland, Switzerland", "Luftseilbahn Kandersteg-Sunnbüel", "https://www.sunnbuel.ch/en/live"),
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
    (REPO/"swiss-hiking-crawl-report-batch4.json").write_text(json.dumps(out,ensure_ascii=False,indent=2))
    print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__ == "__main__": main()
