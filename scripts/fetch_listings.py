import json
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

SOURCE_URL = "https://live.euronext.com/nb/ipo-showcase"

def parse_date_ddmmyyyy(s: str):
    # Format på siden: dd/mm/yyyy :contentReference[oaicite:1]{index=1}
    return datetime.strptime(s.strip(), "%d/%m/%Y").replace(tzinfo=timezone.utc)

def main():
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=48)

    html = requests.get(SOURCE_URL, timeout=30).text
    soup = BeautifulSoup(html, "lxml")

    # Finn tabellrader ved å lese tekst-rader som starter med dd/mm/yyyy
    rows = []
    for tr in soup.find_all("tr"):
        tds = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
        if len(tds) < 6:
            continue
        if not re.match(r"^\d{2}/\d{2}/\d{4}$", tds[0]):
            continue

        date_str, company, ticker, isin, location, market = tds[:6]

        # URL ligger typisk i <a> på company-cellen
        a = tr.find("a", href=True)
        url = urljoin(SOURCE_URL, a["href"]) if a else None

        rows.append({
            "date": date_str,
            "company": company,
            "ticker": ticker,
            "isin": isin,
            "location": location,
            "market": market,
            "url": url
        })

    # Filtrer: Location Oslo + innen 48 timer
    items = []
    for r in rows:
        if r["location"].lower() != "oslo":
            continue
        dt = parse_date_ddmmyyyy(r["date"])
        # Siden har dato uten klokkeslett, så vi tolker som "den dagen".
        if dt >= cutoff.replace(hour=0, minute=0, second=0, microsecond=0):
            items.append(r)

    out = {
        "source": SOURCE_URL,
        "generated_at": now.isoformat(timespec="seconds"),
        "items": items
    }

    with open("data/listings.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
