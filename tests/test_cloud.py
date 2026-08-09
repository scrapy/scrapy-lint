from __future__ import annotations

import sys
from pathlib import Path

import pytest
from ruamel.yaml import CommentedMap
from scrapinghub.client.exceptions import Unauthorized

from scrapy_lint import main
from scrapy_lint.cloud import _api_keys, _client
from scrapy_lint.errors import CloudError

from . import File, project

CONFIG = """\
projects:
  default: 123
"""


class FakeSettings:
    def __init__(self, settings):
        self._settings = settings

    def list(self):
        return list(self._settings.items())


class FakeProject:
    def __init__(self, settings):
        self.settings = FakeSettings(settings)


class FakeProjects:
    def __init__(self, project_ids):
        self._project_ids = project_ids

    def list(self):
        return list(self._project_ids)


class FakeClient:
    def __init__(self, project_ids=(123,), settings=None):
        self.projects = FakeProjects(project_ids)
        self.settings = settings or {}
        self.requested: list[int] = []
        self.built: list[str] = []

    def get_project(self, project_id):
        self.requested.append(project_id)
        return FakeProject(self.settings)


@pytest.fixture
def client(monkeypatch, tmp_path):
    """A single fake client standing in for every group of the run."""
    for variable in ("SHUB_APIKEY", "SH_APIKEY"):
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.setenv("SHUB_APIKEY", "key")
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    fake = FakeClient()

    def build(api_key):
        fake.built.append(api_key)
        return fake

    monkeypatch.setattr("scrapy_lint.cloud._client", build)
    return fake


def run(files=None, options=None):
    with project(files, options), pytest.raises(SystemExit) as excinfo:
        main(["cloud"])
    return excinfo.value.code


def test_no_config(capsys, client):
    with project():
        main(["cloud"])
    out, err = capsys.readouterr()
    assert not out
    assert not err
    assert not client.requested


def test_no_projects(capsys, client):
    with project(File("stack: scrapy:2.13-20250101\n", "scrapinghub.yml")):
        main(["cloud"])
    out, err = capsys.readouterr()
    assert not out
    assert not err
    assert not client.requested


def test_non_mapping_config(capsys, client):
    with project(File("- a\n", "scrapinghub.yml")):
        main(["cloud"])
    out, _ = capsys.readouterr()
    assert not out
    assert not client.requested


def test_invalid_yaml(capsys):
    with (
        project(File("projects: [\n", "scrapinghub.yml")),
        pytest.raises(SystemExit) as excinfo,
    ):
        main(["cloud"])
    out, err = capsys.readouterr()
    assert not out
    assert err.startswith("scrapinghub.yml: Error: ")
    assert excinfo.value.code == 2


def test_reachable_project(capsys, client):
    with project(File(CONFIG, "scrapinghub.yml")):
        main(["cloud"])
    out, err = capsys.readouterr()
    assert not out
    assert not err
    assert client.requested == [123]
    assert client.built == ["key"]


def test_unreachable_project(capsys, client):
    client.projects = FakeProjects([456])
    assert run(File(CONFIG, "scrapinghub.yml")) == 1
    out, err = capsys.readouterr()
    assert out == "scrapinghub.yml:2:11: SCP47 unreachable project: default: 123\n"
    assert not err
    assert not client.requested


@pytest.mark.parametrize(
    ("config", "expected_ids"),
    [
        ("projects:\n  default: 123\n", [123]),
        ("projects:\n  default: '123'\n", [123]),
        ("projects:\n  default: default/123\n", [123]),
        ("projects:\n  default:\n    id: 123\n", [123]),
        ("projects:\n  default:\n    id: 123\n    endpoint: default\n", [123]),
        # An API key that no configuration file defines cannot be used.
        ("projects:\n  default:\n    id: 123\n    apikey: other\n", []),
        # Unusable values.
        ("projects:\n  default: true\n", []),
        ("projects:\n  default: nope\n", []),
        ("projects:\n  default: []\n", []),
        ("projects:\n  default:\n    stack: scrapy:2.13\n", []),
        ("projects: 123\n", []),
    ],
    ids=range(11),
)
def test_project_ids(client, config, expected_ids):
    with project(File(config, "scrapinghub.yml")):
        main(["cloud"])
    assert client.requested == expected_ids


