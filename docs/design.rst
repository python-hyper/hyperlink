Hyperlink Design
================

The URL is a nuanced format with a long history. Suitably, a lot of
work has gone into translating it into a Pythonic interface. Hyperlink
strikes a unique balance of correctness and usability.

A Tale of Two Representations
-----------------------------

The URL is a powerful construct with two canonical representations
that have historically caused some confusion: the URI and the
IRI. (The W3C even recognized this themselves.) Hyperlink's URL sets
this record straight. Simply:

* URI: Fully-encoded, suitable for network transfer
* IRI: Fully-decoded, suitable for display (e.g., in a browser bar)

   >>> url = URL.from_text('http://example.com/café')
   >>> url.to_uri().to_text()
   u'http://example.com/caf%C3%A9'

Ah, there's that percent encoding, characteristic of URIs. Still,
Hyperlink's distinction between URIs and IRIs is limited to
output. Input can contain any mix of percent encoding and Unicode,
without issue:

   >>> url = URL.from_text('http://example.com/caf%C3%A9/au láit')
   >>> print(url.to_iri().to_text())
   http://example.com/café/au láit
   >>> print(url.to_uri().to_text())
   http://example.com/caf%C3%A9/au%20l%C3%A1it

Note that the URI and IRI representation of the same resource are
still different URLs:

   >>> url.to_uri() == url.to_iri()
   False

Immutability
------------

Hyperlink's URL is also notable for being an immutable
representation. Once constructed, instances are not changed. Methods
like :meth:`~URL.click()`, :meth:`~URL.set()`, and
:meth:`~URL.replace()`, all return new URL objects. This enables URLs
to be used in sets, as well as dictionary keys.

Query Parameters
----------------

One of the URL format's most powerful features is query parameters,
encoded in the query string portion of the URL.

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
