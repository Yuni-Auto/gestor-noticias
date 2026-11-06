# Jornal Matinal

The site is static and is published with GitHub Pages. GitHub Actions fetches
the daily edition at approximately 08:00 in Sao Paulo (11:00 UTC), archives it,
and deploys the page. The schedule runs independently of the browser and the
personal computer.

## Initial setup

1. In the repository settings, add an Actions secret named `NEWSAPI_KEY` with
   a valid NewsAPI key. Do not put the key in this repository or in the HTML.
2. In **Settings > Actions > General > Workflow permissions**, allow read and
   write permissions so the scheduled workflow can archive each edition.
3. In **Settings > Pages**, choose **GitHub Actions** as the build and deploy
   source.
4. Run **Actions > Jornal Matinal > Run workflow** once to generate the first
   edition and publish the page.

The scheduled run can be delayed by GitHub Actions. The browser only downloads
the published JSON; it never receives the NewsAPI key. Old daily editions are
kept in `site/editions/` and can be selected from the page.

The previous local script contained API credentials. Revoke those credentials
and use a newly issued NewsAPI key for the `NEWSAPI_KEY` secret. The workflow
does not use the old local script or its credentials.

`scripts/generate_daily.py` uses only Python's standard library. Run its tests
with `python -m unittest discover -s tests`.
