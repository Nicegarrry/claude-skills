# Learning journal

## 2026-09-20 — First run

**What dominated today:**
- Australian grid milestones completely dominated: renewables hit 80%+ of grid demand for the first time, Liddell BESS reached full commercial operation (400 MWh, 8-hour), and the "impossible" wind project closed finance. RenewEconomy delivered 6 of 15 kept items — highest yield by far.
- Storage risk was a counterpoint: Moss Landing caught fire again (second incident), raising systemic safety flags.
- Carbon Brief's macro calls (global fossil-fuel emissions falling in 2026 due to Hormuz; India emissions flat) were high-significance tier-1 signals.
- Tesla's $10.1B Texas solar gigafactory clearing its ITC qualification was a standalone US solar supply-chain story.

**Source performance:**
- RenewEconomy (AU): 10 fetched, 6 kept — best yield, AU-lens boost working as intended. Watch for over-representation if Australian news is slow.
- Carbon Brief: 4 fetched, 2 kept — very high yield rate; small volume but high signal. Core tier-1.
- Canary Media: 15 fetched, 2 kept — reasonable. Strong US grid/storage coverage.
- PV Magazine: 10 fetched, 2 kept — good signal density per fetch.
- Electrek: 40 fetched, 2 kept — high volume, low keep rate. Lots of consumer product news (reviews, deals, individual car models) that the investor lens demotes. Consider raising the bar for Electrek to reduce scoring work.
- CleanTechnica: 40 fetched, 0 kept — very high volume, minimal investor-lens signal. Consumer gadget + car review focus conflicts with Nick's profile. Candidate for removal or minimum tier-3 treatment.
- Euractiv (EU): 0 fetched — feed may be blocked or the default URL has changed; worth validating in an interactive run.
- DeSmog: 0 fetched — confirmed blocked from cloud/CI IPs per the existing note; fine from residential.
- Inside Climate News, Guardian, Grist, Yale E360, Dialogue Earth: fetched items but none cracked the top 15 under investor lens at significance floor 65. Not removal candidates — they regularly carry policy and macro stories that score above 65 in more active news cycles.

**Tuning applied:**
- None (first run, conservative).

**Proposed for next interactive run:**
- Validate Euractiv URL (0 fetched is unusual — possible 404 or rate limit).
- Consider setting CleanTechnica effective floor to 75 (investor lens rarely rewards its consumer-product volume).

---

## 2026-09-21 — Run 2

**What dominated today:**
- Critical minerals + supply chain: China's rare-earth stranglehold story (Guardian) scored highest (75) — Trump-Xi summit timing amplified relevance. Good signal from tier-1 source.
- Grid liability: SF6 super-pollutant from China's grid (Inside Climate News, 72) — novel regulatory risk angle, scored above threshold.
- Transport: Two EV stories above floor — China 65% market share (CleanTechnica, 70) and Sunwoda 9-min flash charge (Electrek, 68). Transport skews heavy today; Australia-specific EV/solar was quiet.
- Policy (AU): QLD coal mine abandonment (Guardian, 68) — stranded asset/rehabilitation liability angle landed just above floor with AU boost.
- Marginal: US diesel $10/gal (Electrek, 67) — kept as 6th item, not included in 5-bullet block.

**Source performance:**
- Inside Climate News: 4 new items, 1 kept (SF6 story) — reasonable yield. Whitehouse political messaging pieces (2 items) correctly demoted.
- The Guardian: 4 new items, 2 kept — solid. 2 off-topic items (quoll survey, sea dragon die-off) correctly dropped.
- CleanTechnica: 4 new, 1 kept — drone agriculture + Elon documentary + battery chemistry debate correctly demoted; China EV sales kept.
- Electrek: 5 new, 2 kept — Tesla Roadster deposits and Cadillac Down Under launch correctly demoted as consumer/car review. Sunwoda and diesel shock kept.
- RenewEconomy (AU): 0 new items this run — all content already seen. Will yield again when AU news cycle refreshes.
- Carbon Brief, PV Magazine, Canary Media, Utility Dive, Yale: 0 new items this run (all previously ingested).
- Euractiv, DeSmog: still 0 fetched — cloud environment confirmed as the cause per run-1 diagnosis.

**Tuning applied:**
- None (conservative second run; proposals from run 1 not yet confirmed interactive).

**Proposed for next interactive run:**
- Euractiv and DeSmog still blocked from this environment — confirm residential IP works, then validate.
- Consider proposing CleanTechnica effective floor raise to 75 if consumer-product bias continues.
