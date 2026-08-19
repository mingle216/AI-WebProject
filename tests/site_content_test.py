from html.parser import HTMLParser
from pathlib import Path
import unittest


PROJECT = Path(__file__).resolve().parents[1]
HOME = PROJECT / "test-last.html"
PHONE = "15682112719"
EMAIL = "hmm@rongelec.com"
ADDRESS = "江苏省南通市通州区五街镇南通睦融电气设备有限公司"


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.resources = []
        self.text = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "a" and values.get("href"):
            self.links.append(values["href"])
        if tag == "link" and values.get("rel") == "stylesheet" and values.get("href"):
            self.resources.append(values["href"])
        for attribute in ("src", "poster"):
            if values.get(attribute):
                self.resources.append(values[attribute])
        if values.get("srcset"):
            self.resources.extend(candidate.strip().split()[0] for candidate in values["srcset"].split(","))

    def handle_data(self, data):
        self.text.append(data)


def parse_page(path):
    parser = PageParser()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser


class SiteContentTests(unittest.TestCase):
    def test_home_page_publishes_one_current_contact_identity(self):
        for page_path in (HOME, PROJECT / "terms.html", PROJECT / "privacy.html"):
            page = page_path.read_text(encoding="utf-8")
            self.assertIn(PHONE, page, page_path.name)
            self.assertIn(EMAIL, page, page_path.name)
            self.assertIn(ADDRESS, page, page_path.name)
            for obsolete in (
                "13585623392",
                "13962796574",
                "service@ptmarineservice.com",
                "hjg@rongelec.com",
                "示例地址",
                "Sample Address",
            ):
                self.assertNotIn(obsolete, page, page_path.name)

    def test_home_page_links_to_both_legal_pages(self):
        page = parse_page(HOME)
        self.assertIn("terms.html", page.links)
        self.assertIn("privacy.html", page.links)

    def test_local_resources_and_internal_pages_resolve(self):
        pages = [HOME, PROJECT / "terms.html", PROJECT / "privacy.html"]
        for page_path in pages:
            self.assertTrue(page_path.is_file(), page_path.name)
            page = parse_page(page_path)
            for ref in page.resources + page.links:
                if ref.startswith(("http://", "https://", "mailto:", "tel:", "#", "javascript:")):
                    continue
                target = (PROJECT / ref.split("#", 1)[0].split("?", 1)[0]).resolve()
                self.assertTrue(target.is_file(), f"{page_path.name}: {ref}")


if __name__ == "__main__":
    unittest.main()
