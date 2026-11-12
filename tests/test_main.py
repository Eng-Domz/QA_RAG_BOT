from pathlib import Path

import pytest

import main


def test_openai_provider_never_silently_falls_back_without_key():
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        main._provider_flags("openai", False)

    assert main._provider_flags("openai", True) == (True, False)
    assert main._provider_flags("ollama", False) == (False, True)


def test_normal_cli_source_is_windows_cp1252_safe():
    source = Path(main.__file__).read_text(encoding="utf-8")

    source.encode("cp1252")


def test_console_output_is_reconfigured_for_utf8(monkeypatch):
    class Stream:
        def __init__(self):
            self.options = None

        def reconfigure(self, **options):
            self.options = options

    stdout = Stream()
    stderr = Stream()
    monkeypatch.setattr(main.sys, "stdout", stdout)
    monkeypatch.setattr(main.sys, "stderr", stderr)

    main._configure_console_output()

    assert stdout.options == {"encoding": "utf-8", "errors": "replace"}
    assert stderr.options == {"encoding": "utf-8", "errors": "replace"}
