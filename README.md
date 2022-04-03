# GraphQLient
Typed client code generator built on top of [GQL](https://github.com/graphql-python/gql).
All fields are annotated with types, IDE auto-completion and hints should work.

# Setup
1. `poetry install`
2. `poetry run python -m gqlient.generator`
3. Use client generated in *generated/client_code.py*
4. `docker run -p 127.0.0.1:9002:9002 apisguru/graphql-faker`

# Roadmap
- [x] Basic client generation
- [x] Simple queries
- [x] Actually creating and executing queries
- [x] Nested fields
- [x] Fragments, Unions, Interfaces
- [ ] Class renaming
- [ ] Conditional imports
- [ ] Mutations
- [ ] Tests
- [ ] Structured jinja templates
- [ ] Well formatted Python code (spaces, blank lines, etc)
- [ ] Client customization
- [ ] Async
- [ ] Subscriptions
- [ ] Minimal dependency client (including required packages etc.)
