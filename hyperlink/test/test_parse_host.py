
import socket

from hyperlink import _url_codecs

from .common import HyperlinkTestCase
from .ipv6_test_cases import DW_IPv6_TEST_CASES


class TestParseHost(HyperlinkTestCase):
    def test_parse_host_dw_ipv6(self):
        for group in DW_IPv6_TEST_CASES:
            for ip_text, is_valid, _ in group['tests']:
                if is_valid:
                    family, host = _url_codecs.parse_host(ip_text)
                    assert family == socket.AF_INET6
                    assert ip_text == host
                    continue

                with self.assertRaises(_url_codecs.URLParseError):
                    family, _ = _url_codecs.parse_host(ip_text)
                    # in cases where an error isn't raised, we
                    # check that we parsed something other than
                    # ipv6 and make the necessary correction
                    if family != socket.AF_INET6:
                        raise _url_codecs.URLParseError
        return
