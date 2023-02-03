import builtins
import enum
import functools
import inspect
import itertools
import typing
from keyword import iskeyword
from typing import Any, Dict, Set, TypedDict, cast

from graphql import (
    GraphQLEnumType,
    GraphQLField,
    GraphQLFieldMap,
    GraphQLInputField,
    GraphQLInputObjectType,
    GraphQLInterfaceType,
    GraphQLList,
    GraphQLNamedType,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLOutputType,
    GraphQLScalarType,
    GraphQLSchema,
    GraphQLType,
    GraphQLUnionType,
    Undefined,
    is_enum_type,
    is_input_object_type,
    is_interface_type,
    is_list_type,
    is_non_null_type,
    is_object_type,
    is_scalar_type,
    is_union_type,
)
from inflection import camelize, underscore

BUILTIN_NAMES = [k for k, v in inspect.getmembers(builtins)]


class Constants(enum.Enum):
    empty = ""
    selection = "Selection"
    selection_type = "SelectionType"
    root_selection = "RootSelection"
    field = "Field"
    mutation_field = "MutationField"
    query_field = "QueryField"
    output = "Output"
    field_output = "FieldOutput"

    def __str__(self) -> str:
        return self.value


def my_underscore(s: str) -> str:
    value = underscore(s)
    if value in BUILTIN_NAMES or iskeyword(value):
        value += "_"
    while value.startswith("_"):
        value = f"{value[1:]}_"
    return value


def my_camelize(value: str) -> str:
    while value.startswith("_"):
        value = f"{value[1:]}_"
    return camelize(value)


def get_graphql_types(type_: GraphQLType) -> list[GraphQLType]:
    if is_list_type(type_):
        return get_graphql_types(cast(GraphQLList, type_).of_type)
    elif is_non_null_type(type_):
        return get_graphql_types(cast(GraphQLNonNull, type_).of_type)
    elif is_scalar_type(type_):
        return []
    return [type_]


def _process_object_type(type_, suffix: Constants, replace_underscores: bool) -> str:
    type_name = type_ if isinstance(type_, str) else type_.name
    camelize_fn = my_camelize if replace_underscores else camelize
    return (
        f'{camelize_fn(f"{type_name}{split_[0]}")}[{split_[1]}'
        if isinstance(suffix, str) and len((split_ := suffix.split("[", 2))) > 1
        else camelize_fn(f"{type_name}{suffix}")
    )


def _process_scalar_type(type_) -> str:
    val = inspect.signature(type_.serialize).return_annotation
    return val.__name__ if hasattr(val, "__name__") else val._name


@functools.lru_cache(maxsize=None)
def get_type(
    type_,
    suffix=Constants.empty,
    enquote=False,
    strip_class=True,
    replace_underscores=True,
    level=0,
):
    if is_non_null_type(type_):
        return get_type(
            type_.of_type, suffix, enquote, strip_class, replace_underscores, level + 1
        )
    if is_list_type(type_):
        val = get_type(
            type_.of_type, suffix, enquote, strip_class, replace_underscores, level + 1
        )
        if not strip_class:
            val = f"List[{val}]"
    elif is_scalar_type(type_):
        val = _process_scalar_type(type_)
    else:
        val = _process_object_type(type_, suffix, replace_underscores)
        if enquote:
            val = f"'{val}'"
    return f"Optional[{val}]" if (level == 0 and not strip_class) else val


def load_defined_types(
    object_type: GraphQLObjectType | GraphQLInterfaceType | GraphQLInputObjectType,
    types: Set[GraphQLObjectType],
    input_types: Set[GraphQLInputObjectType],
    enum_types: Set[GraphQLEnumType],
    union_types: Set[GraphQLUnionType],
    interface_types: Set[GraphQLInterfaceType],
):
    field: GraphQLField
    for field in object_type.fields.values():
        types_ = get_graphql_types(field.type)
        if isinstance(field, GraphQLField):
            types_.extend(
                itertools.chain(
                    *[get_graphql_types(a.type) for a in field.args.values()]
                )
            )
        for actual_type in types_:
            if isinstance(actual_type, GraphQLUnionType):
                if actual_type not in union_types:
                    union_types.add(actual_type)
                    for subtype in actual_type.types:
                        load_defined_types(
                            subtype,
                            types,
                            input_types,
                            enum_types,
                            union_types,
                            interface_types,
                        )
            elif isinstance(actual_type, GraphQLInterfaceType):
                if actual_type not in interface_types:
                    interface_types.add(actual_type)
                    load_defined_types(
                        actual_type,
                        types,
                        input_types,
                        enum_types,
                        union_types,
                        interface_types,
                    )
            elif isinstance(actual_type, GraphQLObjectType):
                if actual_type not in types:
                    types.add(actual_type)
                    load_defined_types(
                        actual_type,
                        types,
                        input_types,
                        enum_types,
                        union_types,
                        interface_types,
                    )
            elif isinstance(actual_type, GraphQLInputObjectType):
                if actual_type not in input_types:
                    input_types.add(actual_type)
                    load_defined_types(
                        actual_type,
                        types,
                        input_types,
                        enum_types,
                        union_types,
                        interface_types,
                    )
            elif isinstance(actual_type, GraphQLEnumType):
                if actual_type not in enum_types:
                    enum_types.add(actual_type)


