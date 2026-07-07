# Prahari — demo video script (target 2:45)

Record at 1440×900+ with the app on `http://127.0.0.1:8008`. One take per scene
is fine — cut between scenes. Speak the narration lines; they total ~2:40 at a
normal pace. Refresh the page before recording so the live benchmark cards load.

| # | Time | On screen | Narration |
|---|------|-----------|-----------|
| 1 | 0:00–0:20 | **Overview.** Hover the five stat cards slowly, left to right. | "India registered 11.4 lakh cybercrime complaints in 2023 — up 60% in a year. Digital-arrest scams alone took ₹1,776 crore in nine months. Prahari is a five-module AI command centre built to catch these threats *before* the money moves — and that last card isn't a claim: it's our classifier benchmarked live, on this machine, this session." |
| 2 | 0:20–0:55 | **Digital Arrest Detection.** Click the *Digital-arrest call* sample. Let the gauge sweep to 94, point at the evidence trail, then scroll to the bottom of the verdict and let the **Intelligence Fusion timeline** play out step by step. | "Paste a live call transcript and the verdict updates as you type — every point of this 94 traces to a matched phrase. And here's the part nobody else has: the moment the scam is confirmed, an agent works the case across every desk automatically. The caller number? A KINGPIN node of campaign CAMP-001 — five mule accounts, ₹88 lakh projected loss. Geospatial says Delhi cluster, patrol priority one. The MHA alert is packaged, and the whole fused case is hash-sealed in the ledger — in milliseconds, court-ready." |
| 3 | 0:55–1:05 | Load the *Legit bank call* sample → SAFE. | "And a genuine bank call scores SAFE — our benchmark shows a 0% false-positive rate, because a citizen tool that cries wolf gets uninstalled." |
| 4 | 1:05–1:30 | **Counterfeit Currency.** Drag `sample_data/currency/500/reverse.jpg` onto the dropzone, tick UV, verify → GENUINE. Then upload `sample_data/counterfeit_500.png`, UV unticked → COUNTERFEIT. | "The counterfeit agent runs eight security-feature checks — microprint energy, security thread, colour-shift ink, the RBI serial grammar. A genuine ₹500 clears; this fake fails the watermark and UV checks and is rejected, with the exact failed features listed for the bank teller." |
| 5 | 1:30–1:55 | **Fraud Network Graph.** Click CAMP-001; the ring highlights. Point at "days to 100 victims". Scroll briefly to the India UPI panel. | "Graph AI clusters victims, mule accounts and cash-out nodes into campaigns using community detection. The key number is lead time: this ring is ~133 days from 100 victims — that's the intervention window. Below it, real Kaggle data on 1,000 India UPI fraud cases grounds the model." |
| 6 | 1:55–2:10 | **Geospatial Intelligence.** Pan the map, toggle the NCRB layer, show the patrol queue. | "The geospatial layer fuses demo hotspots with real NCRB state and city data — 59% of Indian cybercrime is financial fraud — and turns it into a ranked patrol-priority queue." |
| 7 | 2:10–2:30 | **Citizen Shield.** Tap the 🚨 *Digital arrest* chip; verdict appears. Switch language to हिन्दी and tap again. | "Citizens get the same intelligence over WhatsApp, IVR or app. One tap, instant verdict, the reasons in plain language, and guided 1930 reporting inside the golden hour — in 12 Indian languages." |
| 8 | 2:30–2:45 | **Model Performance.** Sweep across the KPI row, the confusion matrix, per-denomination bars, and end on the green "chain intact" audit badge. | "Everything you just saw is measured, not promised: 100% precision, 97% recall, zero false positives, 0% false rejection across denominations — and a hash-chained audit ledger that makes every verdict court-admissible. Prahari: intelligence before victimisation." |

**Tips**
- Cursor moves slowly; pause a beat after each verdict lands (the gauge sweep is the money shot).
- If a chart looks empty, you scrolled too fast — wait for the fetch (~1s).
- Keep the browser at 100% zoom; hide bookmarks bar; use a clean profile so no extensions overlay the UI.
