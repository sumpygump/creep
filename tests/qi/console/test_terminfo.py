"""Tests for QI console terminfo"""

# pylint: disable=protected-access

from unittest import mock

from qi.console.terminfo import Terminfo


def test_terminfo():
    terminfo = Terminfo()
    assert terminfo.has_terminfo_db is True


def test_has_capability():
    terminfo = Terminfo()
    result = terminfo.has_capability("op")
    assert result is True

    result = terminfo.has_capability("barnacle")
    assert result is False

    terminfo.has_terminfo_db = False
    result = terminfo.has_capability("op")
    assert result is False


def test_do_capability():
    terminfo = Terminfo()
    result = terminfo.do_capability("op")
    assert result != ""

    result = terminfo.do_capability("setaf", 1)
    assert result != ""

    result = terminfo.do_capability("cup", 7, 2)
    assert result.encode() != b""

    result = terminfo.do_capability("barnacle")
    assert result == ""

    terminfo.has_terminfo_db = False
    result = terminfo.do_capability("op")
    assert result == ""
