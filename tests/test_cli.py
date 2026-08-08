from pathlib import Path

import pytest

from scrapy_lint import main

from . import File, project


def test_empty_folder(capsys):
    with project():
        main([])
    out, err = capsys.readouterr()
    assert not out
    assert not err


def test_issue(capsys):
    with project(File("settings['FOO']", "a.py")), pytest.raises(SystemExit) as excinfo:
        main([])
    out, err = capsys.readouterr()
    assert out == "a.py:1:9: SCP27 unknown setting\n"
    assert not err
    assert excinfo.value.code == 1


def test_target_paths(capsys):
    files = [
        File("settings['FOO']", "a.py"),
        File("settings['BAR']", "b.py"),
    ]
    with project(files), pytest.raises(SystemExit) as excinfo:
        main(["a.py"])
    out, err = capsys.readouterr()
    assert out == "a.py:1:9: SCP27 unknown setting\n"
    assert not err
    assert excinfo.value.code == 1


def test_gitignore(capsys):
    files = [
        File("settings['FOO']", "a.py"),
        File("/a.py", ".gitignore"),
    ]
    with project(files):
        main([])
    out, err = capsys.readouterr()
    assert not out
    assert not err


def test_rule_ignore(capsys):
    with project(File("settings['FOO']", "a.py"), options={"ignore": ["SCP27"]}):
        main([])
    out, err = capsys.readouterr()
    assert not out
    assert not err


def test_file_rule_ignore(capsys):
    file = File("settings['FOO']", "a.py")
    options = {"per-file-ignores": {"a.py": ["SCP27"]}}
    with project(file, options):
        main([])
    out, err = capsys.readouterr()
    assert not out
    assert not err


def test_fixable_marker(capsys):
    file = File('allowed_domains = ["https://toscrape.com/"]\n', "a.py")
    with project(file), pytest.raises(SystemExit) as excinfo:
        main([])
    out, err = capsys.readouterr()
    assert out == (
        "a.py:1:19: SCP02 URL in allowed_domains [*]\n"
        "[*] 1 fixable with the `--fix` option.\n"
    )
    assert not err
    assert excinfo.value.code == 1


def test_fix_option(capsys):
    file = File('allowed_domains = ["https://toscrape.com/"]\n', "a.py")
    with project(file) as directory:
        main(["--fix"])
        assert (
            Path(directory) / "a.py"
        ).read_text() == 'allowed_domains = ["toscrape.com"]\n'
    out, err = capsys.readouterr()
    assert out == "Fixed 1 error(s).\n"
    assert not err


def test_fix_option_with_remaining(capsys):
    files = [
        File('allowed_domains = ["https://toscrape.com/"]\n', "a.py"),
        File("settings['FOO']\n", "b.py"),
    ]
    with project(files), pytest.raises(SystemExit) as excinfo:
        main(["--fix"])
    out, err = capsys.readouterr()
    assert out == ("b.py:1:9: SCP27 unknown setting\nFixed 1 error(s).\n")
    assert not err
    assert excinfo.value.code == 1


def test_fix_option_nothing_to_fix(capsys):
    with (
        project(File("settings['FOO']\n", "a.py")),
        pytest.raises(SystemExit) as excinfo,
    ):
        main(["--fix"])
    out, err = capsys.readouterr()
    assert out == "a.py:1:9: SCP27 unknown setting\n"
    assert not err
    assert excinfo.value.code == 1


def test_color(capsys, monkeypatch):
    monkeypatch.setenv("FORCE_COLOR", "1")
    file = File('allowed_domains = ["https://toscrape.com/"]\n', "a.py")
    with project(file), pytest.raises(SystemExit):
        main([])
    out, _ = capsys.readouterr()
    assert out == (
        "\033[1ma.py:1:19\033[0m: \033[31mSCP02\033[0m URL in allowed_domains"
        " \033[36m[*]\033[0m\n"
        "\033[36m[*]\033[0m 1 fixable with the `--fix` option.\n"
    )


def test_no_color(capsys, monkeypatch):
    monkeypatch.setenv("FORCE_COLOR", "1")
    monkeypatch.setenv("NO_COLOR", "1")
    with project(File("settings['FOO']", "a.py")), pytest.raises(SystemExit):
        main([])
    out, _ = capsys.readouterr()
    assert out == "a.py:1:9: SCP27 unknown setting\n"


def test_syntax_error(capsys):
    with project(File(")", "a.py")), pytest.raises(SystemExit) as excinfo:
        main([])
    out, err = capsys.readouterr()
    assert not out
    assert err == "a.py: Error: unmatched ')' (a.py, line 1)\n"
    assert excinfo.value.code == 2


def test_unicode_error(capsys):
    with project(File(b"\xff", "a.py")), pytest.raises(SystemExit) as excinfo:
        main([])
    out, err = capsys.readouterr()
    assert not out
    assert err == (
        "a.py: Error: 'utf-8' codec can't decode byte 0xff in position 0: "
        "invalid start byte\n"
    )
    assert excinfo.value.code == 2


def test_invalid_pyproject(capsys):
    with project(File("…", "pyproject.toml")), pytest.raises(SystemExit) as excinfo:
        main([])
    out, err = capsys.readouterr()
    assert not out
    assert err == ("pyproject.toml: Error: Invalid statement (at line 1, column 1)\n")
    assert excinfo.value.code == 2


def test_invalid_pyproject_encoding(capsys):
    with project(File(b"\xff", "pyproject.toml")), pytest.raises(SystemExit) as excinfo:
        main([])
    out, err = capsys.readouterr()
    assert not out
    assert err == (
        "pyproject.toml: Error: 'utf-8' codec can't decode byte 0xff "
        "in position 0: invalid start byte\n"
    )
    assert excinfo.value.code == 2
