# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from hyperlink import parse, EncodedURL, DecodedURL

BASIC_URL = 'http://example.com/#'
TOTAL_URL = "https://%75%73%65%72:%00%00%00%00@xn--bcher-kva.ch:8080/a/nice%20nice/./path/?zot=23%25&zut#frég"
UNDECODABLE_FRAG_URL = TOTAL_URL + '%C3'

def test_parse():
    purl = parse(TOTAL_URL)
    assert isinstance(purl, DecodedURL)
    assert purl.user == 'user'
    assert purl.get('zot') == ['23%']
    assert purl.fragment == 'frég'

    purl2 = parse(TOTAL_URL, decoded=False)
    assert isinstance(purl2, EncodedURL)
    assert purl2.get('zot') == ['23%25']

    try:
        purl3 = parse(UNDECODABLE_FRAG_URL)
    except UnicodeDecodeError:
        pass
    else:
        assert False, 'expected UnicodeDecodeError due to parse(lazy=False) by default'

    try:
        purl3 = parse(UNDECODABLE_FRAG_URL, lazy=True)
    except UnicodeDecodeError:
        assert False, 'expected UnicodeDecodeError due to parse(lazy=True)'

    try:
        purl3.fragment
    except UnicodeDecodeError:
        pass
    else:
        assert False, 'expected UnicodeDecodeError due to undecodable fragment'
