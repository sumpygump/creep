"""Tests for QI console client"""

from unittest import mock

from qi.console.client import Client
from qi.console.terminal import Terminal


def test_client():
    client = Client()
    assert isinstance(client.terminal, Terminal)


def test_client_with_terminal():
    terminal = Terminal()
    terminal.instance_id = 1234
    client = Client(terminal=terminal)
    assert isinstance(client.terminal, Terminal)
    assert client.terminal.instance_id == 1234


def test_client_display_warning(capsys):
    # Mocking the terminal because we don't have an active TTY
    mock_terminal = mock.MagicMock()
    mock_terminal.setaf.return_value = "X"
    mock_terminal.op.return_value = "Y"
    client = Client(terminal=mock_terminal)

    result = client.display_warning("It may break")
    captured = capsys.readouterr()
    assert result is None
    assert captured.out == "XIt may breakY\n"


def test_client_display_error():
    mock_terminal = mock.MagicMock()
    mock_terminal.pretty_message.return_value = "Woo hoo"
    client = Client(terminal=mock_terminal)

    result = client.display_error("It broke")
    assert result == "Woo hoo"
