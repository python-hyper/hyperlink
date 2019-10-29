try:
    from socket import inet_pton
except ImportError:
    import socket

    from .common import HyperlinkTestCase
    from .._socket import inet_pton


    class TestSocket(HyperlinkTestCase):
        def test_inet_pton_ipv4_valid(self):
            data = inet_pton(socket.AF_INET, "127.0.0.1")
            assert isinstance(data, bytes)

        def test_inet_pton_ipv4_bogus(self):
            with self.assertRaises(socket.error):
                inet_pton(socket.AF_INET, "blah")

        def test_inet_pton_ipv6_valid(self):
            data = inet_pton(socket.AF_INET6, "::1")
            assert isinstance(data, bytes)

        def test_inet_pton_ipv6_bogus(self):
            with self.assertRaises(socket.error):
                inet_pton(socket.AF_INET6, "blah")

        def test_inet_pton_bogus_family(self):
            # Find an integer not associated with a known address family
            i = int(socket.AF_INET6) + 100
            while True:
                if i != socket.AF_INET and i != socket.AF_INET6:
                    break
                i += 100

            with self.assertRaises(socket.error):
                inet_pton(i, "blah")
