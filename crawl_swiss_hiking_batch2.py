#!/usr/bin/env python3
from crawl_swiss_hiking import Target, fetch_visible_text, summarize, config, curl
import json, urllib.parse
from pathlib import Path

REPO = Path(__file__).resolve().parent

TARGETS = [
    Target("Oeschinensee", "Oeschinensee / Kandersteg, Bernese Oberland, Switzerland", "Gondelbahn Kandersteg-Oeschinensee AG", "https://www.oeschinensee.ch/en/live/"),
    Target("Niesen", "Niesen, Bernese Oberland, Switzerland", "Niesenbahn AG", "https://www.niesen.ch/en/current/"),
    Target("Niederhorn", "Niederhorn / Beatenberg, Bernese Oberland, Switzerland", "Niederhornbahn AG", "https://www.niederhorn.ch/en/live/"),
    Target("Harder Kulm", "Harder Kulm / Interlaken, Bernese Oberland, Switzerland", "Jungfrau Railways", "https://www.jungfrau.ch/en-gb/harder-kulm/"),
    Target("Brienzer Rothorn", "Brienzer Rothorn, Bernese Oberland, Switzerland", "Brienz Rothorn Bahn AG", "https://brienz-rothorn-bahn.ch/en/timetable-prices/operating-information/"),
    Target("Rochers-de-Naye", "Rochers-de-Naye, Vaud, Switzerland", "MOB / Montreux Riviera", "https://www.mob.ch/en/pages/rochers-de-naye"),
    Target("Glacier 3000", "Glacier 3000 / Les Diablerets, Vaud/Bern, Switzerland", "Glacier 3000", "https://www.glacier3000.ch/en/information/opening-hours"),
    Target("Monte Generoso", "Monte Generoso, Ticino, Switzerland", "Ferrovia Monte Generoso", "https://www.montegeneroso.ch/en/timetables-and-prices"),
    Target("Cardada Cimetta", "Cardada Cimetta / Locarno, Ticino, Switzerland", "Cardada Impianti Turistici", "https://www.cardada.ch/en/opening-hours-prices"),
    Target("Monte San Salvatore", "Monte San Salvatore / Lugano, Ticino, Switzerland", "Funicolare Monte San Salvatore", "https://www.montesansalvatore.ch/en/timetable-prices/"),
    Target("Ebenalp", "Ebenalp / Appenzell, Switzerland", "Luftseilbahn Wasserauen-Ebenalp", "https://www.ebenalp.ch/en/live"),
    Target("Säntis", "Säntis / Schwägalp, Switzerland", "Säntis-Schwebebahn AG", "https://saentisbahn.ch/en/weather/"),
    Target("Hoher Kasten", "Hoher Kasten / Appenzell, Switzerland", "Hoher Kasten Drehrestaurant und Seilbahn AG", "https://www.hoherkasten.ch/en/live"),
    Target("Stanserhorn", "Stanserhorn, Nidwalden, Switzerland", "Stanserhorn-Bahn", "https://www.stanserhorn.ch/en/timetable/"),
    Target("Bürgenstock Hammetschwand", "Bürgenstock / Hammetschwand, Nidwalden, Switzerland", "Bürgenstock Resort / Hammetschwand Lift", "https://burgenstockresort.com/en/activities/hammetschwand-lift"),
    Target("Rochers-de-Naye", "Rochers-de-Naye / Montreux, Vaud, Switzerland", "MOB GoldenPass", "https://www.goldenpass.ch/en/goldenpass/offer/view?id=93"),
]

def main():
    supa_url, key = config()
    rows=[]; reports=[]
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
            for item in json.loads(body):
                curl("DELETE",supa_url,key,f"/rest/v1/announcements?id=eq.{item['id']}")
    if rows:
        code,body=curl("POST",supa_url,key,"/rest/v1/announcements",rows,True)
        print("INSERT",code,body[:1000])
    out={"inserted":len(rows),"reports":reports}
    (REPO/"swiss-hiking-crawl-report-batch2.json").write_text(json.dumps(out,ensure_ascii=False,indent=2))
    print(json.dumps(out,ensure_ascii=False,indent=2))

if __name__ == "__main__": main()
