# GraphQLient
Typed GraphQL client code generator built on top of [GQL](https://github.com/graphql-python/gql).

Tries to make python-written queries easier instead of relying on the user to remember all the correct and required types.

All fields are annotated with types, IDE auto-completion and hints should work.

# Dev setup
1. `poetry install`
2. `poetry run python -m tests.generate`
3. Use client generated in *tests/\*/generated/client.py*
4. For mocked JOBS api - `docker run -d --rm -p 127.0.0.1:9002:9002 -v "$(pwd)/tests/graphql-faker:/mock" apisguru/graphql-faker /mock/schema.graphql`

# Building client package

1. `poetry install`
2. `poetry run python -m gqlient.cli --help` for further instructions

# Roadmap
- [x] Basic client generation
- [x] Simple queries
- [x] Actually creating and executing queries
- [x] Nested fields
- [x] Fragments, Unions, Interfaces
- [x] Class renaming
- [x] Mutations
- [x] Hinting for return types
- [x] Class-like access for returned data
- [x] Hinting for returned union/interface types
- [ ] Aliases
- [ ] Better hinting for returned union/interface types (resolve field type clashes with aliases etc.)
- [ ] Separate client code to multiple modules
- [ ] Add docstrings from graphql schema documentation
- [ ] Eliminate duplicated code
- [ ] Eliminate duplicated templates
- [ ] Conditional imports
- [ ] Tests
- [ ] Documentation
- [ ] Structured jinja templates
- [ ] Well formatted Python code (spaces, blank lines, etc)
- [ ] Client customization
- [ ] Async
- [ ] Subscriptions
- [ ] Minimal dependency client (including required packages etc.)
