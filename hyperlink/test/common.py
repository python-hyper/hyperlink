

from unittest import TestCase

import socket
try:
    from socket import inet_pton
except ImportError:  # pragma: no cover
    # based on https://gist.github.com/nnemkin/4966028
    # this code only applies on Windows Python 2.7
    import ctypes

    class _sockaddr(ctypes.Structure):
        _fields_ = [("sa_family", ctypes.c_short),
                    ("__pad1", ctypes.c_ushort),
                    ("ipv4_addr", ctypes.c_byte * 4),
                    ("ipv6_addr", ctypes.c_byte * 16),
                    ("__pad2", ctypes.c_ulong)]

    WSAStringToAddressA = ctypes.windll.ws2_32.WSAStringToAddressA
    WSAAddressToStringA = ctypes.windll.ws2_32.WSAAddressToStringA

    def inet_pton(address_family, ip_string):
        addr = _sockaddr()
        ip_string = ip_string.encode('ascii')
        addr.sa_family = address_family
        addr_size = ctypes.c_int(ctypes.sizeof(addr))

        if WSAStringToAddressA(ip_string, address_family, None, ctypes.byref(addr), ctypes.byref(addr_size)) != 0:
            raise socket.error(ctypes.FormatError())

        if address_family == socket.AF_INET:
            return ctypes.string_at(addr.ipv4_addr, 4)
        if address_family == socket.AF_INET6:
            return ctypes.string_at(addr.ipv6_addr, 16)
        raise socket.error('unknown address family')



class HyperlinkTestCase(TestCase):
    """This type mostly exists to provide a backwards-compatible
    assertRaises method for Python 2.6 testing.
    """
    def assertRaises(self, excClass, callableObj=None, *args, **kwargs):
        """Fail unless an exception of class excClass is raised
           by callableObj when invoked with arguments args and keyword
           arguments kwargs. If a different type of exception is
           raised, it will not be caught, and the test case will be
           deemed to have suffered an error, exactly as for an
           unexpected exception.

           If called with callableObj omitted or None, will return a
           context object used like this::

                with self.assertRaises(SomeException):
                    do_something()

           The context manager keeps a reference to the exception as
           the 'exception' attribute. This allows you to inspect the
           exception after the assertion::

               with self.assertRaises(SomeException) as cm:
                   do_something()
               the_exception = cm.exception
               self.assertEqual(the_exception.error_code, 3)
        """
        context = _AssertRaisesContext(excClass, self)
        if callableObj is None:
            return context
        with context:
            callableObj(*args, **kwargs)


class _AssertRaisesContext(object):
    "A context manager used to implement HyperlinkTestCase.assertRaises."

    def __init__(self, expected, test_case):
        self.expected = expected
        self.failureException = test_case.failureException

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        if exc_type is None:
            exc_name = self.expected.__name__
            raise self.failureException("%s not raised" % (exc_name,))
        if not issubclass(exc_type, self.expected):
            # let unexpected exceptions pass through
            return False
        self.exception = exc_value  # store for later retrieval
        return True
