"""Tests for creepclient module"""

import os
import shutil
from unittest import mock

from creepclient.creepclient import CreepClient
from creepclient.repository import Repository

TEST_APP_DIR = "/tmp/creep-testing"


def make_tmp_dirs():
    """Make some tmp dirs for use during testing"""
    tmpbase = TEST_APP_DIR
    if os.path.exists(tmpbase):
        shutil.rmtree(tmpbase)

    cachedir = os.path.join(tmpbase, "cache")
    savedir = os.path.join(tmpbase, "save")
    os.makedirs(cachedir, exist_ok=True)
    os.makedirs(savedir, exist_ok=True)
    return cachedir, savedir


def clean_up_tmp_dir():
    tmpbase = TEST_APP_DIR
    if os.path.exists(tmpbase):
        shutil.rmtree(tmpbase)


def test_client():
    client = CreepClient()
    assert client.version != "1.1"
    assert client.appdir != ""


def test_get_attr(capsys):
    """Test the special __getattr__ method on client"""
    client = CreepClient()

    # Nonexistent method that won't exist ever
    try:
        client.make_pizza()
    except AttributeError:
        assert True

    # Help method that doesn't have a corresponding do_ method
    try:
        client.help_make_pizza()
    except AttributeError:
        assert True

    func = client.help_version
    func()
    captured = capsys.readouterr()
    assert captured.out == "Display creep version\n"


def test_version(capsys):
    """Test the 'version' command"""
    client = CreepClient()
    client.do_version([])
    captured = capsys.readouterr()
    assert "Creep v" in captured.out
    assert "Targetting minecraft version" in captured.out
    assert "Profile path" in captured.out


def test_install_with_strategy_empty(capsys):
    cachedir, savedir = make_tmp_dirs()
    package = mock.MagicMock()
    package.name = "flans_mod"
    package.get_local_filename.return_value = "archive1.zip"

    client = CreepClient()
    result = client.install_with_strategy("", package, cachedir, savedir)
    captured = capsys.readouterr()
    assert result is None
    assert captured.out == ""


def test_install_with_strategy_noop(capsys):
    cachedir, savedir = make_tmp_dirs()
    package = mock.MagicMock()
    package.name = "flans_mod"
    package.get_local_filename.return_value = "archive1.zip"

    client = CreepClient()
    result = client.install_with_strategy("do;not;anything", package, cachedir, savedir)
    captured = capsys.readouterr()
    assert result is True
    assert captured.out == "Installing with strategy: do;not;anything\n"
    clean_up_tmp_dir()


def test_install_with_strategy_unzip_only(capsys):
    cachedir, savedir = make_tmp_dirs()
    shutil.copy("tests/data/archive1.zip", os.path.join(cachedir, "archive1.zip"))

    package = mock.MagicMock()
    package.name = "flans_mod"
    package.get_local_filename.return_value = "archive1.zip"

    client = CreepClient()
    result = client.install_with_strategy("unzip", package, cachedir, savedir)
    captured = capsys.readouterr()
    assert result is True
    assert captured.out == (
        "Installing with strategy: unzip\n"
        "Unzipping archive: /tmp/creep-testing/cache/archive1.zip\n"
    )
    clean_up_tmp_dir()


def test_install_with_strategy_unzip_and_move(capsys):
    # Example with unzip and move, but the savedir already exists
    cachedir, savedir = make_tmp_dirs()
    shutil.copy("tests/data/archive1.zip", os.path.join(cachedir, "archive1.zip"))

    package = mock.MagicMock()
    package.name = "flans_mod"
    package.get_local_filename.return_value = "archive1.zip"

    client = CreepClient()
    strategy = "unzip;move dir1"
    result = client.install_with_strategy(strategy, package, cachedir, savedir)
    captured = capsys.readouterr()
    assert result is True
    assert captured.out == (
        "Installing with strategy: unzip;move dir1\n"
        "Unzipping archive: /tmp/creep-testing/cache/archive1.zip\n"
        "Moving files: dir1\n"
    )
    assert sorted(os.listdir(savedir)) == ["file1.txt", "file2.txt", "file3.txt"]
    clean_up_tmp_dir()


def test_install_with_strategy_unzip_and_move_new(capsys):
    # Example with unzip and move, but the savedir doesn't exist
    cachedir, savedir = make_tmp_dirs()
    shutil.copy("tests/data/archive1.zip", os.path.join(cachedir, "archive1.zip"))

    package = mock.MagicMock()
    package.name = "flans_mod"
    package.get_local_filename.return_value = "archive1.zip"

    client = CreepClient()
    strategy = "unzip;move dir1"
    save_alt = savedir.replace("save", "save_alt")
    result = client.install_with_strategy(strategy, package, cachedir, save_alt)
    captured = capsys.readouterr()
    assert result is True
    assert captured.out == (
        "Installing with strategy: unzip;move dir1\n"
        "Unzipping archive: /tmp/creep-testing/cache/archive1.zip\n"
        "Moving files: dir1\n"
    )
    assert sorted(os.listdir(save_alt)) == ["file1.txt", "file2.txt", "file3.txt"]
    clean_up_tmp_dir()


def test_install_with_strategy_with_star(capsys):
    # Example with unzip and move using move /*
    cachedir, savedir = make_tmp_dirs()
    shutil.copy("tests/data/archive1.zip", os.path.join(cachedir, "archive1.zip"))

    package = mock.MagicMock()
    package.name = "flans_mod"
    package.get_local_filename.return_value = "archive1.zip"

    client = CreepClient()
    strategy = "unzip; move 'dir1/*'"
    result = client.install_with_strategy(strategy, package, cachedir, savedir)
    captured = capsys.readouterr()
    assert result is True
    assert captured.out == (
        "Installing with strategy: unzip; move 'dir1/*'\n"
        "Unzipping archive: /tmp/creep-testing/cache/archive1.zip\n"
        "Moving files: dir1/*\n"
    )
    assert sorted(os.listdir(savedir)) == ["file1.txt", "file2.txt", "file3.txt"]
    clean_up_tmp_dir()
