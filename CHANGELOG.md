# Hyperlink Changelog

## "dev"

* Python 2.6 support

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
