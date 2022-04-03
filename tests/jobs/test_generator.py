import ast

from gqlient.generator import generate
from tests.jobs.test_base import BASE_DIR


class TestGenerator:
    def test_client_generation_valid(self):
        code = generate(BASE_DIR / 'schema.graphql')
        assert ast.parse(code)
