# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from .common import HyperlinkTestCase
from .._url import register_scheme, URL


class TestSchemeRegistration(HyperlinkTestCase):

    def test_register_scheme_basic(self):
        register_scheme('deltron', uses_netloc=True, default_port=3030)

        u1 = URL.from_text('deltron://example.com')
        assert u1.scheme == 'deltron'
        assert u1.port == 3030
        assert u1.uses_netloc is True

        # test netloc works even when the original gives no indication
        u2 = URL.from_text('deltron:')
        u2 = u2.replace(host='example.com')
        assert u2.to_text() == 'deltron://example.com'

        # test default port means no emission
        u3 = URL.from_text('deltron://example.com:3030')
        assert u3.to_text() == 'deltron://example.com'

        register_scheme('nonetron', default_port=3031)

    def test_register_no_netloc_scheme(self):
        register_scheme('netlocless', uses_netloc=False)

    def test_register_no_netloc_with_port(self):
        with self.assertRaises(ValueError):
            register_scheme('badnetlocless', uses_netloc=False, default_port=7)

    def test_register_invalid_uses_netloc(self):
        with self.assertRaises(ValueError):
            register_scheme('lol', uses_netloc=lambda: 'nope')

    def test_register_invalid_port(self):
        with self.assertRaises(ValueError):
            register_scheme('nope', default_port=lambda: 'lol')
