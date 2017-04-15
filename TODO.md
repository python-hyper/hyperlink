# hyperlink TODO

* CI
* Get Mark to fix the git history
* Optimize percent decoding

## Complete

* docstrings
* Parse with regular expression
* Parse/emit IPv6
* Add netloc detection logic
* Speed up percent encoding with urlutils approach
* More default ports
* resolve dots on (empty) click
* better error on URL constructor (single string argument leads to succesful instantiation with invalid scheme)
* pct encode userinfo
* `__hash__`
* README

## Questions

* What's the deal with twisted.python.urlpath?
* What's the deal with sip.URL
* Do we need a separate .normalize()?
* Is whitespace really allowed in IRIs?
* Can we drop the ':' when password isn't displayed?
* Why is the constructor's default scheme "http" when host is not None?
* What should the default port of the "s3" scheme be? premature?
* Should _url be lifted?
