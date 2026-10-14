# Born to Play: where Premier League players were born

An interactive 3D map of every Premier League player born in England (switch to all of the UK, Scotland, Wales or Northern Ireland), placed at their birthplace and coloured by birth decade.

- **Period**: one column per player, clustered around their birthplace and coloured by decade. Click a decade to isolate it. Click a cluster to list its players.
- **Hotspots**: players counted in ~20 km squares. Drag the timeline to compare generations.
- **Shift**: each square's *share* of players born before vs from a chosen year, to show which areas have grown or shrunk as sources of talent.
- **Timeline**: a histogram of birth years. Drag it to pick a window, or press ▶ to sweep through the decades.

## Data

`scripts/fetch_pl_players.py` builds `data/players.json` in four steps:

1. **Who counts as a PL player**: every article in English Wikipedia's [Category:Premier League players](https://en.wikipedia.org/wiki/Category:Premier_League_players).
2. **Date and place of birth**: from Wikidata (P569, P19), with the birthplace's coordinates (P625).
3. **Home nation**: whether the birthplace sits inside England, Scotland, Wales or Northern Ireland (P131 chain).
4. **Club spells**: at the 51 clubs that have played in the PL (P54, with start and end years where recorded).

The GitHub Action **Fetch PL birthplace data** runs the script and commits the result. Run it again from the Actions tab whenever you want fresh data. You can also run it locally with `python3 scripts/fetch_pl_players.py` (standard library only).

### Caveats

- A player is missing if their Wikidata entry has no birth date, no birthplace, or no coordinates for the birthplace. The JSON records how many fell out at each step.
- The birthplace is whatever was recorded. Often that's the town of the maternity hospital, not where the player grew up.
- Counts are raw, not adjusted for population, so big cities naturally dominate *Hotspots*. *Shift* compares shares between generations, which partly corrects for this.
- The PL started in 1992, so the oldest birth years (1950s–60s) are only veterans who were still playing then. Those decades are small by design.
