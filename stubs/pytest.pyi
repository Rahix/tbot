from typing import (
    Any,
    Callable,
    ContextManager,
    Generator,
    Iterable,
    NoReturn,
    Optional,
    Pattern,
    Tuple,
    Type,
    TypeVar,
    Union,
    overload,
)

def skip(msg: str = "", *, allow_module_level: bool = False) -> NoReturn: ...

# _Scope = Literal["session", "package", "module", "class", "function"]
_Scope = str
# The value of the fixture -- return/yield of the fixture function (type variable).
_FixtureValue = TypeVar("_FixtureValue")
# The type of the fixture function (type variable).
_FixtureFunction = TypeVar("_FixtureFunction", bound=Callable[..., object])
# The type of a fixture function (type alias generic in fixture value).
_FixtureFunc = Union[
    Callable[..., _FixtureValue], Callable[..., Generator[_FixtureValue, None, None]]
]

class FixtureFunctionMarker:
    def __call__(self, function: _FixtureFunction) -> _FixtureFunction: ...

@overload
def fixture(
    fixture_function: _FixtureFunction,
    *,
    scope: "Union[_Scope, Callable[[str, Any], _Scope]]" = ...,
    params: Optional[Iterable[object]] = ...,
    autouse: bool = ...,
    ids: Optional[
        Union[
            Iterable[Union[None, str, float, int, bool]],
            Callable[[Any], Optional[object]],
        ]
    ] = ...,
    name: Optional[str] = ...,
) -> _FixtureFunction: ...
@overload
def fixture(
    fixture_function: None = ...,
    *,
    scope: "Union[_Scope, Callable[[str, Any], _Scope]]" = ...,
    params: Optional[Iterable[object]] = ...,
    autouse: bool = ...,
    ids: Optional[
        Union[
            Iterable[Union[None, str, float, int, bool]],
            Callable[[Any], Optional[object]],
        ]
    ] = ...,
    name: Optional[str] = None,
) -> FixtureFunctionMarker: ...

_E = TypeVar("_E", bound=BaseException)
@overload
def raises(
    expected_exception: Union[Type[_E], Tuple[Type[_E], ...]],
    *,
    match: Optional[Union[str, Pattern[str]]] = ...,
) -> ContextManager: ...
@overload
def raises(
    expected_exception: Union[Type[_E], Tuple[Type[_E], ...]],
    func: Callable[..., Any],
    *args: Any,
    **kwargs: Any,
) -> ContextManager: ...
