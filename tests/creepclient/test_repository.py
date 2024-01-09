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
    # Mock the url open will raise exception
    mocker.patch(
        "creepclient.repository.urllib.request.urlopen",
        side_effect=urllib.error.URLError("failed"),
    )
    repo = Repository(TEST_DIR)
    result = repo.download_remote_repository()
    assert result is False
