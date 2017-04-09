# -*- coding: utf-8 -*-
u"""Hyperlink provides Pythonic URL parsing, construction, and rendering.

Usage is straightforward:

   >>> url = URL.from_text('http://github.com/mahmoud/hyperlink?utm_source=docs')
   >>> print(url.host)
   github.com
   >>> secure_url = url.replace(scheme=u'https')
   >>> print(secure_url.get('utm_source')[0])
   docs


A Tale of Two Representations
-----------------------------

The URL is a powerful construct with two canonical representations
that have historically caused some confusion: the URI and the
IRI. (The W3C even recognized this themselves.) Hyperlink's URL sets
this record straight. Simply:

* URI: Fully-encoded, suitable for network transfer
* IRI: Fully-decoded, suitable for display (e.g., in a browser bar)

   >>> url = URL.from_text('http://example.com/café')
   >>> url.to_uri().to_text()
   u'http://example.com/caf%C3%A9'

Ah, there's that percent encoding, characteristic of URIs. Still,
Hyperlink's distinction between URIs and IRIs is limited to
output. Input can contain any mix of percent encoding and Unicode,
without issue:

   >>> url = URL.from_text('http://example.com/caf%C3%A9/au láit')
   >>> print(url.to_iri().to_text())
   http://example.com/café/au láit
   >>> print(url.to_uri().to_text())
   http://example.com/caf%C3%A9/au%20l%C3%A1it

Note that the URI and IRI representation of the same resource are
still different URLs:

   >>> url.to_uri() == url.to_iri()
   False

Immutability
------------

Hyperlink's URL is also notable for being an immutable
representation. Once constructed, instances are not changed. Methods
like :meth:`~URL.click()`, :meth:`~URL.set()`, and
:meth:`~URL.replace()`, all return new URL objects. This enables URLs
to be used in sets, as well as dictionary keys.

Query Parameters
----------------

One of the URL format's most powerful features is query parameters,
encoded in the query string portion of the URL.

Query parameters are actually a type of "multidict", where a given key
can have multiple values. This is why the :meth:`~URL.get()` method
returns a list of strings. Keys can also have no value, which is
conventionally interpreted as a truthy flag.

   >>> url = URL.from_text('http://example.com/?a=b&c')
   >>> url.get(u'a')
   ['b']
   >>> url.get(u'c')
   [None]
   >>> url.get('missing')  # returns None
   []


Values can be modified and added using :meth:`~URL.set()` and
:meth:`~URL.add()`.

   >>> url = url.add(u'x', u'x')
   >>> url = url.add(u'x', u'y')
   >>> url.to_text()
   u'http://example.com/?a=b&c&x=x&x=y'
   >>> url = url.set(u'x', u'z')
   >>> url.to_text()
   u'http://example.com/?a=b&c&x=z'


Values can be unset with :meth:`~URL.remove()`.

   >>> url = url.remove(u'a')
   >>> url = url.remove(u'c')
   >>> url.to_text()
   u'http://example.com/?x=z'

Note how all modifying methods return copies of the URL and do not
mutate the URL in place, much like methods on strings.
"""

import re
import string

import socket
try:
    from socket import inet_pton
except ImportError:
    # from https://gist.github.com/nnemkin/4966028
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


try:
    from urllib import unquote as urlunquote
except ImportError:
    from urllib.parse import unquote_to_bytes as urlunquote

from unicodedata import normalize

unicode = type(u'')
try:
    unichr
except NameError:
    unichr = chr  # py3
NoneType = type(None)


# RFC 3986 section 2.2, Reserved Characters
_genDelims = u':/?#[]@'
_subDelims = u"!$&'()*+,;="

_validInPath = _subDelims + u':@'
_validInFragment = _validInPath + u'/?'
_validInQuery = (_validInFragment
                 .replace(u'&', u'').replace(u'=', u'').replace(u'+', u''))

_unspecified = object()