def test_remote_settings(capsys, client):
    client.settings = {"job_settings": {"CONCURRENT_REQUEST": 1, "DOWNLOAD_DELAY": 1}}
    assert run(File(CONFIG, "scrapinghub.yml")) == 1
    out, err = capsys.readouterr()
    assert out == (
        "scrapinghub.yml:2:11: SCP27 unknown setting: CONCURRENT_REQUEST "
        "(did you mean: CONCURRENT_REQUESTS, CONCURRENT_REQUESTS_PER_IP, "
        "CONCURRENT_ITEMS?)\n"
    )
    assert not err


def test_remote_setting_without_detail(capsys, client):
    client.settings = {"job_settings": {"ZYTE_API_DEFAULT_PARAMS": {}}}
    assert run(File(CONFIG, "scrapinghub.yml")) == 1
    out, _ = capsys.readouterr()
    assert out == (
        "scrapinghub.yml:2:11: SCP46 raw Zyte API params: ZYTE_API_DEFAULT_PARAMS\n"
    )


@pytest.mark.parametrize("job_settings", [None, "", []], ids=range(3))
def test_no_remote_job_settings(capsys, client, job_settings):
    client.settings = {"job_settings": job_settings, "default_job_units": 2}
    with project(File(CONFIG, "scrapinghub.yml")):
        main(["cloud"])
    out, _ = capsys.readouterr()
    assert not out


def test_ignored_rule(capsys, client):
    client.projects = FakeProjects([456])
    files = File(CONFIG, "scrapinghub.yml")
    with project(files, options={"ignore": ["SCP47"]}):
        main(["cloud"])
    out, _ = capsys.readouterr()
    assert not out


def test_per_file_ignored_rule(capsys, client):
    client.projects = FakeProjects([456])
    files = File(CONFIG, "scrapinghub.yml")
    options = {"per-file-ignores": {"scrapinghub.yml": ["SCP47"]}}
    with project(files, options):
        main(["cloud"])
    out, _ = capsys.readouterr()
    assert not out


@pytest.mark.parametrize(
    ("config", "endpoint"),
    [
        ("projects:\n  staging: onprem/123\n", "onprem"),
        ("projects:\n  staging:\n    id: 123\n    endpoint: onprem\n", "onprem"),
    ],
    ids=range(2),
)
def test_non_default_project_endpoint(capsys, client, config, endpoint):
    assert run(File(config, "scrapinghub.yml")) == 2
    _, err = capsys.readouterr()
    assert err == (
        f"Error: project staging uses the {endpoint} endpoint, and only "
        "https://app.zyte.com/api/ is supported\n"
    )
    assert not client.built


def test_non_default_endpoints_default(capsys, client):
    config = "endpoints:\n  default: https://staging.example.com/api/\n"
    assert run(File(f"{config}{CONFIG}", "scrapinghub.yml")) == 2
    _, err = capsys.readouterr()
    assert err == (
        "Error: the default endpoint is set to https://staging.example.com/api/, "
        "and only https://app.zyte.com/api/ is supported\n"
    )
    assert not client.built


def test_non_default_endpoints_default_in_global_config(capsys, client, tmp_path):
    (tmp_path / ".scrapinghub.yml").write_text(
        "endpoints:\n  default: https://staging.example.com/api/\n",
    )
    assert run(File(CONFIG, "scrapinghub.yml")) == 2
    _, err = capsys.readouterr()
    assert err.startswith("Error: the default endpoint is set to")


@pytest.mark.parametrize(
    "endpoints",
    [
        "endpoints:\n  default: https://app.zyte.com/api/\n",
        "endpoints:\n  default: https://app.zyte.com/api\n",
        "endpoints:\n  onprem: https://onprem.example.com/api/\n",
        "endpoints: nope\n",
    ],
    ids=range(4),
)
def test_accepted_endpoints(client, endpoints):
    with project(File(f"{endpoints}{CONFIG}", "scrapinghub.yml")):
        main(["cloud"])
    assert client.built == ["key"]


def test_alternative_apikey(client):
    config = "apikeys:\n  other: other-key\nprojects:\n  prod:\n    id: 123\n"
    config += "    apikey: other\n"
    with project(File(config, "scrapinghub.yml")):
        main(["cloud"])
    assert client.built == ["other-key"]


