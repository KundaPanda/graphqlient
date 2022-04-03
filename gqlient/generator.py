import builtins
import enum
import inspect
import itertools
from keyword import iskeyword
from pathlib import Path
from typing import Any, Optional, Set, Union, cast

import gql
from gql.dsl import DSLSchema
from gql.transport.aiohttp import AIOHTTPTransport
from gql.utilities import build_client_schema
from graphql import (
    GraphQLEnumType, GraphQLField,
    GraphQLInputObjectType, GraphQLObjectType,
    GraphQLUnionType,
    build_schema,
    is_enum_type, is_input_object_type, is_list_type,
    is_non_null_type,
    is_object_type,
    is_scalar_type,
    is_union_type,
)
from graphql.utilities import get_introspection_query, print_schema
from inflection import camelize, underscore
from jinja2 import Environment, FileSystemLoader, select_autoescape


class Constants(enum.Enum):
    empty = ''
    selection = 'Selection'
    root_selection = 'RootSelection'
    field = 'Field'
    queryable_field = 'QueryableField'

    def __str__(self):
        return self.value


def get_graphql_types(type_):
    if is_list_type(type_):
        return get_graphql_types(type_.of_type)
    elif is_non_null_type(type_):
        return get_graphql_types(type_.of_type)
    elif is_scalar_type(type_):
        return []
    return [type_]


def get_type(type_, suffix=Constants.empty, enquote=False, strip_class=False, level=0):
    if is_non_null_type(type_):
        return get_type(type_.of_type, suffix, enquote, strip_class, level + 1)
    if is_list_type(type_):
        val = get_type(type_.of_type, suffix, enquote, strip_class, level + 1)
        if not strip_class:
            val = f"List[{val}]"
    elif is_union_type(type_):
        val = type_.name + str(suffix)
        if enquote:
            val = f"'{val}'"
    elif is_scalar_type(type_):
        val = inspect.signature(type_.serialize).return_annotation
        if val != Any:
            val = val.__name__
        else:
            val = val._name
    else:
        val = f"{type_.name}{suffix}"
        if enquote:
            val = f"'{val}'"
    return f'Optional[{val}]' if (level == 0 and not strip_class) else val


def load_defined_types(object_type: GraphQLObjectType, types: Set[GraphQLObjectType],
                       input_types: Set[GraphQLInputObjectType],
                       enum_types: Set[GraphQLEnumType], union_types: Set[GraphQLUnionType]):
    field: GraphQLField
    for field in object_type.fields.values():
        types_ = get_graphql_types(field.type)
        if isinstance(field, GraphQLField):
            types_.extend(itertools.chain(*[get_graphql_types(a.type) for a in field.args.values()]))
        for actual_type in types_:
            if is_union_type(actual_type):
                if actual_type not in union_types:
                    union_types.add(actual_type)
                    for subtype in actual_type.types:
                        load_defined_types(subtype, types, input_types, enum_types, union_types)
            elif is_object_type(actual_type):
                if actual_type not in types:
                    types.add(actual_type)
                    load_defined_types(actual_type, types, input_types, enum_types, union_types)
            elif is_input_object_type(actual_type):
                if actual_type not in input_types:
                    input_types.add(actual_type)
                    load_defined_types(actual_type, types, input_types, enum_types, union_types)
            elif is_enum_type(actual_type):
                if actual_type not in enum_types:
                    enum_types.add(actual_type)


env = Environment(loader=FileSystemLoader(Path(__file__).parent / "templates"), autoescape=select_autoescape())

query_template = env.get_template("query.py.jinja2")

BUILTIN_NAMES = [k for k, v in inspect.getmembers(builtins)]


def my_underscore(s):
    value = underscore(s)
    if value in BUILTIN_NAMES or iskeyword(value):
        value += "_"
    elif value.startswith('_'):
        value = value[1:] + "_"
    return value


def my_camelize(value):
    if value.startswith('_'):
        return '_' + camelize(value[1:])
    return camelize(value)


def get_union_types(type_: GraphQLUnionType):
    return 'Union[' + ', '.join('Type[' + get_type(sub_type, strip_class=True) + ']' for sub_type in type_.types) + ']'


def generate(schema: Union[Path, str],
             client_output: Optional[Union[str, Path]] = None,
             write_schema: Optional[Union[str, Path]] = None) -> str:
    if isinstance(schema, str):
        if Path(schema).exists():
            schema = Path(schema)
    if isinstance(schema, Path):
        graphql_schema = build_schema(schema.read_text())
    else:
        client = gql.Client(transport=AIOHTTPTransport(url=schema))
        graphql_schema = client.execute(gql.gql(get_introspection_query()))
        graphql_schema = build_client_schema(graphql_schema)
        if write_schema:
            Path(write_schema).write_text(print_schema(graphql_schema))
    schema = DSLSchema(graphql_schema)

    types = set()
    input_types = set()
    enum_types = set()
    union_types = set()
    query = cast(GraphQLObjectType, graphql_schema.type_map["Query"])
    load_defined_types(query, types, input_types, enum_types, union_types)
    fields = [
        {
            "name": name,
            "type": f.type,
            "args": f.args,
        }
        for name, f in query.fields.items()
    ]

    code = query_template.render(
        api_url=schema if isinstance(schema, str) else None,
        fields=sorted(fields, key=lambda f: f["name"]),
        types=sorted(types, key=lambda t: t.name),
        input_types=sorted(input_types, key=lambda t: t.name),
        enum_types=sorted(enum_types, key=lambda t: t.name),
        union_types=sorted(union_types, key=lambda t: t.name),
        get_type=get_type,
        constants=Constants,
        get_graphql_types=get_graphql_types,
        get_union_types=get_union_types,
        camelize=my_camelize,
        underscore=my_underscore,
        builtins=BUILTIN_NAMES,
    )

    if client_output:
        with open(client_output, "w+") as f:
            f.write(code)

    return code
