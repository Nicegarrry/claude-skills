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

## 2026-09-22 — Run 3

**What dominated today:**
- AU storage + grid: RenewEconomy delivered 5 kept items out of 10 fetched — the strongest single-run yield of any source across all 3 runs. Stories: AU home battery $78.5M raise (80), Intergenerational Report fossil fuel outlook (77), Victoria coal-country BESS commissioning (77), 2 GW WA hybrid project EPBC approval (77), offshore wind transmission route (75). AU signal was genuinely dense today; AU +5 boost correctly elevated all five.
- Electrek's one kept item (Tesla/Sunrun 580 MW VPP, 76) was the only strong US grid-services story. The other 9 Electrek items were consumer product reviews, deals, and lifestyle content — confirmed as low investor-lens yield.
- Utility Dive delivered 3 strong kept items (Solar for All reinstatement, NY transmission approval, Texas PUC softened data-centre rules) from 7 new non-sponsored items — solid tier-2 yield.
- PV Magazine: 3 kept (US 100 GW production milestone 73, 33.3% perovskite-silicon tandem 72, Canada anti-dumping rescinded 70) from 10 new items. Good signal density.
- Canary Media: 2 kept (Ohio 800 MW solar+BESS permit 73, Duke Energy gas plant rejection 72) from 2 substantive items (1 how-to guide correctly dropped).
- Carbon Brief, Inside Climate News, Guardian: 0 kept items this run. All new content was climate-science / nature / policy stories (El Niño record, planetary boundaries, drought) that score well for science but don't clear the investor-lens floor at 65.
- Grist, Dialogue Earth, Euractiv, DeSmog: 0 kept (last two still blocked from cloud environment).

**Source performance (run 3 only):**
- RenewEconomy (AU): 10 fetched, 5 kept (50% keep rate) — highest ever single-run yield. Dominant today; no concern as AU news was genuinely busy.
- PV Magazine: 10 fetched, 3 kept (30% keep rate) — excellent signal density per item.
- Utility Dive: 7 non-sponsored fetched, 3 kept (43% keep rate) — best US grid/policy yield.
- Canary Media: 3 fetched, 2 kept (67%) — highest hit rate of any source.
- Electrek: 10 fetched, 1 kept (10%) — confirmed pattern of consumer-product dominance vs investor signal. Consider raising effective floor to 72 for Electrek items.
- CleanTechnica: 6 new fetched, 0 kept after dedup (Solar for All story duped with Utility Dive). Consumer product and political commentary items still dominate.
- Carbon Brief, Inside Climate News, Guardian: low investor signal today (climate-science focus cycle). Not a removal concern — pattern consistent with news cycle.

**Tuning applied:**
- None (conservative third run; source proposals from run 1–2 not yet confirmed interactive).

**Proposed for next interactive run:**
- Raise Electrek effective significance floor to 72: over 3 runs it has fetched 55 items, kept 5 (9% rate); all 5 kept items needed to be genuinely exceptional to clear. Raising the bar reduces scoring noise without material quality loss.
- CleanTechnica removal still under consideration: 50 fetched across 3 runs, 1 kept (2% rate). Run 1 proposed this; run 3 confirms the pattern. Recommend removal or tier-3 treatment (score a sample only).
- Euractiv and DeSmog both still 0 fetched across all 3 cloud runs — confirm residential IP works, then validate URLs. If residential also fails, drop DeSmog; try alternate Euractiv URL.

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

---

## 2026-09-23 — Run 4

**What dominated today:**
- AU grid + wind: RenewEconomy delivered 5 kept items out of 8 fetched (63% keep rate, highest single-run rate across all sources across all 4 runs). Stories: AU renewables penetration record (76), impossible wind project breaks investment drought (76), biggest coal project approval vs Albanese climate speech contradiction (74), VIC Labor BYO renewables for data centres (72), wind turbine extra-long blades cost reduction (71). AU signal genuinely dense again.
- Storage economics: RMI's 30% battery growth + lower cost story (78) was the top US signal today — confirms storage has crossed the competitiveness threshold. NC Duke Energy gas peaker blocked by regulator on cost grounds (75) reinforces the same thesis from the demand side.
- Solar manufacturing: IRA capex $12.2B by end 2026 (78) — the strongest solar story of the 4-run series so far; domestic US supply chain is now locked in.
- Transport: Geely's 2.2MW / 4-minute charger (72) is a genuine breakthrough. VW cutting ICE production shifts (73) is the strongest OEM transition signal seen yet.
- Climate-finance: Canary Media's US utilities failing grade (73) provides a sector-wide ESG signal; interesting for portfolio screening.
- Court win for Solar for All grants (73, Inside Climate News) — IRA legal risk lower than feared.
- Canary Media delivered 2/2 kept items (100% this run) — consistently high signal density. Consider tier 1 treatment.

**Source performance (run 4 only):**
- RenewEconomy (AU): 8 fetched, 5 kept (63%) — dominant run. High AU news density is cyclical; watch whether this persists or regresses next run.
- Canary Media: 2 fetched, 2 kept (100%) — perfect hit rate this run, 6/20 cumulative (30%). Strongest US-investor-lens source. 
- PV Magazine: 10 fetched, 3 kept (30%) — consistent. Good signal density without the consumer-product noise of Electrek.
- Utility Dive: 5 fetched, 2 kept (40%) — solid; grid/policy angle consistently investor-relevant.
- Electrek: 13 fetched, 2 kept (15%) — lower hit rate than run 3 (1/10 was already an outlier run). Cumulative 7/68 (10%) — Electrek consumer-product dominance is confirmed across 4 runs.
- CleanTechnica: 15 fetched, 0 kept (0%) — cumulative 1/65 (1.5%). Four runs without meaningful investor signal. Ready for removal recommendation.
- Grist: 4 fetched, 0 kept (0%) — cumulative 0/19. No investor signal across 4 runs. Ready for removal recommendation.
- The Guardian, Carbon Brief, Inside Climate News: low kept rates but not removal candidates — these are climate-science / policy cycles; signal appears in batches. Keep.
- Euractiv (EU), DeSmog: still 0 fetched in 4 consecutive cloud runs. Structural block, not news cycle.

**Tuning applied:**
- None (conservative; interactive confirmation required before any structural changes).

**Proposed for next interactive run:**
- Remove CleanTechnica: 65 fetched, 1 kept (1.5%) across 4 runs. Consumer-product and op-ed dominance is persistent; investor-signal items appear (if at all) in Inside Climate News or Utility Dive first.
- Remove Grist: 19 fetched, 0 kept (0%) across 4 runs. Environmental science / narrative journalism, not investor-signal news.
- Validate Euractiv + DeSmog from a residential IP. If both still 0 fetched, drop DeSmog; try alternate Euractiv URL.
- Raise Electrek effective significance floor to 73 (from default 65): cumulative 10% keep rate over 4 runs; kept items are exceptional — just need a higher bar to trim the 90% that doesn't land.
- Consider promoting Canary Media to tier 1: 30% cumulative keep rate (6/20), 100% this run. Strongest US investor-lens source in the stack.
