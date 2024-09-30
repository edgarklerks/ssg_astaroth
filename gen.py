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
   
doc = """
## Some csv data

[csv]
a,b,c
d,e,f
g,h,i
[csv]
[[test]]
""" 

menu_items = """[[home]]
[[test]]
""".split("\n")

     

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
        
         

SSG = m.MarkoExtension(elements=[DataContainer, WikiLink], renderer_mixins=[DataContainerRenderer, WikiRenderer])

md = m.Markdown(extensions=[SSG])

pl = ProjectLoader()
base_url = "https://astorath.cloud/"
menu = [] # ["<ul>"]

for order, fp, nm in pl.gen_posts():
    (nm, _) = nm.split(".", 1)
    item = "[[{}]]".format(nm)
    menu.append(md(item))

menu = "\n".join(menu)

resources = md(pl.get_component_content("resources"))

for order, fp, nm in pl.gen_posts():
    (nm,_) = nm.split(".", 1)
    cnt = pl.get_post_content(fp)
    cnt = md(cnt)
    with open("src/{}.html".format(nm), "w+") as f: 
        page_url = base_url + nm + ".html" 
        page_id = nm
        f.write(pl.template('page.html', menu=menu, content=cnt, resources=resources, page_id=page_id, page_url=page_url))


index_page = ""
for order, fp, nm in heapq.nsmallest(9, pl.gen_posts()):
    (nm,_) = nm.split(".", 1)

    cnt = pl.get_post_content(fp)
    cnt = md(cnt)
    index_page += pl.template("section.html", content=cnt)

page_url = base_url + "index.html" 
page_id = "index"
with open("src/index.html", "w+") as f: 
    f.write(pl.template('page.html', menu=menu, content=index_page, resources=resources, page_id=page_id, page_url=page_url))



