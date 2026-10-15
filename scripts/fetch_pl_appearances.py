#!/usr/bin/env python3
"""Add career Premier League appearances to footballers-map/data/players.json.

Source: the public stats feed behind premierleague.com (footballapi.pulselive.com).
  1. List every player registered in each PL season since 1992/93.
  2. Fetch each player's PL appearance total.
  3. Match to the Wikidata players by date of birth and surname.
England-born PL players the feed knows about but Wikidata missed are added when their
birthplace name matches a place already on the map; the rest are counted in "plCheck".

Run after fetch_pl_players.py. Standard library only.
"""
import json
import os
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

API = "https://footballapi.pulselive.com/football"
HEADERS = {"Origin": "https://www.premierleague.com", "Referer": "https://www.premierleague.com/",
           "User-Agent": "Mozilla/5.0 (TheCoachAnalyst PL birthplace map)", "Accept": "application/json"}
PATH = os.path.join(os.path.dirname(__file__), "..", "footballers-map", "data", "players.json")
NATIONS = {"GB-ENG": "England", "GB-SCT": "Scotland", "GB-WLS": "Wales", "GB-NIR": "Northern Ireland"}


def get(path, **params):
    url = f"{API}/{path}?{urllib.parse.urlencode(params)}"
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=60) as r:
                return json.load(r)
        except Exception as e:
            time.sleep(2 ** (attempt + 1))
            last = e
    raise RuntimeError(f"{url}: {last}")


def seasons():
    res = get("competitions/1/compseasons", page=0, pageSize=100)
    return [int(s["id"]) for s in res["content"]]


def season_players(cs):
    out, page = [], 0
    while True:
        res = get("players", compSeasons=cs, pageSize=100, page=page, type="player", altIds="true")
        out += res["content"]
        page += 1
        if page >= res["pageInfo"]["numPages"]:
            return out


def appearances(pid):
    try:
        res = get(f"stats/player/{pid}", comps=1)
    except RuntimeError as e:
        print(f"  no stats for {pid}: {e}", file=sys.stderr)
        return pid, None
    stats = {s["name"]: s["value"] for s in res.get("stats", [])}
    return pid, int(stats.get("appearances", 0))


def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return "".join(c if c.isalnum() else " " for c in s).split()


def birth_date(p):
    millis = p.get("birth", {}).get("date", {}).get("millis")
    if millis is None:
        return None
    # dates are local midnight; shift half a day so BST/GMT offsets land on the right day
    return datetime.fromtimestamp(millis / 1000 + 43200, tz=timezone.utc).strftime("%Y-%m-%d")


