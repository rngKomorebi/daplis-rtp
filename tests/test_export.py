"""Exporting the numbers behind a plot.

The point of the export is that a file found on a disk months later can
still say where it came from, and that the numbers in it read back as
the numbers that were drawn. Both are checked here by writing a file and
reading it again with the tools someone would actually use.

"""

import os

import numpy as np
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PyQt5")

from daplis_rtp.gui.main_window import write_plotted_data  # noqa: E402

SAMPLE = {
    "stem": "online-plot",
    "columns": {
        "pixel": np.arange(8),
        "rate_Hz": np.linspace(0, 7000, 8),
        "masked": np.array([0, 0, 1, 0, 0, 0, 0, 0]),
    },
    "notes": [
        "Online plot - photon rate per pixel",
        "daughterboard B7d, motherboard #28, firmware 2212b",
    ],
}


def _read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read().splitlines()


def test_csv_keeps_the_provenance_as_comments(tmp_path):
    path = str(tmp_path / "out.csv")
    write_plotted_data(path, SAMPLE)
    lines = _read(path)

    comments = [line for line in lines if line.startswith("#")]
    assert any("daplis-rtp" in line for line in comments)
    assert any("B7d" in line for line in comments)
    # The version line plus both notes
    assert len(comments) == 3


def test_the_csv_header_row_is_not_commented(tmp_path):
    """So that a spreadsheet reads it as column names.

    ``numpy.savetxt`` comments out every header line it is given,
    including this one, which is why the file is written by hand.

    """
    path = str(tmp_path / "out.csv")
    write_plotted_data(path, SAMPLE)
    body = [line for line in _read(path) if not line.startswith("#")]
    assert body[0] == "pixel,rate_Hz,masked"


def test_csv_values_read_back_as_they_were_written(tmp_path):
    path = str(tmp_path / "out.csv")
    write_plotted_data(path, SAMPLE)
    comments = [line for line in _read(path) if line.startswith("#")]

    table = np.genfromtxt(
        path, delimiter=",", names=True, skip_header=len(comments)
    )
    assert table["pixel"].tolist() == list(range(8))
    np.testing.assert_allclose(
        table["rate_Hz"], SAMPLE["columns"]["rate_Hz"]
    )
    assert table["masked"][2] == 1


def test_npz_reads_back_without_allow_pickle(tmp_path):
    """A plain string array, not an object one.

    ``np.load`` refuses object arrays unless ``allow_pickle`` is set,
    and telling a colleague to enable pickle to read your data is not a
    reasonable thing to do.

    """
    path = str(tmp_path / "out.npz")
    write_plotted_data(path, SAMPLE)

    with np.load(path) as archive:
        np.testing.assert_allclose(
            archive["rate_Hz"], SAMPLE["columns"]["rate_Hz"]
        )
        assert archive["pixel"].tolist() == list(range(8))
        assert any("B7d" in str(note) for note in archive["notes"])


def test_the_extension_decides_the_format(tmp_path):
    csv_path = str(tmp_path / "a.csv")
    npz_path = str(tmp_path / "a.npz")
    write_plotted_data(csv_path, SAMPLE)
    write_plotted_data(npz_path, SAMPLE)

    assert _read(csv_path)[0].startswith("#")
    # A '.npz' is a zip archive, whatever else it is
    with open(npz_path, "rb") as handle:
        assert handle.read(2) == b"PK"
