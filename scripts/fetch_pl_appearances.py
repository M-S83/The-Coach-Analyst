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

    # Fill gaps: UK-born PL players Wikidata lacked, placed on a birthplace already on the map.
    coords = {}
    for p in players:
        coords.setdefault(p["place"].lower(), (p["lat"], p["lon"]))
    added, unplaced = 0, {}
    for f in unmatched:
        nation = NATIONS.get(f.get("birth", {}).get("country", {}).get("isoCode", ""))
        if not nation:
            continue
        place = (f["birth"].get("place") or "").strip()
        c = coords.get(place.lower())
        dob = birth_date(f)
        if not (c and dob):
            unplaced[nation] = unplaced.get(nation, 0) + 1
            continue
        players.append({"id": "", "name": f["name"]["display"], "dob": dob, "place": place,
                        "lat": c[0], "lon": c[1], "pos": f.get("info", {}).get("positionInfo", ""),
                        "clubs": [], "nation": nation, "apps": apps[int(f["id"])], "src": "pl"})
        added += 1

    players.sort(key=lambda p: p["dob"])
    data["plCheck"] = {"registered": len(feed), "played": len(played), "matched": matched,
                       "addedFromFeed": added, "ukBornNotPlaced": unplaced}
    json.dump(data, open(PATH, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"Matched {matched}, added {added} from the feed, could not place {unplaced}", file=sys.stderr)


if __name__ == "__main__":
    main()
