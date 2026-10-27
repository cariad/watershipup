"""Tests for running tasks at the same time."""

from collections.abc import Callable
from functools import partial
from signal import ITIMER_REAL, SIGALRM, setitimer, signal
from threading import Barrier, Lock
from time import sleep
from types import FrameType

from pytest import raises

from watershipup.concurrency import run_all


def test_run_all() -> None:
    """`run_all` must run every task."""
    ran: list[int] = []

    tasks = [lambda n=n: ran.append(n) for n in range(10)]

    run_all(tasks, 4)

    found = sorted(ran)
    expect = list(range(10))

    assert found == expect


def test_run_all_limits_concurrency() -> None:
    """`run_all` must never run more tasks at once than it's allowed."""
    lock = Lock()
    running = 0
    most = 0

    # Each task waits for two others, so the limit must be reached for any to pass.
    barrier = Barrier(
        3,
        timeout=10,
    )

    def task() -> None:
        nonlocal running, most

        with lock:
            running += 1
            most = max(most, running)

        barrier.wait()

        with lock:
            running -= 1

    run_all([task] * 6, 3)

    expect = 3

    assert most == expect


def test_run_all_raises_first_error() -> None:
    """`run_all` must raise the first error that a task raised."""

    def fail() -> None:
        raise ValueError("made-up")

    with raises(ValueError, match="made-up"):
        run_all([fail], 2)


def test_run_all_runs_tasks_at_once() -> None:
    """`run_all` must run tasks at the same time when it's allowed to."""
    # Each task waits for the other, so they pass only if they run at once.
    barrier = Barrier(2, timeout=10)

    run_all([barrier.wait, barrier.wait], 2)


def test_run_all_stops_after_error() -> None:
    """`run_all` must start no more tasks once one has raised an error."""
    ran: list[str] = []

    def fail() -> None:
        raise ValueError("made-up")

    tasks: list[Callable[[], object]] = [fail, lambda: ran.append("after")]

    with raises(ValueError):
        run_all(tasks, 1)

    assert ran == []


def test_run_all_stops_on_interrupt() -> None:
    """`run_all` must start no more tasks after an interrupt, then raise it."""
    ran: list[int] = []

    def interrupt(signum: int, frame: FrameType | None) -> None:
        raise KeyboardInterrupt

    def task(n: int) -> None:
        sleep(0.2)
        ran.append(n)

    tasks = [partial(task, n) for n in range(5)]

    # Like Ctrl+C, a signal raises the interrupt in the main thread, while it waits.
    previous = signal(SIGALRM, interrupt)
    setitimer(ITIMER_REAL, 0.05)

    try:
        with raises(KeyboardInterrupt):
            run_all(tasks, 1)
    finally:
        setitimer(ITIMER_REAL, 0)
        signal(SIGALRM, previous)

    # The first task was running, so it finished. No other task started.
    assert ran == [0]


def test_run_all_waits_on_interrupt() -> None:
    """`run_all` must let the last tasks finish before it raises an interrupt."""
    ran: list[int] = []

    def interrupt(signum: int, frame: FrameType | None) -> None:
        raise KeyboardInterrupt

    def task(n: int) -> None:
        sleep(0.2)
        ran.append(n)

    # There are no more tasks than can run at once, so every task has started by the
    # time the interrupt is raised.
    tasks = [partial(task, n) for n in range(2)]

    previous = signal(SIGALRM, interrupt)
    setitimer(ITIMER_REAL, 0.05)

    try:
        with raises(KeyboardInterrupt):
            run_all(tasks, 2)
    finally:
        setitimer(ITIMER_REAL, 0)
        signal(SIGALRM, previous)

    found = sorted(ran)
    expect = [0, 1]

    assert found == expect
