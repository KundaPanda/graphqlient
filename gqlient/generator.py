from pathlib import Path
from typing import Any, List, Optional, Union, cast

import gql
from gql.dsl import DSLSchema
from gql.transport.aiohttp import AIOHTTPTransport
from gql.utilities import build_client_schema
from graphql import (
    GraphQLSchema,
    IntrospectionQuery,
    build_schema,
)
from graphql.utilities import get_introspection_query, print_schema
from jinja2 import Environment, FileSystemLoader, Template, select_autoescape

from gqlient.type_utils import (
    Constants,
    get_graphql_types,
    get_interface_types,
    get_type,
    get_union_types,
    has_default,
    load_types,
    my_underscore,
    returns_many,
    sort_default_fields,
)

env = Environment(
    loader=FileSystemLoader(Path(__file__).parent / "templates"),
    autoescape=select_autoescape(),
)

client_template = env.get_template("client.py.jinja2")
result_template = env.get_template("result_types.py.jinja2")
query_template = env.get_template("query.py.jinja2")
mutation_template = env.get_template("mutation.py.jinja2")
enum_types_template = env.get_template("enum_types.py.jinja2")
input_types_template = env.get_template("input_types.py.jinja2")
queryable_types_template = env.get_template("queryable_types.py.jinja2")
object_types_template = env.get_template("all_types.py.jinja2")
common_template = env.get_template("common.py.jinja2")
pyproject_template = env.get_template("pyproject.toml.jinja2")


def generate_pyproject(
    client_output: Path,
    package_name: str,
    version: Optional[str] = None,
    description: Optional[str] = None,
    authors: Optional[List[str]] = None,
):
    if not authors:
        authors = []
    code = pyproject_template.render(
        authors=authors,
        package_name=package_name.replace(".", "_"),
        include=package_name.split(".")[0],
        version=version,
        description=description,
    )

    with open(client_output / "pyproject.toml", "w+") as f:
        f.write(code)


def _render_file(template: Template, output: Path, **kwargs):
    res = template.render(**kwargs)
    with output.open("w+") as f:
        f.write(res)
    return res


def _load_schema(schema: str | Path) -> tuple[GraphQLSchema, DSLSchema]:
    if isinstance(schema, Path):
        graphql_schema = build_schema(schema.read_text())
    else:
        client = gql.Client(transport=AIOHTTPTransport(url=schema))
        graphql_schema = client.execute(gql.gql(get_introspection_query()))
        graphql_schema = build_client_schema(cast(IntrospectionQuery, graphql_schema))
    return graphql_schema, DSLSchema(graphql_schema)


def _prepare_template_kwargs() -> dict[str, Any]:
    return dict(
        get_type=get_type,
        constants=Constants,
        get_graphql_types=get_graphql_types,
        get_union_types=get_union_types,
        geterscore=my_underscore,
        has_default=has_default,
        get_interface_types=get_interface_types,
        sort_default_fields=sort_default_fields,
        returns_many=returns_many,
        underscore=my_underscore,
    )


def generate_client(schema, client_output, build_package=False) -> dict[Template, str]:
    graphql_schema, dsl_schema = _load_schema(schema)
    if isinstance(schema, Path) and build_package:
        (Path(client_output) / "schema.graphql").write_text(
            print_schema(graphql_schema)
        )

    gql_types = load_types(graphql_schema)

    outputs = [
        (client_template, client_output / "client.py"),
        (result_template, client_output / "result_types.py"),
        (common_template, client_output / "common.py"),
        (queryable_types_template, client_output / "queryable_types.py"),
        (enum_types_template, client_output / "enum_types.py"),
        (input_types_template, client_output / "input_types.py"),
        (mutation_template, client_output / "mutation.py"),
        (query_template, client_output / "query.py"),
        (object_types_template, client_output / "object_types.py"),
    ]

    print("Generating client files...")

    kwargs = dict(
        **_prepare_template_kwargs(),
        api_url=dsl_schema if isinstance(dsl_schema, str) else None,
        gql_types=gql_types,
    )

    return {
        template: _render_file(template, output, **kwargs)
        for template, output in outputs
    }


def _prepare_paths(
    schema: str | Path, client_output: str | Path | None, package_name: str | None
) -> tuple[str, Path | None]:
    if isinstance(schema, str):
        if Path(schema).exists():
            schema = Path(schema)
    if isinstance(client_output, str):
        client_output = Path(client_output)
    if client_output and not client_output.exists():
        client_output.mkdir(parents=True, exist_ok=True)
    package_path = ""
    if package_name:
        package_path = package_name.replace(".", "/")
        if client_output:
            (client_output / package_path).mkdir(parents=True, exist_ok=True)
    return package_path, client_output


def generate(
    schema: Union[Path, str],
    client_output: Optional[Union[str, Path]] = None,
    package_name: Optional[str] = None,
    version: Optional[str] = None,
    description: Optional[str] = None,
    authors: Optional[List[str]] = None,
) -> dict[Template, str]:
    package_path, output_path = _prepare_paths(schema, client_output, package_name)

    code = generate_client(
        schema,
        output_path / package_path if output_path else None,
        package_name is not None,
    )
    if output_path and package_name:
        generate_pyproject(output_path, package_name, version, description, authors)
        (output_path / output_path / "__init__.py").touch()

    return code