def get_union_types(
    type_: typing.Union[GraphQLUnionType, GraphQLNonNull, GraphQLList],
    suffix=Constants.empty,
):
    if isinstance(type_, (GraphQLNonNull, GraphQLList)):
        return get_union_types(type_.of_type, suffix)
    return (
        "Union["
        + ", ".join(
            f"Type[{get_type(sub_type, strip_class=True, suffix=suffix)}]"
            for sub_type in type_.types
        )
        + "]"
    )


def get_interface_types(type_: GraphQLInterfaceType):
    return get_union_types(cast(GraphQLUnionType, type_))


def has_default(field: GraphQLInputField) -> bool:
    return field.default_value != Undefined


def sort_default_fields(fields: Dict[str, GraphQLInputField]):
    return dict(sorted(fields.items(), key=lambda x: has_default(x[1])))


def returns_many(field: GraphQLField):
    ft = type(field.type)
    return isinstance(GraphQLList, ft) or (
        isinstance(GraphQLNonNull, ft)
        and isinstance(GraphQLList, cast(GraphQLNonNull, ft).of_type)
    )


class Types(TypedDict):
    query_fields: GraphQLFieldMap
    mutation_fields: GraphQLFieldMap
    types: list[GraphQLObjectType]
    input_types: list[GraphQLInputObjectType]
    enum_types: list[GraphQLEnumType]
    union_types: list[GraphQLUnionType]
    union_type_names: list[str]
    interface_types: list[GraphQLInterfaceType]


def load_types(graphql_schema: GraphQLSchema) -> Types:
    types = set()
    input_types = set()
    enum_types = set()
    union_types = set()
    interface_types = set()

    query = cast(GraphQLObjectType, graphql_schema.type_map["Query"])
    mutation = cast(GraphQLObjectType, graphql_schema.type_map.get("Mutation"))

    load_defined_types(
        query, types, input_types, enum_types, union_types, interface_types
    )
    if mutation:
        load_defined_types(
            mutation, types, input_types, enum_types, union_types, interface_types
        )

    for t in interface_types:
        # So that interfaces can be cast to unions (collect all their implementations)
        setattr(t, "types", [type_ for type_ in types if t in type_.interfaces])
        all_fields = dict(
            itertools.chain(
                *map(
                    dict.items,
                    [type_.fields for type_ in types if t in type_.interfaces],
                )
            )
        )
        setattr(t, "all_fields", all_fields)

    for t in union_types:
        all_fields = dict(
            itertools.chain(*map(dict.items, [type_.fields for type_ in t.types]))
        )
        setattr(t, "all_fields", all_fields)

    query_fields = dict(sorted(query.fields.items(), key=lambda f: f[0]))  # type: ignore
    for name, field in query_fields.items():
        setattr(
            field,
            "name",
            get_type(name, strip_class=True, suffix=Constants.query_field),
        )

    mutation_fields = dict(sorted(mutation.fields.items(), key=lambda f: f[0])) if mutation else {}  # type: ignore
    for name, field in mutation_fields.items():
        setattr(
            field,
            "name",
            get_type(name, strip_class=True, suffix=Constants.mutation_field),
        )

    interface_types = sorted(interface_types, key=lambda t: t.name)
    union_types = sorted(union_types, key=lambda t: t.name)
    enum_types = sorted(enum_types, key=lambda t: t.name)
    return Types(
        query_fields=query_fields,
        mutation_fields=mutation_fields,
        types=sorted(types, key=lambda t: t.name),
        input_types=sorted(input_types, key=lambda t: t.name),
        enum_types=enum_types,
        union_types=union_types,
        union_type_names=[get_type(t.name, strip_class=True) for t in union_types],
        interface_types=interface_types,
    )
