import statistics
import time
import tbot
import typing
import collections

TimingResults = collections.namedtuple(
    "TimingResults", ["mean", "harmonic_mean", "median", "pvariance", "pstdev"]
)


@tbot.testcase
def time_testcase(
    testcase: typing.Callable, *args: typing.Any, **kwargs: typing.Any
) -> typing.Tuple[float, typing.Any]:
    """
    Time the duration of a testcase.

    :param testcase: Testcase to call.
    :param args,\\ kwargs: Arguments to pass to the testcase.
    :returns: A tuple of the time (in seconds) and the testcase's return value.

    **Example**:

    .. code-block:: python

        from tbot_contrib import timing

        def foo(arg1: str, arg2: int) -> int:
            ...

        duration, ret = timing.time_testcase(foo, "hello", arg2=42)

    .. versionadded:: 0.8.2
    """
    start = time.monotonic()
    result = testcase(*args, **kwargs)
    finish = time.monotonic()
    return (finish - start, result)


@tbot.testcase
def time_testcase_statistics(
    testcase: typing.Callable,
    *args: typing.Any,
    runs: int = 10,
    sleep: float = 0,
    **kwargs: typing.Any,
) -> None:
    """
    Take multiple measurements about the run-time of a testcase and return/display statistics.

    :param testcase: Testcase to call.
    :param args,\\ kwargs: Arguments to pass to the testcase.
    :param int runs: How many samples to take.
    :param float sleep: How much time to sleep in between the runs.  Example
        use:  Maybe the board does not discharge quick enough so it can cause
        troubles when the subsecuent testcase run tries to boot again the board

    .. versionadded:: 0.8.2
    """

    elapsed_times = []

    for n in range(runs):
        elapsed_time, _ = time_testcase(testcase, *args, **kwargs)
        elapsed_times.append(elapsed_time)
        time.sleep(sleep)

    results = TimingResults(
        statistics.mean(elapsed_times),
        statistics.harmonic_mean(elapsed_times),
        statistics.median(elapsed_times),
        statistics.pvariance(elapsed_times),
        statistics.pstdev(elapsed_times),
    )

    tbot.log.message(
        f"""\
    Timing Results:
        {tbot.log.c('mean').green}: {results.mean}
        {tbot.log.c('harmonic mean').green}: {results.harmonic_mean}
        {tbot.log.c('median').green}: {results.median}
        {tbot.log.c('variance').green}: {results.pvariance}
        {tbot.log.c('standard deviation').green}: {results.pstdev}
    """
    )
