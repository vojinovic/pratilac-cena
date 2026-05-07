#!/usr/bin/env python3
"""
Pratilac cena oglasa - polovniautomobili.com
Å alje email notifikaciju (preko Resend.com) kad cena padne.
"""

import json
import os
import re
import time
from datetime import datetime

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Pokreni: pip install requests beautifulsoup4")
    exit(1)

# âââââââââââââââââââââââââââââââââââââââââââââ
# KONFIGURACIJA
# âââââââââââââââââââââââââââââââââââââââââââââ

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
EMAIL_PRIMALAC = os.environ.get("EMAIL_PRIMALAC", "")

# Lista oglasa koje pratiÅ¡
OGLASI = [
    "https://www.polovniautomobili.com/auto-oglasi/28482744/volvo-xc60-20b4-mhev-r-design?attp=p9_pv0_pc0_pl11_plv0",
    "https://www.polovniautomobili.com/auto-oglasi/28877577/volvo-xc60-20-awd?attp=p9_pv0_pc0_pl11_plv0",
    "https://www.polovniautomobili.com/auto-oglasi/28054398/skoda-kodiaq-20-tdi-style-4x4?attp=p9_pv0_pc0_pl11_plv0",
    "https://www.polovniautomobili.com/auto-oglasi/29012594/volvo-xc60?attp=p9_pv0_pc0_pl11_plv0",
    "https://www.polovniautomobili.com/auto-oglasi/28215893/volvo-xc60-b4-d-awd-r-design?attp=p9_pv0_pc0_pl11_plv0",
    "https://www.polovniautomobili.com/auto-oglasi/28451802/volvo-xc60-20b4mhev-momentum?attp=p9_pv0_pc0_pl11_plv0",
    "https://www.polovniautomobili.com/auto-oglasi/28597036/volvo-xc60-b4-awd-inscription?attp=p9_pv0_pc0_pl11_plv0",
    "https://www.polovniautomobili.com/auto-oglasi/28733983/volvo-xc60-inscription-m-hev?attp=p9_pv0_pc0_pl11_plv0",
    "https://www.polovniautomobili.com/auto-oglasi/28837990/volvo-xc60-20-b4-momentum-pro?attp=p9_pv0_pc0_pl11_plv0",
    "https://www.polovniautomobili.com/auto-oglasi/29091836/skoda-kodiaq-style-20?attp=p9_pv0_pc0_pl11_plv0",
    "https://www.polovniautomobili.com/auto-oglasi/28808020/volvo-xc60-b4-d-awd-restajling?attp=p1_pv0_pc1_pl1_plv0",
]

# âââââââââââââââââââââââââââââââââââââââââââââ

BAZA_FAJL = "cene_oglasa.json"
PAUZA     = 4

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "sr-RS,sr;q=0.9,en-US;q=0.8",
}


