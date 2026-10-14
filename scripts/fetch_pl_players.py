#!/usr/bin/env python3
"""Build footballers-map/data/players.json: every Premier League player born in the UK,
with date of birth and birthplace coordinates.

Sources (both free, CC0 / CC BY-SA):
  1. English Wikipedia "Category:Premier League players"  -> who has played in the PL
  2. Wikidata                                              -> date of birth, place of birth,
                                                              coordinates, home nation, position, clubs

Standard library only. Run:  python3 scripts/fetch_pl_players.py
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

UA = "TheCoachAnalyst-PLBirthplaces/1.0 (https://github.com/m-s83/the-coach-analyst)"
WIKI_API = "https://en.wikipedia.org/w/api.php"
SPARQL = "https://query.wikidata.org/sparql"
CATEGORY = "Category:Premier League players"
OUT = os.path.join(os.path.dirname(__file__), "..", "footballers-map", "data", "players.json")

NATIONS = {"Q21": "England", "Q22": "Scotland", "Q25": "Wales", "Q26": "Northern Ireland"}

# Every club that has played in the Premier League (English Wikipedia titles).
PL_CLUBS = [
    "AFC Bournemouth", "Arsenal F.C.", "Aston Villa F.C.", "Barnsley F.C.", "Birmingham City F.C.",
    "Blackburn Rovers F.C.", "Blackpool F.C.", "Bolton Wanderers F.C.", "Bradford City A.F.C.",
    "Brentford F.C.", "Brighton & Hove Albion F.C.", "Burnley F.C.", "Cardiff City F.C.",
    "Charlton Athletic F.C.", "Chelsea F.C.", "Coventry City F.C.", "Crystal Palace F.C.",
    "Derby County F.C.", "Everton F.C.", "Fulham F.C.", "Huddersfield Town A.F.C.", "Hull City A.F.C.",
    "Ipswich Town F.C.", "Leeds United F.C.", "Leicester City F.C.", "Liverpool F.C.", "Luton Town F.C.",
    "Manchester City F.C.", "Manchester United F.C.", "Middlesbrough F.C.", "Newcastle United F.C.",
    "Norwich City F.C.", "Nottingham Forest F.C.", "Oldham Athletic A.F.C.", "Portsmouth F.C.",
    "Queens Park Rangers F.C.", "Reading F.C.", "Sheffield United F.C.", "Sheffield Wednesday F.C.",
    "Southampton F.C.", "Stoke City F.C.", "Sunderland A.F.C.", "Swansea City A.F.C.",
    "Swindon Town F.C.", "Tottenham Hotspur F.C.", "Watford F.C.", "West Bromwich Albion F.C.",
    "West Ham United F.C.", "Wigan Athletic F.C.", "Wimbledon F.C.", "Wolverhampton Wanderers F.C.",
]


def get_json(url, data=None, tries=4):
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers={
                "User-Agent": UA, "Accept": "application/sparql-results+json, application/json"})
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)
        except Exception as e:  # network blip, 429, 5xx
            wait = 2 ** (attempt + 1)
            print(f"  retry in {wait}s ({e})", file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError(f"failed: {url[:120]}")


def sparql(query):
    body = urllib.parse.urlencode({"query": query, "format": "json"}).encode()
    res = get_json(SPARQL, data=body)
    time.sleep(1)  # be polite to the public endpoint
    return res["results"]["bindings"]


def category_titles():
    titles, cont = [], {}
    while True:
        params = {"action": "query", "list": "categorymembers", "cmtitle": CATEGORY,
                  "cmnamespace": 0, "cmlimit": 500, "format": "json", **cont}
        res = get_json(WIKI_API + "?" + urllib.parse.urlencode(params))
        titles += [m["title"] for m in res["query"]["categorymembers"]]
        if "continue" not in res:
            return titles
        cont = res["continue"]


def titles_to_qids(titles):
    qids = {}
    for i in range(0, len(titles), 50):
        params = {"action": "query", "prop": "pageprops", "ppprop": "wikibase_item", "redirects": 1,
                  "titles": "|".join(titles[i:i + 50]), "format": "json"}
        res = get_json(WIKI_API + "?" + urllib.parse.urlencode(params))
        for page in res["query"]["pages"].values():
            q = page.get("pageprops", {}).get("wikibase_item")
            if q:
                qids[q] = page["title"]
    return qids


def chunks(xs, n):
    for i in range(0, len(xs), n):
        yield xs[i:i + n]


def fetch_people(qids):
    people = {}
    for batch in chunks(qids, 150):
        values = " ".join("wd:" + q for q in batch)
        rows = sparql(f"""
