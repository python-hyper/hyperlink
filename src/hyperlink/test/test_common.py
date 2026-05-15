"""
Tests for hyperlink.test.common
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest import TestCase
from .common import HyperlinkTestCase

if TYPE_CHECKING:
    from typing import Any


class _ExpectedException(Exception):
    """An exception used to test HyperlinkTestCase.assertRaises."""


class _UnexpectedException(Exception):
    """An exception used to test HyperlinkTestCase.assertRaises."""


class TestHyperlink(TestCase):
    """Tests for HyperlinkTestCase"""

    def setUp(self):
        # type: () -> None
        self.hyperlink_test = HyperlinkTestCase("run")

    def test_assertRaisesWithCallable(self):
        # type: () -> None
        """HyperlinkTestCase.assertRaises does not raise an AssertionError
        when given a callable that, when called with the provided
        arguments, raises the expected exception.

        """
        called_with = []

        def raisesExpected(*args: Any, **kwargs: Any) -> None:
            called_with.append((args, kwargs))
            raise _ExpectedException

        self.hyperlink_test.assertRaises(
            _ExpectedException, raisesExpected, 1, keyword=True
        )
        self.assertEqual(called_with, [((1,), {"keyword": True})])

    def test_assertRaisesWithCallableUnexpectedException(self) -> None:
        """When given a callable that raises an unexpected exception,
        HyperlinkTestCase.assertRaises raises that exception.

        """

        def doesNotRaiseExpected(*args: Any, **kwargs: Any) -> None:
            raise _UnexpectedException

        try:
            self.hyperlink_test.assertRaises(
                _ExpectedException, doesNotRaiseExpected
            )
        except _UnexpectedException:
            pass

    def test_assertRaisesWithCallableDoesNotRaise(self) -> None:
        """HyperlinkTestCase.assertRaises raises an AssertionError when given
        a callable that, when called, does not raise any exception.

        """

        def doesNotRaise(*args: Any, **kwargs: Any) -> None:
            pass

        try:
            self.hyperlink_test.assertRaises(_ExpectedException, doesNotRaise)
        except AssertionError:
            pass

    def test_assertRaisesContextManager(self) -> None:
        """HyperlinkTestCase.assertRaises does not raise an AssertionError
        when used as a context manager with a suite that raises the
        expected exception.  The context manager stores the exception
        instance under its `exception` instance variable.

        """
        with self.hyperlink_test.assertRaises(_ExpectedException) as cm:
            raise _ExpectedException

        self.assertTrue(  # type: ignore[unreachable]
            isinstance(cm.exception, _ExpectedException)
        )

    def test_assertRaisesContextManagerUnexpectedException(self) -> None:
        """When used as a context manager with a block that raises an
        unexpected exception, HyperlinkTestCase.assertRaises raises
        that unexpected exception.

        """
        try:
            with self.hyperlink_test.assertRaises(_ExpectedException):
                raise _UnexpectedException
        except _UnexpectedException:
            pass

    def test_assertRaisesContextManagerDoesNotRaise(self) -> None:
        """HyperlinkTestcase.assertRaises raises an AssertionError when used
        as a context manager with a block that does not raise any
        exception.

        """
        try:
            with self.hyperlink_test.assertRaises(_ExpectedException):
                pass
        except AssertionError:
            pass
