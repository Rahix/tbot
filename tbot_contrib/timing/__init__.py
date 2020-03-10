import statistics
import time
import tbot
import typing
import collections


@tbot.testcase
def time_testcase(
    testcase: typing.Callable, *args: typing.Any, **kwargs: typing.Any
) -> tuple:
    """Return the time that the given testcase took
    you can pass any arguments that the testcase needs"""
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
    """receive a testcase and prints descriptive statics
    you can pass as an argument:
    runs = the number of times that the testcase is to be repeated
    sleep = the time in seconds that the bucle must wait

    example use of sleep: maybe the board does not discharge quick enough
    so it can cause troubles when the subsecuent testcase tries to boot again the board

    you can pass any arguments that the testcase needs """

    elapsed_times = []

    for n in range(runs):

        elapsed_time, _ = time_testcase(testcase, *args, **kwargs)
        elapsed_times.append(elapsed_time)
        time.sleep(sleep)

    TimingResults = collections.namedtuple(
        "TimingResults", ["mean", "harmonic_mean", "median", "pvariance", "pstdev"]
    )
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
