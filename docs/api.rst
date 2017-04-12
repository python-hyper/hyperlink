Hyperlink API
===========

.. automodule:: hyperlink._url

Creation
--------


.. autoclass:: hyperlink.URL
.. automethod:: hyperlink.URL.from_text

Transformation
--------------

.. automethod:: hyperlink.URL.to_text
.. automethod:: hyperlink.URL.to_uri
.. automethod:: hyperlink.URL.to_iri
.. automethod:: hyperlink.URL.replace

Navigation
----------

.. automethod:: hyperlink.URL.click
.. automethod:: hyperlink.URL.sibling
.. automethod:: hyperlink.URL.child

Query Parameters
----------------

.. automethod:: hyperlink.URL.get
.. automethod:: hyperlink.URL.add
.. automethod:: hyperlink.URL.set
.. automethod:: hyperlink.URL.remove

Attributes
----------

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

Low-level functions
-------------------

.. autofunction:: hyperlink._url.parse_host
.. autoclass:: hyperlink._url.URLParseError

.. TODO: headings within class docs? navigation, query parameter manipulation, transformation (to/from)
.. TODO: run doctests in docs?
