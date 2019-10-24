# hyperlink TODO

* RFC 3986 6.2.3 (always slash on empty path and non-empty host, not
  just when query string is present)
* Polish logo
* Get coverage up
* Switch off ctypes/socket for IP validation
* rebase method for path (prepends to path)
* sibling() should be maximal=False like child()
* make subencoding an exposed parameter

## normalize method

* unquote all unreserved characters (RFC 3986 2.3)
* lowercase scheme
* lowercase host (including lowercase ipv6 addresses)
* resolve path parts (RFC 3986 6.2.2)
* percent encoding (RFC 3986 2.1) to uppercase (add a
  `normalize_case=False` to `_percent_decode`, with appropriate upward
  propagation)


## Complete

* docstrings
* Parse with regular expression
* Parse/emit IPv6
* Add netloc detection logic
* Speed up percent encoding with urlutils approach
* More default ports
* resolve dots on (empty) click
* better error on URL constructor (single string argument leads to successful instantiation with invalid scheme)
* pct encode userinfo
* `__hash__`
* README
* CI
* Get Mark to fix the git history
* Python 2.6 support
* Full read the docs

## Questions

* What's the deal with twisted.python.urlpath?
* What's the deal with sip.URL?
* Should we take the alternative IPv6 literal approach and just
  interpret anything with colons in the host as requiring square
  brackets? Or should we try to validate with a regex?
* Do we need a separate .normalize()? Resolves all dots, lowercases scheme and host.
* Is whitespace really allowed in IRIs?
* Can we drop the ':' when password isn't displayed?
* Why is the constructor's default scheme "http" when host is not None?
* What should the default port of the "s3" scheme be? premature?
* Should _url be lifted?
