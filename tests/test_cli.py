"""The namespace must forward arguments unchanged to existing research CLIs."""
import pytest

from aethon import __main__ as cli


@pytest.mark.parametrize("command,module", cli.COMMANDS.items())
def test_dispatch_preserves_arguments_and_restores_argv(monkeypatch, command, module):
    original = ["aethon", command, "--help"]
    monkeypatch.setattr(cli.sys, "argv", original)
    observed = []
    def run(name, run_name):
        observed.append((name, run_name, list(cli.sys.argv)))
    monkeypatch.setattr(cli.runpy, "run_module", run)
    cli.main()
    assert observed == [(module, "__main__", [module, "--help"])]
    assert cli.sys.argv is original
