from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pytest

import typed_configs as typed_configs


@dataclass
class SubConfigA:
    prop1: tuple[int, float] = (3, 10.0)
    prop2: tuple[str, ...] = ("3", "4", "5")


@dataclass
class SubConfigB:
    prop1: bool = False


@dataclass
class Config:
    sub_config_a: SubConfigA
    sub_config_b: SubConfigB
    prop1: str
    prop2: int = 3
    prop3: float = 1.0
    prop4: Optional[int] = None
    prop5: int | None = None

    @staticmethod
    def some_factory_method(a: int) -> Config:
        return Config(SubConfigA(), SubConfigB(), prop1="a")


def test__no_default_value__not_set__raises_exception() -> None:
    with pytest.raises(TypeError):
        _parse("prop2=4")


def test__str__parses_correctly() -> None:
    config = _parse("prop1=astring")
    assert config.prop1 == "astring"


def test__int__parses_correctly() -> None:
    config = _parse("prop1=h prop2=4")
    assert config.prop2 == 4


def test__float__parses_correctly() -> None:
    config = _parse("prop3=4.2 prop1=g")
    assert config.prop3 == 4.2


def test__multiple_parameters__parses_correctly() -> None:
    config = _parse("prop3=4.2 prop1=g")
    assert config.prop3 == 4.2
    assert config.prop1 == "g"


def test__boolean__parses_correctly() -> None:
    assert _parse("prop1=g sub_config_b.prop1=True").sub_config_b.prop1 is True
    assert _parse("prop1=g sub_config_b.prop1=true").sub_config_b.prop1 is True
    assert _parse("prop1=g sub_config_b.prop1=False").sub_config_b.prop1 is False
    assert _parse("prop1=g sub_config_b.prop1=false").sub_config_b.prop1 is False


def test__optional__not_none__parses_to_value() -> None:
    assert _parse("prop1=h prop4=4").prop4 == 4


def test__optional__none__parses_to_None() -> None:
    assert _parse("prop1=h prop4=none").prop4 is None
    assert _parse("prop1=h prop4=None").prop4 is None


def test__union_bar_type__parses_correctly() -> None:
    # The new "None | int" syntax for unions added in Python 3.10
    assert _parse("prop1=h prop5=None").prop5 is None
    assert _parse("prop1=h prop5=8").prop5 == 8


def test__tuple__fully_specified__parses_correctly() -> None:
    config = _parse("prop1=h sub_config_a.prop1=(4,20.)")
    assert config.sub_config_a.prop1 == (4, 20.0)


def test__tuple__variable_length__parses_correctly() -> None:
    config = _parse("prop1=h sub_config_a.prop2=(a,b,50,three)")
    assert config.sub_config_a.prop2 == ("a", "b", "50", "three")


def test__value_not_valid__raises_exception() -> None:
    with pytest.raises(ValueError):
        _parse("prop1=g prop2=3.2")
    with pytest.raises(ValueError):
        _parse("prop1=g prop3=error")
    with pytest.raises(ValueError):
        _parse("prop1=g prop4=non")
    with pytest.raises(ValueError):
        _parse("prop1=g sub_config_b.prop1=trued")
    with pytest.raises(ValueError):
        _parse("prop1=g sub_config_a.prop1=(1.0,1.0)")
    with pytest.raises(ValueError):
        _parse("prop1=g sub_config_a.prop1=(1.0,1.0)")


def test__non_existent_property__raises_exception() -> None:
    with pytest.raises(KeyError):
        _parse("prop1=2 doesntexist=3")


def test__non_existent_subclass__raises_exception() -> None:
    with pytest.raises(KeyError):
        _parse("prop1=2 doesntexist.a=3")


def _parse(args: str) -> Config:
    return typed_configs.parse(Config, args=["script.py"] + args.split(" "))
