import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

from scripts import generate_daily


class GenerateDailyTests(unittest.TestCase):
    def test_build_edition_deduplicates_technology(self):
        portal_article = {
            "titulo": "Notícia compartilhada",
            "resumo": "Resumo",
            "fonte": "Portal",
            "link": "https://example.com/portal",
        }
        extra_article = {
            "titulo": "Notícia extra",
            "resumo": "Outro resumo",
            "fonte": "Geral",
            "link": "https://example.com/extra",
        }
        with patch.object(
            generate_daily,
            "fetch_articles",
            side_effect=[
                [portal_article],
                [portal_article, extra_article],
                [],
            ],
        ):
            edition = generate_daily.build_edition(
                "test-key",
                datetime(2026, 11, 5, 8, tzinfo=ZoneInfo("America/Sao_Paulo")),
            )

        self.assertEqual(edition["date"], "2026-11-05")
        self.assertEqual(
            [article["titulo"] for article in edition["tech"]],
            ["Notícia compartilhada", "Notícia extra"],
        )
        self.assertEqual(edition["eco"], [])

    def test_write_edition_updates_latest_and_archive_index(self):
        edition = {
            "date": "2026-11-05",
            "generated_at": "2026-11-05T08:00:00-03:00",
            "tech": [],
            "eco": [],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            site_dir = root / "site"
            editions_dir = site_dir / "editions"
            with (
                patch.object(generate_daily, "ROOT", root),
                patch.object(generate_daily, "SITE_DIR", site_dir),
                patch.object(generate_daily, "EDITIONS_DIR", editions_dir),
            ):
                generate_daily.write_edition(edition)

            self.assertEqual(
                json.loads((site_dir / "latest_news.json").read_text())["date"],
                "2026-11-05",
            )
            index = json.loads((editions_dir / "index.json").read_text())
            self.assertEqual(index, {"latest": "2026-11-05", "dates": ["2026-11-05"]})


if __name__ == "__main__":
    unittest.main()
