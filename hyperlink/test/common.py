

from unittest import TestCase


class HyperlinkTestCase(TestCase):
    """This type mostly exists to provide a backwards-compatible
    assertRaises method for Python 2.6 testing.
    """
    def assertRaises(self, excClass, callableObj=None, *args, **kwargs):
        """Fail unless an exception of class excClass is raised
           by callableObj when invoked with arguments args and keyword
           arguments kwargs. If a different type of exception is
           raised, it will not be caught, and the test case will be
           deemed to have suffered an error, exactly as for an
           unexpected exception.

           If called with callableObj omitted or None, will return a
           context object used like this::

                with self.assertRaises(SomeException):
                    do_something()

           The context manager keeps a reference to the exception as
           the 'exception' attribute. This allows you to inspect the
           exception after the assertion::

               with self.assertRaises(SomeException) as cm:
                   do_something()
               the_exception = cm.exception
               self.assertEqual(the_exception.error_code, 3)
        """
        context = _AssertRaisesContext(excClass, self)
        if callableObj is None:
            return context
        with context:
            callableObj(*args, **kwargs)


class _AssertRaisesContext(object):
    "A context manager used to implement HyperlinkTestCase.assertRaises."

    def __init__(self, expected, test_case, expected_regexp=None):
        self.expected = expected
        self.failureException = test_case.failureException
        self.expected_regexp = expected_regexp

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        if exc_type is None:
            try:
                exc_name = self.expected.__name__
            except AttributeError:
                exc_name = str(self.expected)
            raise self.failureException("%s not raised" % exc_name)
        if not issubclass(exc_type, self.expected):
            # let unexpected exceptions pass through
            return False
        self.exception = exc_value  # store for later retrieval
        if self.expected_regexp is None:
            return True

        expected_regexp = self.expected_regexp
        exc_str = str(exc_value)
        if not expected_regexp.search(exc_str):
            raise self.failureException('%r does not match %r' %
                                        (expected_regexp.pattern, exc_str))
        return True
