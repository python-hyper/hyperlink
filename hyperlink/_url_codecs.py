
import re
import socket

# RFC 3986 Section 2.3, Unreserved URI Characters
#   https://tools.ietf.org/html/rfc3986#section-2.3
_UNRESERVED_CHARS = frozenset('~-._0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                              'abcdefghijklmnopqrstuvwxyz')

# RFC 3986 section 2.2, Reserved Characters
#   https://tools.ietf.org/html/rfc3986#section-2.2
_GEN_DELIMS = frozenset(u':/?#[]@')
_SUB_DELIMS = frozenset(u"!$&'()*+,;=")
_ALL_DELIMS = _GEN_DELIMS | _SUB_DELIMS


# The following is based on Ian Cordasco's rfc3986 package

IPv4_PATT = '([0-9]{1,3}.){3}[0-9]{1,3}'
IPv4_RE = re.compile(IPv4_PATT)
# Hexadecimal characters used in each piece of an IPv6 address
HEXDIG_PATT = '[0-9A-Fa-f]{1,4}'
# Least-significant 32 bits of an IPv6 address
LS32_RE = '(%(hex)s:%(hex)s|%(ipv4)s)' % {'hex': HEXDIG_PATT, 'ipv4': IPv4_PATT}
# Substitutions into the following patterns for IPv6 patterns defined
# http://tools.ietf.org/html/rfc3986#page-20
_subs = {'hex': HEXDIG_PATT, 'ls32': LS32_RE}

# Below: h16 = hexdig, see: https://tools.ietf.org/html/rfc5234 for details
# about ABNF (Augmented Backus-Naur Form) use in the comments
_ipv6_variations = [
    #                            6( h16 ":" ) ls32
    '(%(hex)s:){6}%(ls32)s' % _subs,
    #                       "::" 5( h16 ":" ) ls32
    '::(%(hex)s:){5}%(ls32)s' % _subs,
    # [               h16 ] "::" 4( h16 ":" ) ls32
    '(%(hex)s)?::(%(hex)s:){4}%(ls32)s' % _subs,
    # [ *1( h16 ":" ) h16 ] "::" 3( h16 ":" ) ls32
    '((%(hex)s:)?%(hex)s)?::(%(hex)s:){3}%(ls32)s' % _subs,
    # [ *2( h16 ":" ) h16 ] "::" 2( h16 ":" ) ls32
    '((%(hex)s:){0,2}%(hex)s)?::(%(hex)s:){2}%(ls32)s' % _subs,
    # [ *3( h16 ":" ) h16 ] "::"    h16 ":"   ls32
    '((%(hex)s:){0,3}%(hex)s)?::%(hex)s:%(ls32)s' % _subs,
    # [ *4( h16 ":" ) h16 ] "::"              ls32
    '((%(hex)s:){0,4}%(hex)s)?::%(ls32)s' % _subs,
    # [ *5( h16 ":" ) h16 ] "::"              h16
    '((%(hex)s:){0,5}%(hex)s)?::%(hex)s' % _subs,
    # [ *6( h16 ":" ) h16 ] "::"
    '((%(hex)s:){0,6}%(hex)s)?::' % _subs,
]

IPv6_PATT = '(%s)' % '|'.join(['(%s)' % v for v in _ipv6_variations])

PERCENT_ENCODED_PATT = '%[A-Fa-f0-9]{2}'

UNRESERVED_CHAR_PATT = 'A-Za-z0-9._~\-'
SUBDELIMS_CHAR_PATT = "!$&'()\*+,;="

IPv_FUTURE_PATT = ('v[0-9A-Fa-f]+.[%s]+'
                 % UNRESERVED_CHAR_PATT + SUBDELIMS_CHAR_PATT + ':')


# RFC 6874 Zone ID ABNF
ZONE_ID_PATT = '(?:[' + UNRESERVED_CHAR_PATT + ']|' + PERCENT_ENCODED_PATT + ')+'
IPv6_ADDRZ_PATT = IPv6_PATT + '%25' + ZONE_ID_PATT

IP_LITERAL_PATT = ('\[(%s|(?:%s)|%s)\]'
                   % (IPv6_PATT, IPv6_ADDRZ_PATT, IPv_FUTURE_PATT))


_IP_LITERAL_RE = re.compile(IP_LITERAL_PATT)


def parse_host(host):
    if u':' in host:
        try:
            _IP_LITERAL_RE.match(host)
            # TODO: pull out lowest 32-bits in case of ipv4-in-ipv6
            # pattern match and inet_pton them
            ipv4_match = IPv4_RE.search(host)
            if ipv4_match:
                try:
                    socket.inet_pton(socket.AF_INET, ipv4_match.group(0))
                except socket.error as se:
                    raise ValueError('invalid IPv6 host with IPv4: %r (%r)' % (host, se))
        except socket.error as se:
            # TODO: URLParseError
            raise ValueError('invalid IPv6 host: %r (%r)' % (host, se))
        else:
            return socket.AF_INET6, host
    try:
        socket.inet_pton(socket.AF_INET, host)
    except (socket.error, UnicodeEncodeError):
        family = None  # not an IP
    else:
        family = socket.AF_INET
    return family, host
