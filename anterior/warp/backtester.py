import datetime
import logging
import multiprocessing
import re
import time
import warnings
from typing import Callable
from typing import Optional
from zoneinfo import ZoneInfo

import time_machine
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.job import Job
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from pydantic import BaseModel
from pydantic import model_validator
from rich.progress import Progress, BarColumn, TimeElapsedColumn, TextColumn, TaskProgressColumn, SpinnerColumn
from tzlocal import get_localzone
from urllib3.exceptions import SystemTimeWarning

from anterior import logger, console
from .schedule import Schedule, _schedule_decorator

warnings.filterwarnings("ignore", category=SystemTimeWarning)


class BackTester(BaseModel):
    timezone: str = get_localzone().__str__()
    function_map: dict = {}
    _tzinfo: ZoneInfo = None

    @model_validator(mode="after")
    def _model_validator(self):
        try:
            self._tzinfo = ZoneInfo(self.timezone)
        except Exception:
            raise ValueError(f"Invalid timezone: {self.timezone}")

    def __init__(self, workers: int = 1, **kwargs):
        super().__init__(**kwargs)

        # =================== Scheduling ===================
        workers = workers if workers > 0 else multiprocessing.cpu_count() - 2
        # self._scheduler = BlockingScheduler(executors={"default": ThreadPoolExecutor(workers)}, timezone=self._tzinfo)
        self._scheduler = BackgroundScheduler(executors={"default": ThreadPoolExecutor(workers)}, timezone=self._tzinfo)

    def now(self):
        """
        Returns the timezone-aware datetime of the backtester.

        Returns
        -------
        datetime.datetime
            The timezone-aware datetime of the backtester.

        Notes
        -----
        - The datetime is timezone-aware and is in the timezone specified by the backtester's `timezone` attribute.
        - The datetime is the simulated time in the backtest if the backtester is being backtested.
        - The datetime is the current system time if the backtester is running in live mode.
        """

        return datetime.datetime.now(tz=self._tzinfo)

    def on_start(self):
        """
        Gets called when the backtester starts.

        Tip
        -----
        - Override this method to add custom behavior when the backtester starts.

        """
        pass

    def on_stop(self):
        """
        Gets called when the backtester stops.

        Tip
        -----
        - Override this method to add custom behavior when the backtester stops.
        """
        pass

    def do(self, function: Callable, name: Optional[str] = None, log: bool = True):
        """
        Schedules a function to run immediately during the backtester's run.

        Parameters
        ----------
        function : Callable
            The function to schedule.
        name : str, optional
            The name of the function to schedule. Defaults to the function"s name.
        log : bool
            Whether to log the function to the backtester's logs. Defaults to True.

        Returns
        -------
        Job
            The job object running the specified function.

        See Also
        --------
        - [`Schedule.do`](schedule.md#anterior.warp.schedule.Schedule.do) Defines the function to run on the schedule object.

        Examples
        --------

        ???+ Example "Running a function immediately"
            ```python
            bt = BackTester(name="do_example")

            def function():
                print("Hello, world!")

            bt.do(function)
            bt.run()   # prints "Hello, world!" as soon as the backtester starts
            ```
        """
        return Schedule(self).do(function=function, name=name, log=log)

    def after(self, delta: Optional[datetime.timedelta] = None, days: int = 0, hours: int = 0, minutes: int = 0,
              seconds: int = 0) -> Schedule:
        """
        Creates a Schedule object that will trigger after the specified time interval.

        Parameters
        ----------
        delta : datetime.timedelta, optional
            The time interval to trigger after. Mutually exclusive with days, hours, minutes, and seconds.
        days : int, optional
            The number of days to trigger after. Mutually exclusive with delta.
        hours : int, optional
            The number of hours to trigger after. Mutually exclusive with delta.
        minutes : int, optional
            The number of minutes to trigger after. Mutually exclusive with delta.
        seconds : int, optional
            The number of seconds to trigger after. Mutually exclusive with delta.

        Returns
        -------
        Schedule
            Schedule object that will trigger after the specified time interval.

        Raises
        ------
        ValueError
            If both a timedelta and individual time intervals are provided.

        See Also
        --------
        - [`do_after`](./#anterior.warp.backtester.BackTester.do_after) Decorator to schedule a function to run after a time interval.

        Info
        -----
        The time interval can be specified either as a timedelta or as individual time intervals. For example,
        the following two calls are equivalent:

        ```python
        bt.after(datetime.timedelta(days=2)).do(...)
        bt.after(days=2).do(...)
        ```

        Examples
        --------
        ???+ Example "Running a function after a time interval"

            ```python
            bt = BackTester(name="after_example")

            bt.after(days=2).do(...)
            bt.after(hours=12).do(...)
            bt.after(datetime.timedelta(minutes=30)).do(...)
            ```
        """

        any_time = any([days, hours, minutes, seconds])

        if any_time:
            if delta is not None:
                raise ValueError("Cannot provide both a timedelta and individual time intervals.")
            delta = datetime.timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)

        return self.on(self.now() + delta)

    def between(self, years: Optional[str | tuple[int, int]] = None, months: Optional[str | tuple[int, int]] = None,
                days: Optional[str | tuple[int, int]] = None, weeks: Optional[str | tuple[int, int]] = None,
                days_of_week: Optional[str | tuple[int, int] | tuple[str, str]] = None,
                hours: Optional[str | tuple[int, int]] = None, minutes: Optional[str | tuple[int, int]] = None,
                seconds: Optional[str | tuple[int, int]] = None,
                dates: Optional[tuple[datetime.datetime, datetime.datetime]] = None) -> Schedule:
        """
        Creates a Schedule object that runs a function between a specified time range.

        Parameters
        ----------
        years : str | tuple[int, int], optional
            The years to trigger between. Start and end values must represent integers.
        months :str |  tuple[int, int], optional
            The months to trigger between. Start and end values must represent integers between 1 and 12.
        days : str | tuple[int, int], optional
            The days to trigger between. Start and end values must represent integers between 1 and 31.
        weeks : str | tuple[int, int], optional
            The weeks to trigger between. Start and end values must represent integers between 1 and 53.
        days_of_week : str | tuple[int, int], optional
            The days of the week to trigger between. Start and end values must represent integers between 0 and 6,
            or one of the following strings: "mon", "tue", "wed", "thu", "fri", "sat", "sun".
        hours : str | tuple[int, int], optional
            The hours to trigger between. Start and end values must represent integers between 0 and 23.
        minutes : str | tuple[int, int], optional
            The minutes to trigger between. Start and end values must represent integers between 0 and 59.
        seconds : str | tuple[int, int], optional
            The seconds to trigger between. Start and end values must represent integers between 0 and 59.
        dates : tuple[datetime.datetime, datetime.datetime], optional
            The dates to trigger between. Start and end values must be datetime objects.

        Returns
        -------
        Schedule
            Schedule object that will trigger between the specified time intervals.

        Raises
        ------
        ValueError
            If the time intervals are not in the correct format.

        See Also
        --------
        - [`do_between`](./#anterior.warp.backtester.BackTester.do_between) Decorator to schedule a function to run between a specified time range.

        Examples
        --------
        ???+ Example "Running a function between a time range with tuples"

            ```python
            bt = BackTester(name="between_example_with_tuples")

            # runs a function every weekday between January and May
            bt.between(months=("jan", "may"), days_of_week=(0, 4)).do(...)

            # runs a function every 15 minutes between 9 AM and 5 PM
            (bt.between(hours=(9, 17)) & bt.every(minutes=15)).do(...)
            ```

        ???+ Example "Running a function between a time range with strings"

            ```python
            bt = BackTester(name="between_example_with_strings")

            # runs a function every weekday between January and May
            bt.between(months="1-5", days_of_week="mon-fri").do(...)

            # runs a function every 15 minutes between 9 AM and 5 PM
            (bt.between(hours="9-17") & bt.every(minutes=15)).do(...)
            ```
        """

        field_dict = {"year": years, "month": months, "day": days, "week": weeks, "day_of_week": days_of_week,
                      "hour": hours, "minute": minutes, "second": seconds}

        for k, v in field_dict.items():
            if v is not None:
                if isinstance(v, tuple) and len(v) == 2:
                    field_dict[k] = f"{v[0]}-{v[1]}"
                elif isinstance(v, str):
                    if not re.match(r"^\w+-\w+$", v):
                        raise ValueError(f"{k} must be a string in the format 'a-b', where a and b "
                                         f"represent the start and end of the range respectively.")
                else:
                    raise ValueError(f"{k} must be a string in the format 'a-b' or a tuple of start and end values.")

        if dates is not None:
            field_dict["start_date"], field_dict["end_date"] = dates

        return Schedule(backtester=self, trigger=CronTrigger(**field_dict, timezone=self._tzinfo))

    def cron(self, expression: str):
        """
        Creates a Schedule object that runs a function on a cron schedule.

        Parameters
        ----------
        expression : str
            The cron expression to trigger on.

        Returns
        -------
        Schedule
            Schedule object that will trigger according to the specified cron expression.

        See Also
        --------
        - [`do_cron`](./#anterior.warp.backtester.BackTester.do_cron) Decorator to schedule a function to run on a cron schedule.

        Info
        ----
        Check out [crontab.guru](https://crontab.guru/) for more information on cron expressions.

        Examples
        --------
        ???+ Example "Running functions with cron expressions"

            ```python
            bt = BackTester(name="cron_example")

            bt.cron("* */5 * 0 0 0").do(...)   # runs a function every 5 minutes
            bt.cron("0 0 1 1 0 0").do(...)     # runs a function every January 1st
            ```
        """
        return Schedule(self, trigger=CronTrigger.from_crontab(expression, timezone=self._tzinfo))

    def on(self, dt: Optional[str | datetime.datetime | datetime.date] = None,
           year: Optional[int] = None, month: Optional[int] = None, day: Optional[int] = None,
           weekday: Optional[int] = None, day_of_week: Optional[int] = None,
           hour: Optional[int] = None, minute: Optional[int] = None, second: Optional[int] = None) -> Schedule:
        """
        Creates a Schedule object that will trigger on a specific date or datetime.

        Parameters
        ----------
        dt : str | atetime.datetime | datetime.date, optional
            The datetime to trigger on. Mutually exclusive with year, month, day, weekday, day_of_week, hour, minute,
            and second. Must be a string in the format "YYYY-MM-DD HH:MM:SS", a datetime object, or a date object.
        year : int, optional
            The year to trigger on. Mutually exclusive with dt.
        month : int, optional
            The month to trigger on. Mutually exclusive with dt.
        day : int, optional
            The day to trigger on. Mutually exclusive with dt.
        weekday : int, optional
            The weekday to trigger on. Mutually exclusive with dt.
        day_of_week : int, optional
            The day of the week to trigger on. Mutually exclusive with dt.
        hour : int, optional
            The hour to trigger on. Mutually exclusive with dt.
        minute : int, optional
            The minute to trigger on. Mutually exclusive with dt.
        second : int, optional
            The second to trigger on. Mutually exclusive with dt.

        Returns
        -------
        Schedule
            Schedule object that will trigger on the specified date and time.

        Raises
        ------
        ValueError
            If both a dt and individual date components are provided.

        See Also
        --------
        - [`do_on`](./#anterior.warp.backtester.BackTester.do_on) Decorator to schedule a function to run on a specific date or datetime.

        Example
        --------
        ```python
        import datetime

        bt = BackTester(name="on_example")

        # both schedules run a function on January 1st, 2023 at 10:00 AM
        bt.on(dt=datetime.datetime(2023, 1, 1, 10, 0)).do(...)
        bt.on(year=2023, month=1, day=1, hour=10, minute=0).do()
        ```
        """
        any_date = any([year, month, day, weekday, day_of_week, hour, minute, second])

        if isinstance(dt, str):
            dt = datetime.datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")

        if dt is not None:
            if any_date:
                raise ValueError("Cannot provide both a datetime and individual date components.")
            return Schedule(self, trigger=DateTrigger(run_date=dt, timezone=self._tzinfo))
        else:
            if not any_date:
                raise ValueError("Must provide either a datetime or individual date components.")
            return Schedule(self, trigger=CronTrigger(year=year, month=month, day=day, week=weekday,
                                                      day_of_week=day_of_week, hour=hour, minute=minute, second=second,
                                                      timezone=self._tzinfo))

    def every(self, years: Optional[int] = None, months: Optional[int] = None, days: Optional[int] = None,
              weeks: Optional[int] = None, hours: Optional[int] = None, minutes: Optional[int] = None,
              seconds: Optional[int] = None) -> Schedule:
        """
        Creates a Schedule object that will run every x years/months/days/weeks/hours/minutes/seconds.

        Parameters
        ----------
        years : int, optional
            The number of years to trigger every. Defaults to None.
        months : int, optional
            The number of months to trigger every. Defaults to None.
        days : int, optional
            The number of days to trigger every. Defaults to None.
        weeks : int, optional
            The number of weeks to trigger every. Defaults to None.
        hours : int, optional
            The number of hours to trigger every. Defaults to None.
        minutes : int, optional
            The number of minutes to trigger every. Defaults to None.
        seconds : int, optional
            The number of seconds to trigger every. Defaults to None.

        Returns
        -------
        Schedule
            Schedule object that will trigger every x years/months/days/weeks/hours/minutes/seconds.

        See Also
        --------
        - [`do_every`](./#anterior.warp.backtester.BackTester.do_every) Decorator to schedule a function to run every x years/months/days/weeks/hours/minutes/seconds.

        Examples
        --------
        ???+ Example "Running functions periodically"
            ```python
            bt = BackTester(name="every_example")

            bt.every(days=1).do(...)       # runs a function every day
            bt.every(minutes=15).do(...)   # runs a function every 15 minutes
            ```
        """
        field_dict = {"year": years, "month": months, "day": days, "week": weeks, "hour": hours, "minute": minutes,
                      "second": seconds}

        for k, v in field_dict.items():
            if v is not None:
                if not isinstance(v, int):
                    raise ValueError(f"{k} must be an integer.")
                field_dict[k] = f"*/{int(v)}"
        return Schedule(self, trigger=CronTrigger(**field_dict, timezone=self._tzinfo))

    def when(self, condition: Callable) -> Schedule:
        """
        Creates a Schedule object that will trigger when the specified condition function returns True.

        Parameters
        ----------
        condition : Callable
            The condition function to trigger on. Must return a boolean value when called.

        Returns
        -------
        Schedule
            Schedule object that will trigger when the specified condition function returns True.

        Info
        -----
        - By default, `once` checks the condition function every second. To override this, combine the `when` schedule.
        with an `every` schedule:

            ```python
            (bt.when(condition) & bt.every(minutes=15)).do(...)     # checks every 15 minutes
            (bt.when(condition) & bt.after(days=2)).do(...)         # checks every 2 days
            ```

        Examples
        --------

        ???+ Example "Running a function when a condition is met"
            ```python
            import random

            bt = BackTester(name="when_example")

            def condition():
                return random.randint(0, 1)  # returns True 50% of the time

            bt.when(condition).do(lambda: print("Conditional second!"))
            (bt.when(condition) & bt.every(hours=1)).do(lambda: print("Conditional hour!"))
            ```
        """
        return Schedule(self, trigger=CronTrigger(timezone=self._tzinfo), conditions=[condition])

    def once(self, condition_function: Callable) -> Schedule:
        """
        Creates a Schedule object that will trigger only once when the specified condition function returns True.

        Parameters
        ----------
        condition_function : Callable
            The condition function to trigger on. Must return a boolean value when called.

        Returns
        -------
        Schedule
            Schedule object that will trigger only once when the specified condition function returns True.

        Info
        -----
        - The difference between the `once` and `when` schedules is that the `once` schedule will only trigger once,
        and then remove itself from the scheduler. The `when` schedule will continue to trigger as long as the
        condition function returns true.

        - By default, `once` checks the condition function every second. To override this, combine the `when` schedule.
        with an `every` schedule:

        ```python
        (bt.once(condition) & bt.every(minutes=15)).do(...)     # checks every 15 minutes
        (bt.once(condition) & bt.after(days=2)).do(...)         # checks every 2 days
        ```

        Examples
        --------
        ???+ Example "Running a function once a condition is met"

            ```python
            import random

            bt = BackTester(name="once_example")

            def condition():
                # returns True 50% of the time
                return random.randint(0, 1)

            bt.once(condition).do(lambda: print("Hello, condition!"))

            (bt.once(condition) & bt.every(hours=1)).do(lambda: print("Hello, hourly condition!")
            ```
        """
        return Schedule(self, trigger=DateTrigger(run_date=self.now(), timezone=self._tzinfo),
                        conditions=[condition_function], listen_once=True)

    def do_after(self, *args, **kwargs):
        """
        Decorator to schedule a function to run after the specified time interval. Equivalent to `after` schedule function.


        === "`do_after` decorator"

            ```python linenums="1" hl_lines="5"
            from anterior.warp import BackTester

            bt = BackTester()

            @bt.do_after(days=2)
            def update():
                print("Hello, world!")

            bt.run("2020-01-01", "2024-01-01")
            ```

        === "`after` function"

            ```python linenums="1" hl_lines="8"
            from anterior.warp import BackTester

            bt = BackTester()


            def update():
                print("Hello, world!")
            bt.after(days=2).do(update)
            bt.run("2020-01-01", "2024-01-01")
            ```

        See Also
        --------
        - [`after`](site:/#anterior.warp.backtester.BackTester.after): Creates a Schedule object that will trigger after the specified time interval.
        """
        return _schedule_decorator(self, "every", *args, **kwargs)

    def do_between(self, *args, **kwargs):
        """
        Decorator to schedule a function to run between a specified time range. Equivalent to `between` schedule function.

        === "`do_between` decorator"

            ```python linenums="1" hl_lines="5"
            from anterior.warp import BackTester

            bt = BackTester()

            @bt.do_between(days_of_week="mon-fri")
            def update():
                print("Hello, world!")

            bt.run("2020-01-01", "2024-01-01")
            ```

        === "`between` function"

            ```python linenums="1" hl_lines="8"
            from anterior.warp import BackTester

            bt = BackTester()


            def update():
                print("Hello, world!")
            bt.between(days_of_week="mon-fri").do(update)
            bt.run("2020-01-01", "2024-01-01")
            ```

        See Also
        --------
        - [`between`](./#anterior.warp.backtester.BackTester.between): Creates a Schedule object that runs a function between a specified time range.
        """
        return _schedule_decorator(self, "between", *args, **kwargs)

    def do_cron(self, *args, **kwargs):
        """
        Decorator to schedule a function to run on a cron schedule. Equivalent to `cron` schedule function.

        === "`do_cron` decorator"

            ```python linenums="1" hl_lines="5"
            from anterior.warp import BackTester

            bt = BackTester()

            @bt.do_cron("* */5 * 0 0 0")
            def update():
                print("Hello, world!")

            bt.run("2020-01-01", "2024-01-01")
            ```

        === "`cron` function"

            ```python linenums="1" hl_lines="8"
            from anterior.warp import BackTester

            bt = BackTester()


            def update():
                print("Hello, world!")
            bt.cron("* */5 * 0 0 0").do(update)
            bt.run("2020-01-01", "2024-01-01")
            ```

        See Also
        --------
        - [`cron`](./#anterior.warp.backtester.BackTester.cron): Creates a Schedule object that runs a function on a cron schedule.
        """
        return _schedule_decorator(self, "cron", *args, **kwargs)

    def do_on(self, *args, **kwargs):
        """
        Decorator to schedule a function to run on a specific date or datetime. Equivalent to `on` schedule function.

        === "`do_on` decorator"

            ```python linenums="1" hl_lines="5"
            from anterior.warp import BackTester

            bt = BackTester()

            @bt.do_on(year=2023, month=1, day=1, hour=10, minute=0)
            def update():
                print("Hello, world!")

            bt.run("2020-01-01", "2024-01-01")
            ```

        === "`on` function"

            ```python linenums="1" hl_lines="8"
            from anterior.warp import BackTester

            bt = BackTester()


            def update():
                print("Hello, world!")
            bt.on(year=2023, month=1, day=1, hour=10, minute=0).do(update)
            bt.run("2020-01-01", "2024-01-01")
            ```

        See Also
        --------
        - [`on`](./#anterior.warp.backtester.BackTester.on): Creates a Schedule object that will trigger on a specific date or datetime.
        """
        return _schedule_decorator(self, "on", *args, **kwargs)

    def do_every(self, *args, **kwargs):
        """
        Decorator to schedule a function to run every x years/months/days/weeks/hours/minutes/seconds.
        Equivalent to `every` schedule function.

        === "`do_every` decorator"

            ```python linenums="1" hl_lines="5"
            from anterior.warp import BackTester

            bt = BackTester()

            @bt.do_every(days=1)
            def update():
                print("Hello, world!")

            bt.run("2020-01-01", "2024-01-01")
            ```

        === "`every` function"

            ```python linenums="1" hl_lines="8"
            from anterior.warp import BackTester

            bt = BackTester()


            def update():
                print("Hello, world!")
            bt.every(days=1).do(update)
            bt.run("2020-01-01", "2024-01-01")
            ```

        See Also
        --------
        - [`every`](./#anterior.warp.backtester.BackTester.every): Creates a Schedule object that will run every x years/months/days/weeks/hours/minutes/seconds.
        """
        return _schedule_decorator(self, "every", *args, **kwargs)

    def get_scheduler(self) -> BlockingScheduler:
        """
        Returns the scheduler object associated with the backtester.

        Returns
        -------
        BlockingScheduler
            The scheduler object associated with the backtester.
        """

        return self._scheduler

    def pause(self) -> None:
        """
        Pauses the running backtester.

        See Also
        --------
        - [`run`](./#anterior.warp.backtester.BackTester.run): Runs or backtests the backtester.
        - [`resume`](./#anterior.warp.backtester.BackTester.resume): Resumes the backtester.
        - [`stop`](./#anterior.warp.backtester.BackTester.stop): Stops the running backtester.
        """

        self._scheduler.pause()
        logger.info("BackTester paused.")

    def resume(self) -> None:
        """
        Resumes the paused backtester.

        See Also
        --------
        - [`run`](./#anterior.warp.backtester.BackTester.run): Runs or backtests the backtester.
        - [`pause`](./#anterior.warp.backtester.BackTester.pause): Pauses the running backtester.
        - [`stop`](./#anterior.warp.backtester.BackTester.stop): Stops the running backtester.
        """

        self._scheduler.resume()
        logger.info("BackTester resumed.")

    def stop(self, wait: float = 0) -> None:
        """
        Stops the backtester.

        Parameters
        ----------
        wait : float, optional
            The number of seconds to wait before stopping the backtester. Defaults to 0 (no wait).

        See Also
        --------
        - [`run`](./#anterior.warp.backtester.BackTester.run): Runs or backtests the backtester.
        - [`pause`](./#anterior.warp.backtester.BackTester.pause): Pauses the running backtester.
        - [`resume`](./#anterior.warp.backtester.BackTester.resume): Resumes the backtester.

        Warning
        -----
        We recommend specifying the `wait` parameter to give the backtester time to stop gracefully.
        """

        if wait:
            if isinstance(wait, float):
                time.sleep(wait)
        if self._scheduler.running:
            self._scheduler.shutdown(wait=True)

        self.on_stop()
        self._scheduler.remove_all_jobs()

        logger.info(f"Run stopped.")

    def run(self, start: Optional[datetime.datetime | datetime.date | str] = None,
            end: Optional[datetime.datetime | datetime.date | str] = None,
            start_buffer: Optional[datetime.timedelta] = datetime.timedelta(),
            end_buffer: Optional[datetime.timedelta] = datetime.timedelta(),
            log_level: int = logging.INFO) -> None:
        """
        Runs the backtester from the specified start datetime to the end datetime.

        Parameters
        ----------
        start : datetime.datetime | datetime.date | str, optional
            Datetime or ISO-8601 string ("YYYY-MM-DD") to start the run from (inclusive).
        end : datetime.datetime | datetime.date | str, optional
            Datetime or ISO-8601 string ("YYYY-MM-DD") to end the run at (inclusive).
        start_buffer : datetime.timedelta, optional
            The data buffer to add to the start date when caching datafeeds. Defaults to 0.
        end_buffer : datetime.timedelta, optional
            The data buffer to add to the end date when caching datafeeds. Defaults to 0.
        log_level : int, optional
            The logging level to use for the backtest. Defaults to logging.INFO.

        Raises
        ------
        RuntimeError
            If the backtester is already running.

        See Also
        --------
        - [`pause`](./#anterior.warp.backtester.BackTester.pause): Pauses the running backtester.
        - [`resume`](./#anterior.warp.backtester.BackTester.resume): Resumes the backtester.
        - [`stop`](./#anterior.warp.backtester.BackTester.stop): Stops the running backtester.

        Examples
        --------

        ???+ Example "Backtest a backtester between two past dates"

            Provide both the start and end dates in the past:

            ```python
            bt = BackTester(name="run_example_1")
            ...
            bt.run(start="2023-01-01", end="2023-01-10")
            ```

        ???+ Example "Backtest a backtester from a past date until the present"

            Provide only the start date in the past:

            ```python
            bt = BackTester(name="run_example_2")
            ...
            bt.run(start="2023-01-01")
            ```

        ???+ Example "Run a live backtester until a future date"

            Provide only the end date in the future:

            ```python
            bt = BackTester(name="run_example_3")
            ...
            bt.run(end="2025-01-01")
            ```

        ???+ Example "Run a live backtester indefinitely until stopped"

            Leave both the start and end dates blank:

            ```python
            bt = BackTester(name="run_example_4")
            ...
            bt.run()
            # do something
            bt.stop()
            ```

        ???+ Example "Backtest a backtester from a past date until the present, and then run live until a future date"

            Provide both the start and end dates where the start date is in the past and the end date is in the future:

            ```python
            bt = BackTester(name="run_example_5")
            ...
            bt.run(start="2023-01-01", end="2030-01-01")
            ```
        """

        logger.setLevel(log_level)

        start = self._to_datetime(start)
        end = self._to_datetime(end)

        if start is None:
            _start = self.now()
        else:
            _start = start

        if start is not None:
            if end is None:
                # only start is provided, backtest from start to now
                self._backtest(start=start, end=self.now())
            elif end < self.now():
                # start and end are provided and end is in the past, backtest from start to end
                self._backtest(start=start, end=end)
            else:
                """ 
                start is provided and end is in the future, backtest from start to now 
                and then runs live from now until end
                """
                self._backtest(start=start, end=end)
                self._start(live=True)
                self.on(end).do(lambda: self.stop())
        else:
            if end is not None:
                # only end is provided, runs live from now until end
                self.on(end).do(lambda: self.stop())

            self._start(live=True)

    def _start(self, live: bool = False) -> None:

        self.on_start()
        self._kickstart_functions(live=live)

        if live:
            self._scheduler.start()

        logger.info(f"Run started.")

    def _backtest(self, start: datetime.datetime, end: datetime.datetime):

        total_seconds = int((end - start).total_seconds())
        logger.info(f"Backtesting from {start} to {end}.", extra={"markup": True})

        with time_machine.travel(start, tick=False) as traveller, \
                Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), BarColumn(),
                         TaskProgressColumn(), TimeElapsedColumn(), console=console,
                         refresh_per_second=60, get_time=time_machine.escape_hatch.time.time) as progress:

            self._start(live=False)
            task = progress.add_task(f"Backtesting", total=int(total_seconds))

            try:
                while self.now() < end:

                    # Gets the next job and its next fire datetime with the current datetime as the now parameter
                    next_jobs, next_fire_datetime = self._get_next_jobs()

                    # Terminates the backtest if there are no more jobs or the next job is scheduled for a later date
                    if not next_fire_datetime or next_fire_datetime > end:
                        break

                    # Updates the progress bar if the next job is scheduled for a later date """
                    progress.update(task, advance=(next_fire_datetime - self.now()).total_seconds())
                    time.sleep(1e-10)

                    # Moves the frozen time to the last scheduled time
                    traveller.move_to(next_fire_datetime)

                    for job in next_jobs:
                        # Updates the last job thread and the frozen time to the next job"s fire date
                        job.next_run_time = next_fire_datetime

                        # Runs the next job
                        job.func()

                # Updates the progress bar to 100%
                while not progress.finished:
                    progress.update(task, advance=60 * 60 * 24)

            except Exception as e:
                self.stop()
                raise e

            self.stop()

    def _kickstart_functions(self, live: bool):

        for _, func in self.function_map.items():

            if live:
                if not hasattr(func, "live") or (hasattr(func, "live") and getattr(func, "live")):
                    func(_scheduled=True)
            else:
                if not hasattr(func, "backtest") or (hasattr(func, "backtest") and getattr(func, "backtest")):
                    func(_scheduled=True)

    def _to_datetime(self, dt: datetime.datetime | datetime.date | str) -> Optional[datetime.datetime]:
        if dt is None:
            return None
        if isinstance(dt, str):
            dt = datetime.datetime.fromisoformat(dt)
        if isinstance(dt, datetime.date):
            dt = datetime.datetime.combine(dt, datetime.datetime.min.time())

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=self._tzinfo)

        return dt

    def _get_jobs(self) -> list:
        return self._scheduler.get_jobs()

    def _remove_job(self, job_id: str) -> None:
        self._scheduler.remove_job(job_id)

    def _get_next_jobs(self) -> tuple[list[Job], datetime.datetime]:

        next_fire_datetime = None
        next_fire_jobs = []

        # iterates through all jobs and find the next job to run
        for job in self._get_jobs():

            if not hasattr(job, "next_run_time"):
                job.next_run_time = None

            fire_datetime = job.trigger.get_next_fire_time(previous_fire_time=job.next_run_time, now=self.now())

            if fire_datetime is None:
                job.remove()  # Removes inactive jobs

            else:
                if next_fire_datetime is None or fire_datetime < next_fire_datetime:
                    next_fire_datetime = fire_datetime
                    next_fire_jobs = [job]
                elif fire_datetime == next_fire_datetime:
                    next_fire_jobs.append(job)

        if next_fire_datetime is not None:
            next_fire_datetime = next_fire_datetime.astimezone(self._tzinfo)

        next_fire_jobs.reverse()

        return next_fire_jobs, next_fire_datetime
