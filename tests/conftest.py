"""Shared test helpers.

The desks are scripts, not a package — their filenames carry hyphens, so they
cannot be imported by name. Load each one from its path instead, which is also
how the agent invokes them, and keeps the desks free of packaging ceremony.
"""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def load_desk(filename: str):
    """Import a desk script by path, e.g. load_desk("weather-desk.py")."""
    path = SCRIPTS / filename
    name = filename.replace("-", "_").removesuffix(".py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def weather_desk():
    return load_desk("weather-desk.py")


@pytest.fixture(scope="session")
def paper_sections() -> set[str]:
    """The only section ids a desk is allowed to use (AGENTS.md, hard rules)."""
    paper = json.loads((REPO / "editions" / "paper.json").read_text())
    return {s["id"] for s in paper["sections"]}


@pytest.fixture(scope="session")
def open_meteo() -> dict:
    return json.loads((FIXTURES / "open-meteo.json").read_text())




def frontmatter(article: str) -> dict:
    """Parse the leading `---` block. Deliberately small: the desks emit flat
    `key: value` pairs plus one nested `chart:` block, which we skip."""
    assert article.startswith("---\n"), "article must open with frontmatter"
    _, block, _ = article.split("---\n", 2)
    out, in_nested = {}, False
    for line in block.splitlines():
        if not line.strip():
            continue
        if line.startswith((" ", "\t", "-")):
            continue                      # inside chart:/sources:
        key, _, value = line.partition(":")
        in_nested = not value.strip()
        if not in_nested:
            out[key.strip()] = value.strip()
        else:
            out[key.strip()] = None
    return out
