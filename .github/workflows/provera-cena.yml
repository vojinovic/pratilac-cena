name: Provera cena oglasa

on:
  schedule:
    # Pokreće se svakih 6 sati (00:00, 06:00, 12:00, 18:00 UTC = 01:00, 07:00, 13:00, 19:00 po Srbiji)
    - cron: "0 */6 * * *"
  workflow_dispatch:  # Možeš i ručno pokrenuti sa GitHub-a

jobs:
  proveri-cene:
    runs-on: ubuntu-latest

    steps:
      - name: Preuzmi kod
        uses: actions/checkout@v4

      - name: Postavi Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Instaliraj biblioteke
        run: pip install requests beautifulsoup4

      # Učitaj prethodno sačuvane cene (da ne zaboravi između pokretanja)
      - name: Učitaj bazu cena
        uses: actions/cache@v4
        with:
          path: cene_oglasa.json
          key: cene-baza-${{ github.run_id }}
          restore-keys: |
            cene-baza-

      - name: Pokreni proveru
        env:
          EMAIL_POSILJALAC: ${{ secrets.EMAIL_POSILJALAC }}
          EMAIL_LOZINKA:    ${{ secrets.EMAIL_LOZINKA }}
          EMAIL_PRIMALAC:   ${{ secrets.EMAIL_PRIMALAC }}
        run: python pratilac_cena.py
