import re
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
INDEX_PATH = PROJECT_ROOT / "frontend/src/templates/index.html"
ACTION_CSS_PATH = PROJECT_ROOT / "frontend/src/static/css/action.css"


class PageSectionsReachableTest(unittest.TestCase):
  """每个内容区块都必须真的能被点开。

  区块的显示是纯 CSS：`#name:target ~ .content-main #name-content` 控制
  display，而那份选择器清单是硬编码的。加了 section 和侧边栏链接却漏了这
  一行，页面就会存在但永远打不开——点击毫无反应，也没有任何报错。person
  页第一次上线时正是这样漏的。
  """

  def sections(self):
    """页面里声明的所有内容区块名。"""
    html = INDEX_PATH.read_text(encoding="utf-8")
    return set(re.findall(r'<section id="([a-z-]+)-content"', html))

  def sidebar_targets(self):
    """侧边栏里能点的所有目标名。"""
    html = INDEX_PATH.read_text(encoding="utf-8")
    return set(re.findall(r'class="sidebar-menu-link"\s+href="#([a-z-]+)"', html)) | \
           set(re.findall(r'href="#([a-z-]+)"\s+class="sidebar-menu-link"', html))

  def displayed_sections(self):
    """CSS 里真正会被显示出来的区块名。"""
    css = ACTION_CSS_PATH.read_text(encoding="utf-8")
    return set(re.findall(r"#([a-z-]+):target ~ \.content-main #[a-z-]+-content", css))

  def test_every_section_can_be_opened(self):
    missing = self.sections() - self.displayed_sections()

    self.assertEqual(
      set(),
      missing,
      "这些区块在 index.html 里存在但 action.css 没有让它显示，"
      "点侧边栏不会有任何反应: {}".format(sorted(missing)),
    )

  def test_every_sidebar_link_leads_to_a_section(self):
    dangling = self.sidebar_targets() - self.sections()

    self.assertEqual(
      set(),
      dangling,
      "这些侧边栏链接没有对应的内容区块: {}".format(sorted(dangling)),
    )

  def test_the_person_page_is_among_them(self):
    """回归保护：person 页就是漏掉这一步的那个。"""
    self.assertIn("person", self.sections())
    self.assertIn("person", self.displayed_sections())
    self.assertIn("person", self.sidebar_targets())


if __name__ == "__main__":
  unittest.main()
