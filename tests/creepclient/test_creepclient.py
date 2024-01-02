"""Tests for creepclient module"""

# pylint: disable=redefined-outer-name

import json
import os
import pytest
import shutil
from unittest import mock
import urllib.error

from creepclient.creepclient import CreepClient
from creepclient.entity.package import Package

TEST_DIR = "/tmp/creep-testing"
APP_DIR = os.path.join(TEST_DIR, "_creep")


@pytest.fixture(autouse=True)
def make_tmp_dirs():
    """Make some tmp dirs for use during testing"""
    tmpbase = TEST_DIR
    if os.path.exists(tmpbase):
        shutil.rmtree(tmpbase)

    os.makedirs(APP_DIR, exist_ok=True)

    cachedir = os.path.join(tmpbase, "cache")
    os.makedirs(cachedir, exist_ok=True)

    savedir = os.path.join(tmpbase, "save")
    os.makedirs(savedir, exist_ok=True)

    # Add sample packages file
    shutil.copy("tests/data/packages.json", os.path.join(APP_DIR, "packages.json"))

    # Define sample user options file
    make_options(
        os.path.join(APP_DIR, "options.json"),
        {
            "minecraft_target": "1.20.2",
            "profile_dir": os.path.join(TEST_DIR, "_minecraft"),
        },
    )

    yield cachedir, savedir

    # Tear down
    clean_up_tmp_dir()


def clean_up_tmp_dir():
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)


def make_options(options_path, data):
    with open(options_path, "w", encoding="utf-8") as outfile:
        json.dump(
            {
                "minecraft_target": data.get("minecraft_target", ""),
                "profile_dir": data.get("profile_dir", ""),
            },
            outfile,
            indent=4,
        )


@pytest.fixture
def sample_mods(make_tmp_dirs):
    _ = make_tmp_dirs
    mods_path = os.path.join(TEST_DIR, "_minecraft", "mods")
    os.makedirs(mods_path, exist_ok=True)

    # Just create some fake 'jar' files in the mods dir
    filenames = ["example.jar", "jei-1.20.2-forge-16.0.0.28.jar"]
    for filename in filenames:
        with open(os.path.join(mods_path, filename), "wb") as f:
            f.write(b"ABC")

    # Also add a file that is ignored
    with open(os.path.join(mods_path, ".DS_Store"), "wb") as f:
        f.write(b"ABC")

    return filenames


@pytest.fixture
def sample_mod_list(make_tmp_dirs):
    _ = make_tmp_dirs
    filename = os.path.join(TEST_DIR, "sample_mod_list.txt")
    with open(filename, "wb") as f:
        f.write(b"jei\njer-integration")

    return filename


def make_file(filename):
    """Make a file with some dummy content"""

    # Get path to file and make sure it exists first
    path = os.path.dirname(filename)
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

    with open(filename, "wb") as f:
        f.write(b"ABC")


def test_client():
    client = CreepClient(appdir=APP_DIR)
    assert client.version != "0.2"
    assert client.appdir == APP_DIR
    assert client.minecraft_target == "1.20.2"
    assert client.profiledir == os.path.join(TEST_DIR, "_minecraft")


def test_client_default_options():
    # If the options file isn't there, starts with default options
    os.unlink(os.path.join(APP_DIR, "options.json"))
    client = CreepClient(appdir=APP_DIR)
    assert client.minecraft_target == "1.20.1"
    assert client.profiledir != os.path.join(TEST_DIR, "_minecraft")


def test_get_attr(capsys):
    """Test the special __getattr__ method on client"""
    client = CreepClient(appdir=APP_DIR)

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
    client = CreepClient(appdir=APP_DIR)
    client.do_version([])
    captured = capsys.readouterr()
    assert "Creep v" in captured.out
    assert "Targetting minecraft version" in captured.out
    assert "Profile path" in captured.out


