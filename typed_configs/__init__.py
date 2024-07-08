import sys
from dataclasses import Field, fields, is_dataclass
from types import NoneType
from typing import (
    Any,
    Iterator,
    Literal,
    TypeVar,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)


class ArgumentParseError(Exception):
    def __init__(self, value: str, t: Any) -> None:
        self.value = value
        self.t = t


class UnknownTypeError(Exception):
    def __init__(self, t: Any) -> None:
        self.t = t


UnparsedArgs = list[tuple[str, str]]
C = TypeVar("C")


def parse(config: type[C], args: list[str] = sys.argv) -> C:
    parsed_args = list(_split_keys_values(args[1:]))
    return _parse(config, parsed_args)


def _split_keys_values(args: list[str]) -> Iterator[tuple[str, str]]:
    for arg in args:
        split = arg.split("=")
        if len(split) == 1:
            raise ValueError(f"Argument '{arg}' does not contain '='")
        key = split[0].strip()
        value = "".join(split[1:]).strip()
        yield key, value


def _parse(config: type[C], args: UnparsedArgs) -> C:
    if not is_dataclass(config):
        raise ValueError
    field_types = get_type_hints(config)
    expected_fields = {f.name: field_types[f.name] for f in fields(config)}

    parsed_args: dict[str, Any] = {}

    for sub_config_name, sub_config in _get_expected_sub_configs(expected_fields):
        sub_config_args = _find_args_for_sub_config(sub_config_name, args)
        parsed_args[sub_config_name] = _parse(sub_config, sub_config_args)

    this_config_args = [(k, v) for k, v in args if "." not in k]
    for k, v in this_config_args:
        try:
            parsed_args[k] = _parse_value(expected_fields[k], v)
        except ArgumentParseError as e:
            raise ValueError(f"Could not parse argument '{k}={v}' as '{e.t}'")
        except UnknownTypeError as e:
            raise ValueError(f"Argument '{config}.{k}' has unknown type '{e.t}'")

    return config(**parsed_args)  # type: ignore


def _get_expected_sub_configs(
    expected_fields: dict[str, Any]
) -> Iterator[tuple[str, Any]]:
    for field_name, field_type in expected_fields.items():
        if is_dataclass(field_type):
            yield field_name, field_type


def _find_args_for_sub_config(name: str, args: UnparsedArgs) -> UnparsedArgs:
    prefix = f"{name}."
    return [(k.removeprefix(prefix), v) for k, v in args if k.startswith(prefix)]


V = TypeVar("V")


def _parse_value(expected_type: Any, v: str) -> Any:
    if expected_type in (str, int, float):
        return _parse_to_type(expected_type, v)

    if expected_type == bool:
        if v in ("true", "True"):
            return True
        elif v in ("false", "False"):
            return False
        else:
            raise ArgumentParseError(v, expected_type)

    if get_origin(expected_type) == Union:
        return _parse_union(expected_type, v)

    if get_origin(expected_type) == tuple:
        return _parse_tuple(expected_type, v)

    if get_origin(expected_type) == Literal:
        sub_types = get_args(expected_type)
        if v in sub_types:
            return v
        else:
            raise ArgumentParseError(v, expected_type)

    if expected_type == NoneType:
        if v in ("none", "None"):
            return None

    if expected_type == list:
        raise ValueError("Lists are not supported because they are mutable. Use tuple.")

    raise UnknownTypeError(expected_type)


def _parse_union(expected_type: Any, v: str) -> Any:
    # Union includes both actual Unions and Optionals.
    sub_types = list(get_args(expected_type))

    # We try None first, so the strings "none" and "None" are None not strings.
    if NoneType in sub_types:
        sub_types.remove(NoneType)
        sub_types.insert(0, NoneType)

    for sub_type in sub_types:
        try:
            return _parse_value(sub_type, v)
        except UnknownTypeError:
            pass

    raise UnknownTypeError(expected_type)


def _parse_tuple(expected_type: Any, v: str) -> Any:
    items = v.removeprefix("(").removesuffix(")").split(",")
    items = [item.strip() for item in items if item.strip() != ""]
    sub_types = get_args(expected_type)
    if len(sub_types) == 2 and sub_types[-1] == Ellipsis:
        item_types = tuple(sub_types[0] for _ in items)
    elif len(sub_types) == len(items):
        item_types = sub_types
    else:
        raise ArgumentParseError(v, expected_type)
    return tuple(_parse_value(t, item) for t, item in zip(item_types, items))


def _parse_to_type(t: type[V], v: str) -> V:
    try:
        return t(v)  # type: ignore
    except ValueError:
        raise ArgumentParseError(v, t)
