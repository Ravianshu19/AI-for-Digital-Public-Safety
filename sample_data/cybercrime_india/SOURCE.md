# Cybercrime in India — city-level by motive

**File:** `cybercrime_by_city_motive.csv` — 191 Indian cities × cybercrime motive
(Fraud, Extortion, Sexual Exploitation, Personal Revenge, Stealing Information, etc.)
with a per-city total.

**Source:** Kaggle — *Dataset Cybercrime in India*, `seanangelonathanael/dataset-cybercrime-in-india`
(derived from NCRB "Crime in India" city-level cybercrime motive tables).
https://www.kaggle.com/datasets/seanangelonathanael/dataset-cybercrime-in-india

**How we use it:** powers the **Cybercrime by motive** real-data panel in the Geospatial
module (`geospatial.cybercrime_motives()` → `/api/geo/analyze`): national motive
breakdown + top cybercrime cities, alongside the NCRB state stats.
