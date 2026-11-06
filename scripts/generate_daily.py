#!/usr/bin/env python3
"""Fetch the daily news edition and write static files for GitHub Pages."""

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
SITE_DIR = ROOT / "site"
EDITIONS_DIR = SITE_DIR / "editions"
NEWS_API_URL = "https://newsapi.org/v2/everything"
PORTAIS_TECH = [
    "tecmundo.com.br",
    "folha.uol.com.br",
    "tecnoblog.net",
    "canaltech.com.br",
    "olhardigital.com.br",
    "techtudo.com.br",
]
TECH_PORTAL_QUERY = (
    "tecnologia OR inteligência artificial OR software OR hardware OR app OR internet"
)
TECH_GENERAL_QUERY = (
    '"inteligência artificial" OR "IA generativa" OR "big tech" OR "Apple" '
    'OR "Google" OR "Meta" OR "Microsoft" OR "startup" OR "cibersegurança" '
    'OR "chip" OR "processador" OR "Amazon" OR "OpenAI"'
)
ECONOMY_QUERY = (
    '"mercado financeiro" OR "Ibovespa" OR "Selic" OR "IPCA" '
    'OR "dólar" OR "PIB" OR "Banco Central" OR "inflação" '
    'OR "bolsa de valores" OR "investimento" OR "economia brasileira" '
    'OR "juros" OR "recessão" OR "desemprego" OR "câmbio"'
)


def fetch_articles(query, api_key, domains=None, limit=10):
    params = {
        "q": query,
        "language": "pt",
        "sortBy": "publishedAt",
        "pageSize": 100,
        "apiKey": api_key,
    }
    if domains:
        params["domains"] = ",".join(domains)

    request = urllib.request.Request(
        NEWS_API_URL + "?" + urllib.parse.urlencode(params)
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read())
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"NewsAPI retornou HTTP {error.code}.") from None
    except urllib.error.URLError as error:
        raise RuntimeError(f"Não foi possível acessar a NewsAPI: {error.reason}.") from None

    if data.get("status") != "ok":
        code = data.get("code", "erro")
        raise RuntimeError(f"NewsAPI respondeu com erro ({code}).")

    articles = []
    seen = set()
    for article in data.get("articles", []):
        title = (article.get("title") or "").split(" - ")[0].strip()
        summary = (article.get("description") or article.get("content") or "")[:600].strip()
        if not title or not summary or title in seen:
            continue
        seen.add(title)
        articles.append(
            {
                "titulo": title,
                "resumo": summary,
                "fonte": article.get("source", {}).get("name") or "Desconhecida",
                "link": article.get("url") or "",
            }
        )
        if len(articles) == limit:
            break
    return articles


def build_edition(api_key, now=None):
    now = now or datetime.now(ZoneInfo("America/Sao_Paulo"))
    tech_portals = fetch_articles(
        TECH_PORTAL_QUERY, api_key, domains=PORTAIS_TECH, limit=7
    )
    tech_general = fetch_articles(TECH_GENERAL_QUERY, api_key, limit=6)
    seen_tech = {article["titulo"] for article in tech_portals}
    tech = tech_portals + [
        article for article in tech_general if article["titulo"] not in seen_tech
    ]
    economy = fetch_articles(ECONOMY_QUERY, api_key, limit=10)

    return {
        "date": now.strftime("%Y-%m-%d"),
        "generated_at": now.isoformat(timespec="seconds"),
        "tech": tech,
        "eco": economy,
    }


def write_edition(edition):
    EDITIONS_DIR.mkdir(parents=True, exist_ok=True)
    edition_path = EDITIONS_DIR / f"{edition['date']}.json"
    edition_path.write_text(
        json.dumps(edition, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (SITE_DIR / "latest_news.json").write_text(
        json.dumps(edition, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    dates = sorted(
        (path.stem for path in EDITIONS_DIR.glob("????-??-??.json")),
        reverse=True,
    )
    index = {"latest": edition["date"], "dates": dates}
    (EDITIONS_DIR / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"Edição {edition['date']} salva: "
        f"{len(edition['tech'])} notícias de tecnologia, "
        f"{len(edition['eco'])} de economia."
    )


def main():
    api_key = os.environ.get("NEWSAPI_KEY", "").strip()
    if not api_key:
        print(
            "::error::Configure o secret NEWSAPI_KEY no repositório do GitHub.",
            file=sys.stderr,
        )
        return 1
    try:
        write_edition(build_edition(api_key))
    except (RuntimeError, json.JSONDecodeError) as error:
        print(f"::error::{error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
