.. hyperlink documentation master file, created on Mon Apr 10 00:34:18 2017.
hyperlink
=========

*Cool URLs that don't change.*

|release| |calver| |changelog|

**Hyperlink** provides a pure-Python implementation of immutable
URLs. Based on `RFC 3986`_ and `RFC 3987`_, the Hyperlink URL balances
simplicity and correctness for both :ref:`URIs and IRIs <uris_and_iris>`.

Hyperlink is tested against Python 2.7, 3.4, 3.5, 3.6, 3.7, 3.8, and PyPy.

For an introduction to the hyperlink library, its background, and URLs
in general, see `this talk from PyConWeb 2017`_ (and `the accompanying
slides`_).

.. _RFC 3986: https://tools.ietf.org/html/rfc3986
.. _RFC 3987: https://tools.ietf.org/html/rfc3987
.. _this talk from PyConWeb 2017: https://www.youtube.com/watch?v=EIkmADO-r10
.. _the accompanying slides: https://speakerdeck.com/mhashemi/urls-in-plain-view
.. |release| image:: https://img.shields.io/pypi/v/hyperlink.svg
             :target: https://pypi.python.org/pypi/hyperlink

.. |calver| image:: https://img.shields.io/badge/calver-YY.MINOR.MICRO-22bfda.svg
   :target: http://calver.org
.. |changelog| image:: https://img.shields.io/badge/CHANGELOG-UPDATED-b84ad6.svg
   :target: https://github.com/python-hyper/hyperlink/blob/master/CHANGELOG.md


Installation and Integration
----------------------------

Hyperlink is a pure-Python package and only depends on the standard
library. The easiest way to install is with pip::

  pip install hyperlink

Then, URLs are just an import away::

  import hyperlink

  url = hyperlink.parse(u'http://github.com/python-hyper/hyperlink?utm_source=readthedocs')

  better_url = url.replace(scheme=u'https', port=443)
  org_url = better_url.click(u'.')

  print(org_url.to_text())
  # prints: https://github.com/python-hyper/

  print(better_url.get(u'utm_source')[0])
  # prints: readthedocs

See :ref:`the API docs <hyperlink_api>` for more usage examples.

Gaps
----

Found something missing in hyperlink? `Pull Requests`_ and `Issues`_ are welcome!

.. _Pull Requests: https://github.com/python-hyper/hyperlink/pulls
.. _Issues: https://github.com/python-hyper/hyperlink/issues

Table of Contents
-----------------

.. toctree::
   :maxdepth: 2

   design
   api
   faq
