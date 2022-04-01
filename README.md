# GraphQLient
Typed client code generator built on top of [GQL](https://github.com/graphql-python/gql).
All fields are annotated with types, IDE auto-completion and hints should work.

# Setup
1. `poetry install`
2. `poetry run python -m gqlient.generator`
3. Use client generated in *generated/client_code.py*

# Roadmap
- [x] Basic client generation
- [x] Simple queries
- [x] Actually creating and executing queries
- [x] Nested fields
- [ ] Fragments, Unions, Interfaces
- [ ] Mutations
- [ ] Tests
- [ ] Structured jinja templates
- [ ] Well formatted Python code (spaces, blank lines, etc)
- [ ] Client customization
- [ ] Async
- [ ] Subscriptions
- [ ] Minimal dependency client (including required packages etc.)
