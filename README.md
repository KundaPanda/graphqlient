# GraphQLient
Typed client code generator built on top of [GQL](https://github.com/graphql-python/gql).
All fields are annotated with types, IDE auto-completion and hints should work.

# Dev setup
1. `poetry install`
2. `poetry run python -m tests.generate`
3. Use client generated in *tests/\*/generated/client.py*
4. For mocked JOBS api - `docker run -d --rm -p 127.0.0.1:9002:9002 -v "$(pwd)/tests/graphql-faker:/mock" apisguru/graphql-faker /mock/schema.graphql`

# Building client package

1. `poetry install`
2. `poetry run python -m gqlient.cli --help` for help

# Roadmap
- [x] Basic client generation
- [x] Simple queries
- [x] Actually creating and executing queries
- [x] Nested fields
- [x] Fragments, Unions, Interfaces
- [x] Class renaming
- [x] Mutations
- [ ] Conditional imports
- [ ] Tests
- [ ] Structured jinja templates
- [ ] Well formatted Python code (spaces, blank lines, etc)
- [ ] Client customization
- [ ] Async
- [ ] Subscriptions
- [ ] Minimal dependency client (including required packages etc.)
