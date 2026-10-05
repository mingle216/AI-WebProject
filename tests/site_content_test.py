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
        self.elements_by_id = {}

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        element = {
            "tag": tag,
            "attrs": values,
            "parent": self.element_stack[-1] if self.element_stack else None,
        }
        if values.get("data-i18n"):
            self.elements_by_i18n[values["data-i18n"]] = element
        if values.get("id"):
            self.elements_by_id[values["id"]] = element
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
    def test_business_scope_gallery_keeps_all_original_real_assets(self):
        page = parse_page(HOME)
        self.assertIn("business-scope-gallery", page.elements_by_id)
        gallery = page.elements_by_id["business-scope-gallery"]
        self.assertEqual("section", gallery["tag"])

        source = HOME.read_text(encoding="utf-8")
        gallery_source = source.split('id="business-scope-gallery"', 1)[1].split("</section>", 1)[0]
        expected_images = [
            f"assets/business-scope/product-img{index:02d}.webp"
            for index in range(1, 17)
        ]

        for image in expected_images:
            self.assertEqual(1, gallery_source.count(f'src="{image}"'), image)
            self.assertTrue((PROJECT / image).is_file(), image)
        self.assertNotIn("images.unsplash.com", gallery_source)

    def test_business_scope_gallery_groups_assets_into_five_filterable_categories(self):
        source = HOME.read_text(encoding="utf-8")
        self.assertIn('id="business-scope-gallery"', source)
        gallery = source.split('id="business-scope-gallery"', 1)[1].split("</section>", 1)[0]
        categories = {
            "power-control": 7,
            "alarm-monitoring": 3,
            "communications": 1,
            "testing-instruments": 3,
            "environmental-support": 2,
        }

        self.assertEqual(16, gallery.count("data-business-item"))
        for category, expected_count in categories.items():
            self.assertEqual(
                expected_count,
                gallery.count(f'data-business-category="{category}"'),
                category,
            )
            self.assertIn(f'data-business-filter="{category}"', gallery)
        self.assertIn('data-business-filter="all"', gallery)
        self.assertIn('aria-live="polite"', gallery)

    def test_business_scope_gallery_controls_are_accessible_and_localized(self):
        source = HOME.read_text(encoding="utf-8")
        self.assertIn('id="business-scope-gallery"', source)
        gallery = source.split('id="business-scope-gallery"', 1)[1].split("</section>", 1)[0]

        self.assertIn('role="group"', gallery)
        self.assertIn('aria-label="业务范围筛选"', gallery)
        self.assertIn('aria-pressed="true"', gallery)
        self.assertEqual(16, gallery.count('data-business-lightbox-trigger'))
        self.assertEqual(16, gallery.count('loading="lazy"'))
        self.assertEqual(16, gallery.count('decoding="async"'))
        self.assertEqual(16, gallery.count('data-i18n-alt="scope_item_'))
        self.assertNotIn('onclick="openBusinessLightbox', gallery.split("<button", 1)[0])

        page = parse_page(HOME)
        self.assertIn("business-scope-lightbox", page.elements_by_id)
        lightbox = page.elements_by_id["business-scope-lightbox"]
        self.assertEqual("div", lightbox["tag"])
        self.assertEqual("dialog", lightbox["attrs"].get("role"))
        self.assertEqual("true", lightbox["attrs"].get("aria-modal"))
        self.assertIn(
            '\n    </div>\n\n    <div id="business-scope-lightbox"',
            source,
            "fixed lightbox must follow the main stacking context so it covers the sticky header",
        )

    def test_home_page_leads_with_automation_repair_outcome_and_contact_path(self):
        source = HOME.read_text(encoding="utf-8")
        hero = source.split('<main id="page-home"', 1)[1].split("</section>", 1)[0]

        self.assertIn("让船舶自动化系统", hero)
        self.assertIn("稳定运行", hero)
        self.assertIn("船舶自动化设备维修", hero)
        self.assertIn("主机遥控", hero)
        self.assertIn("报警监测", hero)
        self.assertIn("调试验证", hero)
        self.assertIn("navigate('contact')", hero)
        self.assertIn("提交服务需求", hero)

    def test_home_page_places_proof_banner_before_company_story(self):
        source = HOME.read_text(encoding="utf-8")
        home = source.split('<main id="page-home"', 1)[1].split('<main id="page-services"', 1)[0]

        for section_id in (
            'id="service-overview-section"',
            'id="capability-section"',
            'id="workflow-section"',
            'id="ship-types-section"',
            'id="welcome-section"',
        ):
            self.assertIn(section_id, home)

        ordered_sections = [
            home.index('aria-label="服务能力摘要"'),
            home.index('id="welcome-section"'),
            home.index('id="service-overview-section"'),
            home.index('id="capability-section"'),
            home.index('id="workflow-section"'),
            home.index('id="ship-types-section"'),
        ]
        self.assertEqual(sorted(ordered_sections), ordered_sections)

    def test_animated_grid_background_is_visible_on_home_only(self):
        source = HOME.read_text(encoding="utf-8")
        page = parse_page(HOME)

        self.assertEqual(1, source.count('id="techCanvas"'))
        self.assertEqual("main-content", page.elements_by_id["techCanvas"]["parent"]["attrs"].get("id"))
        main_content = source.split('<div id="main-content"', 1)[1].split("<footer", 1)[0]
        self.assertLess(main_content.index('id="techCanvas"'), main_content.index('id="page-home"'))

        main_content_tag = source.split('<div id="main-content"', 1)[1].split(">", 1)[0]
        self.assertIn("home-background-active", main_content_tag)

        styles = source.split("<style>", 1)[1].split("</style>", 1)[0]
        self.assertIn("#main-content:not(.home-background-active) #techCanvas", styles)

        navigate = source.split("function navigate(pageId", 1)[1].split("function ", 1)[0]
        self.assertIn("classList.toggle('home-background-active', pageId === 'home')", navigate)

        self.assertIn("new ResizeObserver(resize)", source)
        self.assertIn("resizeObserver.observe(canvas.parentElement)", source)

    def test_inner_pages_use_clean_white_and_light_gray_surfaces(self):
        source = HOME.read_text(encoding="utf-8")
        styles = source.split("<style>", 1)[1].split("</style>", 1)[0]
        self.assertIn(".welcome-copy-card {", styles)
        welcome_card_rules = styles.split(".welcome-copy-card {", 1)[1].split("}", 1)[0]

        self.assertIn("#page-services,", styles)
        self.assertIn("#page-about,", styles)
        self.assertIn("#page-contact", styles)
        self.assertIn("background: #f8fafc", styles)
        self.assertIn("#page-services .site-surface", styles)
        self.assertIn("#page-about .site-surface", styles)
        self.assertIn("#page-contact .site-surface", styles)
        self.assertIn("background: #fff", styles)
        self.assertIn("rgba(255, 255, 255", welcome_card_rules)

    def test_home_page_surfaces_concrete_customer_proof_points(self):
        page = parse_page(HOME)
        for proof_key in (
            "proof_experience",
            "proof_coverage",
            "proof_diagnosis",
            "proof_handover",
        ):
            self.assertIn(proof_key, page.elements_by_i18n)

    def test_about_page_avoids_unverifiable_guarantees_and_overstatements(self):
        source = HOME.read_text(encoding="utf-8")
        for unsupported_claim in (
            "确保航期零延误",
            "zero delay",
            "全球服务网络",
            "Global Service Network",
            "各大船级社",
            "all major classification societies",
            "极速物流通道",
            "express logistics channel",
            "全栈式系统攻坚",
            "Full-Stack Troubleshooting",
            "零摩擦岸基与船检支持",
            "Seamless Shore Support",
            "原厂备件全球直供",
            "Global Original Parts Supply",
            "原厂配件与全球供应",
            "Original Parts & Global Supply",
            "致力于为全球航线提供",
        ):
            self.assertNotIn(unsupported_claim, source)

    def test_yangtze_delta_service_map_uses_local_vector_data_with_a_separate_port_list(self):
        """Map labels must not crowd the geographic view; every port remains discoverable in the list."""
        source = HOME.read_text(encoding="utf-8")
        network = source.split('data-i18n="network_title"', 1)[1].split('<div class="site-surface-soft py-16', 1)[0]
        map_asset = PROJECT / "assets/maps/yangtze-delta-geo.js"

        self.assertTrue(map_asset.is_file())
        self.assertIn('src="assets/maps/yangtze-delta-geo.js"', source)
        self.assertIn('src="https://cdn.jsdelivr.net/npm/echarts@5.5.1/dist/echarts.min.js"', source)
        self.assertIn('id="yangtze-delta-map"', network)
        self.assertIn('id="yangtze-delta-map-fallback"', network)
        self.assertIn('id="service-port-list"', network)
        self.assertNotIn("map-bg-dots", network)

        for port in ("南京", "泰州", "靖江", "张家港", "南通", "上海", "舟山"):
            self.assertIn(port, source)
        self.assertIn("boundingCoords", source)
        self.assertIn("renderServicePortList", source)
        self.assertIn("window.YANGTZE_DELTA_GEOJSON", map_asset.read_text(encoding="utf-8"))

    def test_yangtze_delta_map_uses_small_hubs_without_geographic_labels(self):
        """Dense Yangtze ports must use small points while their names live in the side list."""
        source = HOME.read_text(encoding="utf-8")
        ports_source = source.split("const yangtzeDeltaPorts = [", 1)[1].split("]\n\n      const yangtzeDeltaRoutes", 1)[0]

        for port in (
            "连云港", "南京", "扬州", "泰州", "靖江", "江阴", "张家港",
            "太仓", "南通", "上海", "嘉兴", "宁波", "舟山",
        ):
            self.assertIn(f"name: '{port}'", ports_source)

        self.assertEqual(13, ports_source.count("name: '"))
        self.assertEqual(4, ports_source.count("primary: true"))
        self.assertIn("symbolSize: port.primary ? 7 : 4", source)
        self.assertIn("label: { show: false }", source)
        self.assertNotIn("rippleEffect", source)

    def test_contact_form_does_not_report_a_fake_success(self):
        source = HOME.read_text(encoding="utf-8")

        self.assertNotIn("表单提交成功", source)
        self.assertNotIn("Form submitted successfully", source)
        self.assertIn("页面暂未接入自动提交", source)
        self.assertIn("This page is not connected to automatic submission", source)

    def test_footer_restores_spacious_backup_layout(self):
        source = HOME.read_text(encoding="utf-8")
        footer_tag = source.split("<footer", 1)[1].split(">", 1)[0]
        footer = source.split("<footer", 1)[1].split("</footer>", 1)[0]

        self.assertIn("md:aspect-[16/9]", footer_tag)
        self.assertIn('<div class="flex-grow"></div>', footer)
        self.assertIn('class="relative z-10 pt-16 pb-6', footer)

    def test_home_canvas_and_footer_use_complementary_edge_fades(self):
        source = HOME.read_text(encoding="utf-8")
        styles = source.split("<style>", 1)[1].split("</style>", 1)[0]
        canvas_rules = styles.split("#techCanvas {", 1)[1].split("}", 1)[0]
        self.assertIn("footer::before {", styles)
        footer_fade_rules = styles.split("footer::before {", 1)[1].split("}", 1)[0]

        self.assertIn("calc(100% - 180px)", canvas_rules)
        self.assertIn("mask-image: linear-gradient", canvas_rules)
        self.assertIn("#main-content.home-background-active + footer", styles)
        self.assertIn("height: clamp(96px, 12vw, 180px)", footer_fade_rules)
        self.assertIn("var(--footer-transition-start)", footer_fade_rules)

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
        self.assertIn("“全方位”海事电气服务", welcome)
        self.assertIn("供应 · 安全 · 工程 · 技术", welcome)
        self.assertIn("深耕海事电气与自动化技术服务", welcome)
        self.assertIn("为船舶设备恢复可靠运行提供支持", welcome)
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
