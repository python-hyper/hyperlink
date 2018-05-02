"""The humble, but powerful, URL runs everything around us. Chances
are you've used several just to read this text.

Hyperlink is a featureful, pure-Python implementation of the URL, with
an emphasis on correctness. BSD licensed.

See the docs at http://hyperlink.readthedocs.io.
"""

from setuptools import setup


__author__ = 'Mahmoud Hashemi and Glyph Lefkowitz'
__version__ = '18.0.1dev'
__contact__ = 'mahmoud@hatnote.com'
__url__ = 'https://github.com/python-hyper/hyperlink'
__license__ = 'MIT'


setup(name='hyperlink',
      version=__version__,
      description="A featureful, immutable, and correct URL for Python.",
      long_description=__doc__,
      author=__author__,
      author_email=__contact__,
      url=__url__,
      packages=['hyperlink', 'hyperlink.test'],
      include_package_data=True,
      zip_safe=False,
      license=__license__,
      platforms='any',
      install_requires=['idna>=2.5'],
      classifiers=[
          'Topic :: Utilities',
          'Intended Audience :: Developers',
          'Topic :: Software Development :: Libraries',
          'Development Status :: 5 - Production/Stable',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: Implementation :: PyPy', ]
      )

"""
A brief checklist for release:

* tox
* git commit (if applicable)
* Bump setup.py version off of -dev
* git commit -a -m "bump version for x.y.z release"
* python setup.py sdist bdist_wheel upload
* bump docs/conf.py version
* git commit
* git tag -a vx.y.z -m "brief summary"
* write CHANGELOG
* git commit
* bump setup.py version onto n+1 dev
* git commit
* git push

"""
