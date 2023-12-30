"""Tests for QI console terminal"""

# pylint: disable=protected-access

from unittest import mock

from qi.console.terminal import Terminal
from qi.console.terminfo import Terminfo


def test_terminal():
    terminal = Terminal()
    assert isinstance(terminal.terminfo, Terminfo)


def test_terminal_setting_terminfo():
    terminfo = Terminfo()
    terminfo.instance_id = 1234
    terminal = Terminal(terminfo=terminfo)
    assert isinstance(terminal.terminfo, Terminfo)
    assert terminal.terminfo.instance_id == 1234


def test_terminal_isatty():
    terminal = Terminal()
    assert terminal.isatty() is False

    terminal._isatty = True
    assert terminal.isatty() is True


def test_terminal_getattr():
    terminal = Terminal()
    result = terminal.bold()
    assert result == ""

    terminal._isatty = True
    result = terminal.bold()
    assert result == "\x1b[1m"


def test_terminal_getattr_noexist():
    terminal = Terminal()
    result = terminal.spaghetti()
    assert result == ""


def test_printterm(capsys):
    terminal = Terminal()
    terminal._isatty = False
    terminal.printterm("Only print if a tty")

    captured = capsys.readouterr()
    assert captured.out == ""

    terminal._isatty = True
    terminal.printterm("Now it thinks it is")
    captured = capsys.readouterr()
    assert captured.out == "Now it thinks it is"


def test_clear(capsys):
    # Mock the return value because the test runner overrides sys.stdout
    mock_terminfo = mock.MagicMock()
    mock_terminfo.clear.return_value = "HG"

    terminal = Terminal(terminfo=mock_terminfo)
    terminal._isatty = True
    terminal.clear()
    captured = capsys.readouterr()
    assert captured.out == "HG"


def test_locate(capsys):
    mock_terminfo = mock.MagicMock()
    mock_terminfo.cup.return_value = "Q4"

    terminal = Terminal(terminfo=mock_terminfo)
    terminal._isatty = True
    terminal.locate(2, 4)
    captured = capsys.readouterr()
    assert captured.out == "Q4"


def test_bold_type():
    terminal = Terminal()
    terminal._isatty = True
    terminal.bold_type()


def test_set_fg_color():
    terminal = Terminal()
    terminal._isatty = True
    terminal.set_fg_color(1)


def test_set_bg_color():
    terminal = Terminal()
    terminal._isatty = True
    terminal.set_bg_color(1)


def test_get_columns_lines():
    with mock.patch("qi.console.terminal.Terminal._get_size") as mock_gs:
        mock_gs.return_value = 20, 40
        terminal = Terminal()
        assert terminal.get_columns() == 20
        assert terminal.get_lines() == 40


def test_pretty_message(capsys):
    terminal = Terminal()
    terminal.pretty_message("Yay for doors")
    captured = capsys.readouterr()
    assert captured.out == "                 \n  Yay for doors  \n                 \n\n"


def test_pretty_message_multiline(capsys):
    terminal = Terminal()
    terminal.pretty_message("BIG\nTIME", max_width=12)
    captured = capsys.readouterr()
    assert captured.out == "            \n  BIG       \n  TIME      \n            \n\n"


def test_pretty_message_no_vert_padding(capsys):
    terminal = Terminal()
    terminal.pretty_message("Yay for doors", vertical_padding=False)
    captured = capsys.readouterr()
    assert captured.out == "  Yay for doors  \n\n"


def test_wordwrap():
    terminal = Terminal()
    result = terminal.wordwrap("Let's get this show on the road", 20, 2, 4, "#")
    assert result == "#  Let's get this\n#    show on the\n#    road"


def test_wordwrap_fill():
    terminal = Terminal()
    result = terminal.wordwrap_fill(
        "Let's get this show on the road friends and foes come one come all", 36, 2
    )
    assert result == (
        "Let's get this show on the road\n  friends and foes come one come all"
    )
