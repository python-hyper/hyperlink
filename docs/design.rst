Hyperlink Design
================

The URL is a nuanced format with a long history. Suitably, a lot of
work has gone into translating it into a Pythonic interface. Hyperlink
strikes a unique balance of correctness and usability.

A Tale of Two Representations
-----------------------------

The URL is a powerful construct, designed to be used by both humans
and computers.

This important dual purpose has resulted in two canonical
representations which have historically caused some confusion: the URI
and the IRI.

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

Immutability
------------

Hyperlink's URL is notable for being an immutable representation. Once
constructed, instances are not changed. Methods like
:meth:`~URL.click()`, :meth:`~URL.set()`, and :meth:`~URL.replace()`,
all return new URL objects. This enables URLs to be used in sets, as
well as dictionary keys.

.. TODO links for RFCs, "immutable", "multidict", "GET parameters",
   twisted.python.url, boltons.urlutils, from "immutable" in the API
   doc to the design doc. "BNF grammar"

Query Parameters
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

Hyperlink's URL is descended directly from twisted.python.url.URL (in
all but the literal code-inheritance sense). Care has been taken to
maintain backwards-compatibility in all legacy APIs, making hyperlink
a drop-in replacement for Twisted's URL class.

Versus text
-----------

There are two major advantages of using :class:`~hyperlink.URL` over
representing URLs as strings.  The first is that it's really easy to
evaluate a relative hyperlink, for example, when crawling documents,
to figure out what is linked::

    >>> URL.from_text(u'https://example.com/base/uri/').click(u"/absolute")
    URL.from_text(u'https://example.com/absolute')
    >>> URL.from_text(u'https://example.com/base/uri/').click(u"rel/path")
    URL.from_text(u'https://example.com/base/uri/rel/path')

The other is that URLs have two normalizations.  One representation is
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
