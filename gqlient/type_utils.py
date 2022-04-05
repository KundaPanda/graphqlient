import builtins
import enum
import functools
import inspect
import itertools
import typing
from keyword import iskeyword
from typing import Any, Dict, Set, cast

from graphql import (
    GraphQLEnumType, GraphQLField,
    GraphQLInputField, GraphQLInputObjectType, GraphQLInterfaceType, GraphQLList, GraphQLNonNull, GraphQLObjectType,
    GraphQLUnionType,
    Undefined, is_enum_type, is_input_object_type, is_interface_type, is_list_type,
    is_non_null_type,
    is_object_type,
    is_scalar_type,
    is_union_type,
)
from inflection import camelize, underscore

BUILTIN_NAMES = [k for k, v in inspect.getmembers(builtins)]


class Constants(enum.Enum):
    empty = ''
    selection = 'Selection'
    selection_type = 'SelectionType'
    root_selection = 'RootSelection'
    field = 'Field'
    mutation_field = 'MutationField'
    query_field = 'QueryField'
    output = 'Output'
    field_output = 'FieldOutput'

    def __str__(self):
        return self.value


def my_underscore(s):
    value = underscore(s)
    if value in BUILTIN_NAMES or iskeyword(value):
        value += "_"
    while value.startswith('_'):
        value = value[1:] + "_"
    return value


def my_camelize(value):
    while value.startswith('_'):
        value = value[1:] + '_'
    return camelize(value)


def get_graphql_types(type_):
    if is_list_type(type_):
        return get_graphql_types(type_.of_type)
    elif is_non_null_type(type_):
        return get_graphql_types(type_.of_type)
    elif is_scalar_type(type_):
        return []
    return [type_]


@functools.lru_cache(maxsize=None)
def get_type(type_, suffix=Constants.empty, enquote=False, strip_class=True, replace_underscores=True, level=0):
    if is_non_null_type(type_):
        return get_type(type_.of_type, suffix, enquote, strip_class, replace_underscores, level + 1)
    if is_list_type(type_):
        val = get_type(type_.of_type, suffix, enquote, strip_class, replace_underscores, level + 1)
        if not strip_class:
            val = f"List[{val}]"
    elif is_scalar_type(type_):
        val = inspect.signature(type_.serialize).return_annotation
        if val != Any:
            val = val.__name__
        else:
            val = val._name
    else:
        type_name = type_ if isinstance(type_, str) else type_.name
        camelize_fn = my_camelize if replace_underscores else camelize
        if isinstance(suffix, str) and len((split_ := suffix.split('[', 2))) > 1:
            val = camelize_fn(f"{type_name}{split_[0]}") + '[' + split_[1]
        else:
            val = camelize_fn(f"{type_name}{suffix}")
        if enquote:
            val = f"'{val}'"
    return f'Optional[{val}]' if (level == 0 and not strip_class) else val


def load_defined_types(object_type: GraphQLObjectType, types: Set[GraphQLObjectType],
                       input_types: Set[GraphQLInputObjectType],
                       enum_types: Set[GraphQLEnumType], union_types: Set[GraphQLUnionType],
                       interface_types: Set[GraphQLInterfaceType]):
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
                        load_defined_types(subtype, types, input_types, enum_types, union_types, interface_types)
            elif is_interface_type(actual_type):
                if actual_type not in interface_types:
                    interface_types.add(actual_type)
                    load_defined_types(actual_type, types, input_types, enum_types, union_types, interface_types)
            elif is_object_type(actual_type):
                if actual_type not in types:
                    types.add(actual_type)
                    load_defined_types(actual_type, types, input_types, enum_types, union_types, interface_types)
            elif is_input_object_type(actual_type):
                if actual_type not in input_types:
                    input_types.add(actual_type)
                    load_defined_types(actual_type, types, input_types, enum_types, union_types, interface_types)
            elif is_enum_type(actual_type):
                if actual_type not in enum_types:
                    enum_types.add(actual_type)


def get_union_types(type_: typing.Union[GraphQLUnionType, GraphQLNonNull, GraphQLList], suffix=Constants.empty):
    if isinstance(type_, (GraphQLNonNull, GraphQLList)):
        return get_union_types(type_.of_type, suffix)
    return 'Union[' + ', '.join('Type[' + get_type(sub_type, strip_class=True, suffix=suffix) + ']' for sub_type in type_.types) + ']'


def get_interface_types(type_: GraphQLInterfaceType):
    return get_union_types(cast(GraphQLUnionType, type_))


def has_default(field: GraphQLInputField):
    return field.default_value != Undefined


def sort_default_fields(fields: Dict[str, GraphQLInputField]):
    return dict(sorted(fields.items(), key=lambda x: has_default(x[1])))


def returns_many(field: GraphQLField):
    return is_list_type(field.type) or (is_non_null_type(field.type) and is_list_type(field.type.of_type))
