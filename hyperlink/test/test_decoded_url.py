# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from hyperlink import DecodedURL

BASIC_URL = "http://xn--bcher-kva.ch:8080/a/nice%20nice/path/?zot=23%25&zut#frég"


def test_durl_basic():
    durl = DecodedURL.from_text(BASIC_URL)

    assert durl.host == 'bücher.ch'
    assert durl.port == 8080
    assert durl.path == ('a', 'nice nice', 'path', '')
    assert durl.fragment == 'frég'
    assert durl.get('zot') == ['23%']
