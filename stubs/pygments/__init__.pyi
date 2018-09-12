from . import formatters
from . import lexers

def highlight(code: str, lexer: lexers.Lexer, formatter: formatters.Formatter) -> str: ...
