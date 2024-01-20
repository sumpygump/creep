"""Tests for creepclient repository module"""

import json
import os
import pytest
import shutil
from unittest import mock
import urllib.error

# import creepclient.creepclient
from creepclient.repository import Repository

# from creepclient.entity.package import Package

TEST_DIR = "/tmp/creep-testing"


@pytest.fixture(autouse=True)
def make_tmp_dirs():
    """Make some tmp dirs for use during testing"""
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)

    os.makedirs(TEST_DIR, exist_ok=True)


def test_repository():
    repo = Repository(TEST_DIR)
    assert repo.local_registry_location == os.path.join(TEST_DIR, "packages.json")


def test_set_minecraft_target():
    repo = Repository(TEST_DIR)
    repo.set_minecraft_target("1.20.2")
    assert repo.minecraft_target == "1.20.2"


def test_download_repository(mocker):
    """Download the repository, but mocked so it returns bin data"""

    package_registry = b""
    with open(os.path.join("tests", "data", "packages.json"), "rb") as fd:
        package_registry = fd.read()
    # Mock out the context manager of the urllib request
    stub_response = mock.MagicMock()
    stub_response.read.return_value = package_registry
    stub_context = mock.MagicMock()
    stub_context.__enter__.return_value = stub_response
    mocker.patch(
        "creepclient.repository.urllib.request.urlopen", return_value=stub_context
    )

    repo = Repository(TEST_DIR)
    result = repo.download_remote_repository()
    assert result is True


def test_download_repository_fails(mocker):
    """Test download repository, but the download fails"""

    # Mock the url open will raise exception
    mocker.patch(
        "creepclient.repository.urllib.request.urlopen",
        side_effect=urllib.error.URLError("failed"),
    )
    repo = Repository(TEST_DIR)
    result = repo.download_remote_repository()
    assert result is False


def test_load_repository(mocker):
    """Test load_repository, local file doesn't exist, so it downloads file"""

    package_registry = b""
    with open(os.path.join("tests", "data", "packages.json"), "rb") as fd:
        package_registry = fd.read()
    # Mock out the context manager of the urllib request
    stub_response = mock.MagicMock()
    stub_response.read.return_value = package_registry
    stub_context = mock.MagicMock()
    stub_context.__enter__.return_value = stub_response
    mocker.patch(
        "creepclient.repository.urllib.request.urlopen", return_value=stub_context
    )

    repo = Repository(TEST_DIR)
    result = repo.load_repository()
    assert list(result.keys()) == ["repository_version", "date", "packages"]


def test_load_repository_cannot_download(mocker, capsys):
    """Test load_repository, but it cannot download the file"""

    # Mock the url open will raise exception
    mocker.patch(
        "creepclient.repository.urllib.request.urlopen",
        side_effect=urllib.error.URLError("failed"),
    )
    repo = Repository(TEST_DIR)
    result = repo.load_repository()
    captured = capsys.readouterr()
    assert "Package definition file not found" in captured.out
    assert result == {"packages": {}}


def test_load_repository_cache_expired(mocker, capsys):
    """Test load_repository, local file exists but is old"""

    # Add sample packages file
    target_package_loc = os.path.join(TEST_DIR, "packages.json")
    shutil.copy(os.path.join("tests", "data", "packages.json"), target_package_loc)
    # Make it have an old file time
    os.utime(target_package_loc, (1705001000, 1705001000))

    package_registry = b""
    with open(os.path.join("tests", "data", "packages.json"), "rb") as fd:
        package_registry = fd.read()
    # Mock out the context manager of the urllib request
    stub_response = mock.MagicMock()
    stub_response.read.return_value = package_registry
    stub_context = mock.MagicMock()
    stub_context.__enter__.return_value = stub_response
    mocker.patch(
        "creepclient.repository.urllib.request.urlopen", return_value=stub_context
    )

    repo = Repository(TEST_DIR)
    result = repo.load_repository()
    captured = capsys.readouterr()
    assert "Refreshing registry" in captured.out
    assert list(result.keys()) == ["repository_version", "date", "packages"]


def test_load_repository_file_old_and_cannot_download(mocker, capsys):
    """Test load_repository, the file is old, but it cannot download new one"""

    # Add sample packages file
    target_package_loc = os.path.join(TEST_DIR, "packages.json")
    shutil.copy(os.path.join("tests", "data", "packages.json"), target_package_loc)
    # Make it have an old file time
    os.utime(target_package_loc, (1705001000, 1705001000))

    # Mock the url open will raise exception
    mocker.patch(
        "creepclient.repository.urllib.request.urlopen",
        side_effect=urllib.error.URLError("failed"),
    )
    repo = Repository(TEST_DIR)
    result = repo.load_repository()
    captured = capsys.readouterr()
    assert "Using current version of repository" in captured.out
    assert list(result.keys()) == ["repository_version", "date", "packages"]
    assert result.get("repository_version") == "e397849ee30ec3a306b29a9629394a5b"


def test_clear_cache():
    """Test clear_cache"""

    # Add sample packages file
    target_package_loc = os.path.join(TEST_DIR, "packages.json")
    shutil.copy(os.path.join("tests", "data", "packages.json"), target_package_loc)

    repo = Repository(TEST_DIR)
    result = repo.clear_cache()
    assert result is True


