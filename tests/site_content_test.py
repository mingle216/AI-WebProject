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
        self.element_stack = []
        self.elements_by_i18n = {}

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        element = {
            "tag": tag,
            "attrs": values,
            "parent": self.element_stack[-1] if self.element_stack else None,
        }
        if values.get("data-i18n"):
            self.elements_by_i18n[values["data-i18n"]] = element
        if tag not in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}:
            self.element_stack.append(element)
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

    def handle_endtag(self, tag):
        while self.element_stack:
            element = self.element_stack.pop()
            if element["tag"] == tag:
                break


def parse_page(path):
    parser = PageParser()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser


class SiteContentTests(unittest.TestCase):
    def test_home_page_explains_field_capability_and_service_delivery(self):
        page = HOME.read_text(encoding="utf-8")
        for required_copy in (
            "技术团队与专业装备",
            "Technical Capability & Equipment",
            "15 年一线船舶电气/自动化排查经验",
            "规范技术交付",
            "现场服务流程",
            "Onboard Service Workflow",
            "需求确认",
            "登轮检测",
            "故障处置与调试验证",
            "技术报告交付",
        ):
            self.assertIn(required_copy, page)

    def test_capability_tools_are_explained_without_inventory_badges(self):
        page = parse_page(HOME)
        for badge_key in (
            "tool_multimeter",
            "tool_megger",
            "tool_scope",
            "tool_generator",
            "tool_fixture",
        ):
            self.assertNotIn(badge_key, page.elements_by_i18n)

    def test_workflow_heading_uses_the_same_vertical_structure_as_capability(self):
        page = parse_page(HOME)
        workflow_title = page.elements_by_i18n["workflow_title"]
        workflow_intro = page.elements_by_i18n["workflow_intro"]

        self.assertIs(workflow_title["parent"], workflow_intro["parent"])
        parent_classes = workflow_title["parent"]["attrs"].get("class", "").split()
        self.assertIn("flex-col", parent_classes)
        self.assertNotIn("lg:flex-row", parent_classes)

    def test_welcome_section_uses_company_heading_and_local_ship_visual(self):
        source = HOME.read_text(encoding="utf-8")
        welcome = source.split('id="welcome-section"', 1)[1].split("</section>", 1)[0]

        self.assertIn("南通睦融电气设备有限公司", welcome)
        self.assertIn('src="murong-pic/pic3.jpg"', welcome)
        self.assertNotIn("images.unsplash.com", welcome)
        self.assertIn("MURONG", welcome)
        self.assertIn("RELIABLE &amp; RESPONSIVE", welcome)

    def test_home_core_value_dots_use_breathing_animation(self):
        source = HOME.read_text(encoding="utf-8")

        self.assertIn("@keyframes core-value-breathe", source)
        self.assertIn(".core-value-dot", source)
        self.assertEqual(4, source.count('class="core-value-dot"'))

    def test_home_page_does_not_claim_unverified_certification_or_guarantees(self):
        page = HOME.read_text(encoding="utf-8")
        for unsupported_claim in (
            "船级社认证级别校验",
            "class-certified calibrations",
            "ISO 认证信息",
            "ISO Certification",
        ):
            self.assertNotIn(unsupported_claim, page)

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
