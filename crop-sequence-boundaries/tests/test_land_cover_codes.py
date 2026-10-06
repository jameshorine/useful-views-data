import pytest

from crop_sequence_boundaries.config import METADATA_PATH
from crop_sequence_boundaries.step2_land_cover_codes import extract_land_cover


def test_parses_release_metadata():
    rows = extract_land_cover(METADATA_PATH.read_bytes())
    assert len(rows) == 135
    assert rows[0] == (0, "Background")
    assert rows[-1] == (254, "Dbl Crop Barley/Soybeans")
    assert len({code for code, _ in rows}) == len(rows)


def test_rejects_page_without_dictionary():
    with pytest.raises(ValueError, match="exactly one"):
        extract_land_cover(b"<html><pre>nothing here</pre></html>")


def test_rejects_duplicate_codes():
    html = b"""<pre>Categorization Code  Land Cover
    "1" Corn
    "1" Corn again
    </pre>"""
    with pytest.raises(ValueError, match="duplicate"):
        extract_land_cover(html)
