import datetime
import inspect
import logging
import random
import re
import time
from functools import wraps
from typing import Iterable, Callable, Self
from typing import Union, Optional

import time_machine
from apscheduler.triggers.base import BaseTrigger
from apscheduler.triggers.combining import OrTrigger, AndTrigger
from apscheduler.triggers.cron import CronTrigger

from anterior import logger as cubyc_logger


def _is_int_or_numeric(value: any):
    """
    Checks if a value is an integer or numeric string.

    :param any value: value to check
    :return: whether the value is an integer or numeric string
    :rtype: bool
    """
    return isinstance(value, int) or (isinstance(value, str) and value.isnumeric())


def _is_xth_weekday(value: any):
    """
    Checks if a value is a string of the format "xth mon/tue/wed/thu/fri/sat/sun".

    :param any value: value to check
    :return: whether the value is a string of the format "xth mon/tue/wed/thu/fri/sat/sun"
    :rtype: bool
    """
    return isinstance(value, str) and re.match(r"^\d+(?:st|nd|rd|th)\s+(?:mon|tue|wed|thu|fri|sat|sun)$", value)


def _is_last_weekday(value: any):
    """
    Checks if a value is a string of the format "last mon/tue/wed/thu/fri/sat/sun".

    :param any value: value to check
    :return: whether the value is a string of the format "last mon/tue/wed/thu/fri/sat/sun"
    :rtype: bool
    """
    return isinstance(value, str) and re.match(r"^last\s+(?:mon|tue|wed|thu|fri|sat|sun)$", value)


def _is_range(value: str):
    """
    Checks if a value is a string of the format "x-y".

    :param any value: value to check
    :return: whether the value is a string of the format "x-y"
    :rtype: bool
    """

    return re.match(r"\w+-\w+$", value)


def _is_recurrent(value: str):
    """
    Checks if a value is a string of the format "*/x".

    :param any value: value to check
    :return: whether the value is a string of the format "*/x"
    :rtype: bool
    """
    return re.match(r"\*\/\d+$", value)


def _schedule_decorator(scheduler, schedule_type: str, *schedule_args, **schedule_kwargs):
    def decorator(func):
        name = func.__name__

        @wraps(func)
        def inner(*args, _scheduled=False, **kwargs):

            if not _scheduled:
                return func(*args, **kwargs)

            if len(inspect.signature(func).parameters):
                raise RuntimeError(f"Functions with parameters cannot be decorated with schedules. "
                                   f"Please use regular schedules.")

            getattr(scheduler, schedule_type)(*schedule_args, **schedule_kwargs).do(lambda: func(*args, **kwargs),
                                                                                    name=name)

        if name not in scheduler.function_map:
            scheduler.function_map[name] = inner
        else:
            raise RuntimeError(f"Function {name} is already scheduled. Please use a different name.")

        return inner

    return decorator


