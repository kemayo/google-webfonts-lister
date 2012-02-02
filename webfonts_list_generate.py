#!/usr/bin/python

import urllib2
import gzip
import StringIO
import re

__version__ = 1
USER_AGENT = 'dAlist/%s +http://dt.deviantart.com' % __version__
GOOGLE = 'http://www.google.com'
WEBFONTS = 'https://googlefontdirectory.googlecode.com/hg/'
SPECIMEN = 'http://www.google.com/webfonts/specimen/'

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


def extract_family(info, family_url):
    family = re.findall(r"^family: (.+)$", info, re.MULTILINE)
    if not family:
        # A lot of them have this command left in the metadata file
        family = re.findall(r'--chars="([^"]+)"', info)
    if not family:
        # Failing that, try a capitalized version of the URL
        family = [family_url.capitalize()]
    if len(family) != 1:
        print "too many results for family", family_url
        return
    return family[0]


def get_font_data(family_url):
    try:
        info = _fetch(WEBFONTS + family_url + '/METADATA')
    except Exception, e:
        print e
        return

    # We have metadata, such as https://googlefontdirectory.googlecode.com/hg/sueellenfrancisco/METADATA
    # ...now we need to get actual useful information.

    family = extract_family(info, family_url)
    if not family:
        print "family troubles", family_url
        return

    # We have the *properly capitalized/spaced* name of the family (i.e. why we needed that metadata)
    # we use that to fetch a specimen page like www.google.com/webfonts/specimen/Sue+Ellen+Francisco
    specimen_url = SPECIMEN + family.replace(' ', '+')
    specimen = _fetch(specimen_url)
    if not specimen:
        print "No specimen"
        return
    font_param = re.findall(r'<link href=\'//fonts.googleapis.com/css\?family=' + family.replace(' ', '\\+') + r':([^&]+)', specimen)
    if not (font_param and len(font_param) == 1):
        print "Can't find CSS link", specimen_url, font_param
        return
    font_param = font_param[0]

    return {family: font_param.split(',')}


if __name__ == "__main__":
    # print get_font_data(WEBFONTS + 'abrilfatface/')
    page = _fetch(WEBFONTS)
    # fetched the listing of a mercurial repo...

    families = re.findall(r'<li><a href="([^"]+)/"', page)

    font_data = []
    for family_url in families:
        print 'fetching', family_url
        data = get_font_data(family_url)
        # break
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
