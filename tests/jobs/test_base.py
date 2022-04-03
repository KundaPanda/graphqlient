from pathlib import Path

import pytest

from gqlient.generator import generate

BASE_DIR = Path(__file__).parent


@pytest.fixture(scope='session', autouse=True)
def generate_client():
    print("Creating client code")
    generate(BASE_DIR / 'schema.graphql', client_output=BASE_DIR / 'generated/client_code.py')


@pytest.fixture(scope='session')
def client():
    from generated.client_code import Client
    return Client('http://localhost:9002/graphql')
