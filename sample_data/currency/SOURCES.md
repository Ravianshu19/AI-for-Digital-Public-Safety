# Genuine reference banknote images — sources

These are images of **genuine** Indian banknotes (Reserve Bank of India, Mahatma
Gandhi New Series), used only to benchmark the counterfeit agent's
**genuine-acceptance / false-rejection** rate across denominations.

- **Source:** [Wikimedia Commons](https://commons.wikimedia.org/), category *Banknotes of the Indian rupee*.
- Downloaded via `sample_data/fetch_reference_notes.py` (re-run to refresh).
- Each denomination folder holds the obverse and reverse of one note.
- Attribution/licences are per the respective Commons file pages; reused here for
  non-commercial educational/hackathon benchmarking.

To extend the benchmark with your **own** captured genuine notes, drop additional
images into `sample_data/currency/<denom>/` and re-run `backend/counterfeit_eval.py`.

> No counterfeit notes are included or required. Possessing/sharing real Fake Indian
> Currency Notes (FICN) is a criminal offence; fake-detection is demonstrated via a
> synthetic print-quality stress test only.
