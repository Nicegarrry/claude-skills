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

---

## 2026-09-27 — Run 6

**What dominated today:**
- US solar supply chain shock: Anza's 40% module price spike projection from Section 232 tariffs (78) was the top-scoring story. Concurrent with Growatt's 10% inverter/battery price increase, this points to converging cost pressures on US and global solar+storage project economics — a theme worth tracking over next 2–3 runs.
- AU storage economics confirmed: RenewEconomy data showing batteries displacing gas as the "biggest loser" in the NEM (76) and Snowy 2.0 foundations poured (78) were both high-signal AU grid stories. AU news cycle dense again.
- IRA capital de-risked: Second federal court reinstating Solar for All (76) strengthens the thesis that IRA programs survive legal challenge — useful signal for investors in US clean energy that were discounting IRA exposure.
- China market design: Chinese province spot-market mechanism for grid-side BESS (74) is a leading indicator worth following. If it scales nationally, it changes the merchant-BESS economics globally.
- ESG lock-in risk: Texas utility gas-only plan for Meta's $10B data centre (72) is a direct illustration of how hyperscale demand growth is being captured by gas in deregulated markets.

**Source performance (run 6):**
- RenewEconomy (AU): 10 fetched, 6 kept (60%) — cumulative 48 fetched, 28 kept (58%). Dominant and consistent.
- PV Magazine: 10 fetched, 3 kept (30%) — cumulative 50 fetched, 14 kept (28%). Reliable signal density; two stories today linked to tariff/cost pressures.
- Utility Dive: 3 new fetched (after dedup), 1 kept (33%) — Solar for All second ruling.
- Electrek: 18 new fetched, 1 kept (6%) — Tesla Semi volume production kept; all others consumer product news (car reviews, VW discounts, charging deals). Cumulative 110 fetched, 8 kept (7%). Proposed floor raise to 73 now even more justified.
- Inside Climate News: 7 new fetched, 1 kept (14%) — Meta data centre gas story. Science/health/nature stories dropped.
- CleanTechnica: 15 new fetched, 1 kept (7%) — NYC Comptroller $5B climate investment (from Sierra Club piece). Cumulative 101 fetched, 2 kept (2%). Removal still warranted; that kept item was a climate-finance brief, not CleanTechnica original content.
- Carbon Brief, The Guardian, Grist, Yale, Canary Media, Dialogue Earth: all 0 new items this run (full dedup against prior runs).
- Euractiv (EU), DeSmog: still 0 fetched, 6 consecutive cloud runs.

**Tuning applied:**
- None (conservative; pending interactive confirmation from prior proposals).

**Proposed for next interactive run (cumulative):**
- Remove CleanTechnica: 101 fetched, 2 kept (2%) across 6 runs.
- Remove Grist: 31 fetched, 0 kept (0%) across 6 runs.
- Raise Electrek effective significance floor to 73: 110 fetched, 8 kept (7%), confirmed consumer-product dominance.
- Validate Euractiv and DeSmog from residential IP: 0 fetched for 6 straight cloud runs is structural.
- Consider Canary Media tier-1 promotion: consistent 30% keep rate; best US investor-lens source.

---

## 2026-09-25 — Run 5

**What dominated today:**
- AU clean-energy M&A: Singapore asset manager acquiring a leading AU renewable developer (82) was the top story — offshore capital continuing to flow into AU transition assets ahead of capacity buildout.
- AU wind revival: Contracts awarded for AU's biggest wind project start in 2+ years (79) — strong de-risking milestone signal.
- US capital unlocked: $7B Solar for All freed by court ruling (78) removes a major IRA capital blockage; DOE's $1.9B advanced transmission funding (77) continues US grid modernisation spend.
- AU grid risk: Origin reviving gas/diesel peaker (76) and $10B fracked gas pipeline cost blowout (74) are AU stranded-asset/lock-in risk signals running counter to the AU transition narrative.
- Transport cost curve: Carbon Brief's 9x EV cheapness finding (75) is the strongest published TCO confirmation of EV transition point.
- China signals: Solar manufacturing layoffs (74) and financial institutions in China carbon market (73) round out the global picture.

**Source performance (run 5):**
- RenewEconomy (AU): 10 fetched, 6 kept (60%) — cumulative 38 fetched, 22 kept (58%). Dominant across all 5 runs; AU signal density remains high.
- Carbon Brief: 2 fetched, 2 kept (100%) — perfect this run. Cumulative 9 fetched, 4 kept (44%). Consistently highest quality-per-item source.
- Canary Media: 7 fetched, 2 kept (29%) — cumulative 27/8 (30%). Steady US investor-lens signal. 
- PV Magazine: 10 fetched, 3 kept (30%) — cumulative 40/11 (28%). Reliable solar manufacturing and market-pricing signal.
- Utility Dive: 8 fetched, 1 kept (13%) — lower this run; DOE transmission story was the single keep. Cumulative 30/7 (23%).
- Dialogue Earth: 5 fetched, 2 kept (40%) — China solar layoffs + carbon market finance stories both above floor. Cumulative 10/2 (20%). Better than its early track record.
- Inside Climate News: 10 fetched, 0 kept — mostly environmental science, aquaculture, and health stories; none cleared investor-lens floor.
- The Guardian: 7 fetched, 0 kept — editorial opinion, wildlife, and climate-science cycle today.
- CleanTechnica: 21 fetched, 0 kept — cumulative 86/1 (1%). Removal justified.
- Electrek: 24 fetched, 0 kept — cumulative 92/7 (8%). Consumer-product dominance persists; confirm floor raise to 73.
- Grist: 8 fetched, 0 kept — cumulative 27/0 (0%). Removal justified.
- Euractiv (EU), DeSmog: still 0 fetched across all 5 cloud runs.

**Tuning applied:**
- None (conservative; proposals still pending interactive confirmation).

**Proposed for next interactive run (persistent):**
- Remove CleanTechnica: 86 fetched, 1 kept (1.2%) across 5 runs. No investor-signal pattern.
- Remove Grist: 27 fetched, 0 kept (0%) across 5 runs.
- Raise Electrek effective significance floor to 73: 92 fetched, 7 kept (8%) cumulative; kept items are exceptional.
- Validate Euractiv and DeSmog from residential IP; 0 fetched across 5 cloud runs is structural.
- Consider Dialogue Earth tier upgrade: 10 fetched, 2 kept (20%) — China-specific finance and supply-chain angle is adding value.
