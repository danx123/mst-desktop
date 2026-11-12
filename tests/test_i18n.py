import string
import unittest

from mst import i18n


def _fields(text: str) -> set[str]:
    return {name for _, name, _, _ in string.Formatter().parse(text) if name}


class I18nTests(unittest.TestCase):
    def tearDown(self):
        i18n.set_language("id")

    def test_every_key_has_both_languages(self):
        for key, (idn, eng) in i18n.STRINGS.items():
            self.assertTrue(idn.strip(), f"{key}: empty Indonesian")
            self.assertTrue(eng.strip(), f"{key}: empty English")

    def test_placeholders_match_between_languages(self):
        for key, (idn, eng) in i18n.STRINGS.items():
            self.assertEqual(_fields(idn), _fields(eng), key)

    def test_switching_language(self):
        i18n.set_language("en")
        self.assertEqual(i18n.tr("cat.stations"), "Stations")
        i18n.set_language("id")
        self.assertEqual(i18n.tr("cat.stations"), "Stasiun")

    def test_format_and_unknown_key(self):
        i18n.set_language("en")
        self.assertEqual(i18n.tr("passes.count", n=3), "3 Passes Predicted")
        self.assertEqual(i18n.tr("does.not.exist"), "does.not.exist")

    def test_detect_language(self):
        self.assertEqual(i18n.detect_language("id_ID"), "id")
        self.assertEqual(i18n.detect_language("en_US"), "en")
        self.assertEqual(i18n.detect_language("de_DE"), "en")

    def test_every_tr_key_used_in_code_exists(self):
        import pathlib
        import re

        used = set()
        for path in pathlib.Path("mst").rglob("*.py"):
            if path.name == "i18n.py":
                continue
            used |= set(re.findall(r'tr\("([a-z_]+\.[a-z_0-9]+)"', path.read_text(encoding="utf-8")))
        used |= {k for _, _, k in __import__("mst.data.celestrak", fromlist=["SYNC_GROUPS"]).SYNC_GROUPS}
        used |= {k for _, k in __import__("mst.ui.pages.catalog_page", fromlist=["CATEGORIES"]).CATEGORIES}
        missing = sorted(k for k in used if k not in i18n.STRINGS)
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
