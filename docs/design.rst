Hyperlink Design
================

The URL is a nuanced format with a long history. Suitably, a lot of
work has gone into translating the standards, `RFC 3986`_ and `RFC
3987`_, into a Pythonic interface. Hyperlink's design strikes a unique
balance of correctness and usability.

.. _uris_and_iris:

A Tale of Two Representations
-----------------------------

The URL is a powerful construct, designed to be used by both humans
and computers.

This dual purpose has resulted in two canonical representations: the
URI and the IRI.

Even though the W3C themselves have `recognized the confusion`_ this can
cause, Hyperlink's URL makes the distinction quite natural. Simply:

* **URI**: Fully-encoded, ASCII-only, suitable for network transfer
* **IRI**: Fully-decoded, Unicode-friendly, suitable for display (e.g., in a browser bar)

We can use Hyperlink to very easily demonstrate the difference::

   >>> url = URL.from_text('http://example.com/café')
   >>> url.to_uri().to_text()
   u'http://example.com/caf%C3%A9'

We construct a URL from text containing Unicode (``é``), then
transform it using :meth:`~URL.to_uri()`. This results in ASCII-only
percent-encoding familiar to all web developers, and a common
characteristic of URIs.

Still, Hyperlink's distinction between URIs and IRIs is pragmatic, and
only limited to output. Input can contain *any mix* of percent
encoding and Unicode, without issue:

   >>> url = URL.from_text("http://example.com/caf%C3%A9 au lait/s'il vous plaît!")
   >>> print(url.to_iri().to_text())
   http://example.com/café au lait/s'il vous plaît!
   >>> print(url.to_uri().to_text())
   http://example.com/caf%C3%A9%20au%20lait/s'il%20vous%20pla%C3%AEt!

Note that even when a URI and IRI point to the same resource, they
will often be different URLs:

   >>> url.to_uri() == url.to_iri()
   False

And with that caveat out of the way, you're qualified to correct other
people (and their code) on the nuances of URI vs IRI.

.. _recognized the confusion: https://www.w3.org/TR/uri-clarification/

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
.. _RFC 3987: https://tools.ietf.org/html/rfc3987
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

In the simplest case, these query parameters can be provided as a
dictionary:

   >>> url = URL.from_text('http://example.com/')
   >>> url = url.replace(query={'a': 'b', 'c': 'd'})
   >>> url.to_text()
   u'http://example.com/?a=b&c=d'

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

.. _file an issue: https://github.com/python-hyper/hyperlink/issues
