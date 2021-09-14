import sys
import typing

import attr
import sqlparse
from pygments import highlight
from pygments.formatters import TerminalFormatter
from pygments.lexers import PostgresLexer, Python3Lexer, SqlLexer

from .timedelta import TimeDelta

from .stacktrace import StackTrace, StacktraceLine


@attr.s(auto_attribs=True, repr=False)
class Query:
    code: str
    db: str
    duration: TimeDelta
    idx: int
    is_select: bool
    location: str
    params: str
    raw_params: typing.Tuple
    sql: str
    sql_parameterized: str
    stacktrace: StackTrace
    start_time: int
    stop_time: int
    db_type: str
    """Executed query."""

    def __repr__(self) -> str:
        truncated_sql = repr(self.sql)[:30].strip("'")
        return (
            f"Query("
            f"idx={self.idx}, "
            f"code='{self.code}', "
            f"duration={repr(self.duration)}, "
            f"location='{self.location}', "
            f"sql='{truncated_sql}...')"
        )

    def __str__(self) -> str:
        return self.display_string()

    @classmethod
    def create(
        cls,
        db: str,
        duration: TimeDelta,
        idx: int,
        is_select: bool,
        params: str,
        raw_params: typing.Tuple,
        sql: str,
        sql_parameterized: str,
        stacktrace: StackTrace,
        start_time: int,
        stop_time: int,
        db_type: str,
    ) -> "Query":
        last_executed_line: StacktraceLine = (
            stacktrace[-1] if stacktrace else StacktraceLine.null()
        )

        return cls(
            code=last_executed_line.code,
            db=db,
            duration=duration,
            idx=idx,
            is_select=is_select,
            location=last_executed_line.location(),
            params=params,
            raw_params=raw_params,
            sql=sql,
            sql_parameterized=sql_parameterized,
            stacktrace=stacktrace,
            start_time=start_time,
            stop_time=stop_time,
            db_type=db_type,
        )

    def display(
        self,
        *,
        code: bool = True,
        duration: bool = True,
        idx: bool = False,
        location: bool = True,
        stacktrace: bool = False,
        sql=True,
        colored=True,
        formatted=True,
    ):
        sys.stdout.write(
            self.display_string(
                code=code,
                duration=duration,
                idx=idx,
                location=location,
                sql=sql,
                stacktrace=stacktrace,
                colored=colored,
                formatted=formatted,
            )
            + "\n"
        )

    def display_string(
        self,
        *,
        code: bool = True,
        duration: bool = True,
        idx: bool = False,
        location: bool = True,
        stacktrace: bool = False,
        sql=True,
        colored=True,
        formatted=True,
    ) -> str:
        attributes = []

        if idx:
            attributes.append(f"index: {self.idx}")

        if duration:
            attributes.append(self.duration.humanize())

        if location:
            attributes.append(self.location)

        if code:
            attributes.append(
                highlight(f"{self.code}", Python3Lexer(), TerminalFormatter())
                if (colored and formatted)
                else self.code
            )

        if stacktrace:
            attributes.append(str(self.stacktrace))

        if sql:
            attributes.append(
                self._enhanced_sql(colored=colored, formatted=formatted)
                if colored
                else self.sql
            )

        attributes = [c.strip() for c in attributes]
        return "\n\n".join(attributes).rstrip()

    def _enhanced_sql(self, *, formatted: bool, colored: bool) -> str:
        lexer = SqlLexer()

        # TODO: Handle other db_types?
        if self.db_type.lower() == "postgresql":
            lexer = PostgresLexer()

        sql = self.sql

        if formatted:
            sql = sqlparse.format(self.sql, reindent=True)

        if colored:
            sql = highlight(f"{sql}", lexer, TerminalFormatter())

        return sql