# The unreserved URI characters (per RFC 3986 Section 2.3)
_UNRESERVED_CHARS = frozenset('~-._0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                              'abcdefghijklmnopqrstuvwxyz')

# URL parsing regex (based on RFC 3986 Appendix B, with modifications)
_URL_RE = re.compile(r'^((?P<scheme>[^:/?#]+):)?'
                     r'((?P<_netloc_sep>//)(?P<authority>[^/?#]*))?'
                     r'(?P<path>[^?#]*)'
                     r'(\?(?P<query>[^#]*))?'
                     r'(#(?P<fragment>.*))?')
_SCHEME_RE = re.compile(r'^[a-zA-Z0-9+-.]*$')


_HEX_CHAR_MAP = dict([((a + b).encode('ascii'),
                       unichr(int(a + b, 16)).encode('charmap'))
                      for a in string.hexdigits for b in string.hexdigits])
_ASCII_RE = re.compile('([\x00-\x7f]+)')


# RFC 3986 section 2.2, Reserved Characters
_GEN_DELIMS = frozenset(u':/?#[]@')
_SUB_DELIMS = frozenset(u"!$&'()*+,;=")
_ALL_DELIMS = _GEN_DELIMS | _SUB_DELIMS

_USERINFO_SAFE = _UNRESERVED_CHARS | _SUB_DELIMS
_USERINFO_DELIMS = _ALL_DELIMS - _USERINFO_SAFE
_PATH_SAFE = _UNRESERVED_CHARS | _SUB_DELIMS | set(u':@%')
_PATH_DELIMS = _ALL_DELIMS - _PATH_SAFE
_FRAGMENT_SAFE = _UNRESERVED_CHARS | _PATH_SAFE | set(u'/?')
_FRAGMENT_DELIMS = _ALL_DELIMS - _FRAGMENT_SAFE
_QUERY_SAFE = _UNRESERVED_CHARS | _FRAGMENT_SAFE - set(u'&=+')
_QUERY_DELIMS = _ALL_DELIMS - _QUERY_SAFE


def _make_quote_map(safe_chars):
    ret = {}
    # v is included in the dict for py3 mostly, because bytestrings
    # are iterables of ints, of course!
    for i, v in zip(range(256), range(256)):
        c = chr(v)
        if c in safe_chars:
            ret[c] = ret[v] = c
        else:
            ret[c] = ret[v] = '%{0:02X}'.format(i)
    return ret


_USERINFO_PART_QUOTE_MAP = _make_quote_map(_USERINFO_SAFE)
_PATH_PART_QUOTE_MAP = _make_quote_map(_PATH_SAFE)
_QUERY_PART_QUOTE_MAP = _make_quote_map(_QUERY_SAFE)
_FRAGMENT_QUOTE_MAP = _make_quote_map(_FRAGMENT_SAFE)


def _encode_path_part(text, maximal=True):
    """Percent-encode a single segment of a URL path.

    Setting *maximal* to False percent-encodes only the reserved
    characters that are syntactically necessary for serialization,
    preserving any IRI-style textual data.

    Leaving *maximal* set to its default True percent-encodes
    everything required to convert a portion of an IRI to a portion of
    a URI.
    """
    if maximal:
        bytestr = normalize('NFC', to_unicode(text)).encode('utf8')
        return u''.join([_PATH_PART_QUOTE_MAP[b] for b in bytestr])
    return u''.join([_PATH_PART_QUOTE_MAP[t] if t in _PATH_DELIMS else t
                     for t in text])


def _encode_query_part(text, maximal=True):
    """
    Percent-encode a single query string key or value.
    """
    if maximal:
        bytestr = normalize('NFC', to_unicode(text)).encode('utf8')
        return u''.join([_QUERY_PART_QUOTE_MAP[b] for b in bytestr])
    return u''.join([_QUERY_PART_QUOTE_MAP[t] if t in _QUERY_DELIMS else t
                     for t in text])


def _encode_fragment_part(text, maximal=True):
    """Quote the fragment part of the URL. Fragments don't have
    subdelimiters, so the whole URL fragment can be passed.
    """
    if maximal:
        bytestr = normalize('NFC', to_unicode(text)).encode('utf8')
        return u''.join([_FRAGMENT_QUOTE_MAP[b] for b in bytestr])
    return u''.join([_FRAGMENT_QUOTE_MAP[t] if t in _FRAGMENT_DELIMS else t
                     for t in text])


def _encode_userinfo_part(text, maximal=True):
    """Quote special characters in either the username or password
    section of the URL.
    """
    if maximal:
        bytestr = normalize('NFC', to_unicode(text)).encode('utf8')
        return u''.join([_USERINFO_PART_QUOTE_MAP[b] for b in bytestr])
    return u''.join([_USERINFO_PART_QUOTE_MAP[t] if t in _USERINFO_DELIMS
                     else t for t in text])


# This port list painstakingly curated by hand searching through
# https://www.iana.org/assignments/uri-schemes/uri-schemes.xhtml
# and
# https://www.iana.org/assignments/service-names-port-numbers/service-names-port-numbers.xhtml
SCHEME_PORT_MAP = {'acap': 674, 'afp': 548, 'dict': 2628, 'dns': 53,
                   'file': None, 'ftp': 21, 'git': 9418, 'gopher': 70,
                   'http': 80, 'https': 443, 'imap': 143, 'ipp': 631,
                   'ipps': 631, 'irc': 194, 'ircs': 6697, 'ldap': 389,
                   'ldaps': 636, 'mms': 1755, 'msrp': 2855, 'msrps': None,
                   'mtqp': 1038, 'nfs': 111, 'nntp': 119, 'nntps': 563,
                   'pop': 110, 'prospero': 1525, 'redis': 6379, 'rsync': 873,
                   'rtsp': 554, 'rtsps': 322, 'rtspu': 5005, 'sftp': 22,
                   'smb': 445, 'snmp': 161, 'ssh': 22, 'steam': None,
                   'svn': 3690, 'telnet': 23, 'ventrilo': 3784, 'vnc': 5900,
                   'wais': 210, 'ws': 80, 'wss': 443, 'xmpp': None}

# This list of schemes that don't use authorities is also from the link above.
NO_NETLOC_SCHEMES = set(['urn', 'about', 'bitcoin', 'blob', 'data', 'geo',
                         'magnet', 'mailto', 'news', 'pkcs11',
                         'sip', 'sips', 'tel'])
# As of Mar 11, 2017, there were 44 netloc schemes, and 13 non-netloc


def register_scheme(text, uses_netloc=None, default_port=None):
    """Registers new scheme information, resulting in correct port and
    slash behavior from the URL object. There are dozens of standard
    schemes preregistered, so this function is mostly meant for
    proprietary internal customizations or stopgaps on missing
    standards information. If a scheme seems to be missing, please
    `file an issue`_!

    Args:
        text (str): Text representing the scheme.
           (the 'http' in 'http://hatnote.com')
        uses_netloc (bool): Does the scheme support specifying a
           network host? For instance, "http" does, "mailto" does not.
        default_port (int): The default port, if any, for netloc-using
           schemes.

    .. _file an issue: https://github.com/mahmoud/boltons/issues
    """
    text = text.lower()
    if default_port is not None:
        try:
            default_port = int(default_port)
        except ValueError:
            raise ValueError('default_port expected integer or None, not %r'
                             % (default_port,))

    if uses_netloc is True:
        SCHEME_PORT_MAP[text] = default_port
    elif uses_netloc is False:
        if default_port is not None:
            raise ValueError('unexpected default port while specifying'
                             ' non-netloc scheme: %r' % default_port)
        NO_NETLOC_SCHEMES.add(text)
    elif uses_netloc is not None:
        raise ValueError('uses_netloc expected True, False, or None')

    return


def scheme_uses_netloc(scheme, default=None):
    """Whether or not a URL uses :code:`:` or :code:`://` to separate the
    scheme from the rest of the URL depends on the scheme's own
    standard definition. There is no way to infer this behavior
    from other parts of the URL. A scheme either supports network
    locations or it does not.

    The URL type's approach to this is to check for explicitly
    registered schemes, with common schemes like HTTP
    preregistered. This is the same approach taken by
    :mod:`urlparse`.

    URL adds two additional heuristics if the scheme as a whole is
    not registered. First, it attempts to check the subpart of the
    scheme after the last ``+`` character. This adds intuitive
    behavior for schemes like ``git+ssh``. Second, if a URL with
    an unrecognized scheme is loaded, it will maintain the
    separator it sees.
    """
    if not scheme:
        return False
    scheme = scheme.lower()
    if scheme in SCHEME_PORT_MAP:
        return True
    if scheme in NO_NETLOC_SCHEMES:
        return False
    if scheme.split('+')[-1] in SCHEME_PORT_MAP:
        return True
    return default


class URLParseError(ValueError):
    """Exception inheriting from :exc:`ValueError`, raised when failing to
    parse a URL. Mostly raised on invalid ports and IPv6 addresses.
    """
    pass


def _optional(argument, default):
    """
    If the given value is C{_unspecified}, return C{default}; otherwise return
    C{argument}.

    @param argument: The argument passed.

    @param default: The default to use if C{argument} is C{_unspecified}.

    @return: C{argument} or C{default}
    """
    if argument is _unspecified:
        return default
    else:
        return argument


def _typecheck(name, value, *types):
    """
    Check that the given C{value} is of the given C{type}, or raise an
    exception describing the problem using C{name}.

    @param name: a name to use to describe the type mismatch in the error if
        one occurs
    @type name: native L{str}

    @param value: the value to check
    @type value: L{object}

    @param types: the expected types of C{value}
    @type types: L{tuple} of L{type}

    @raise TypeError: if there is a type mismatch between C{value} and C{type}

    @return: C{value} if the type check succeeds
    """
    if not types:
        types = (unicode,)
    if not isinstance(value, types):
        raise TypeError("expected {0} for {1}, got {2}".format(
            " or ".join([t.__name__ for t in types]), name, repr(value),
        ))
    return value


def _percent_decode(text):
    """
    Replace percent-encoded characters with their UTF-8 equivalents.

    @param text: The text with percent-encoded UTF-8 in it.
    @type text: L{unicode}

    @return: the encoded version of C{text}
    @rtype: L{unicode}
    """
    try:
        quotedBytes = text.encode("ascii")
    except UnicodeEncodeError:
        return text
    unquotedBytes = urlunquote(quotedBytes)
    try:
        return unquotedBytes.decode("utf-8")
    except UnicodeDecodeError:
        return text


def _resolve_dot_segments(path):
    """
    Normalise the URL path by resolving segments of '.' and '..'.

    @param path: list of path segments

    @see: RFC 3986 section 5.2.4, Remove Dot Segments

    @return: a new L{list} of path segments with the '.' and '..' elements
        removed and resolved.
    """
    segs = []

    for seg in path:
        if seg == u'.':
            pass
        elif seg == u'..':
            if segs:
                segs.pop()
        else:
            segs.append(seg)

    if list(path[-1:]) in ([u'.'], [u'..']):
        segs.append(u'')

    return segs


DEFAULT_ENCODING = 'utf8'


def to_unicode(obj):
    try:
        return unicode(obj)
    except UnicodeDecodeError:
        return unicode(obj, encoding=DEFAULT_ENCODING)


def parse_host(host):
    """\
    returns:
      family (socket constant or None), host (string)

    >>> parse_host('googlewebsite.com') == (None, 'googlewebsite.com')
    True
    >>> parse_host('[::1]') == (socket.AF_INET6, '::1')
    True
    >>> parse_host('192.168.1.1') == (socket.AF_INET, '192.168.1.1')
    True

    (odd doctest formatting above due to py3's switch from int to enums
    for socket constants)
    """
    if not host:
        return None, u''
    if u':' in host and u'[' == host[0] and u']' == host[-1]:
        host = host[1:-1]
        try:
            inet_pton(socket.AF_INET6, host)
        except socket.error as se:
            raise URLParseError('invalid IPv6 host: %r (%r)' % (host, se))
        except UnicodeEncodeError:
            pass  # TODO: this can't be a real host right?
        else:
            family = socket.AF_INET6
            return family, host
    try:
        inet_pton(socket.AF_INET, host)
    except (socket.error, UnicodeEncodeError):
        family = None  # not an IP
    else:
        family = socket.AF_INET
    return family, host


class URL(object):
    u"""
    A L{URL} represents a URL and provides a convenient API for modifying its
    parts.

    A URL is split into a number of distinct parts: scheme, host, port, path
    segments, query parameters and fragment identifier::

        http://example.com:8080/a/b/c?d=e#f
        ^ scheme           ^ port     ^ query parameters
               ^ host           ^ path segments
                                          ^ fragment

    You can construct L{URL} objects by passing in these components directly,
    like so::

        >>> from hyperlink import URL
        >>> url = URL(scheme=u'https', host=u'example.com', path=[u'hello', u'world'])
        >>> print(url.to_text())
        https://example.com/hello/world

    Or you can use the L{from_text} method you can see in the output there::

        >>> url = URL.from_text(u'https://example.com/hello/world')
        >>> print(url.to_text())
        https://example.com/hello/world

    There are two major advantages of using L{URL} over representing URLs as
    strings.  The first is that it's really easy to evaluate a relative
    hyperlink, for example, when crawling documents, to figure out what is
    linked::

        >>> URL.from_text(u'https://example.com/base/uri/').click(u"/absolute")
        URL.from_text(u'https://example.com/absolute')
        >>> URL.from_text(u'https://example.com/base/uri/').click(u"rel/path")
        URL.from_text(u'https://example.com/base/uri/rel/path')

    The other is that URLs have two normalizations.  One representation is
    suitable for humans to read, because it can represent data from many
    character sets - this is the Internationalized, or IRI, normalization.  The
    other is the older, US-ASCII-only representation, which is necessary for
    most contexts where you would need to put a URI.  You can convert *between*
    thes
    e representations according to certain rules.  L{URL} exposes these
    conversions as methods::

        >>> URL.from_text(u"https://→example.com/foo⇧bar/").to_uri()
        URL.from_text(u'https://xn--example-dk9c.com/foo%E2%87%A7bar/')
        >>> URL.from_text(u'https://xn--example-dk9c.com/foo%E2%87%A7bar/').to_iri()
        URL.from_text(u'https://\\u2192example.com/foo\\u21e7bar/')

    @see: U{RFC 3986, Uniform Resource Identifier (URI): Generic Syntax
        <https://tools.ietf.org/html/rfc3986>}
    @see: U{RFC 3987, Internationalized Resource Identifiers
        <https://tools.ietf.org/html/rfc3987>}

    @ivar scheme: The URI scheme.
    @type scheme: L{unicode}

    @ivar user: The username portion of the URL, if specified; otherwise the
        empty string.
    @type user: L{unicode}

    @ivar userinfo: The username and password portions of the URL, if
        specified, separated with colons.  If not specified, the empty string.
    @type userinfo: L{unicode}

    @ivar host: The host name.
    @type host: L{unicode}

    @ivar port: The port number.
    @type port: L{int}

    @ivar path: The path segments.
    @type path: L{tuple} of L{unicode}.

    @ivar query: The query parameters, as (name, value) pairs.
    @type query: L{tuple} of 2-L{tuple}s of (name: L{unicode}, value:
        (L{unicode} for values or L{None} for stand-alone query parameters with
        no C{=} in them)).

    @ivar fragment: The fragment identifier.
    @type fragment: L{unicode}

    @ivar rooted: Does the path start with a C{/}?  This is taken from the
        terminology in the BNF grammar, specifically the C{path-rootless},
        rule, since "absolute path" and "absolute URI" are somewhat ambiguous.
        C{path} does not contain the implicit prefixed C{"/"} since that is
        somewhat awkward to work with.
    @type rooted: L{bool}
    """

    def __init__(self, scheme=None, host=None, path=(), query=(), fragment=u'',
                 port=None, rooted=None, userinfo=u'', family=None, uses_netloc=None):
        """From blogs to billboards, URLs are so common, that it's easy to
        overlook their complexity and power. With hyperlink's
        :class:`URL` type, working with URLs doesn't have to be hard.

        The URL constructor builds a URL from its individual
        parts. Most of these parts are officially named in RFC 3986
        and this diagram may prove handy in identifying them::

           foo://user:pass@example.com:8042/over/there?name=ferret#nose
           \_/   \_______/ \_________/ \__/\_________/ \_________/ \__/
            |        |          |        |      |           |        |
          scheme  userinfo     host     port   path       query   fragment


        The :class:`URL` constructor does not do much value checking,
        beyond type checks. All strings are expected to be decoded
        (:class:`unicode` in Python 2). All arguments default to
        respective empty values, so ``URL()`` is valid.

        Args:
           scheme (str): The text name of the scheme.
           host (str): The host portion of the network location
           port (int): The port part of the network location. If
              ``None`` or no port is passed, the port will default to
              the default port of the scheme, if it is known. See the
              ``SCHEME_PORT_MAP`` and :func:`register_default_port`
              for more info.
           path (tuple): A tuple of strings representing the
              slash-separated parts of the path.
           query (tuple): The query parameters, as a tuple of
              key-value pairs.
           fragment (str): The fragment part of the URL.
           rooted (bool): Whether or not the path begins with a slash.
           userinfo (str): The username or colon-separated
              username:password pair.
           family: A socket module constant used when the host is an
              IP constant to differentiate IPv4 and domain names, as
              well as validate IPv6.
           uses_netloc (bool): Indicates whether two slashes appear
              between the scheme and the host (``http://eg.com`` vs
              ``mailto:e@g.com``)

        All of these parts are also exposed as read-only attributes of
        URL instances, along with several useful methods. See below
        for more info!

        """
        if host is not None and scheme is None:
            scheme = u'http'  # TODO: why
        if port is None:
            port = SCHEME_PORT_MAP.get(scheme)
        if host and query and not path:
            path = ()  # (u'',)

        # Now that we're done detecting whether they were passed, we can set
        # them to their defaults:
        if scheme is None:
            scheme = u''
        if host is None:
            host = u''
        if rooted is None:
            rooted = bool(host)

        # Set attributes.
        self._scheme = _typecheck("scheme", scheme)
        if self._scheme:
            if not _SCHEME_RE.match(self._scheme):
                raise ValueError('invalid scheme: %r. Only alphanumeric, "+",'
                                 ' "-", and "." allowed. Did you meant to call'
                                 ' %s.from_text()?'
                                 % (self._scheme, self.__class__.__name__))
        self._host = _typecheck("host", host)
        if isinstance(path, unicode):
            raise TypeError("expected iterable of text for path, not: %r"
                            % (path,))
        self._path = tuple((_typecheck("path segment", segment)
                            for segment in path))
        self._query = tuple(
            (_typecheck("query parameter name", k),
             _typecheck("query parameter value", v, unicode, NoneType))
            for (k, v) in query
        )
        self._fragment = _typecheck("fragment", fragment)
        self._port = _typecheck("port", port, int, NoneType)
        self._rooted = _typecheck("rooted", rooted, bool)
        self._userinfo = _typecheck("userinfo", userinfo)
        self._family = _typecheck("family", family,
                                  type(socket.AF_INET), NoneType)

        uses_netloc = scheme_uses_netloc(self._scheme, uses_netloc)
        self._uses_netloc = _typecheck("uses_netloc", uses_netloc, bool, NoneType)

        return

    scheme = property(lambda self: self._scheme)
    host = property(lambda self: self._host)
    port = property(lambda self: self._port)
    path = property(lambda self: self._path)
    query = property(lambda self: self._query)
    fragment = property(lambda self: self._fragment)
    rooted = property(lambda self: self._rooted)
    userinfo = property(lambda self: self._userinfo)
    family = property(lambda self: self._family)
    uses_netloc = property(lambda self: self._uses_netloc)

    @property
    def user(self):
        """
        The user portion of C{userinfo}; everything up to the first C{":"}.
        """
        return self.userinfo.split(u':')[0]

    def authority(self, include_secrets=False, **kw):
        """
        Compute and return the appropriate host/port/userinfo combination.

        @param includeSecrets: should the return value of this method include
            secret information?  C{True} if so, C{False} if not
        @type includeSecrets: L{bool}

        @return: The authority (network location and user information) portion
            of the URL.
        @rtype: L{unicode}
        """
        # first, a bit of twisted compat
        include_secrets = kw.pop('includeSecrets', include_secrets)
        if kw:
            raise TypeError('got unexpected keyword arguments: %r' % kw.keys())
        if self.family == socket.AF_INET6:
            hostport = ['[' + self.host + ']']
        else:
            hostport = [self.host]
        if self.port != SCHEME_PORT_MAP.get(self.scheme):
            hostport.append(unicode(self.port))
        authority = []
        if self.userinfo:
            userinfo = self.userinfo
            if not include_secrets and u":" in userinfo:
                userinfo = userinfo[:userinfo.index(u":") + 1]
            authority.append(userinfo)
        authority.append(u":".join(hostport))
        return u"@".join(authority)

    def __eq__(self, other):
        """
        L{URL}s are equal to L{URL} objects whose attributes are equal.
        """
        if not isinstance(other, self.__class__):
            return NotImplemented
        for attr in ['scheme', 'userinfo', 'host', 'path', 'query',
                     'fragment', 'port', 'rooted', 'family', 'uses_netloc']:
            if getattr(self, attr) != getattr(other, attr):
                return False
        return True

    def __ne__(self, other):
        """
        L{URL}s are unequal to L{URL} objects whose attributes are unequal.
        """
        if not isinstance(other, self.__class__):
            return NotImplemented
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.__class__, self.scheme, self.userinfo, self.host,
                     self.path, self.query, self.fragment, self.port,
                     self.rooted, self.family, self.uses_netloc))

    @property
    def absolute(self):
        """Whether or not the URL is "absolute", meaning that has both a
        scheme and a host set. This means it's complete enough to
        resolve to a resource without resolution relative to a base URI.
        """
        return bool(self.scheme and self.host)

    def replace(self, scheme=_unspecified, host=_unspecified,
                path=_unspecified, query=_unspecified,
                fragment=_unspecified, port=_unspecified,
                rooted=_unspecified, userinfo=_unspecified):
        """:class:`URL` objects are immutable, which means that attributes
        are designed to be set only once, at construction. Instead of
        modifying an existing URL, one simply creates a copy with the
        desired changes.

        If any of the following arguments is omitted, it defaults to
        the value on the current URL.

        Args:
           scheme (str): The text name of the scheme.
           host (str): The host portion of the network location
           port (int): The port part of the network location.
           path (tuple): A tuple of strings representing the
              slash-separated parts of the path.
           query (tuple): The query parameters, as a tuple of
              key-value pairs.
           fragment (str): The fragment part of the URL.
           rooted (bool): Whether or not the path begins with a slash.
           userinfo (str): The username or colon-separated
              username:password pair.
           family: A socket module constant used when the host is an
              IP constant to differentiate IPv4 and domain names, as
              well as validate IPv6.
           uses_netloc (bool): Indicates whether two slashes appear
              between the scheme and the host (``http://eg.com`` vs
              ``mailto:e@g.com``)

        Returns:
           URL: a copy of the current :class:`URL`, with new values for
              parameters passed.

        """
        return self.__class__(
            scheme=_optional(scheme, self.scheme),
            host=_optional(host, self.host),
            path=_optional(path, self.path),
            query=_optional(query, self.query),
            fragment=_optional(fragment, self.fragment),
            port=_optional(port, self.port),
            rooted=_optional(rooted, self.rooted),
            userinfo=_optional(userinfo, self.userinfo),
        )

    @classmethod
    def from_text(cls, s):
        """
        Parse the given string into a URL object.

        Relative path references are not supported.

        @param s: a valid URI or IRI
        @type s: L{unicode}

        @return: the parsed representation of C{s}
        @rtype: L{URL}
        """
        s = to_unicode(s)
        um = _URL_RE.match(s)
        try:
            gs = um.groupdict()
        except AttributeError:
            raise URLParseError('could not parse url: %r' % s)

        au_text = gs['authority']
        userinfo, hostinfo = u'', au_text

        if au_text:
            userinfo, sep, hostinfo = au_text.rpartition('@')

        host, port = None, None
        if hostinfo:
            host, sep, port_str = hostinfo.partition(u':')
            if sep:
                if u']' in port_str:
                    host = hostinfo  # wrong split, was an ipv6
                else:
                    try:
                        port = int(port_str)
                    except ValueError:
                        if not port_str:  # TODO: excessive?
                            raise URLParseError('port must not be empty')
                        raise URLParseError('expected integer for port, not %r'
                                            % port_str)
        family, host = parse_host(host)

        scheme = gs['scheme'] or u''
        fragment = gs['fragment'] or u''
        uses_netloc = bool(gs['_netloc_sep'])

        if gs['path']:
            path = gs['path'].split(u"/")
            if not path[0]:
                path.pop(0)
                rooted = True
            else:
                rooted = False
        else:
            path = ()
            rooted = bool(hostinfo)
        if gs['query']:
            query = ((qe.split(u"=", 1) if u'=' in qe else (qe, None))
                     for qe in gs['query'].split(u"&"))
        else:
            query = ()
        return cls(scheme, host, path, query, fragment, port,
                   rooted, userinfo, family, uses_netloc)

    def child(self, *segments):
        """Make a new :class:`URL` where the given path segments are a child
        of this URL, preserving other parts of the URL, including the
        query string and fragment.

        For example::

            >>> url = URL.from_text(u"http://localhost/a/b?x=y")
            >>> child_url = url.child(u"c", u"d")
            >>> child_url.to_text()
            u'http://localhost/a/b/c/d?x=y'

        Args:
           segments (str): Additional parts to be joined and added to the
              path, like :func:`os.path.join`.

        Returns:
           URL: A copy of the current URL with the extra path segments.

        @return: a new L{URL} with the additional path segments.
        @rtype: L{URL}

        """
        new_path = self.path[:-1 if (self.path and self.path[-1] == u'')
                             else None] + segments
        return self.replace(path=new_path)

    def sibling(self, segment):
        """Make a new :class:`URL` with a single path segment that is a
        sibling of this URL path.

        Args:
           segment (str): A single path segment.

        Returns:
           URL: A copy of the current URL with the last path segment
              replaced by *segment*.
        """
        return self.replace(path=self.path[:-1] + (segment,))

    def click(self, href):
        """Resolve the given URL relative to this URL.

        The resulting URI should match what a web browser would
        generate if you visited the current URL and clicked on *href*.

           >>> url = URL.from_text('http://blog.hatnote.com/')
           >>> url.click(u'/post/155074058790').to_text()
           u'http://blog.hatnote.com/post/155074058790'
           >>> url = URL.from_text('http://localhost/a/b/c/')
           >>> url.click(u'../d/./e').to_text()
           u'http://localhost/a/b/d/e'

        Args:
            href (str): A string representing a clicked URL.

        Return:
            URL: A copy of the current URL with navigation logic applied.

        For more information, see RFC 3986 section 5.
        """
        # TODO: default arg? URL arg?
        _typecheck("relative URL", href)
        if href:
            clicked = URL.from_text(href)
            if clicked.absolute:
                return clicked
        else:
            clicked = self

        query = clicked.query
        if clicked.scheme and not clicked.rooted:
            # Schemes with relative paths are not well-defined.  RFC 3986 calls
            # them a "loophole in prior specifications" that should be avoided,
            # or supported only for backwards compatibility.
            raise NotImplementedError('absolute URI with rootless path: %r'
                                      % (href,))
        else:
            if clicked.rooted:
                path = clicked.path
            elif clicked.path:
                path = self.path[:-1] + clicked.path
            else:
                path = self.path
                if not query:
                    query = self.query
        return self.replace(scheme=clicked.scheme or self.scheme,
                            host=clicked.host or self.host,
                            port=clicked.port or self.port,
                            path=_resolve_dot_segments(path),
                            query=query,
                            fragment=clicked.fragment)

    def to_uri(self):
        u""" Make a new :class:`URL` instance with all non-ASCII characters
        appropriately percent-encoded.  This is useful to do in preparation
        for sending a :class:`URL` over a network protocol.

        For example::

            >>> URL.from_text(u"https://→example.com/foo⇧bar/").to_uri()
            URL.from_text(u'https://xn--example-dk9c.com/foo%E2%87%A7bar/')

        Returns:
            URL: A new instance with its path segments, query parameters, and
            hostname encoded, so that they are all in the standard
            US-ASCII range.
        """
        new_userinfo = u':'.join([_encode_userinfo_part(p) for p in
                                  self.userinfo.split(':', 1)])
        return self.replace(
            userinfo=new_userinfo,
            host=self.host.encode("idna").decode("ascii"),
            path=(_encode_path_part(segment, maximal=True)
                  for segment in self.path),
            query=(tuple(_encode_query_part(x, maximal=True)
                         if x is not None else None
                         for x in (k, v))
                   for k, v in self.query),
            fragment=_encode_fragment_part(self.fragment, maximal=True)
        )

    def to_iri(self):
        u"""Make a new :class:`URL` instance with all but a few reserved
        characters decoded into human-readable format.

        Percent-encoded Unicode and IDNA-encoded hostnames are
        decoded, like so::

            >>> url = URL.from_text(u'https://xn--example-dk9c.com/foo%E2%87%A7bar/')
            >>> print(url.to_iri().to_text())
            https://→example.com/foo⇧bar/

        Returns:
            URL: A new instance with its path segments, query parameters, and
            hostname decoded for display purposes.
        """
        new_userinfo = u':'.join([_percent_decode(p) for p in
                                  self.userinfo.split(':', 1)])
        try:
            asciiHost = self.host.encode("ascii")
        except UnicodeEncodeError:
            textHost = self.host
        else:
            textHost = asciiHost.decode("idna")
        return self.replace(userinfo=new_userinfo,
                            host=textHost,
                            path=[_percent_decode(segment)
                                  for segment in self.path],
                            query=[tuple(_percent_decode(x)
                                         if x is not None else None
                                         for x in (k, v))
                                   for k, v in self.query],
                            fragment=_percent_decode(self.fragment))

    def to_text(self, include_secrets=False):
        """Render this URL to its textual representation.

        By default, the URL text will *not* include a password, if one
        is set. RFC 3986 considers using URLs to represent such
        sensitive information as deprecated. Quoting from RFC3986,
        section 3.2.1:

            "Applications should not render as clear text any data after the
            first colon (":") character found within a userinfo subcomponent
            unless the data after the colon is the empty string (indicating no
            password)."

        Args:
            include_secrets (bool): Whether or not to include the
               password in the URL text. Defaults to False.

        Returns:
            str: The serialized textual representation of this URL,
            such as ``u"http://example.com/some/path?some=query"``.
        """
        scheme = self.scheme
        authority = self.authority(include_secrets)
        path = u'/'.join(([u''] if (self.rooted and self.path) else [])
                         + [_encode_path_part(segment, maximal=False)
                            for segment in self.path])
        query_string = u'&'.join(
            u'='.join((_encode_query_part(x, maximal=False)
                       for x in ([k] if v is None else [k, v])))
            for (k, v) in self.query)

        fragment = self.fragment

        parts = []
        _add = parts.append
        if scheme:
            _add(scheme)
            _add(':')
        if authority:
            _add('//')
            _add(authority)
        elif (scheme and path[:2] != '//' and self.uses_netloc):
            _add('//')
        if path:
            if scheme and authority and path[:1] != '/':
                _add('/')  # relpaths with abs authorities auto get '/'
            _add(path)
        if query_string:
            _add('?')
            _add(query_string)
        if fragment:
            _add('#')
            _add(fragment)
        return u''.join(parts)

    def __repr__(self):
        """Convert this URL to an representation that shows all of its
        constituent parts, as well as being a valid argument to
        :func:`eval`.
        """
        return '%s.from_text(%r)' % (self.__class__.__name__, self.to_text())

    # # Begin Twisted Compat Code
    fromText = from_text
    asURI = to_uri
    asIRI = to_iri

    def asText(self, includeSecrets=False):
        return self.to_text(include_secrets=includeSecrets)

    def __dir__(self):
        try:
            ret = object.__dir__(self)
        except AttributeError:
            # object.__dir__ == AttributeError  # pdw for py2
            ret = dir(self.__class__) + list(self.__dict__.keys())
        ret = sorted(set(ret) - set(['fromText', 'asURI', 'asIRI', 'asText']))
        return ret

    # # End Twisted Compat Code

    def add(self, name, value=None):
        """Make a new :class:`URL` instance with a given query argument,
        *name*, added to it with the value *value*, like so::

            >>> URL.from_text(u'https://example.com/?x=y').add(u'x')
            URL.from_text(u'https://example.com/?x=y&x')
            >>> URL.from_text(u'https://example.com/?x=y').add(u'x', u'z')
            URL.from_text(u'https://example.com/?x=y&x=z')

        Args:
            name (str): The name of the query parameter to add. The
                part before the ``=``.
            value (str): The value of the query parameter to add. The
                part after the ``=``. Defaults to ``None``, meaning no
                value.

        Returns:
            URL: A new :class:`URL` instance with the parameter added.
        """
        return self.replace(query=self.query + ((name, value),))

    def set(self, name, value=None):
        """Make a new :class:`URL` instance with the query parameter *name*
        set to *value*. All existing occurences, if any are replaced
        by the single name-value pair.

            >>> URL.from_text(u'https://example.com/?x=y').set(u'x')
            URL.from_text(u'https://example.com/?x')
            >>> URL.from_text(u'https://example.com/?x=y').set(u'x', u'z')
            URL.from_text(u'https://example.com/?x=z')

        Args:
            name (str): The name of the query parameter to set. The
                part before the ``=``.
            value (str): The value of the query parameter to set. The
                part after the ``=``. Defaults to ``None``, meaning no
                value.

        Returns:
            URL: A new :class:`URL` instance with the parameter set.
        """
        # Preserve the original position of the query key in the list
        q = [(k, v) for (k, v) in self.query if k != name]
        idx = next((i for (i, (k, v)) in enumerate(self.query)
                    if k == name), -1)
        q[idx:idx] = [(name, value)]
        return self.replace(query=q)

    def get(self, name):  # TODO: default
        """Get a list of values for the given query parameter, *name*::

            >>> url = URL.from_text('?x=1&x=2')
            >>> url.get('x')
            [u'1', u'2']
            >>> url.get('y')
            []

        Args:
            name (str): The name of the query parameter to get.

        Returns:
            list: A list of all the values associated with the key, in
                string form.
        """
        return [value for (key, value) in self.query if name == key]

    def remove(self, name):
        """Make a new :class:`URL` instance with all occurrences of the query
        parameter *name* removed. No exception is raised if the
        parameter is not already set.

        Args:
            name (str): The name of the query parameter to remove.

        Returns:
            URL: A new :class:`URL` instance with the parameter removed.

        """
        return self.replace(query=((k, v) for (k, v) in self.query
                                   if k != name))