class Schedule:
    """
    A Schedule object that represents a schedule for running a function.

    Parameters
    ----------
    backtester : BackTester
        The backtester to schedule the function on.
    trigger : BaseTrigger, optional
        The trigger to run the function on. Defaults to None.
    start_datetime : datetime.datetime, optional
        The datetime to start running the function on. Defaults to None.
    end_datetime : datetime.datetime, optional
        The datetime to stop running the function on. Defaults to None.
    conditions : Callable | Iterable[Callable], optional
        The condition function(s) to run the function on. Defaults to None.
    listen_once : bool, optional
        Whether to run the function only once. Defaults to False.

    See Also
    --------
    - [`BackTester`](backtester.md#cubyc.warp.backtester.BackTester): The backtester to schedule the function on.

    Info
    ----
    Schedules should be declared through a `BackTester` object.

    ```python
    from cubyc import BackTester

    bt = BackTester()


    @bt.do_every(minutes=15)
    def update_1():
        print("This function runs every 15 minutes")

    def update_2():
        print("This function also runs every 15 minutes")

    bt.every(minutes=15).do(update_2)
    ```

    Tip
    ---
    Declared schedules can be combined using the `&` and `|` operators.

    ```python
    from cubyc import BackTester

    bt = BackTester()

    def update():
        print("Hello, world!")

    (bt.every(minutes=15) & between(days_of_week="mon-fri")).do(update) # Runs every 15 minutes on weekdays
    (bt.between(hours=(9, 12)) | bt.between(hours=(13, 16))).do(update) # Runs between 9-12 and 13-16
    ```

    Warnings
    --------
    Most users won't need to create a `Schedule` object directly. Instead, use the `@Schedule` decorators or the
    `BackTester` class to create schedules.
    """
    def __init__(self, backtester, trigger: BaseTrigger = None, start_datetime=None, end_datetime=None,
                 conditions: Union[Callable, Iterable[Callable]] = None, listen_once=False):

        self.backtester = backtester
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime
        self.listen_once = listen_once
        self.job = None

        if conditions is None:
            self.conditions = []
        else:
            self.conditions = [conditions] if isinstance(conditions, Callable) else conditions

        self.trigger = trigger

    @staticmethod
    def after(**kwargs):
        def decorator(func):
            setattr(func, "after", kwargs)

            @wraps(func)
            def inner(self, *args, **kwargs):
                return func(self, *args, **kwargs)

            return inner

        return decorator

    @staticmethod
    def _datetime_to_date_dict(dt):
        return {"year": dt.year, "month": dt.month, "day": dt.day, "hour": dt.hour, "minute": dt.minute,
                "second": dt.second}

    @staticmethod
    def _date_dict_to_datetime(date_dict):
        return datetime.datetime(**date_dict)

    def _listener(self, conditions: Iterable[Callable], execution_function: Callable):
        # Creates a wrapper function that runs the execution function once the condition function is met

        def wrapper():
            if all(cond() for cond in conditions):
                self.backtester.do(execution_function)
                if self.listen_once:
                    # removes the listening job from the scheduler
                    self.job.remove()

        wrapper.__name__ = execution_function.__name__
        return wrapper

    def do(self, function: Callable, name: str = None, log: bool = True) -> Self:
        """
        Defines the function to run on the schedule object.

        Parameters
        ----------
        function : Callable
            The function to run.
        name : str, optional
            The name of the function to display in the logs. If not provided, the function's given name will be used.
        log : bool, optional
            Whether to log the function's execution. Defaults to True.

        Returns
        -------
        Schedule
            The Schedule object with the function to run.
        """

        if name is not None:
            function.__name__ = name

        if len(self.conditions):
            function = self._listener(self.conditions, function)
        elif log:
            function = _func_wrapper(function)

        self.job = self.backtester.get_scheduler().add_job(function, trigger=self.trigger, name=name)

        return self

    def __str__(self):
        return f"Schedule(trigger={self.trigger}, start_datetime={self.start_datetime}, end_datetime={self.end_datetime}, " \
               f"conditions={self.conditions}, listen_once={self.listen_once})"

    def __and__(self, other):

        if self.trigger.timezone != other.trigger.timezone:
            raise ValueError("Cannot combine schedules with different timezones")

        if self.trigger.__class__.__name__ != other.trigger.__class__.__name__:
            trigger = AndTrigger([self.trigger, other.trigger])
        else:
            if not (isinstance(self.trigger, CronTrigger) and isinstance(other.trigger, CronTrigger)):
                raise NotImplementedError("Cannot combine schedules.")

            self_fields = {f.name: str(f) for f in self.trigger.fields if not f.is_default}
            other_fields = {f.name: str(f) for f in other.trigger.fields if not f.is_default}

            trigger_fields = {}

            for common_key in self_fields.keys() & other_fields.keys():
                value_1 = self_fields[common_key]
                value_2 = other_fields[common_key]

                """
                Fires every c values within the a-b range, where
                a-b is the current attribute value and c is the argument value
                see a-b/c in https://apscheduler.readthedocs.io/en/3.x/modules/triggers/cron.html for more info.
                """
                if _is_recurrent(value_1) and _is_range(value_2):
                    recurrent_value = value_1.split("/")[1]
                    range_value = value_2
                elif _is_range(value_1) and _is_recurrent(value_2):
                    recurrent_value = value_2.split("/")[1]
                    range_value = value_1
                else:
                    raise ValueError(
                        "Cannot combine schedules with different values for the same field {} unless one is an every"
                        " schedule and the other is a between schedule.".format(common_key))

                trigger_fields[common_key] = "{}/{}".format(range_value, recurrent_value)

            trigger = CronTrigger(**self_fields | other_fields | trigger_fields, timezone=self.trigger.timezone)

        return Schedule(self.backtester, trigger=trigger, conditions=self.conditions + other.conditions,
                        listen_once=self.listen_once or other.listen_once)

    def __or__(self, other):
        if self.trigger.timezone != other.trigger.timezone:
            raise ValueError("Cannot combine schedules with different timezones")

        if self.condition_functions != other.condition_functions:
            raise ValueError("Cannot " or " schedules with different condition functions")

        return Schedule(self.backtester, trigger=OrTrigger([self.trigger, other.trigger]),
                        conditions=self.conditions + other.conditions)


