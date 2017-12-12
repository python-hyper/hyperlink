# Hyperlink Changelog

## dev (not yet released)

* Also accept dictionaries as ‘query=’ arguments (see #50)

## 17.3.1

*(August 19, 2017)*

* Add `URL.normalize()` method, which applies five normalizations from
  RFC 3986 (sections 2.3, 2.1, 3.2.2, 6.2.2.3, 6.2.3). See [the docs](http://hyperlink.readthedocs.io/en/latest/api.html#hyperlink.URL.normalize)
  for more details.
* Enable `URL.click()` to accept a URL object as a target.

## 17.3.0

*(July 18, 2017)*

Fixed a couple major decoding issues and simplified the URL API.

* limit types accepted by `URL.from_text()` to just text (str on py3,
  unicode on py2), see #20
* fix percent decoding issues surrounding multiple calls to
  `URL.to_iri()` (see #16)
* remove the `socket`-inspired `family` argument from `URL`'s APIs. It
  was never consistently implemented and leaked slightly more problems
  than it solved.
* Improve authority parsing (see #26)
* include LICENSE, README, docs, and other resources in the package

## 17.2.1

*(June 18, 2017)*

A small bugfix release after yesterday's big changes. This patch
version simply reverts an exception message for parameters expecting
strings on Python 3, returning to compliance with Twisted's test
suite.

## 17.2.0

*(June 17, 2017)*

Fixed a great round of issues based on the amazing community review
(@wsanchez and @jvanasco) after our first listserv announcement and
[PyConWeb talk](https://www.youtube.com/watch?v=EIkmADO-r10).

* Add checking for invalid unescaped delimiters in parameters to the
  `URL` constructor. No more slashes and question marks allowed in
  path segments themselves.
* More robust support for IDNA decoding on "narrow"/UCS-2 Python
  builds (e.g., Mac's built-in Python).
* Correctly encode colons in the first segment of relative paths for
  URLs with no scheme set.
* Make URLs with empty paths compare as equal (`http://example.com`
  vs. `http://example.com/`) per RFC 3986. If you need the stricter
  check, you can check the attributes directly or compare the strings.
* Automatically escape the arguments to `.child()` and `.sibling()`
* Fix some IPv6 and port parsing corner cases.

## 17.1.1

* Python 2.6 support
* Added LICENSE
* Automated CI and code coverage
* When a host and a query string are present, empty paths are now
  rendered as a single slash. This is slightly more in line with RFC
  3986 section 6.2.3, but might need to go further and use an empty
  slash whenever the authority is present. This also better replicates
  Twisted URL's old behavior.

## 17.1.0

* Correct encoding for username/password part of URL (userinfo)
* Dot segments are resolved on empty URL.click
* Many, many more schemes and default ports
* Faster percent-encoding with segment-specific functions
* Better detection and inference of scheme netloc usage (the presence
  of `//` in URLs)
* IPv6 support with IP literal validation
* Faster, regex-based parsing
* URLParseError type for errors while parsing URLs
* URL is now hashable, so feel free to use URLs as keys in dicts
* Improved error on invalid scheme, directing users to URL.from_text
  in the event that they used the wrong constructor
* PEP8-compatible API, with full, transparent backwards compatibility
  for Twisted APIs, guaranteed.
* Extensive docstring expansion.

## Pre-17.0.0

* Lots of good features! Used to be called twisted.python.url
