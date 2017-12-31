# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from hyperlink import DecodedURL

BASIC_URL = 'http://example.com/#'
TOTAL_URL = "https://%75%73%65%72:%00%00%00%00@xn--bcher-kva.ch:8080/a/nice%20nice/./path/?zot=23%25&zut#frég"


def test_durl_basic():
    bdurl = DecodedURL.from_text(BASIC_URL)
    assert bdurl.scheme == 'http'
    assert bdurl.host == 'example.com'
    assert bdurl.port == 80
    assert bdurl.path == ('',)
    assert bdurl.fragment == ''

    durl = DecodedURL.from_text(TOTAL_URL)

    assert durl.scheme == 'https'
    assert durl.host == 'bücher.ch'
    assert durl.port == 8080
    assert durl.path == ('a', 'nice nice', '.', 'path', '')
    assert durl.fragment == 'frég'
    assert durl.get('zot') == ['23%']

    assert durl.user == 'user'
    assert durl.password == '\0\0\0\0'
    assert durl.userinfo == ('user', '\0\0\0\0')


def test_passthroughs():
    # just basic tests for the methods that more or less pass straight
    # through to the underlying URL

    durl = DecodedURL.from_text(TOTAL_URL)
    assert durl.sibling('te%t').path[-1] == 'te%t'
    assert durl.child('../test2%').path[-1] == '../test2%'
    assert durl.click('/').path[-1] == ''
    assert durl.user == 'user'

    assert '.' in durl.path
    assert '.' not in durl.normalize().path

    assert durl.to_uri().fragment == 'fr%C3%A9g'
    assert ' ' in durl.to_iri().path[1]

    assert durl.to_text(with_password=True) == TOTAL_URL

    assert durl.absolute
    assert durl.rooted


def test_repr():
    durl = DecodedURL.from_text(TOTAL_URL)
    assert repr(durl) == 'DecodedURL(url=' + repr(durl._url) + ')'


def test_query_manipulation():
    durl = DecodedURL.from_text(TOTAL_URL)

    assert durl.get('zot') == ['23%']
    durl = durl.add(' ', 'space')
    assert durl.get(' ') == ['space']
    durl = durl.set(' ', 'spa%ed')
    assert durl.get(' ') == ['spa%ed']

    durl = DecodedURL(url=durl.to_uri())
    assert durl.get(' ') == ['spa%ed']
    durl = durl.remove(' ')
    assert durl.get(' ') == []

    durl = DecodedURL.from_text('/?%61rg=b&arg=c')
    assert durl.get('arg') == ['b', 'c']

    assert durl.set('arg', 'd').get('arg') == ['d']


def test_equivalences():
    durl = DecodedURL.from_text(TOTAL_URL)
    durl2 = DecodedURL.from_text(TOTAL_URL)
    burl = DecodedURL.from_text(BASIC_URL)

    assert durl == durl
    assert durl == durl2
    assert durl != burl
    assert durl != None
    assert durl != durl._url

    durl_map = {}
    durl_map[durl] = durl
    durl_map[durl2] = durl2

    assert len(durl_map) == 1


def test_replace_roundtrip():
    durl = DecodedURL.from_text(TOTAL_URL)

    durl2 = durl.replace(scheme=durl.scheme,
                         host=durl.host,
                         path=durl.path,
                         query=durl.query,
                         fragment=durl.fragment,
                         port=durl.port,
                         rooted=durl.rooted,
                         userinfo=durl.userinfo,
                         uses_netloc=durl.uses_netloc)

    assert durl == durl2
