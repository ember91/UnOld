from version import Version, VersionComparison


def test_compare_equal() -> None:
    assert Version('', '', 4, 3, 2, 1).compare(Version('', '', 4, 3, 2, 1)) == VersionComparison.EQUAL
    assert Version('', '', 4, 3, 2, None).compare(Version('', '', 4, 3, 2, None)) == VersionComparison.EQUAL
    assert Version('', '', 4, 3, None, None).compare(Version('', '', 4, 3, None, None)) == VersionComparison.EQUAL
    assert Version('', '', 4, None, None, None).compare(Version('', '', 4, None, None, None)) == VersionComparison.EQUAL

    assert Version('', '', 4, 3, 2, 1).compare(Version('', '', 4, 3, 2, None)) == VersionComparison.EQUAL
    assert Version('', '', 4, 3, 2, 1).compare(Version('', '', 4, 3, None, None)) == VersionComparison.EQUAL
    assert Version('', '', 4, 3, 2, 1).compare(Version('', '', 4, None, None, None)) == VersionComparison.EQUAL

    assert Version('', '', 4, 3, 2, None).compare(Version('', '', 4, 3, 2, 1)) == VersionComparison.EQUAL
    assert Version('', '', 4, 3, None, None).compare(Version('', '', 4, 3, 2, 1)) == VersionComparison.EQUAL
    assert Version('', '', 4, None, None, None).compare(Version('', '', 4, 3, 2, 1)) == VersionComparison.EQUAL


def test_compare_smaller() -> None:
    assert Version('', '', 4, 3, 2, 0).compare(Version('', '', 4, 3, 2, 1)) == VersionComparison.LESS_THAN_OTHER
    assert Version('', '', 4, 3, 1, 2).compare(Version('', '', 4, 3, 2, 1)) == VersionComparison.LESS_THAN_OTHER
    assert Version('', '', 4, 2, 3, 1).compare(Version('', '', 4, 3, 2, 1)) == VersionComparison.LESS_THAN_OTHER
    assert Version('', '', 3, 4, 2, 1).compare(Version('', '', 4, 3, 2, 1)) == VersionComparison.LESS_THAN_OTHER

    assert Version('', '', 4, 3, 1, None).compare(Version('', '', 4, 3, 2, 1)) == VersionComparison.LESS_THAN_OTHER
    assert Version('', '', 4, 2, None, None).compare(Version('', '', 4, 3, 2, 1)) == VersionComparison.LESS_THAN_OTHER
    assert (
        Version('', '', 3, None, None, None).compare(Version('', '', 4, 3, 2, 1)) == VersionComparison.LESS_THAN_OTHER
    )

    assert Version('', '', 4, 3, 2, 1).compare(Version('', '', 4, 3, 3, None)) == VersionComparison.LESS_THAN_OTHER
    assert Version('', '', 4, 3, 2, 1).compare(Version('', '', 4, 4, None, None)) == VersionComparison.LESS_THAN_OTHER
    assert (
        Version('', '', 4, 3, 2, 1).compare(Version('', '', 5, None, None, None)) == VersionComparison.LESS_THAN_OTHER
    )


def test_compare_greater() -> None:
    assert Version('', '', 4, 3, 2, 2).compare(Version('', '', 4, 3, 2, 1)) == VersionComparison.GREATER_THAN_OTHER
    assert Version('', '', 4, 3, 3, 0).compare(Version('', '', 4, 3, 2, 1)) == VersionComparison.GREATER_THAN_OTHER
    assert Version('', '', 4, 4, 1, 1).compare(Version('', '', 4, 3, 2, 1)) == VersionComparison.GREATER_THAN_OTHER
    assert Version('', '', 5, 2, 2, 1).compare(Version('', '', 4, 3, 2, 1)) == VersionComparison.GREATER_THAN_OTHER

    assert Version('', '', 4, 3, 3, None).compare(Version('', '', 4, 3, 2, 1)) == VersionComparison.GREATER_THAN_OTHER
    assert (
        Version('', '', 4, 4, None, None).compare(Version('', '', 4, 3, 2, 1)) == VersionComparison.GREATER_THAN_OTHER
    )
    assert (
        Version('', '', 5, None, None, None).compare(Version('', '', 4, 3, 2, 1))
        == VersionComparison.GREATER_THAN_OTHER
    )

    assert Version('', '', 4, 3, 2, 1).compare(Version('', '', 4, 3, 1, None)) == VersionComparison.GREATER_THAN_OTHER
    assert (
        Version('', '', 4, 3, 2, 1).compare(Version('', '', 4, 2, None, None)) == VersionComparison.GREATER_THAN_OTHER
    )
    assert (
        Version('', '', 4, 3, 2, 1).compare(Version('', '', 3, None, None, None))
        == VersionComparison.GREATER_THAN_OTHER
    )
