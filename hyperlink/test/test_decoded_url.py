# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from hyperlink import DecodedURL

BASIC_URL = 'http://example.com/#'
TOTAL_URL = "https://%75%73%65%72:%00%00%00%00@xn--bcher-kva.ch:8080/a/nice%20nice/path/?zot=23%25&zut#frég"


def test_durl_basic():
    bdurl = DecodedURL.from_text(BASIC_URL)
    assert bdurl.scheme == 'http'
    assert bdurl.host == 'example.com'
    assert bdurl.port == 80
    assert bdurl.path == ('',)
    assert bdurl.fragment == ''

    durl = DecodedURL.from_text(TOTAL_URL)

    assert durl.host == 'bücher.ch'
    assert durl.port == 8080
    assert durl.path == ('a', 'nice nice', 'path', '')
    assert durl.fragment == 'frég'
    assert durl.get('zot') == ['23%']
