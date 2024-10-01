#!env python
import marko as m
import marko.inline as mi
import re
import unittest
import pprint
import csv
import jinja2
import os 
import posix
import heapq
import itertools


class MetaTag(mi.InlineElement):
    priority = 5
    open = r"\|meta\|"
    close = r"\|meta\|"
    attr = r"(?P<key>[\w]+):(?P<val>[\s\w\d_,-]+)"
    pattern = re.compile(fr"""
                        {open}\s* # OPENING tag
                        (?P<attrs>(({attr})\n?)+) # Get all attributes
                        {close} # CLOSED tag
                         """, re.MULTILINE | re.VERBOSE )
    def __init__(self, match):
        attrs = [attr.strip().split(":") for attr in match.group("attrs").split("\n")] 
        self.attrs = {}
        for attr in attrs:
            if len(attr) == 2:
                k = attr[0].strip()
                v = attr[1].strip()
                self.attrs[k] = v


                

class MetaTagRenderer(object):
    def render_meta_tag(self, element):
        return ''

class DataContainer(mi.InlineElement):
    priority = 6
    open = r"\[(?P<block>data|csv)\]"
    close = r"\[(?P=block)\]"
    cols = r"[,\w\s]+"
    rows = fr"(?P<rows>{cols})"
    pattern = re.compile(fr"""
                        {open} # OPENING tag
                        {rows}
                        {close} # CLOSED tag
                         """, re.MULTILINE | re.VERBOSE )
    parse_children = False
    def __init__(self, match):
        self.rows = match.group('rows')
        self.type = match.group('block')
        pass


class WikiLink(mi.InlineElement):
    priority = 5
    pattern = re.compile(r"\[\[(?P<link>[\w_]+)\]\]", re.VERBOSE)

    def __init__(self, match):
        self.link = match.group('link')
    
class WikiRenderer(object):
    def render_wiki_link(self, element):
        print(element.link)
        (_, nm) = element.link.split("_", 1)
        nm = nm.replace("_"," ")
        return f"<a href='./{element.link}.html'>{nm}</a>"

        

class DataContainerRenderer(object):
    def render_data_container(self, element):
        if element.type == 'data':
            return element.rows 
        elif element.type == 'csv':
            q =  list(csv.reader(element.rows.split("\n")))
            output = []
            for r in q:
                if not r:
                    continue  # skip empty rows
                line = ["<tr>"]
                for e in r:
                    line.append(f"<td>{e}</td>")
                line.append("</tr>")
                output.append(" ".join(line)) 
            
            return "<table>" + "\n".join(output) + "</table>" 
   

class ProjectLoader(object):
    def __init__(self):
        self.loader = jinja2.FileSystemLoader("./templates/")
        self.env = jinja2.Environment(loader=self.loader)
    
    def template(self, name, **kwargs):
        template = self.env.get_template(name)
        return template.render(**kwargs)
    def gen_posts(self):
        posts = []
        paths = posix.listdir("posts")
        nr_paths = len(paths)
        for fp in paths:
            (order, nm) = fp.split("_", 1)
            # Reverse order (nr_paths - order)
            heapq.heappush(posts, (nr_paths - int(order), "posts/{}_{}".format(order, nm,), fp))
        return posts
    def get_post_content(self, fp):
        with open(fp, "r") as f:
            return f.read()
    def get_component_content(self,fp):
        with open("components/{}.md".format(fp), "r") as f:
            return f.read()
        
        
        
                
class Site(object):
    def __init__(self, base_url : str, title : str, components : [str]) -> None:
        self.pl = ProjectLoader()
        self.title = title
        self.base_url = base_url
        self.components = components
        self.menu_items = []
        self.md = m.Markdown(extensions=[
            m.MarkoExtension(
                elements=[
                    MetaTag, 
                    DataContainer, 
                    WikiLink], 
                renderer_mixins=[
                    DataContainerRenderer, 
                    WikiRenderer, 
                    MetaTagRenderer])]
        )

    def build_component_dict(self):
        self.component_dict = {k: self.get_component(k) for k in self.components}
    def remove_ext(self, nm : str) -> str:
        return nm.split(".", 1)[0]

    def generate_menu_entries(self):
        self.menu_items = [self.md(f"[[{self.remove_ext(nm)}]]") for _, _, nm in self.pl.gen_posts()]
        
    def get_component(self, name : str):
        return self.md(self.pl.get_component_content(name))
 
    def extract_meta(self, doc):
        if isinstance(doc, str): 
            return None
        if doc.get_type() == "MetaTag":
            return doc.attrs
        elif hasattr(doc, "children"):
            for el in doc.children:
                s = extract_meta(el)
                if s: 
                    return s
        else: 
                return None

    def render_meta(self, meta):
        if not meta:
            return ""
        output = ""
        for k, v in meta.items():
            output += "<meta name=\"{}\" content=\"{}\" />\n".format(k,v)
            if k == "title":
                output += "<title>{} - {}</title>\n".format(v, self.title)
                output += "<meta property=\"og:title\" content=\"{} - {}\" />\n".format(v, self.title)
                output += "<meta name=\"twitter:title\" content=\"{} - {}\" />\n".format(v, self.title)
        return output


    def build_posts(self):
        for order, fp, nm in self.pl.gen_posts():
            cnt = self.md.parse(self.pl.get_post_content(fp))
            meta = self.render_meta(self.extract_meta(cnt))
            cnt = self.md.render(cnt)
            self.write_post(self.remove_ext(nm), cnt, meta)
    
    def write_post(self, nm, cnt, meta):
        with open("src/{}.html".format(nm), "w+") as f:
            page_url = self.base_url + nm  + ".html"
            page_id = nm
            f.write(self.pl.template('page.html',
                                    meta=meta,
                                    menu=self.menu,
                                    content=cnt, 
                                    page_id=page_id,
                                    page_url=page_url,
                                    **self.component_dict
                                     ))

        
            
    def get_generic_meta(self,v):
        output = ""
        output += "<title>{} - {}</title>\n".format(v, self.title)
        output += "<meta property=\"og:title\" content=\"{} - {}\" />\n".format(v, self.title)
        output += "<meta name=\"twitter:title\" content=\"{} - {}\" />\n".format(v, self.title)
        return output
            
    def build_index_page(self):
        index_page = ""
        for order, fp, nm in heapq.nsmallest(9, self.pl.gen_posts()):
            cnt = self.pl.get_post_content(fp)
            cnt = self.md(cnt)
            index_page += self.pl.template("section.html", content=cnt)
        
        page_id = "index"
        self.write_post(page_id, index_page, self.get_generic_meta("index"))
    

    def build_site(self):
        self.generate_menu_entries()
        self.build_component_dict()
        self.menu = "\n".join(self.menu_items)
        self.build_posts()
        self.build_index_page()




site = Site("https://astorath.cloud/", "Astaroth",
            ["resources"])
site.build_site()



