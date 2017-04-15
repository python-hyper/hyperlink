FAQ
===

There were bound to be questions.

.. contents::
   :local:

Why not just use text?
----------------------

URLs were designed as a text format, so, apart from the principle of
structuring structured data, why use URL objects?

There are two major advantages of using :class:`~hyperlink.URL` over
representing URLs as strings. The first is that it's really easy to
evaluate a relative hyperlink, for example, when crawling documents,
to figure out what is linked::

    >>> URL.from_text(u'https://example.com/base/uri/').click(u"/absolute")
    URL.from_text(u'https://example.com/absolute')
    >>> URL.from_text(u'https://example.com/base/uri/').click(u"rel/path")
    URL.from_text(u'https://example.com/base/uri/rel/path')

The other is that URLs have two normalizations. One representation is
suitable for humans to read, because it can represent data from many
character sets - this is the Internationalized, or IRI, normalization.
The other is the older, US-ASCII-only representation, which is
necessary for most contexts where you would need to put a URI.  You
can convert *between* these representations according to certain
rules.  :class:`~hyperlink.URL` exposes these conversions as methods::

    >>> URL.from_text(u"https://→example.com/foo⇧bar/").to_uri()
    URL.from_text(u'https://xn--example-dk9c.com/foo%E2%87%A7bar/')
    >>> URL.from_text(u'https://xn--example-dk9c.com/foo%E2%87%A7bar/').to_iri()
    URL.from_text(u'https://\\u2192example.com/foo\\u21e7bar/')

For more info, see A Tale of Two Representations, above.

How does Hyperlink compare to other libraries?
----------------------------------------------

Hyperlink certainly isn't the first library to provide a Python model
for URLs. It just happens to be among the best.

urlparse: Built-in to the standard library (merged into urllib for
Python 3). No URL type, requires user to juggle a bunch of
strings. Overly simple approach makes it easy to make mistakes.

boltons.urlutils: Shares some underlying implementation. Two key
differences. First, the boltons URL is mutable, intended to work like
a string factory for URL text. Second, the boltons URL has advanced
query parameter mapping type. Complete implementation in a single
file.

furl: Not a single URL type, but types for many parts of the
URL. Similar approach to boltons for query parameters. Poor netloc
handling (support for non-network schemes like mailto). Unlicensed.

purl: Another immutable implementation. Method-heavy API.

rfc3986: Very heavily focused on various types of validation. Large
for a URL library, if that matters to you. Exclusively supports URIs,
`lacking IRI support`_ at the time of writing.

In reality, any of the third-party libraries above do a better job
than the standard library, and much of the hastily thrown together
code in a corner of a util.py deep in a project. URLs are easy to mess
up, make sure you use a tested implementation.

.. _lacking IRI support: https://github.com/sigmavirus24/rfc3986/issues/23

Are URLs really a big deal in 201X?
-----------------------------------

Hyperlink's first release, in 2017, comes somewhere between 23 and 30
years after URLs were already in use. Is the URL really still that big
of a deal?

Look, buddy, I don't know how you got this document, but I'm pretty
sure you (and your computer) used one if not many URLs to get
here. URLs are only getting more relevant. Buy stock in URLs.

And if you're worried that URLs are just another technology with an
obsoletion date planned in advance, I'll direct your attention to the
``IPvFuture`` rule in the `BNF grammar`_. If it has plans to outlast
IPv6, the URL will probably outlast you and me, too.

.. _BNF grammar: https://tools.ietf.org/html/rfc3986#appendix-A
