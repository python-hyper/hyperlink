# Hyperlink Changelog

## 17.0.0

* Improved error on invalid scheme, directing users to URL.from_text
  in the event that they used the wrong constructor
* Correct encoding for username/password part of URL (userinfo)
* Dot segments are resolved on empty URL.click
* Many, many more schemes and default ports
* Faster percent-encoding with segment-specific functions
* Better detection and inference of scheme netloc usage (the presence
  of // in URLs)
* IPv6 support
* Faster, regex-based parsing
* URLParseError type for errors while parsing URLs

## Pre-17.0.0

* Lots of good features! Used to be called twisted.python.url
