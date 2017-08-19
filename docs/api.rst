.. _hyperlink_api:

Hyperlink API
=============

.. automodule:: hyperlink._url

Creation
--------

Before you can work with URLs, you must create URLs. There are two
ways to create URLs, from parts and from text.

.. autoclass:: hyperlink.URL
.. automethod:: hyperlink.URL.from_text

Transformation
--------------

Once a URL is created, some of the most common tasks are to transform
it into other URLs and text.

.. automethod:: hyperlink.URL.to_text
.. automethod:: hyperlink.URL.to_uri
.. automethod:: hyperlink.URL.to_iri
.. automethod:: hyperlink.URL.replace
.. automethod:: hyperlink.URL.normalize

Navigation
----------

Go places with URLs. Simulate browser behavior and perform semantic
path operations.

.. automethod:: hyperlink.URL.click
.. automethod:: hyperlink.URL.sibling
.. automethod:: hyperlink.URL.child

Query Parameters
----------------

CRUD operations on the query string multimap.

.. automethod:: hyperlink.URL.get
.. automethod:: hyperlink.URL.add
.. automethod:: hyperlink.URL.set
.. automethod:: hyperlink.URL.remove

Attributes
----------

URLs have many parts, and URL objects have many attributes to represent them.

.. autoattribute:: hyperlink.URL.absolute
.. autoattribute:: hyperlink.URL.scheme
.. autoattribute:: hyperlink.URL.host
.. autoattribute:: hyperlink.URL.port
.. autoattribute:: hyperlink.URL.path
.. autoattribute:: hyperlink.URL.query
.. autoattribute:: hyperlink.URL.fragment
.. autoattribute:: hyperlink.URL.userinfo
.. autoattribute:: hyperlink.URL.user
.. autoattribute:: hyperlink.URL.rooted
.. autoattribute:: hyperlink.URL.family

Low-level functions
-------------------

A couple of notable helpers used by the :class:`~hyperlink.URL` type.

.. autoclass:: hyperlink.URLParseError
.. autofunction:: hyperlink.register_scheme
.. autofunction:: hyperlink.parse_host

.. TODO: run doctests in docs?