def listen(data_stream):
    def decorator(func):
        setattr(func, "listen", True)

        @wraps(func)
        def inner(self, _scheduled=False, *args, **kwargs):
            if not _scheduled:
                return func(self, *args, **kwargs)

            data_stream.do(lambda message: func(self, message))

        return inner

    return decorator


def cron(*args, **kwargs):
    return _schedule_decorator("cron", *args, **kwargs)


def every(*args, **kwargs):
    return _schedule_decorator("every", *args, **kwargs)


def on(*args, **kwargs):
    return _schedule_decorator("on", *args, **kwargs)


def when(*args, **kwargs):
    return _schedule_decorator("when", *args, **kwargs)


def once(*args, **kwargs):
    return _schedule_decorator("once", *args, **kwargs)


def retry(tries: int = 0, delay: int = 0, max_delay: Optional[int] = None, backoff: int = 1, jitter: int = 0,
          exception=Exception):
    # """
    # Retries calling the decorated function.
    #
    # :param Exception exceptions: an exception to catch
    # :param int tries: number of times to retry before giving up and raising the exception
    # :param int delay: initial delay between retries in seconds
    # :param int max_delay: maximum delay between retries in seconds
    # :param int backoff: multiplier by which the delay grows after each attempt
    # :param int|tuple jitter: extra seconds to wait between retries, or a tuple of lower and upper bounds for a uniform
    #     random jitter
    # :return: the return value of the decorated function
    # """

    def decorator(func):
        name = func.__name__

        @wraps(func)
        def inner(self, _tries=tries, _delay=delay, _scheduled=False, *args, **kwargs):

            # If the function is called by the scheduler, then we want to run it regardless
            if _scheduled and not hasattr(func, "kickstart"):
                return
            try:
                func(self, *args, **kwargs)
            except exception as e:
                _tries -= 1

                if not _tries:
                    raise e

                self.log(
                    f"{func.__name__}() failed with [bold red]{e.__class__.__name__}[/]: {e}. Retrying in {_delay} seconds.",
                    logging_level=logging.ERROR, exc_info=True, extra={"markup": True})

                _new_delay = _delay * backoff
                if isinstance(jitter, tuple):
                    _new_delay += random.uniform(*jitter)
                else:
                    _new_delay += jitter

                if max_delay is not None:
                    _new_delay = min(_new_delay, max_delay)

                # Run the function again after the specified delay
                self.after(datetime.timedelta(seconds=_delay)).do(
                    lambda: inner(self, _tries=_tries, _delay=_new_delay, _scheduled=False, *args, **kwargs), name=name)

        return inner

    return decorator


def _func_wrapper(func):
    @wraps(func)
    def inner(*args, **kwargs):

        if time_machine.escape_hatch.is_travelling():
            start_time = time_machine.escape_hatch.time.time()
        else:
            start_time = time.time()

        try:
            func(*args, **kwargs)

            if time_machine.escape_hatch.is_travelling():
                delta_sec = (time_machine.escape_hatch.time.time() - start_time)
            else:
                delta_sec = (time.time() - start_time)

            if delta_sec < 1:
                cubyc_logger.debug(f"{func.__name__}() finished in {delta_sec * 1000} milliseconds",
                                   extra={"markup": True})
            elif delta_sec < 60:
                cubyc_logger.debug(f"{func.__name__}() finished in {delta_sec} seconds", extra={"markup": True})
            else:
                cubyc_logger.debug(f"{func.__name__}() finished in {delta_sec * 60} minutes", extra={"markup": True})

        except Exception as e:
            cubyc_logger.error(f"{func.__name__}() failed with [bold red]{e.__class__.__name__}[/]: {e}",
                               exc_info=False, extra={"markup": True})
            raise e

    return inner