def test_target(capsys):
    """Test the 'target' command"""
    client = CreepClient(appdir=APP_DIR)
    client.do_target("")
    captured = capsys.readouterr()
    assert "Targetting minecraft version" in captured.out


def test_target_set(capsys):
    """Test the 'target' command"""
    client = CreepClient(appdir=APP_DIR)
    client.do_target("1.20.2")
    captured = capsys.readouterr()
    assert "Targetting minecraft version" in captured.out
    assert client.minecraft_target == "1.20.2"

    client = CreepClient(appdir=APP_DIR)
    assert client.minecraft_target == "1.20.2"


def test_profile(capsys):
    """Test the 'profile' command"""
    client = CreepClient(appdir=APP_DIR)
    client.do_profile("")
    captured = capsys.readouterr()
    assert "Profile path" in captured.out


def test_profile_set(capsys):
    """Test the 'profile' command"""
    client = CreepClient(appdir=APP_DIR)
    client.do_profile("/tmp/creep-testing/")
    captured = capsys.readouterr()
    assert "Profile path" in captured.out
    assert client.profiledir == "/tmp/creep-testing"

    client = CreepClient(appdir=APP_DIR)
    assert client.profiledir == "/tmp/creep-testing"
    client.do_profile("/")
    captured = capsys.readouterr()
    assert "Invalid directory" in captured.out
    assert client.profiledir == "/tmp/creep-testing"


def test_profile_set_invalid(capsys):
    """Test the 'profile' command"""
    client = CreepClient(appdir=APP_DIR)
    client.do_profile("/tmp/barnacles/")
    captured = capsys.readouterr()
    assert "Invalid directory" in captured.out


def test_list(capsys):
    """Test the 'list' command"""
    client = CreepClient(appdir=APP_DIR)
    client.do_list("")
    captured = capsys.readouterr()
    assert "mezz/jei" in captured.out
    assert "View Items and Recipes" in captured.out
    assert "jer-integration" in captured.out


def test_list_short(capsys):
    """Test the 'list' command"""
    client = CreepClient(appdir=APP_DIR)
    client.do_list("--short")
    captured = capsys.readouterr()
    assert "mezz/jei" in captured.out
    assert "View Items and Recipes" not in captured.out
    assert "jer-integration" in captured.out


def test_list_installed(capsys):
    """Test the 'list' command"""
    client = CreepClient(appdir=APP_DIR)
    client.do_list("installed")
    captured = capsys.readouterr()
    assert "Looking in /tmp/creep-testing/_minecraft/mods" in captured.out
    assert "No mods installed" in captured.out


def test_get_packages_in_dir(sample_mods):
    """Test the get_packages_in_dir method"""
    filenames = sample_mods
    client = CreepClient(appdir=APP_DIR)
    library = client.get_packages_in_dir(os.path.join(TEST_DIR, "_minecraft", "mods"))
    assert library != {}
    assert len(library) == len(filenames)

    # The first one is unknown, the second one is a valid package obj
    assert library[filenames[0]] is None
    assert isinstance(library[filenames[1]], Package)


def test_get_packages_in_dir_display(sample_mods, capsys):
    """Test the get_packages_in_dir method but with display mode enabled"""
    _ = sample_mods
    client = CreepClient(appdir=APP_DIR)
    mods_path = os.path.join(TEST_DIR, "_minecraft", "mods")
    library = client.get_packages_in_dir(mods_path, display_list=True)
    assert library != {}

    captured = capsys.readouterr()
    assert "Installed mods (in" in captured.out
    assert "mezz/jei" in captured.out
    assert "View Items and Recipes" in captured.out
    assert "example.jar" in captured.out