def test_clear_cache_nofile():
    """Test clear_cache"""

    repo = Repository(TEST_DIR)
    result = repo.clear_cache()
    assert result is False


def test_populate():
    """Test populate"""

    # Add sample packages file
    target_package_loc = os.path.join(TEST_DIR, "packages.json")
    shutil.copy(os.path.join("tests", "data", "packages.json"), target_package_loc)

    repo = Repository(TEST_DIR)
    assert 0 == len(repo.packages)
    result = repo.populate()
    assert result is True
    assert 5 == len(repo.packages)
    assert repo.version_hash == "e397849ee30ec3a306b29a9629394a5b"
    assert repo.version_date == "2023-12-29 17:52:10"
    assert "mezz/jei" == repo.unique_packages[0].name


def test_populate_custom_location():
    """Test populate"""

    # Add sample packages file
    target_package_loc = os.path.join(TEST_DIR, "custom_packages.json")
    shutil.copy(os.path.join("tests", "data", "packages.json"), target_package_loc)

    repo = Repository(TEST_DIR)
    repo.minecraft_target = "1.20.2"
    assert 0 == len(repo.packages)
    result = repo.populate(target_package_loc)
    assert result is True
    assert 5 == len(repo.packages)
    assert repo.version_hash == "e397849ee30ec3a306b29a9629394a5b"
    assert repo.version_date == "2023-12-29 17:52:10"
    assert "alasdiablo/jer-integration" == repo.unique_packages[0].name
    expected = [
        "jei",
        "jer-integration",
        "testing-collection",
        "testing-strategy",
    ]
    assert expected == sorted(list(repo.simple_name_packages.keys()))


def test_populate_no_post_process():
    # Add sample packages file
    target_package_loc = os.path.join(TEST_DIR, "packages.json")
    shutil.copy(os.path.join("tests", "data", "packages.json"), target_package_loc)

    repo = Repository(TEST_DIR)
    assert 0 == len(repo.packages)
    result = repo.populate(should_post_process=False)
    assert result is True
    assert 5 == repo.count_packages()
    assert repo.version_hash == "e397849ee30ec3a306b29a9629394a5b"
    assert repo.version_date == "2023-12-29 17:52:10"
    assert 0 == len(repo.unique_packages)


def test_normalize_version():
    repo = Repository(TEST_DIR)
    assert ["1", "0", "2"] == repo.normalize_version("1.0.2")
    assert ["01", "00", "02"] == repo.normalize_version("01.00.02")
    assert ["1", "2"] == repo.normalize_version("1.2")
    assert ["1", "2"] == repo.normalize_version("1.2.0")
    assert ["1", "2"] == repo.normalize_version("1.2.0.0")
    assert ["1", "03a", "2b"] == repo.normalize_version("1.03a.2b")
    assert ["seven", "3", "1"] == repo.normalize_version("seven.3.1")


def test_fetch_package():
    """Test fetch_package"""

    # Add sample packages file
    target_package_loc = os.path.join(TEST_DIR, "packages.json")
    shutil.copy(os.path.join("tests", "data", "packages.json"), target_package_loc)

    repo = Repository(TEST_DIR)
    repo.minecraft_target = "1.20.2"
    repo.populate()
    repo.simple_name_packages["jer-integration"].append("another/jer-integration")

    assert repo.fetch_package("") is False

    package = repo.fetch_package("mezz/jei")
    assert package.name == "mezz/jei"

    package = repo.fetch_package("mezz/jei:1.20.2-forge-16.0.0.28")
    assert package.name == "mezz/jei"

    package = repo.fetch_package("jei")
    assert package.name == "mezz/jei"

    # This one has two
    package = repo.fetch_package("jer-integration")
    assert package is False

    package = repo.fetch_package("foobarman")
    assert package is False


def test_fetch_package_byfilename():
    """Test fetch_package_byfilename"""

    # Add sample packages file
    target_package_loc = os.path.join(TEST_DIR, "packages.json")
    shutil.copy(os.path.join("tests", "data", "packages.json"), target_package_loc)

    repo = Repository(TEST_DIR)
    repo.minecraft_target = "1.20.2"
    repo.populate()

    package = repo.fetch_package_byfilename("jei-1.20.2-forge-16.0.0.28.jar")
    assert package.name == "mezz/jei"

    package = repo.fetch_package_byfilename("hooha-1.5.6.jar")
    assert package is False


def test_search():
    """Test search"""

    # Add sample packages file
    target_package_loc = os.path.join(TEST_DIR, "packages.json")
    shutil.copy(os.path.join("tests", "data", "packages.json"), target_package_loc)

    repo = Repository(TEST_DIR)
    repo.minecraft_target = "1.20.2"
    repo.populate()

    packages = repo.search("integration")
    assert [p.name for p in packages] == ["alasdiablo/jer-integration"]

    packages = repo.search("items")
    assert [p.name for p in packages] == ["mezz/jei"]

    packages = repo.search("map-and-information")
    assert [p.name for p in packages] == ["alasdiablo/jer-integration", "mezz/jei"]

    packages = repo.search("integrat")
    assert [p.name for p in packages] == ["alasdiablo/jer-integration"]

    packages = repo.search("collection example")
    assert [p.name for p in packages] == ["sumpygump/testing-collection"]