SELECT ?p ?pLabel ?dob ?pob ?pobLabel ?coord ?posLabel WHERE {{
  VALUES ?p {{ {values} }}
  ?p wdt:P569 ?dob ; wdt:P19 ?pob .
  ?pob wdt:P625 ?coord .
  OPTIONAL {{ ?p wdt:P413 ?pos }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}""")
        for r in rows:
            q = r["p"]["value"].rsplit("/", 1)[1]
            if q in people:
                continue  # several DOB/POB/position values: keep the first
            lon, lat = r["coord"]["value"].removeprefix("Point(").rstrip(")").split()
            people[q] = {
                "id": q, "name": r["pLabel"]["value"], "dob": r["dob"]["value"][:10],
                "pobId": r["pob"]["value"].rsplit("/", 1)[1], "place": r["pobLabel"]["value"],
                "lat": round(float(lat), 4), "lon": round(float(lon), 4),
                "pos": r.get("posLabel", {}).get("value", ""), "clubs": [],
            }
        print(f"  people: {len(people)}", file=sys.stderr)
    return people


def classify_places(pob_ids):
    nation = {}
    for batch in chunks(sorted(pob_ids), 100):
        values = " ".join("wd:" + q for q in batch)
        rows = sparql(f"""
SELECT ?pob ?n WHERE {{
  VALUES ?pob {{ {values} }}
  VALUES ?n {{ wd:Q21 wd:Q22 wd:Q25 wd:Q26 }}
  ?pob wdt:P131* ?n .
}}""")
        for r in rows:
            nation[r["pob"]["value"].rsplit("/", 1)[1]] = NATIONS[r["n"]["value"].rsplit("/", 1)[1]]
    return nation


def fetch_clubs(people):
    titles = " ".join('"%s"@en' % t for t in PL_CLUBS)
    rows = sparql(f"""
SELECT ?club ?title WHERE {{
  VALUES ?title {{ {titles} }}
  ?article schema:about ?club ; schema:isPartOf <https://en.wikipedia.org/> ; schema:name ?title .
}}""")
    clubs = {r["club"]["value"].rsplit("/", 1)[1]: r["title"]["value"] for r in rows}
    missing = set(PL_CLUBS) - set(clubs.values())
    if missing:
        print(f"  clubs not found on Wikidata: {sorted(missing)}", file=sys.stderr)
    club_values = " ".join("wd:" + q for q in clubs)
    for batch in chunks(list(people), 100):
        values = " ".join("wd:" + q for q in batch)
        try:
            rows = sparql(f"""
SELECT ?p ?club ?start ?end WHERE {{
  VALUES ?p {{ {values} }}
  VALUES ?club {{ {club_values} }}
  ?p p:P54 ?st . ?st ps:P54 ?club .
  OPTIONAL {{ ?st pq:P580 ?start }} OPTIONAL {{ ?st pq:P582 ?end }}
}}""")
        except RuntimeError as e:  # club spells are a nice-to-have; keep going
            print(f"  skipped a club batch: {e}", file=sys.stderr)
            continue
        for r in rows:
            q = r["p"]["value"].rsplit("/", 1)[1]
            club = clubs[r["club"]["value"].rsplit("/", 1)[1]]
            for suffix in (" F.C.", " A.F.C."):
                club = club.removesuffix(suffix)
            spell = [club, r.get("start", {}).get("value", "")[:4], r.get("end", {}).get("value", "")[:4]]
            if spell not in people[q]["clubs"]:
                people[q]["clubs"].append(spell)


def nation_from_coords(lat, lon):
    """Rough fallback for UK birthplaces whose Wikidata entry lacks an admin-area chain."""
    if lon < -5.4 and 54.0 < lat < 55.4:
        return "Northern Ireland"
    if lat > 55.8 or (lat > 55.0 and lon < -2.6 and not (lat < 55.2 and lon > -3.1)):
        return "Scotland"
    # English-Welsh border as longitude steps, south to north
    border = -2.68 if lat < 51.85 else -3.05 if lat < 52.9 else -2.75 if lat < 53.1 else -3.0
    if 51.35 < lat < 53.45 and lon < border:
        return "Wales"
    return "England"


def uk_places(pob_ids):
    found = set()
    for batch in chunks(sorted(pob_ids), 150):
        values = " ".join("wd:" + q for q in batch)
        for r in sparql(f"SELECT ?pob WHERE {{ VALUES ?pob {{ {values} }} ?pob wdt:P17 wd:Q145 . }}"):
            found.add(r["pob"]["value"].rsplit("/", 1)[1])
    return found


def main():
    print("1/5 Category members...", file=sys.stderr)
    titles = category_titles()
    print(f"  {len(titles)} articles", file=sys.stderr)
    print("2/5 Wikidata IDs...", file=sys.stderr)
    qids = titles_to_qids(titles)
    print(f"  {len(qids)} linked to Wikidata", file=sys.stderr)
    print("3/5 Birth dates and places...", file=sys.stderr)
    people = fetch_people(list(qids))
    print("4/5 Home nation of each birthplace...", file=sys.stderr)
    nation = classify_places({p["pobId"] for p in people.values()})
    unclassified = {p["pobId"] for p in people.values()} - set(nation)
    fallback = uk_places(unclassified)
    print(f"  {len(fallback)} UK birthplaces placed by coordinates", file=sys.stderr)
    uk = {}
    for q, p in people.items():
        n = nation.get(p["pobId"])
        if not n and p["pobId"] in fallback:
            n = nation_from_coords(p["lat"], p["lon"])
            p["approxNation"] = True
        if n:
            p["nation"] = n
            uk[q] = p
    print(f"  {len(uk)} born in the UK", file=sys.stderr)
    print("5/5 Premier League club spells...", file=sys.stderr)
    fetch_clubs(uk)

    players = sorted(uk.values(), key=lambda p: p["dob"])
    for p in players:
        del p["pobId"]
    out = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "source": "Wikipedia 'Category:Premier League players' + Wikidata (CC0)",
        "categoryArticles": len(titles),
        "withWikidata": len(qids),
        "withBirthData": len(people),
        "players": players,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    by_nation = {}
    for p in players:
        by_nation[p["nation"]] = by_nation.get(p["nation"], 0) + 1
    print(f"Wrote {len(players)} players to {os.path.normpath(OUT)}: {by_nation}", file=sys.stderr)


if __name__ == "__main__":
    main()