def test_get_packages_in_dir_display_no_unknowns(sample_mods, capsys):
    """Test the get_packages_in_dir method but with display mode enabled,
    exclude unknown packages"""
    _ = sample_mods
    client = CreepClient(appdir=APP_DIR)
    mods_path = os.path.join(TEST_DIR, "_minecraft", "mods")
    library = client.get_packages_in_dir(
        mods_path, display_list=True, include_unknowns=False
    )
    assert library != {}
    captured = capsys.readouterr()
    assert "Installed mods (in" in captured.out
    assert "mezz/jei" in captured.out
    assert "View Items and Recipes" in captured.out
    assert "example.jar" not in captured.out


def test_get_packages_in_dir_display_short_form(sample_mods, capsys):
    """Test the get_packages_in_dir method but with display mode enabled,
    short form flag"""
    _ = sample_mods
    client = CreepClient(appdir=APP_DIR)
    mods_path = os.path.join(TEST_DIR, "_minecraft", "mods")
    library = client.get_packages_in_dir(mods_path, display_list=True, short_form=True)
    assert library != {}
    captured = capsys.readouterr()
    assert "Installed mods (in" not in captured.out
    assert "mezz/jei" in captured.out
    assert "View Items and Recipes" not in captured.out
    assert "example.jar" in captured.out


def test_search_blank(capsys):
    """Test the 'search' command"""
    client = CreepClient(appdir=APP_DIR)
    result = client.do_search("")
    captured = capsys.readouterr()
    assert result == 1
    assert "Missing argument" in captured.out


def test_search(capsys):
    """Test the 'search' command"""
    client = CreepClient(appdir=APP_DIR)
    client.do_search("jei")
    captured = capsys.readouterr()
    assert "mezz/jei" in captured.out


def test_info_missing_arg(capsys):
    """Test the 'info' command"""
    client = CreepClient(appdir=APP_DIR)
    result = client.do_info("")
    captured = capsys.readouterr()
    assert result == 1
    assert "Missing argument" in captured.out


def test_info_unknown_package(capsys):
    """Test the 'info' command"""
    client = CreepClient(appdir=APP_DIR)
    result = client.do_info("fdsarew")
    captured = capsys.readouterr()
    assert result == 1
    assert "Unknown package 'fdsarew'" in captured.out


def test_info(capsys):
    """Test the 'info' command"""
    client = CreepClient(appdir=APP_DIR)
    client.do_info("jei")
    captured = capsys.readouterr()
    assert "mezz/jei" in captured.out
    assert "Version:" in captured.out
    assert "Keywords:" in captured.out
    assert "Dependencies:" in captured.out


def test_install_blank(capsys):
    """Test the 'install' command"""
    client = CreepClient(appdir=APP_DIR)
    result = client.do_install("")
    captured = capsys.readouterr()
    assert result == 1
    assert "Missing argument" in captured.out


def test_install_unknown(capsys):
    """Test the 'install' command"""
    client = CreepClient(appdir=APP_DIR)
    result = client.do_install("barnacle-fdsa")
    captured = capsys.readouterr()
    assert result is None
    assert "Unknown package 'barnacle-fdsa'" in captured.out


def test_install(capsys, mocker):
    """Test the 'install' command"""
    mocker.patch("creepclient.repository.Package.download", return_value=True)

    client = CreepClient(appdir=APP_DIR)
    result = client.do_install("barnacle-fdsa")
    captured = capsys.readouterr()
    assert result is None
    assert "Unknown package 'barnacle-fdsa'" in captured.out


def test_install_no_deps(capsys, mocker):
    """Test the 'install' command"""
    mocker.patch("creepclient.repository.Package.download", return_value=True)

    client = CreepClient(appdir=APP_DIR)
    result = client.do_install("barnacle-fdsa -n")
    captured = capsys.readouterr()
    assert result is None
    assert "skipping dependencies" in captured.out
    assert "Unknown package 'barnacle-fdsa'" in captured.out


