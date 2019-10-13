import sys

from lxml import etree


if sys.version_info.major == 2:
    from urllib import urlopen
else:
    from urllib.request import urlopen


def video_title(youtube_url):
    c = urlopen(youtube_url).read()
    root_node = etree.HTML(c)
    return root_node.xpath("//span[@id='eow-title']/@title")
