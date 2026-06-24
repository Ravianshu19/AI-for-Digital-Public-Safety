"""
Download genuine reference banknote images (RBI Mahatma Gandhi New Series) from
Wikimedia Commons for the counterfeit-accuracy benchmark.

Source: Wikimedia Commons (public, official RBI note imagery). These are *genuine*
notes — used to measure the genuine-acceptance rate (low false-rejection) of the
counterfeit agent across denominations. To extend the benchmark, drop your own
captured genuine-note images into sample_data/currency/<denom>/.

Run:  .venv/bin/python sample_data/fetch_reference_notes.py
"""
import os
import time
import urllib.parse
import urllib.request

OUT = os.path.join(os.path.dirname(__file__), "currency")

# denom -> list of candidate Commons file titles (first that resolves is used)
FILES = {
    10:  ["India new 10 INR, MG series, 2018, obverse.jpg",
          "India new 10 INR, MG series, 2018, reverse.jpg"],
    20:  ["India new 20 INR, MG series, 2019, obverse.jpg",
          "India new 20 INR, MG series, 2019, reverse.jpg"],
    50:  ["India new 50 INR, MG series, 2018, obverse.jpg",
          "India new 50 INR, MG series, 2018, reverse.jpg"],
    100: ["India new 100 INR, Mahatma Gandhi New Series, 2018, obverse.jpg",
          "India new 100 INR, Mahatma Gandhi New Series, 2018, reverse.jpg"],
    200: ["India, 200 INR, 2018, obverse.jpg",
          "India, 200 INR, 2018, reverse.jpg"],
    500: ["India new 500 INR, MG series, 2016, obverse.jpg",
          "India new 500 INR, MG series, 2016, reverse.jpg"],
}

UA = {"User-Agent": "PrahariBenchmark/1.0 (hackathon; contact: local)"}


def filepath_url(title: str) -> str:
    return "https://commons.wikimedia.org/wiki/Special:FilePath/" + \
        urllib.parse.quote(title) + "?width=1200"


def download(title: str, dest: str) -> bool:
    try:
        req = urllib.request.Request(filepath_url(title), headers=UA)
        with urllib.request.urlopen(req, timeout=40) as r:
            data = r.read()
        if len(data) < 5000:  # too small => not a real image
            return False
        with open(dest, "wb") as f:
            f.write(data)
        return True
    except Exception as e:
        print(f"    ! {title[:50]}… -> {e}")
        return False


def main():
    total = 0
    for denom, titles in FILES.items():
        d = os.path.join(OUT, str(denom))
        os.makedirs(d, exist_ok=True)
        got = 0
        for title in titles:
            side = "obverse" if "obverse" in title else "reverse"
            dest = os.path.join(d, f"{side}.jpg")
            if os.path.exists(dest):
                got += 1
                continue
            time.sleep(1.5)  # be polite to Commons; avoids HTTP 429
            if download(title, dest):
                got += 1
                print(f"  ₹{denom:<4} {side:8s} <- {title}")
        total += got
        if got == 0:
            print(f"  ₹{denom}: NO images resolved")
    print(f"Done. {total} reference images under {OUT}")


if __name__ == "__main__":
    main()
