from pathlib import Path
from typing import List, Optional, Union, cast

import gql
from gql.dsl import DSLSchema
from gql.transport.aiohttp import AIOHTTPTransport
from gql.utilities import build_client_schema
from gqlient.type_utils import (
    Constants, get_graphql_types, get_interface_types, get_type, get_union_types,
    has_default, load_defined_types, my_underscore, returns_many, sort_default_fields
)
from graphql import GraphQLObjectType, Undefined, UndefinedType, build_schema
from graphql.utilities import get_introspection_query, print_schema
from jinja2 import Environment, FileSystemLoader, select_autoescape

env = Environment(loader=FileSystemLoader(Path(__file__).parent / "templates"), autoescape=select_autoescape())

query_template = env.get_template("base.py.jinja2")
pyproject_template = env.get_template("pyproject.toml.jinja2")


def generate_pyproject(client_output: Path, package_name: str, version: Optional[str] = None,
                       description: Optional[str] = None, authors: Optional[List[str]] = None):
    if not authors:
        authors = []
    code = pyproject_template.render(
        authors=authors,
        package_name=package_name.replace('.', '_'),
        include=package_name.split('.')[0],
        version=version,
        description=description
    )

    with open(client_output / 'pyproject.toml', "w+") as f:
        f.write(code)


def generate_client(schema, client_output, build_package=False):
    if isinstance(schema, Path):
        graphql_schema = build_schema(schema.read_text())
    else:
        client = gql.Client(transport=AIOHTTPTransport(url=schema))
        graphql_schema = client.execute(gql.gql(get_introspection_query()))
        graphql_schema = build_client_schema(graphql_schema)
        if build_package:
            (Path(client_output) / 'schema.graphql').write_text(print_schema(graphql_schema))
    schema = DSLSchema(graphql_schema)

    types = set()
    input_types = set()
    enum_types = set()
    union_types = set()
    interface_types = set()

    query = cast(GraphQLObjectType, graphql_schema.type_map["Query"])
    mutation = cast(GraphQLObjectType, graphql_schema.type_map.get("Mutation"))

    load_defined_types(query, types, input_types, enum_types, union_types, interface_types)
    if mutation:
        load_defined_types(mutation, types, input_types, enum_types, union_types, interface_types)

    for t in interface_types:
        # So that interfaces can be cast to unions (collect all their implementations)
        setattr(t, 'types', [type_ for type_ in types if t in type_.interfaces])

    query_fields = dict(sorted(query.fields.items(), key=lambda f: f[0]))  # type: ignore
    for name, field in query_fields.items():
        setattr(field, 'name', get_type(name, strip_class=True, suffix=Constants.query_field))

    mutation_fields = dict(sorted(mutation.fields.items(), key=lambda f: f[0])) if mutation else {}  # type: ignore
    for name, field in mutation_fields.items():
        setattr(field, 'name', get_type(name, strip_class=True, suffix=Constants.mutation_field))

    code = query_template.render(
        api_url=schema if isinstance(schema, str) else None,
        query_fields=query_fields,
        mutation_fields=mutation_fields,
        types=sorted(types, key=lambda t: t.name),
        input_types=sorted(input_types, key=lambda t: t.name),
        enum_types=sorted(enum_types, key=lambda t: t.name),
        union_types=sorted(union_types, key=lambda t: t.name),
        interface_types=sorted(interface_types, key=lambda t: t.name),
        get_type=get_type,
        constants=Constants,
        get_graphql_types=get_graphql_types,
        get_union_types=get_union_types,
        get_interface_types=get_interface_types,
        underscore=my_underscore,
        has_default=has_default,
        sort_default_fields=sort_default_fields,
        returns_many=returns_many
    )

    if client_output:
        with open(client_output / 'client.py', "w+") as f:
            f.write(code)

    return code


def generate(schema: Union[Path, str],
             client_output: Optional[Union[str, Path]] = None,
             package_name: Optional[str] = None,
             version: Optional[str] = None,
             description: Optional[str] = None,
             authors: Optional[List[str]] = None) -> str:
    if isinstance(schema, str):
        if Path(schema).exists():
            schema = Path(schema)
    if isinstance(client_output, str):
        client_output = Path(client_output)
    if client_output and not client_output.exists():
        client_output.mkdir(parents=True, exist_ok=True)
    package_path = ''
    if package_name:
        package_path = package_name.replace('.', '/')
        (client_output / package_path).mkdir(parents=True, exist_ok=True)

    code = generate_client(schema, client_output / package_path if client_output else None, package_name is not None)
    if client_output and package_name:
        generate_pyproject(client_output, package_name, version, description, authors)
        (client_output / package_path / '__init__.py').touch()

    return code
