#!/usr/bin/python

import urllib2
import gzip
import httplib
import StringIO
import re

__version__ = 1
USER_AGENT = 'dAlist/%s +http://dt.deviantart.com' % __version__
GOOGLE = 'http://www.google.com'
WEBFONTS = GOOGLE + '/webfonts'

CACHE = {}

def _fetch(url, cached = True, ungzip = True):
    """A generic URL-fetcher, which handles gzipped content, returns a string"""
    if cached and url in CACHE:
        return CACHE[url]
    request = urllib2.Request(url)
    request.add_header('Accept-encoding', 'gzip')
    request.add_header('User-agent', USER_AGENT)
    f = urllib2.urlopen(request)
    data = f.read()
    if ungzip and f.headers.get('content-encoding', '') == 'gzip':
        data = gzip.GzipFile(fileobj=StringIO(data)).read()
    f.close()
    CACHE[url] = data
    return data

def extract_font_urls(page):
    return re.findall(r'href="(/webfonts/family\?family=[^&]+&(?:amp)?;subset=latin)"', page)

def extract_list_urls(page):
    return re.findall(r'href="(/webfonts/list\?family=[^&]+&(?:amp)?;subset=latin)"', page)

def handle_font(font_url):
    """Fetches information about the family
    
    It'd be nice if this didn't have to actually load the page... but the full parameter isn't available on
    the initial page, unfortunately
    """
    font_page = _fetch(GOOGLE + font_url)
    
    parameter_match = re.search(r'<span id="urlFamily">([^<]+)</span>', font_page)
    if not parameter_match:
        print "skipping %s no parameter" % font_url
        return False
    parameter = parameter_match.group(1)
    
    name_match = re.search(r'<h2><span[^>]+>([^<]+)</span></h2>', font_page)
    if not name_match:
        print "skipping %s no name" % font_url
        return False
    name = name_match.group(1)
    
    return name, parameter

def handle_list(list_url):
    page = _fetch(GOOGLE + list_url)
    return extract_font_urls(page)

if __name__ == "__main__":
    page = _fetch(WEBFONTS)
    fonts = extract_font_urls(page)
    lists = extract_list_urls(page)
    
    for l in lists:
        fonts.extend(handle_list(l))
    
    print "%d fonts found" % len(fonts)
    
    font_details = []
    for font in fonts:
        font_details.append(handle_font(font))
    
    # I could just do this with map if I didn't want nice linebreaks. ;_;
    out = []
    line_length = 0
    font_details.sort()
    for f in font_details:
        o = "'%s' => '%s', " % f
        line_length = line_length + len(o)
        if line_length > 90:
            out.append("\n")
            line_length = len(o)
        out.append(o)
    print ''.join(out)
