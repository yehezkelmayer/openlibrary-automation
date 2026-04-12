"""Pytest configuration - minimal fixtures, browser managed by Singleton."""
import pytest
import yaml
import asyncio
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

AUTH_STATE_PATH = Path(__file__).parent / "auth_state.json"


def load_config():
    config_path = Path(__file__).parent / "config" / "config.yaml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def config():
    return load_config()


@pytest.fixture(scope="session")
def auth_state_path():
    """Path to authentication state file."""
    return AUTH_STATE_PATH
