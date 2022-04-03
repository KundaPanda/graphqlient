from pathlib import Path

import pytest

from gqlient.generator import generate

BASE_DIR = Path(__file__).parent


@pytest.fixture(scope='class')
def generate_client():
    generate(BASE_DIR / 'schema.graphql', client_output=BASE_DIR / 'generated/client_code.py')
