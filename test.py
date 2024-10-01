import unittest
import gen

class Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.site = gen.Site("http://test","test", [])
        self.csv_data="""[csv]
1,2,3
4,5,6
[csv]
    """

        self.meta_data = """|meta|
title: My Post
author: John Doe
date: 2022-01-01
|meta|"""

        self.wiki_link = "[[03_WikiLink]]"

        self.complex_csv = """# Test
[csv]
2,3,4
5,6,7
[csv]
        """

        self.post = """|meta|
author: John Doe
date: 2022-01-01
|meta|
# Welcome to shit

[[02_somelink]]

[csv]
1,2,3,4,5
6,7,8,9,10
a,b,d,e,g
[csv]
"""
    

    def parse_md(self, data):
        return self.site.md.parse(data)

    def test_regex_datacontainer(self):
        self.assertRegex(self.csv_data,gen.DataContainer.pattern)

    def test_type_datacontainer(self):
        m = gen.DataContainer.pattern.match(self.csv_data)
        self.assertEqual(m.group("block"), "csv")
    def test_regex_meta(self):
        self.assertRegex(self.meta_data, gen.MetaTag.pattern)
    def extract_meta_simple(self):
        cnt = self.parse_md(self.meta_data)
        meta = self.site.extract_meta(cnt)
        self.assertEqual(meta, {"title": "My Post", "author": "John Doe", "date": "2022-01-01"})
    
    def test_csv_simple(self):
        cnt = self.parse_md(self.csv_data)
        self.assertEqual(cnt.children[0].children[0].rows, '1,2,3\n4,5,6')
    
    def test_wiki_link(self):
        self.assertRegex(self.wiki_link, gen.WikiLink.pattern)
        m = gen.WikiLink.pattern.match(self.wiki_link)
        self.assertEqual(m.group("link"), "03_WikiLink")
        self.assertEqual(m.group("order"), "03")
    def test_complex_csv(self):
        cnt = self.parse_md(self.complex_csv)
        self.assertEqual(cnt.children[1].children[0].rows, '2,3,4\n5,6,7')
    def test_render_post(self):
        cnt = self.site.md(self.post)
        print(cnt)
        self.assertIn("02_somelink.html", cnt)
        self.assertIn("<td>7</td>",cnt)
        self.assertIn("<table>", cnt)
    def test_extract_meta_post(self):
        cnt = self.parse_md(self.post)
        meta = self.site.extract_meta(cnt)
        self.assertEqual(meta, {"author": "John Doe", "date": "2022-01-01"})

    
    
        


if __name__ == '__main__':
    unittest.main()

        