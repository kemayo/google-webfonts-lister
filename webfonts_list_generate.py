#!/usr/bin/python

import urllib2
import gzip
import StringIO
import re

__version__ = 1
USER_AGENT = 'dAlist/%s +http://dt.deviantart.com' % __version__
GOOGLE = 'http://www.google.com'
WEBFONTS = 'https://googlefontdirectory.googlecode.com/hg/'

CACHE = {}


def _fetch(url, data=None, cached=True, ungzip=True):
    """A generic URL-fetcher, which handles gzipped content, returns a string"""
    if cached and url in CACHE:
        return CACHE[url]
    request = urllib2.Request(url)
    request.add_header('Accept-encoding', 'gzip')
    request.add_header('User-agent', USER_AGENT)
    f = urllib2.urlopen(request, data)
    data = f.read()
    if ungzip and f.headers.get('content-encoding', '') == 'gzip':
        data = gzip.GzipFile(fileobj=StringIO(data)).read()
    f.close()
    CACHE[url] = data
    return data


def get_font_data(url):
    try:
        info = _fetch(url + 'md5sum')
    except Exception, e:
        print e
        return

    font_data = {}
    for f in re.findall("^([^:]+):([^,]+),", info, re.MULTILINE):
        if f[0] not in font_data:
            font_data[f[0]] = []
        value = f[1].replace(':', '').replace('normal', '')
        font_data[f[0]].append(value or 'normal')

    return font_data

if __name__ == "__main__":
    page = _fetch(WEBFONTS)
    # fetched the listing of a mercurial repo...

    families = re.findall(r'<li><a href="([^"]+/)"', page)

    font_data = []
    for family_url in families:
        print 'fetching', family_url
        data = get_font_data(WEBFONTS + family_url)
        if not data:
            print "Couldn't find data from", family_url
            continue

        font_data.extend(data.items())

    print "%d fonts found" % len(font_data)

    # I could just do this with map if I didn't want nice linebreaks. ;_;
    out = []
    line_length = 0
    font_data.sort()
    for f in font_data:
        family = f[0]
        types = ','.join(f[1])
        if types == 'normal':
            types = ''
        if types:
            types = ':' + types
        o = "'%s' => '%s%s', " % (family, family.replace(' ', '+'), types)
        line_length = line_length + len(o)
        if line_length > 90:
            out.append("\n")
            line_length = len(o)
        out.append(o)
    print ''.join(out)