def ucitaj_bazu() -> dict:
    if os.path.exists(BAZA_FAJL):
        with open(BAZA_FAJL, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def sacuvaj_bazu(baza: dict):
    with open(BAZA_FAJL, "w", encoding="utf-8") as f:
        json.dump(baza, f, ensure_ascii=False, indent=2)


def izvuci_cenu(soup):
    selektori = [
        {"class": "price-box__price"},
        {"class": "priceBox"},
        {"itemprop": "price"},
        {"class": "price"},
    ]
    for sel in selektori:
        el = soup.find(attrs=sel)
        if el:
            cifre = re.sub(r"[^\d]", "", el.get_text(strip=True))
            if cifre:
                return int(cifre)

    meta = soup.find("meta", {"property": "og:price:amount"})
    if meta and meta.get("content"):
        cifre = re.sub(r"[^\d]", "", meta["content"])
        if cifre:
            return int(cifre)
    return None


def izvuci_naslov(soup):
    meta = soup.find("meta", {"property": "og:title"})
    if meta and meta.get("content"):
        return meta["content"].strip()
    title = soup.find("title")
    return title.get_text(strip=True) if title else "Nepoznat oglas"


def proveri_oglas(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  â ï¸  GreÅ¡ka: {e}")
        return None, None, False

    soup = BeautifulSoup(resp.text, "html.parser")
    if resp.status_code == 404:
        return None, None, False

    return izvuci_naslov(soup), izvuci_cenu(soup), True


def formatiraj_cenu(cena):
    if cena is None:
        return "N/A"
    return f"{cena:,}".replace(",", ".") + " â¬"


def posalji_email(snizenja):
    if not RESEND_API_KEY or not EMAIL_PRIMALAC:
        print("â ï¸  RESEND_API_KEY ili EMAIL_PRIMALAC nisu postavljeni.")
        return

    vreme = datetime.now().strftime("%d.%m.%Y %H:%M")

    stavke = ""
    for s in snizenja:
        stavke += f"""
        <tr>
          <td style="padding:12px; border-bottom:1px solid #eee;">
            <a href="{s['url']}" style="color:#1a73e8; font-weight:bold; text-decoration:none;">
              {s['naslov']}
            </a>
          </td>
          <td style="padding:12px; border-bottom:1px solid #eee; color:#999; text-decoration:line-through;">
            {formatiraj_cenu(s['stara_cena'])}
          </td>
          <td style="padding:12px; border-bottom:1px solid #eee; color:#2e7d32; font-weight:bold;">
            {formatiraj_cenu(s['nova_cena'])}
          </td>
          <td style="padding:12px; border-bottom:1px solid #eee; color:#c62828;">
            â¼ {formatiraj_cenu(s['razlika'])} ({s['procenat']:.1f}%)
          </td>
        </tr>
        """

    html = f"""
    <html><body style="font-family:Arial,sans-serif; max-width:700px; margin:auto; padding:20px;">
      <h2 style="color:#1a73e8;">ð SniÅ¾enje cene oglasa!</h2>
      <p style="color:#555;">Provera obavljena: <strong>{vreme}</strong></p>
      <table width="100%" cellpadding="0" cellspacing="0"
             style="border-collapse:collapse; border:1px solid #eee; border-radius:8px;">
        <thead>
          <tr style="background:#f5f5f5;">
            <th style="padding:12px; text-align:left;">Oglas</th>
            <th style="padding:12px; text-align:left;">Bila</th>
            <th style="padding:12px; text-align:left;">Sada</th>
            <th style="padding:12px; text-align:left;">Razlika</th>
          </tr>
        </thead>
        <tbody>{stavke}</tbody>
      </table>
      <p style="color:#999; font-size:12px; margin-top:20px;">
        Ovu poruku je poslao tvoj pratilac cena sa GitHub Actions.
      </p>
    </body></html>
    """

    response = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "from":    "Pratilac cena <onboarding@resend.dev>",
            "to":      [EMAIL_PRIMALAC],
            "subject": f"ð SniÅ¾enje cene na Polovni automobili ({len(snizenja)} oglas(a))",
            "html":    html,
        },
    )

    if response.status_code == 200:
        print(f"â Email poslat na {EMAIL_PRIMALAC}")
    else:
        print(f"â GreÅ¡ka pri slanju: {response.text}")


def pokreni_proveru():
    if not OGLASI:
        print("â ï¸  Dodaj URL-ove oglasa u listu OGLASI!")
        return

    baza     = ucitaj_bazu()
    snizenja = []
    vreme    = datetime.now().strftime("%d.%m.%Y %H:%M")

    print(f"\nð Provera cena â {vreme}")
    print(f"   PratiÅ¡ {len(OGLASI)} oglas(a)\n")

    for i, url in enumerate(OGLASI, 1):
        print(f"[{i}/{len(OGLASI)}] {url[:65]}...")
        naslov, cena, aktivan = proveri_oglas(url)

        if not aktivan:
            print("  â Oglas nedostupan\n")
            continue

        stara_cena = baza.get(url, {}).get("cena")
        print(f"  ð {naslov}")
        print(f"  ð° Cena: {formatiraj_cenu(cena)}", end="")

        if stara_cena is None:
            print(" (novo, zapamÄeno)")
        elif cena and cena < stara_cena:
            razlika  = stara_cena - cena
            procenat = razlika / stara_cena * 100
            print(f" â bila {formatiraj_cenu(stara_cena)} ð SNIÅ½ENJE!")
            snizenja.append({
                "url":        url,
                "naslov":     naslov,
                "stara_cena": stara_cena,
                "nova_cena":  cena,
                "razlika":    razlika,
                "procenat":   procenat,
            })
        elif cena and cena > stara_cena:
            print(f" â bila {formatiraj_cenu(stara_cena)} ð poveÄana")
        else:
            print(" (nepromenjena)")

        print()
        baza[url] = {
            "naslov":            naslov,
            "cena":              cena,
            "aktivan":           True,
            "poslednja_provera": vreme,
        }

        if i < len(OGLASI):
            time.sleep(PAUZA)

    sacuvaj_bazu(baza)

    if snizenja:
        print(f"ð {len(snizenja)} sniÅ¾enje(a) â Å¡aljem email...")
        posalji_email(snizenja)
    else:
        print("â¹ï¸  Nema sniÅ¾enja, email se ne Å¡alje.")


if __name__ == "__main__":
    pokreni_proveru()
