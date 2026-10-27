"""Functions for running tasks at the same time."""

from collections.abc import Callable, Iterable
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait


def run_all(
    tasks: Iterable[Callable[[], object]],
    concurrency: int,
) -> None:
    """Run tasks in threads, with no more than a number of them running at once.

    Once a task raises an error, no more tasks start. The tasks already running finish,
    then the first error, in the tasks' order, is raised.

    An interrupt, like Ctrl+C, stops tasks starting in the same way, then is raised once
    the running tasks finish.

    Args:
        tasks: The tasks to run.
        concurrency: The most tasks to run at once.

    Raises:
        BaseException: The first error that a task raised.
    """
    futures: list[Future[object]] = []
    running: set[Future[object]] = set()

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        for task in tasks:
            if len(running) == concurrency:
                wait(
                    running,
                    return_when=FIRST_COMPLETED,
                )

            done = {future for future in running if future.done()}
            running -= done

            if any(future.exception() for future in done):
                break

            future = executor.submit(task)
            futures.append(future)
            running.add(future)

        # The block waits for the running tasks as it closes, but an interrupt during
        # that wait ends it early. An interrupt during this wait is raised inside the
        # block, so the block still waits as it closes.
        wait(running)

    for future in futures:
        if error := future.exception():
            raise error