def test_install_no_deps_valid_package(capsys, mocker):
    """Test the 'install' command"""

    # Mock out the context manager of the urllib request
    stub_response = mock.MagicMock()
    stub_response.read.return_value = b"ABC"
    stub_context = mock.MagicMock()
    stub_context.__enter__.return_value = stub_response
    mocker.patch(
        "creepclient.entity.package.urllib.request.urlopen", return_value=stub_context
    )

    client = CreepClient(appdir=APP_DIR)
    result = client.do_install("jer-integration -n")
    captured = capsys.readouterr()
    assert result is None
    assert "Performing install and skipping dependencies" in captured.out
    assert "Skipping dependency 'mezz/jei'" in captured.out
    assert (
        "Skipping dependency 'way2muchnoise/just-enough-resources-jer'" in captured.out
    )
    assert "Installed mod 'alasdiablo/jer-integration'" in captured.out


def test_install_collection(capsys, mocker):
    """Test the 'install' command"""

    # Mock out the context manager of the urllib request
    stub_response = mock.MagicMock()
    stub_response.read.return_value = b"ABC"
    stub_context = mock.MagicMock()
    stub_context.__enter__.return_value = stub_response
    mocker.patch(
        "creepclient.entity.package.urllib.request.urlopen", return_value=stub_context
    )

    client = CreepClient(appdir=APP_DIR)
    result = client.do_install("testing-collection")
    captured = capsys.readouterr()
    assert result is None
    assert "Installing package 'sumpygump/testing-collection (1.0.0)'" in captured.out
    assert "Installing dependency 'mezz/jei'" in captured.out
    assert "Installed collection 'sumpygump/testing-collection'" in captured.out


def test_install_collection_no_deps(capsys, mocker):
    """Test the 'install' command"""

    # Mock out the context manager of the urllib request
    stub_response = mock.MagicMock()
    stub_response.read.return_value = b"ABC"
    stub_context = mock.MagicMock()
    stub_context.__enter__.return_value = stub_response
    mocker.patch(
        "creepclient.entity.package.urllib.request.urlopen", return_value=stub_context
    )

    client = CreepClient(appdir=APP_DIR)
    result = client.do_install("testing-collection -n")
    captured = capsys.readouterr()
    assert result is None
    assert "Cannot install collection without dependencies." in captured.out


def test_install_download_fails(capsys, mocker):
    """Test the 'install' command"""

    # Mock the url open will raise exception
    mocker.patch(
        "creepclient.entity.package.urllib.request.urlopen",
        side_effect=urllib.error.URLError("failed"),
    )

    client = CreepClient(appdir=APP_DIR)
    result = client.do_install("jei")
    captured = capsys.readouterr()
    assert result is None
    assert "Download failed." in captured.out


def test_install_from_list_file(capsys, mocker, sample_mod_list):
    """Test the 'install' command"""

    # This file is what the download function would normally do
    cachedir = os.path.join(TEST_DIR, "_creep", "cache", "mods")
    make_file(os.path.join(cachedir, "mezz_jei_1.20.2-forge-16.0.0.28.jar"))
    make_file(os.path.join(cachedir, "alasdiablo_jer-integration_4.3.1.jar"))
    mocker.patch("creepclient.repository.Package.download", return_value=True)

    sample_filename = sample_mod_list

    client = CreepClient(appdir=APP_DIR)
    result = client.do_install(" ".join(("--list", sample_filename)))
    captured = capsys.readouterr()
    assert result is None
    assert "Reading packages from file" in captured.out
    assert "Installing package 'mezz/jei" in captured.out
    assert "Installed mod 'mezz/jei' in" in captured.out
    assert "Installing package 'alasdiablo/jer-integration (4.3.1)'" in captured.out
    assert "Installed mod 'alasdiablo/jer-integration' in" in captured.out


def test_install_from_list_noexist(capsys):
    """Test the 'install' command"""

    client = CreepClient(appdir=APP_DIR)
    result = client.do_install("--list foobar_none.txt")
    captured = capsys.readouterr()
    assert result is None
    assert "File 'foobar_none.txt' not found." in captured.out