def test_one_client_per_apikey(capsys, client):
    config = "apikeys:\n  other: other-key\nprojects:\n  a: 123\n  b: 123\n"
    config += "  c:\n    id: 123\n    apikey: other\n"
    with project(File(config, "scrapinghub.yml")):
        main(["cloud"])
    assert sorted(client.built) == ["key", "other-key"]
    assert client.requested == [123, 123, 123]


def test_apikey_from_global_config(client, tmp_path):
    (tmp_path / ".scrapinghub.yml").write_text("apikeys:\n  other: other-key\n")
    config = "projects:\n  prod:\n    id: 123\n    apikey: other\n"
    with project(File(config, "scrapinghub.yml")):
        main(["cloud"])
    assert client.built == ["other-key"]


def test_project_config_overrides_global_config(client, tmp_path):
    (tmp_path / ".scrapinghub.yml").write_text("apikeys:\n  other: old-key\n")
    config = "apikeys:\n  other: new-key\nprojects:\n  prod:\n    id: 123\n"
    config += "    apikey: other\n"
    with project(File(config, "scrapinghub.yml")):
        main(["cloud"])
    assert client.built == ["new-key"]


@pytest.mark.parametrize(
    "config",
    ["apikeys: nope\n", "apikeys:\n  other: 1\n", "apikeys:\n  1: other-key\n"],
    ids=range(3),
)
def test_unusable_apikey_mappings(client, config):
    config += "projects:\n  prod:\n    id: 123\n    apikey: other\n"
    with project(File(config, "scrapinghub.yml")):
        main(["cloud"])
    assert not client.built


def test_no_api_key(capsys, client, monkeypatch):
    monkeypatch.delenv("SHUB_APIKEY")
    assert run(File(CONFIG, "scrapinghub.yml")) == 2
    _, err = capsys.readouterr()
    assert err.startswith("Error: no Scrapy Cloud API key found")


def test_api_error(capsys, client, monkeypatch):
    def fail():
        raise Unauthorized("bad key")

    monkeypatch.setattr(client.projects, "list", fail)
    assert run(File(CONFIG, "scrapinghub.yml")) == 2
    out, err = capsys.readouterr()
    assert not out
    assert err == "Error: Scrapy Cloud API request failed: bad key\n"


def test_network_error(capsys, client, monkeypatch):
    def fail():
        raise OSError("no route to host")

    monkeypatch.setattr(client.projects, "list", fail)
    assert run(File(CONFIG, "scrapinghub.yml")) == 2
    _, err = capsys.readouterr()
    assert err == "Error: Scrapy Cloud API request failed: no route to host\n"


@pytest.fixture
def home(monkeypatch, tmp_path):
    for variable in ("SHUB_APIKEY", "SH_APIKEY"):
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    return tmp_path


@pytest.mark.parametrize("variable", ["SHUB_APIKEY", "SH_APIKEY"], ids=range(2))
def test_api_key_from_env(home, monkeypatch, variable):
    monkeypatch.setenv(variable, "key")
    assert _api_keys(CommentedMap()) == {"default": "key"}


def test_api_key_from_global_config(home):
    (home / ".scrapinghub.yml").write_text("apikeys:\n  default: key\n")
    assert _api_keys(CommentedMap()) == {"default": "key"}


@pytest.mark.parametrize(
    "text",
    [
        None,
        "apikeys: [\n",
        "- a\n",
        "apikeys: nope\n",
        "apikeys: {}\n",
        "apikeys:\n  default: 1\n",
    ],
    ids=range(6),
)
def test_no_api_keys(home, text):
    if text is not None:
        (home / ".scrapinghub.yml").write_text(text)
    assert not _api_keys(CommentedMap())


def test_client():
    built = _client("key")
    assert built._connection.url == "https://app.zyte.com/api/"
    assert built._hsclient.endpoint == "https://storage.scrapinghub.com/"


def test_client_without_scrapinghub(monkeypatch):
    monkeypatch.setitem(sys.modules, "scrapinghub", None)
    with pytest.raises(CloudError, match="requires python-scrapinghub"):
        _client("key")
