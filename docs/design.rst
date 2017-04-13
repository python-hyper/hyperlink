Hyperlink Design
================

The URL is a nuanced format with a long history. Suitably, a lot of
work has gone into translating it into a Pythonic
interface. Hyperlink's design strikes a unique balance of correctness
and usability.

A Tale of Two Representations
-----------------------------

The URL is a powerful construct, designed to be used by both humans
and computers.

This dual purpose has resulted in two canonical representations: the
URI and the IRI.

Even though the W3C themselves have recognized the confusion this can
cause, Hyperlink's URL makes the distinction quite natural. Simply:

* **URI**: Fully-encoded, ASCII-only, suitable for network transfer
* **IRI**: Fully-decoded, Unicode-friendly, suitable for display (e.g., in a browser bar)

Hyperlink's dual support in action::

   >>> url = URL.from_text('http://example.com/café')
   >>> url.to_uri().to_text()
   u'http://example.com/caf%C3%A9'

We construct a URL from text containing Unicode, then transform it
using :meth:`~URL.to_uri()`. This results in ASCII-only
percent-encoding characteristic of URIs.

Still, Hyperlink's distinction between URIs and IRIs is limited to
output. Input can contain *any mix* of percent encoding and Unicode,
without issue:

   >>> url = URL.from_text('http://example.com/caf%C3%A9/au láit')
   >>> print(url.to_iri().to_text())
   http://example.com/café/au láit
   >>> print(url.to_uri().to_text())
   http://example.com/caf%C3%A9/au%20l%C3%A1it

Note that even when a URI and IRI point to the same resource, they can
still easily be different URLs:

   >>> url.to_uri() == url.to_iri()
   False

And just like that, you're qualified to correct other people (and
their code) on the nuances of URI vs IRI.

Immutability
------------

Hyperlink's URL is notable for being an `immutable`_ representation. Once
constructed, instances are not changed. Methods like
:meth:`~URL.click()`, :meth:`~URL.set()`, and :meth:`~URL.replace()`,
all return new URL objects. This enables URLs to be used in sets, as
well as dictionary keys.

.. _immutable: https://docs.python.org/2/glossary.html#term-immutable
.. _multidict: https://en.wikipedia.org/wiki/Multimap
.. _query string: https://en.wikipedia.org/wiki/Query_string
.. _GET parameters: http://php.net/manual/en/reserved.variables.get.php
.. _twisted.python.url.URL: https://twistedmatrix.com/documents/current/api/twisted.python.url.URL.html
.. _boltons.urlutils: http://boltons.readthedocs.io/en/latest/urlutils.html
.. _uri clarification: https://www.w3.org/TR/uri-clarification/
.. _BNF grammar: https://tools.ietf.org/html/rfc3986#appendix-A


.. _RFC 3986: https://tools.ietf.org/html/rfc3986
.. _section 5.4: https://tools.ietf.org/html/rfc3986#section-5.4
.. _section 3.4: https://tools.ietf.org/html/rfc3986#section-3.4
.. _section 5.2.4: https://tools.ietf.org/html/rfc3986#section-5.2.4
.. _section 2.2: https://tools.ietf.org/html/rfc3986#section-2.2
.. _section 2.3: https://tools.ietf.org/html/rfc3986#section-2.3
.. _section 3.2.1: https://tools.ietf.org/html/rfc3986#section-3.2.1


Query parameters
----------------

One of the URL format's most useful features is the mapping formed
by the query parameters, sometimes called "query arguments" or "GET
parameters". Regardless of what you call them, they are encoded in
the query string portion of the URL, and they are very powerful.

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

Origins and backwards-compatibility
-----------------------------------

Hyperlink's URL is descended directly from `twisted.python.url.URL`_,
in all but the literal code-inheritance sense. While a lot of
functionality has been incorporated from `boltons.urlutils`_, extra
care has been taken to maintain backwards-compatibility for legacy
APIs, making Hyperlink's URL a drop-in replacement for Twisted's URL type.

If you are porting a Twisted project to use Hyperlink's URL, and
encounter any sort of incompatibility, please do not hesitate to `file
an issue`_.

.. _file an issue: https://github.com/mahmoud/hyperlink/issues

Why Hyperlink?
--------------

Let us count the ways.

Advantages over text
~~~~~~~~~~~~~~~~~~~~

URLs were designed as a text format, so, apart from the principle of
structuring structured data, why build a library dedicated to URLs?

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

Compared to other libraries
~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

The Future of URLs
~~~~~~~~~~~~~~~~~~

Hyperlink's first release, in 2017, comes somewhere between 23 and 30
years after URLs were already in use. Is the URL really still that big
of a deal?

Look, buddy, I don't know how you got this document, but I'm pretty
sure you (and your computer) used one if not many URLs to get
here. URLs are only getting more relevant. Buy stock in URLs.

And if you're worried that URLs are just another technology with an
obsoletion date planned in advance, I'll direct your attention to the
``IPvFuture`` rule in the `BNF grammar`_. The URL has plans to outlast
IPv6, and probably you and me.