def test_install_with_strategy(mocker, capsys):
    """Test the 'install' command with an install strategy"""

    cachedir = os.path.join(TEST_DIR, "_creep", "cache", "mods")
    os.makedirs(cachedir, exist_ok=True)
    shutil.copy(
        "tests/data/archive1.zip",
        os.path.join(cachedir, "sumpygump_testing-strategy_1.0.0.zip"),
    )

    # This file is what the download function would normally do
    cachedir = os.path.join(TEST_DIR, "_creep", "cache", "mods")
    mocker.patch("creepclient.repository.Package.download", return_value=True)

    client = CreepClient(appdir=APP_DIR)
    result = client.do_install("testing-strategy")
    captured = capsys.readouterr()
    assert result is None
    assert "Installing package 'sumpygump/testing-strategy" in captured.out
    assert "Installing with strategy: unzip\n" in captured.out


def test_install_with_strategy_empty(make_tmp_dirs, capsys):
    cachedir, savedir = make_tmp_dirs
    package = mock.MagicMock()
    package.name = "flans_mod"
    package.get_local_filename.return_value = "archive1.zip"

    client = CreepClient(appdir=APP_DIR)
    result = client.install_with_strategy("", package, cachedir, savedir)
    captured = capsys.readouterr()
    assert result is None
    assert captured.out == ""


def test_install_with_strategy_noop(make_tmp_dirs, capsys):
    cachedir, savedir = make_tmp_dirs
    package = mock.MagicMock()
    package.name = "flans_mod"
    package.get_local_filename.return_value = "archive1.zip"

    client = CreepClient(appdir=APP_DIR)
    result = client.install_with_strategy("do;not;anything", package, cachedir, savedir)
    captured = capsys.readouterr()
    assert result is True
    assert captured.out == "Installing with strategy: do;not;anything\n"


def test_install_with_strategy_unzip_only(make_tmp_dirs, capsys):
    cachedir, savedir = make_tmp_dirs
    shutil.copy("tests/data/archive1.zip", os.path.join(cachedir, "archive1.zip"))

    package = mock.MagicMock()
    package.name = "flans_mod"
    package.get_local_filename.return_value = "archive1.zip"

    client = CreepClient(appdir=APP_DIR)
    result = client.install_with_strategy("unzip", package, cachedir, savedir)
    captured = capsys.readouterr()
    assert result is True
    assert captured.out == (
        "Installing with strategy: unzip\n"
        "Unzipping archive: /tmp/creep-testing/cache/archive1.zip\n"
    )


def test_install_with_strategy_unzip_and_move(make_tmp_dirs, capsys):
    # Example with unzip and move, but the savedir already exists
    cachedir, savedir = make_tmp_dirs
    shutil.copy("tests/data/archive1.zip", os.path.join(cachedir, "archive1.zip"))

    package = mock.MagicMock()
    package.name = "flans_mod"
    package.get_local_filename.return_value = "archive1.zip"

    client = CreepClient(appdir=APP_DIR)
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


def test_install_with_strategy_unzip_and_move_new(make_tmp_dirs, capsys):
    # Example with unzip and move, but the savedir doesn't exist
    cachedir, savedir = make_tmp_dirs
    shutil.copy("tests/data/archive1.zip", os.path.join(cachedir, "archive1.zip"))

    package = mock.MagicMock()
    package.name = "flans_mod"
    package.get_local_filename.return_value = "archive1.zip"

    client = CreepClient(appdir=APP_DIR)
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


def test_install_with_strategy_with_star(make_tmp_dirs, capsys):
    # Example with unzip and move using move /*
    cachedir, savedir = make_tmp_dirs
    shutil.copy("tests/data/archive1.zip", os.path.join(cachedir, "archive1.zip"))

    package = mock.MagicMock()
    package.name = "flans_mod"
    package.get_local_filename.return_value = "archive1.zip"

    client = CreepClient(appdir=APP_DIR)
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
