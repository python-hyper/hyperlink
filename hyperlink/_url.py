# -*- coding: utf-8 -*-
"""
URL parsing, construction and rendering.
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


def _percentDecode(text):
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



def _resolveDotSegments(path):
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
        >>> print(url.asText())
        https://example.com/hello/world

    Or you can use the L{fromText} method you can see in the output there::

        >>> url = URL.fromText(u'https://example.com/hello/world')
        >>> print(url.asText())
        https://example.com/hello/world

    There are two major advantages of using L{URL} over representing URLs as
    strings.  The first is that it's really easy to evaluate a relative
    hyperlink, for example, when crawling documents, to figure out what is
    linked::

        >>> URL.fromText(u'https://example.com/base/uri/').click(u"/absolute")
        URL.fromText(u'https://example.com/absolute')
        >>> URL.fromText(u'https://example.com/base/uri/').click(u"rel/path")
        URL.fromText(u'https://example.com/base/uri/rel/path')

    The other is that URLs have two normalizations.  One representation is
    suitable for humans to read, because it can represent data from many
    character sets - this is the Internationalized, or IRI, normalization.  The
    other is the older, US-ASCII-only representation, which is necessary for
    most contexts where you would need to put a URI.  You can convert *between*
    thes
    e representations according to certain rules.  L{URL} exposes these
    conversions as methods::

        >>> URL.fromText(u"https://→example.com/foo⇧bar/").asURI()
        URL.fromText(u'https://xn--example-dk9c.com/foo%E2%87%A7bar/')
        >>> URL.fromText(u'https://xn--example-dk9c.com/foo%E2%87%A7bar/').asIRI()
        URL.fromText(u'https://\\u2192example.com/foo\\u21e7bar/')

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
        """
        Create a new L{URL} from structured information about itself.

        @ivar scheme: The URI scheme.
        @type scheme: L{unicode}

        @ivar host: The host portion of the netloc.
        @type host: L{unicode}

        @ivar port: The port number indicated by this URL, or L{None} if none
            is indicated.  (This is only L{None} if the default port for the
            scheme is unknown; if the port number is unspecified in the text of
            a URL, this will still be set to the default port for that scheme.)
        @type port: L{int} or L{None}

        @ivar path: The path segments.
        @type path: Iterable of L{unicode}.

        @ivar query: The query parameters, as name-value pairs
        @type query: Iterable of pairs of L{unicode} (or L{None}, for values).

        @ivar fragment: The fragment identifier.
        @type fragment: L{unicode}

        @ivar rooted: Does the path start with a C{/}?  This is taken from the
            terminology in the BNF grammar, specifically the C{path-rootless},
            rule, since "absolute path" and "absolute URI" are somewhat
            ambiguous.  C{path} does not contain the implicit prefixed C{"/"}
            since that is somewhat awkward to work with.
        @type rooted: L{bool}

        @ivar userinfo: The username and password portions of the URL, if
            specified, separated with colons.
        @type userinfo: L{unicode}
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


    def authority(self, includeSecrets=False):
        """
        Compute and return the appropriate host/port/userinfo combination.

        @param includeSecrets: should the return value of this method include
            secret information?  C{True} if so, C{False} if not
        @type includeSecrets: L{bool}

        @return: The authority (network location and user information) portion
            of the URL.
        @rtype: L{unicode}
        """
        if self.family == socket.AF_INET6:
            hostport = ['[' + self.host + ']']
        else:
            hostport = [self.host]
        if self.port != SCHEME_PORT_MAP.get(self.scheme):
            hostport.append(unicode(self.port))
        authority = []
        if self.userinfo:
            userinfo = self.userinfo
            if not includeSecrets and u":" in userinfo:
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
        """
        Is this URL complete enough to resolve a resource without resolution
        relative to a base-URI?
        """
        return bool(self.scheme and self.host)


    def replace(self, scheme=_unspecified, host=_unspecified,
                path=_unspecified, query=_unspecified,
                fragment=_unspecified, port=_unspecified,
                rooted=_unspecified, userinfo=_unspecified):
        """
        Make a new instance of C{self.__class__}, passing along the given
        arguments to its constructor.

        @param scheme: the scheme of the new URL; if unspecified, the scheme of
            this URL.
        @type scheme: L{unicode}

        @param host: the host of the new URL; if unspecified, the host of this
            URL.
        @type host: L{unicode}

        @param path: the path segments of the new URL; if unspecified, the path
            segments of this URL.
        @type path: iterable of L{unicode}

        @param query: the query elements of the new URL; if unspecified, the
            query segments of this URL.
        @type query: iterable of 2-L{tuple}s of key, value.

        @param fragment: the fragment of the new URL; if unspecified, the query
            segments of this URL.
        @type fragment: L{unicode}

        @param port: the port of the new URL; if unspecified, the port of this
            URL.
        @type port: L{int}

        @param rooted: C{True} if the given C{path} are meant to start at the
            root of the host; C{False} otherwise.  Only meaningful for relative
            URIs.
        @type rooted: L{bool}

        @param userinfo: A string indicating information about an authenticated
            user.
        @type userinfo: L{unicode}

        @return: a new L{URL}.
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
    def fromText(cls, s):
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
        """
        Construct a L{URL} where the given path segments are a child of this
        url, presering the query and fragment.

        For example::

            >>> URL.fromText(u"http://localhost/a/b?x=y").child(u"c", u"d").asText()
            u'http://localhost/a/b/c/d?x=y'

        @param segments: A path segment.
        @type segments: L{tuple} of L{unicode}

        @return: a new L{URL} with the additional path segments.
        @rtype: L{URL}
        """
        return self.replace(
            path=self.path[:-1 if (self.path and self.path[-1] == u'')
                           else None] + segments
        )


    def sibling(self, segment):
        """
        Construct a url where the given path segment is a sibling of this url.

        @param segment: A path segment.
        @type segment: L{unicode}

        @return: a new L{URL} with its final path segment replaced with
            C{segment}.
        @rtype: L{URL}
        """
        return self.replace(path=self.path[:-1] + (segment,))


    def click(self, href):
        """
        Resolve the given URI reference relative to this (base) URI.

        The resulting URI should match what a web browser would generate if you
        click on C{href} in the context of this URI.

        @param href: a URI reference
        @type href: L{unicode} or ASCII L{str}

        @return: a new absolute L{URL}

        @see: RFC 3986 section 5, Reference Resolution
        """
        _typecheck("relative URL", href)
        if href:
            clicked = URL.fromText(href)
            if clicked.absolute:
                return clicked
        else:
            clicked = self

        query = clicked.query
        if clicked.scheme and not clicked.rooted:
            # Schemes with relative paths are not well-defined.  RFC 3986 calls
            # them a "loophole in prior specifications" that should be avoided,
            # or supported only for backwards compatibility.
            raise NotImplementedError(
                'absolute URI with rootless path: %r' % (href,)
            )
        else:
            if clicked.rooted:
                path = clicked.path
            elif clicked.path:
                path = self.path[:-1] + clicked.path
            else:
                path = self.path
                if not query:
                    query = self.query
        return self.replace(
            scheme=clicked.scheme or self.scheme,
            host=clicked.host or self.host,
            port=clicked.port or self.port,
            path=_resolveDotSegments(path),
            query=query,
            fragment=clicked.fragment
        )


    def asURI(self):
        u"""
        Convert a L{URL} object that potentially contains non-ASCII characters
        into a L{URL} object where all non-ASCII text has been encoded
        appropriately.  This is useful to do in preparation for sending a
        L{URL}, or portions of it, over a wire protocol.  For example::

            >>> URL.fromText(u"https://→example.com/foo⇧bar/").asURI()
            URL.fromText(u'https://xn--example-dk9c.com/foo%E2%87%A7bar/')

        @return: a new L{URL} with its path-segments, query-parameters, and
            hostname appropriately decoded, so that they are all in the
            US-ASCII range.
        @rtype: L{URL}
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


    def asIRI(self):
        """
        Convert a L{URL} object that potentially contains text that has been
        percent-encoded or IDNA encoded into a L{URL} object containing the
        text as it should be presented to a human for reading.

        For example::

            >>> URL.fromText(u'https://xn--example-dk9c.com/foo%E2%87%A7bar/').asIRI()
            URL.fromText(u'https://\u2192example.com/foo\u21e7bar/')

        @return: a new L{URL} with its path-segments, query-parameters, and
            hostname appropriately decoded.
        @rtype: L{URL}
        """
        new_userinfo = u':'.join([_percentDecode(p) for p in
                                  self.userinfo.split(':', 1)])
        try:
            asciiHost = self.host.encode("ascii")
        except UnicodeEncodeError:
            textHost = self.host
        else:
            textHost = asciiHost.decode("idna")
        return self.replace(
            userinfo=new_userinfo,
            host=textHost,
            path=[_percentDecode(segment) for segment in self.path],
            query=[
                tuple(_percentDecode(x)
                      if x is not None else None
                      for x in (k, v))
                for k, v in self.query
            ],
            fragment=_percentDecode(self.fragment)
        )

    def asText(self, includeSecrets=False):
        """
        Convert this URL to its canonical textual representation.

        @param includeSecrets: Should the returned textual representation
            include potentially sensitive information?  The default, C{False},
            if not; C{True} if so.  Quoting from RFC3986, section 3.2.1:

            "Applications should not render as clear text any data after the
            first colon (":") character found within a userinfo subcomponent
            unless the data after the colon is the empty string (indicating no
            password)."

        @type includeSecrets: L{bool}

        @return: The serialized textual representation of this L{URL}, such as
            C{u"http://example.com/some/path?some=query"}.
        @rtype: L{unicode}
        """
        scheme = self.scheme
        authority = self.authority(includeSecrets)
        path = u'/'.join(([u''] if (self.rooted and self.path) else [])
                         + [_encode_path_part(segment, maximal=False)
                            for segment in self.path])
        query_string = u'&'.join(
            u'='.join((_encode_query_part(x, maximal=False)
                       for x in ([k] if v is None else [k, v])))
            for (k, v) in self.query
        )
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

    to_uri = asURI
    to_iri = asIRI
    to_text = asText
    from_text = fromText

    def __repr__(self):
        """
        Convert this URL to an C{eval}-able representation that shows all of
        its constituent parts.
        """
        return 'URL.fromText(%r)' % self.asText()

    def add(self, name, value=None):
        """
        Create a new L{URL} with a given query argument, C{name}, added to it
        with the value C{value}, like so::

            >>> URL.fromText(u'https://example.com/?x=y').add(u'x')
            URL.fromText(u'https://example.com/?x=y&x')
            >>> URL.fromText(u'https://example.com/?x=y').add(u'x', u'z')
            URL.fromText(u'https://example.com/?x=y&x=z')

        @param name: The name (the part before the C{=}) of the query parameter
            to add.
        @type name: L{unicode}

        @param value: The value (the part after the C{=}) of the query
            parameter to add.
        @type value: L{unicode}

        @return: a new L{URL} with the parameter added.
        """
        return self.replace(query=self.query + ((name, value),))


    def set(self, name, value=None):
        """
        Create a new L{URL} with all existing occurrences of the query argument
        C{name}, if any, removed, then add the argument with the given value,
        like so::

            >>> URL.fromText(u'https://example.com/?x=y').set(u'x')
            URL.fromText(u'https://example.com/?x')
            >>> URL.fromText(u'https://example.com/?x=y').set(u'x', u'z')
            URL.fromText(u'https://example.com/?x=z')

        @param name: The name (the part before the C{=}) of the query parameter
            to add.
        @type name: L{unicode}

        @param value: The value (the part after the C{=}) of the query
            parameter to add.
        @type value: L{unicode}

        @return: a new L{URL} with the parameter added or changed.
        """
        # Preserve the original position of the query key in the list
        q = [(k, v) for (k, v) in self.query if k != name]
        idx = next((i for (i, (k, v)) in enumerate(self.query)
                    if k == name), -1)
        q[idx:idx] = [(name, value)]
        return self.replace(query=q)


    def get(self, name):
        """
        Retrieve a list of values for the given named query parameter.

        @param name: The name of the query parameter to retrieve.
        @type name: L{unicode}

        @return: all the values associated with the key; for example, for the
            query string C{u"x=1&x=2"}, C{url.query.get(u"x")} would return
            C{[u'1', u'2']}; C{url.query.get(u"y")} (since there is no C{"y"}
            parameter) would return the empty list, C{[]}.
        @rtype: L{list} of L{unicode}
        """
        return [value for (key, value) in self.query if name == key]


    def remove(self, name):
        """
        Create a new L{URL} with all query arguments with the given name
        removed.

        @param name: The name of the query parameter to remove.
        @type name: L{unicode}

        @return: a new L{URL} with the parameter removed.
        """
        return self.replace(query=((k, v) for (k, v) in self.query
                                   if k != name))
