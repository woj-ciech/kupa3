#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib.request
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse
import networkx as nx
import matplotlib.pyplot as plt
import argparse
import sys

desc = """           (                 ,&&&.
            )                .,.&&
           (  (              \=__/
               )             ,'-'.
         (    (  ,,      _.__|/ /|
          ) /\ -((------((_|___/ |
        (  // | (`'      ((  `'--|
      _ -.;_/ \\--._      \\ \-._/.
     (_;-// | \ \-'.\    <_,\_\`--'|
     ( `.__ _  ___,')      <_,-'__,'
jrei  `'(_ )_)(_)_)' asciiart.eu\n
Tracking the trackers. Draw connections between scripts and domains on website.
medium.com/@woj_ciech github.com/woj-ciech
example: python3 kupa3.py https://nsa.gov\n"""

print (desc)

parser = argparse.ArgumentParser(
    formatter_class=argparse.ArgumentDefaultsHelpFormatter  # added to show default value
)

parser.add_argument("--url", help="URL of website", default="https://nsa.gov")
G = nx.Graph()

args = parser.parse_args()

url = args.url

# two regexps, i have no idea why only one does not work
regex1 = r"""(?i)\b((?:https?:(?:\/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|biz|int|at|ca|eu|fr)\/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|biz|int|at)\b\/?(?!@)))"""
regex2 = r"""(?i)\b((?:https?:(?:\/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|mil|info|at}uk|us)\/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|biz|int)\b\/?(?!@)))"""

parsed_arg = urlparse(url)
try:
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:64.0) Gecko/20100101 Firefox/64.0'})
except Exception as e:
    print(str(e))
    sys.exit()

G.add_node(url)


######It gets everything what is inside <script> tag in html code
def getscripts(url):
    list_of_scripts = []

    # get website
    try:
        oururl = urllib.request.urlopen(url, timeout=10).read()
    except Exception as e:
        print(e)
        sys.exit()
    soup = BeautifulSoup(oururl, 'html.parser')

    # find <script> tags
    for script in soup.findAll("script"):
        list_of_scripts.append(script.extract())

    return list_of_scripts


non_js_url = []
js_url = []


# It gets links from javascript code
def getlinks(request, depth=1):
    try:
        req = urllib.request.urlopen(request, timeout=10).read()

        link2 = re.findall(regex2, str(req))
        # for every link in found links
        for j in link2:
            try:
                second_depth = re.split(r"""\"|\\|'| |\(|""", j)  # xD
                second_depth_url = second_depth[0]  # clean url
                parsed_url = urlparse(second_depth_url)
                if second_depth_url not in js_url:  # check for repetitive to avoid infinite loop
                    if '.js' in parsed_url[2] and 'github' not in parsed_url[1]:  # check if it has javascript extension
                        if not second_depth_url.startswith(
                                ('http://', 'https://')):  # check if url starts with http or https
                            second_depth_url = 'https://' + second_depth_url  # if not add it

                        # Magic?
                        if depth > 1:
                            G.add_edge(request, second_depth_url)
                        else:
                            G.add_edge(request, second_depth_url)

                        print("----" * depth + second_depth_url)
                        js_url.append(second_depth_url)
                        getlinks(second_depth_url, depth=depth + 1)  # recursion

                    else:
                        if parsed_url[1].endswith(("com", "net", "org", "edu", "io")) and parsed_url[
                            1] not in non_js_url:  # Check if url is domain indeed, and if it's unique
                            print("----" * depth + parsed_url[1])
                            G.add_edge(request, second_depth_url)
                            non_js_url.append(parsed_url[1])  # append to list to avoid repetitive
                else:
                    # print ("Infinite LOOP")
                    break
            except Exception as e:
                print("----" * depth + str(e))

    except Exception as e:
        print("----" * depth + str(e))

#It checks if <script> tag has a 'src' attribute, if is save it to list | if not look inside the script <script> whatever </script>
def extractscripts(list_of_scripts):
    urls = []
    for i in list_of_scripts:
        src = 0
        try:
            if i.attrs['src']:
                k = i.attrs['src']
                # I suspect if link start with '//' it refers to external resources, for example src=//www.subdomain.domain.com/a.js
                if i.attrs['src'].startswith("//"):
                    k = "https:" + i.attrs['src']
                # If it starts with '/' it refers to local resource like /application/static/tracking.js
                elif i.attrs['src'].startswith("/"):
                    k = url + i.attrs['src']

                urls.append(k)
                src = 1
        except:
            src = 0

        if not src: #If there is not 'src' attribute
            links = re.findall(regex1, str(i))  # Find all links from javascript code
            if links:
                for j in links:
                    if '.js' in j:
                        clean_link = re.split(r"""\"|\\|'| |\(|""", j)  # hehe
                        urls.append(clean_link[0])
    return urls

# Start
scripts = getscripts(url) #Get all scripts
extracted_scripts = extractscripts(scripts)  # Extract 'src' from script and look for url directly inside of the script

print("-------------------- " + url + " -----------------------")
for script in extracted_scripts:  # add http or https
    if not script.startswith(('http://', 'https://')):
        script = 'https://' + script

    print(script)
    G.add_edge(url, script)
    getlinks(script)

nx.draw(G, with_labels=True)
plt.savefig("simple_path.png")  # save as png
nx.write_gexf(G, parsed_arg[1] + ".gexf")
print("Saved as " + parsed_arg[1] + ".gexf")
plt.show()  # display
