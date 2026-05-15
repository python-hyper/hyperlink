# -*- coding: utf-8 -*-
"""
Hypothesis strategies.
"""

from __future__ import annotations

try:
    import hypothesis

    del hypothesis
except ImportError:
    __all__: tuple[str, ...] = ()
else:
    from csv import reader as csv_reader
    from os.path import dirname, join
    from string import ascii_letters, digits
    from sys import maxunicode
    from typing import (
        TYPE_CHECKING,
        cast,
    )
    from gzip import open as open_gzip

    from . import DecodedURL, EncodedURL

    from hypothesis import assume
    from hypothesis.strategies import (
        composite,
        integers,
        lists,
        sampled_from,
        text,
    )

    from idna import IDNAError, check_label, encode as idna_encode

    if TYPE_CHECKING:
        from typing import (
            Callable,
            Iterable,
            List,
            Optional,
            Sequence,
            TypeVar,
        )

        T = TypeVar("T")
        DrawCallable = Callable[[Callable[..., T]], T]
    else:
        # Runtime stubs for types that are only used in type checking
        # but are imported by test code
        DrawCallable = None  # type: ignore[assignment,misc]

    __all__ = (
        "decoded_urls",
        "encoded_urls",
        "hostname_labels",
        "hostnames",
        "idna_text",
        "paths",
        "port_numbers",
        "DrawCallable",
    )

    def idna_characters() -> str:
        """
        Returns a string containing IDNA characters.
        """
        global _idnaCharacters

        if not _idnaCharacters:
            result = []

            # Data source "IDNA Derived Properties":
            # https://www.iana.org/assignments/idna-tables-6.3.0/
            #   idna-tables-6.3.0.xhtml#idna-tables-properties
            dataFileName = join(
                dirname(__file__), "idna-tables-properties.csv.gz"
            )
            with open_gzip(dataFileName) as dataFile:
                reader = csv_reader(
                    (line.decode("utf-8") for line in dataFile),
                    delimiter=",",
                )
                next(reader)  # Skip header row
                for row in reader:
                    codes, prop, description = row

                    if prop != "PVALID":
                        # CONTEXTO or CONTEXTJ are also allowed, but they come
                        # with rules, so we're punting on those here.
                        # See: https://tools.ietf.org/html/rfc5892
                        continue

                    startEnd = row[0].split("-", 1)
                    if len(startEnd) == 1:
                        # No end of range given; use start
                        startEnd.append(startEnd[0])
                    start, end = (int(i, 16) for i in startEnd)

                    for i in range(start, end + 1):
                        if i > maxunicode:  # Happens using Py2 on Windows
                            break
                        result.append(chr(i))

            _idnaCharacters = "".join(result)

        return _idnaCharacters

    _idnaCharacters: str = ""

    @composite
    def idna_text(
        draw: DrawCallable, min_size: int = 1, max_size: Optional[int] = None
    ) -> str:
        """
        A strategy which generates IDNA-encodable text.

        @param min_size: The minimum number of characters in the text.
            C{None} is treated as C{0}.

        @param max_size: The maximum number of characters in the text.
            Use C{None} for an unbounded size.
        """
        alphabet = idna_characters()

        assert min_size >= 1

        if max_size is not None:
            assert max_size >= 1

        result = cast(
            str,
            draw(text(min_size=min_size, max_size=max_size, alphabet=alphabet)),
        )

        # FIXME: There should be a more efficient way to ensure we produce
        # valid IDNA text.
        try:
            idna_encode(result)
        except IDNAError:
            assume(False)

        return result

    @composite
    def port_numbers(draw: DrawCallable, allow_zero: bool = False) -> int:
        """
        A strategy which generates port numbers.

        @param allow_zero: Whether to allow port C{0} as a possible value.
        """
        if allow_zero:
            min_value = 0
        else:
            min_value = 1

        return cast(int, draw(integers(min_value=min_value, max_value=65535)))

    @composite
    def hostname_labels(draw: DrawCallable, allow_idn: bool = True) -> str:
        """
        A strategy which generates host name labels.

        @param allow_idn: Whether to allow non-ASCII characters as allowed by
            internationalized domain names (IDNs).
        """
        if allow_idn:
            label = cast(str, draw(idna_text(min_size=1, max_size=63)))

            try:
                label.encode("ascii")
            except UnicodeEncodeError:
                # If the label doesn't encode to ASCII, then we need to check
                # the length of the label after encoding to punycode and adding
                # the xn-- prefix.
                while len(label.encode("punycode")) > 63 - len("xn--"):
                    # Rather than bombing out, just trim from the end until it
                    # is short enough, so hypothesis doesn't have to generate
                    # new data.
                    label = label[:-1]

        else:
            label = cast(
                str,
                draw(
                    text(
                        min_size=1,
                        max_size=63,
                        alphabet=str(ascii_letters + digits + "-"),
                    )
                ),
            )

        # Filter invalid labels.
        # It would be better to reliably avoid generation of bogus labels in
        # the first place, but it's hard...
        try:
            check_label(label)
        except UnicodeError:  # pragma: no cover (not always drawn)
            assume(False)

        return label

    @composite
    def hostnames(
        draw: DrawCallable,
        allow_leading_digit: bool = True,
        allow_idn: bool = True,
    ) -> str:
        """
        A strategy which generates host names.

        @param allow_leading_digit: Whether to allow a leading digit in host
            names; they were not allowed prior to RFC 1123.

        @param allow_idn: Whether to allow non-ASCII characters as allowed by
            internationalized domain names (IDNs).
        """
        # Draw first label, filtering out labels with leading digits if needed
        labels: list[str] = [
            cast(
                str,
                draw(
                    hostname_labels(allow_idn=allow_idn).filter(
                        lambda label: (
                            True
                            if allow_leading_digit
                            else label[0] not in digits
                        )
                    )
                ),
            )
        ]
        # Draw remaining labels
        labels += cast(
            list[str],
            draw(
                lists(
                    hostname_labels(allow_idn=allow_idn),
                    min_size=1,
                    max_size=4,
                )
            ),
        )

        # Trim off labels until the total host name length fits in 252
        # characters.  This avoids having to filter the data.
        # For IDNs, the length must also be checked after Punycode encoding,
        # because the encoded form may be much longer due to the 'xn--' prefix
        # and Unicode-to-ASCII expansion. This ensures compliance with RFC 1035
        # and IDNA's 255-byte limit.

        def get_len(lbls: list[str]) -> int:
            d = ".".join(lbls)
            if allow_idn:
                try:
                    return len(idna_encode(d))
                except IDNAError:
                    # Encoding failed due to length or invalidity.
                    # Return large number to force trimming.
                    return 9999
            return len(d)

        # Trim off labels until total hostname length fits IDNA/DNS limits
        while get_len(labels) > 253 and len(labels) > 1:
            labels = labels[:-1]

        return ".".join(labels)

    def path_characters() -> str:
        """
        Returns a string containing valid URL path characters.
        """
        global _path_characters

        if _path_characters is None:

            def chars() -> Iterable[str]:
                for i in range(maxunicode):
                    c = chr(i)

                    # Exclude reserved characters
                    if c in "#/?":
                        continue

                    # Exclude anything not UTF-8 compatible
                    try:
                        c.encode("utf-8")
                    except UnicodeEncodeError:
                        continue

                    yield c

            _path_characters = "".join(chars())

        return _path_characters

    _path_characters: Optional[str] = None

    @composite
    def paths(draw: DrawCallable) -> Sequence[str]:
        return cast(
            "List[str]",
            draw(
                lists(text(min_size=1, alphabet=path_characters()), max_size=10)
            ),
        )

    @composite
    def encoded_urls(draw: DrawCallable) -> EncodedURL:
        """
        A strategy which generates L{EncodedURL}s.
        Call the L{EncodedURL.to_uri} method on each URL to get an HTTP
        protocol-friendly URI.
        """
        port = cast("Optional[int]", draw(port_numbers(allow_zero=True)))
        host = cast(str, draw(hostnames()))
        path = cast("Sequence[str]", draw(paths()))

        if port == 0:
            port = None

        return EncodedURL(
            scheme=cast(str, draw(sampled_from(("http", "https")))),
            host=host,
            port=port,
            path=path,
        )

    @composite
    def decoded_urls(draw: DrawCallable) -> DecodedURL:
        """
        A strategy which generates L{DecodedURL}s.
        Call the L{EncodedURL.to_uri} method on each URL to get an HTTP
        protocol-friendly URI.
        """
        return DecodedURL(draw(encoded_urls()))