def main():
    data = json.load(open(PATH, encoding="utf-8"))
    players = data["players"]

    print("1/3 Premier League seasons and squads...", file=sys.stderr)
    feed = {}
    ids = seasons()
    for cs in ids:
        for p in season_players(cs):
            feed[int(p["id"])] = p
        print(f"  season {cs}: {len(feed)} players so far", file=sys.stderr)

    print("2/3 Appearance totals...", file=sys.stderr)
    with ThreadPoolExecutor(6) as pool:
        apps = dict(pool.map(appearances, feed))
    played = {pid for pid, n in apps.items() if n}
    print(f"  {len(played)} of {len(feed)} registered players made a PL appearance", file=sys.stderr)

    print("3/3 Matching to Wikidata players...", file=sys.stderr)
    by_dob = {}
    for p in players:
        by_dob.setdefault(p["dob"], []).append(p)
    matched, unmatched = 0, []
    for pid in played:
        f = feed[pid]
        dob = birth_date(f)
        cands = by_dob.get(dob, [])
        name = f.get("name", {})
        surname = set(norm(name.get("last", "")) + norm(name.get("display", ""))[-1:])
        hit = [c for c in cands if surname & set(norm(c["name"]))]
        if not hit:  # known-as names ("Ashley Young" vs a full legal surname): any name word in common
            words = set(norm(" ".join(str(v) for v in name.values()))) - {"de", "van", "da", "jr"}
            hit = [c for c in cands if words & set(norm(c["name"]))]
        if len(hit) == 1:
            hit[0]["apps"] = max(apps[pid], hit[0].get("apps", 0))
            matched += 1
        else:
            unmatched.append(f)

    # Pass 2: feed records often lack a birth date (mostly early-90s players), so match the
    # remaining UK-born Wikidata players by full name, allowing a missing or slightly different date.
    left = [p for p in players if p.get("apps") is None]
    by_surname = {}
    for f in unmatched:
        toks = norm(f.get("name", {}).get("display", ""))
        if toks:
            by_surname.setdefault(toks[-1], []).append(f)
    rescued = set()
    for p in left:
        toks = norm(p["name"])
        if not toks:
            continue
        cands = []
        for f in by_surname.get(toks[-1], []):
            ft = norm(f["name"]["display"])
            if ft[0][0] != toks[0][0]:  # first initial must agree
                continue
            fd = birth_date(f)
            if fd and not close_dates(fd, p["dob"]):
                continue
            cands.append(f)
        if len(cands) > 1:  # prefer an exact first name
            cands = [f for f in cands if norm(f["name"]["display"])[0] == toks[0]] or cands
        if len(cands) == 1 and int(cands[0]["id"]) not in rescued:
            p["apps"] = apps[int(cands[0]["id"])]
            rescued.add(int(cands[0]["id"]))
    unmatched = [f for f in unmatched if int(f["id"]) not in rescued]
    # Some old feed records carry a wrong birth date entirely, so also accept a name that is
    # unique on both sides: same surname, and one first name a prefix of the other (Mick/Micky).
    def key(name):
        t = norm(name)
        return (t[-1], t[0]) if len(t) > 1 else None
    left = [p for p in players if p.get("apps") is None]
    for p in left:
        k = key(p["name"])
        if not k:
            continue
        fs = [f for f in unmatched if (fk := key(f["name"]["display"])) and fk[0] == k[0]
              and (fk[1].startswith(k[1]) or k[1].startswith(fk[1]))]
        ps = [q for q in left if (qk := key(q["name"])) and qk[0] == k[0]
              and (qk[1].startswith(k[1]) or k[1].startswith(qk[1]))]
        if len(fs) == 1 and len(ps) == 1 and int(fs[0]["id"]) not in rescued:
            p["apps"] = apps[int(fs[0]["id"])]
            rescued.add(int(fs[0]["id"]))
    unmatched = [f for f in unmatched if int(f["id"]) not in rescued]
    print(f"  passes 2 matched {len(rescued)} more by name", file=sys.stderr)

    # Pass 3: UK-born PL players Wikidata lacked. Place them by looking up their birthplace name.
    coords = {p["place"].lower(): (p["lat"], p["lon"]) for p in players}
    uk_left = [f for f in unmatched if NATIONS.get(f.get("birth", {}).get("country", {}).get("isoCode", ""))]
    # The feed's "country" is nationality for many older players and its place is often blank,
    # so read the birthplace from the player's Wikipedia infobox instead whenever it is blank.
    for f in uk_left:
        if not (f["birth"].get("place") or "").strip():
            place, nation = wikipedia_birthplace(f["name"]["display"], birth_date(f))
            f["birth"]["place"] = place
            f["wikiNation"] = nation  # None means not born in the UK, or unknown
    uk_left = [f for f in uk_left if f.get("wikiNation", "?")]
    names = {(f["birth"].get("place") or "").strip() for f in uk_left} - {""}
    coords.update(geocode([n for n in names if n.lower() not in coords]))
    added, gaps_unplaced = 0, []
    for f in uk_left:
        nation = f.get("wikiNation") or NATIONS[f["birth"]["country"]["isoCode"]]
        place = (f["birth"].get("place") or "").strip()
        c = coords.get(place.lower()) or coords.get(place.split(",")[0].strip().lower())
        dob = birth_date(f)
        if not (c and dob):
            gaps_unplaced.append({"name": f["name"]["display"], "dob": dob, "place": place, "nation": nation,
                                  "apps": apps[int(f["id"])], "why": "no birth date in feed" if not dob else "birthplace not found"})
            continue
        players.append({"id": "", "name": f["name"]["display"], "dob": dob, "place": place.split(",")[0].strip(),
                        "lat": c[0], "lon": c[1], "pos": f.get("info", {}).get("positionInfo", ""),
                        "clubs": [], "nation": nation, "apps": apps[int(f["id"])], "src": "pl"})
        added += 1

    players.sort(key=lambda p: p["dob"])
    def why(p):
        k = key(p["name"])
        fs = [f for f in feed.values() if k and (fk := key(f["name"]["display"])) and fk[0] == k[0]
              and (fk[1].startswith(k[1]) or k[1].startswith(fk[1]))]
        if not fs:
            return "not in the Premier League feed"
        with_apps = [f for f in fs if apps.get(int(f["id"]))]
        if not with_apps:
            return "in the feed with no appearances recorded"
        if len(with_apps) > 1:
            return "several feed players share this name"
        return f"feed birth date differs ({birth_date(with_apps[0])})"
    gaps_noapps = [{"name": p["name"], "dob": p["dob"], "place": p["place"], "nation": p["nation"], "id": p["id"],
                    "why": why(p)} for p in players if p.get("apps") is None]
    data["plCheck"] = {"registered": len(feed), "played": len(played), "matchedByDate": matched,
                       "matchedByName": len(rescued), "addedFromFeed": added,
                       "noAppearanceTotal": len(gaps_noapps), "notPlaced": len(gaps_unplaced)}
    json.dump(data, open(PATH, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    with open(os.path.join(os.path.dirname(PATH), "gaps.json"), "w", encoding="utf-8") as fh:
        json.dump({"noAppearanceTotal": gaps_noapps, "notPlaced": gaps_unplaced}, fh, ensure_ascii=False, indent=1)
    print(f"  {data['plCheck']}", file=sys.stderr)


def wikipedia_birthplace(name, dob):
    """(place, nation) from the infobox of the player's English Wikipedia article, or ("", None)."""
    api = "https://en.wikipedia.org/w/api.php"
    ua = {"User-Agent": "TheCoachAnalyst-PLBirthplaces/1.0 (https://github.com/m-s83/the-coach-analyst)"}
    def call(**params):
        url = api + "?" + urllib.parse.urlencode({"format": "json", **params})
        with urllib.request.urlopen(urllib.request.Request(url, headers=ua), timeout=60) as r:
            return json.load(r)
    try:
        hits = call(action="query", list="search", srsearch=f'"{name}" footballer', srlimit=5)["query"]["search"]
        for h in hits:
            text = call(action="parse", page=h["title"], prop="wikitext", formatversion=2)["parse"]["wikitext"]
            if "birth_place" not in text or (dob and dob[:4] not in text[:3000]):
                continue  # not this player's article
            m = re.search(r"\|\s*birth_place\s*=\s*(.+)", text)
            raw = m.group(1) if m else ""
            raw = re.sub(r"<ref.*?(/>|</ref>)", "", raw)
            raw = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", raw)
            raw = re.sub(r"\{\{.*?\}\}|<[^>]+>", "", raw).strip(" ,|")
            nation = next((n for n in ("Northern Ireland", "England", "Scotland", "Wales") if n in raw), None)
            time.sleep(0.3)
            return raw.split(",")[0].strip(), nation
    except Exception as e:
        print(f"  wikipedia lookup failed for {name}: {e}", file=sys.stderr)
    return "", None


def close_dates(a, b):
    """Same date, day and month swapped, or within a year (typo-level differences)."""
    if a == b or (a[:4] == b[:4] and a[5:7] == b[8:10] and a[8:10] == b[5:7]):
        return True
    if a[:4] == b[:4] and a[8:] == b[8:] and abs(int(a[5:7]) - int(b[5:7])) == 1:
        return True  # the feed has some dates a month out
    return abs(int(a[:4]) - int(b[:4])) <= 1 and a[5:] == b[5:]


def geocode(names):
    """Birthplace name -> (lat, lon) via Wikidata: the best-known UK place with that exact English label."""
    tried = {}
    for n in names:
        for v in (n, n.split(",")[0].strip(), n.removesuffix(", England").strip()):
            tried.setdefault(v, n)
    found = {}
    keys = list(tried)
    for i in range(0, len(keys), 80):
        values = " ".join('"%s"@en' % k.replace('"', '') for k in keys[i:i + 80])
        query = f"""SELECT ?name ?c ?links WHERE {{
  VALUES ?name {{ {values} }}
  ?place rdfs:label ?name ; wdt:P17 wd:Q145 ; wdt:P625 ?c ; wikibase:sitelinks ?links .
}}"""
        body = urllib.parse.urlencode({"query": query, "format": "json"}).encode()
        req = urllib.request.Request("https://query.wikidata.org/sparql", data=body, headers={
            "User-Agent": "TheCoachAnalyst-PLBirthplaces/1.0 (https://github.com/m-s83/the-coach-analyst)",
            "Accept": "application/sparql-results+json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                rows = json.load(r)["results"]["bindings"]
        except Exception as e:
            print(f"  geocode batch failed: {e}", file=sys.stderr)
            continue
        best = {}
        for r in rows:
            name, links = r["name"]["value"], int(r["links"]["value"])
            if links > best.get(name, (-1,))[0]:
                lon, lat = r["c"]["value"].removeprefix("Point(").rstrip(")").split()
                best[name] = (links, round(float(lat), 4), round(float(lon), 4))
        for name, (_, lat, lon) in best.items():
            found.setdefault(tried[name].lower(), (lat, lon))
        time.sleep(1)
    print(f"  geocoded {len(found)} of {len(names)} new birthplace names", file=sys.stderr)
    return found


if __name__ == "__main__":
    main()
