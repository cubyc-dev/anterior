import datetime as datetime
from typing import Hashable, Any

import pandas as pd
import polars as pl


class OracleSeries:
    """
    Series that inherits all the methods and attributes of a pandas or polars Series,
    but only returns and modifies data before/after the current date depending on specification.

    Parameters
    ----------
    series : pd.Series | pl.Series
        The Series to use as the data source.
    past : bool, optional
        If True, the OracleSeries will return only the data before the current date.
        If False, it will return only the data after the current date.

    Examples
    --------
    !!! Example "OracleSeries vs regular Series"

        === "Past"
            ```python hl_lines="6 12-13"
            from pandas import Series
            from anterior import BackTester, OracleSeries

            data = ... #  data between 2010 to 2024
            series = Series(data)
            oracle_series = OracleSeries(data, past=True)

            bt = BackTester()

            @bt.on(year=2020, month=1, day=1)
            def update()
                series.iloc[:-5]        # returns the last 5 rows of the entire ndarray
                oracle_series.iloc[:-5] # returns the last 5 rows of the ndarray before 2020-01-01

            bt.run("2010-01-01", "2024-01-01")
            ```

        === "Future"
            ```python hl_lines="6 12-13"
            from pandas import Series
            from anterior import BackTester, OracleSeries

            data = ... #  data between 2010 to 2024
            series = Series(data)
            oracle_series = OracleSeries(data, past=False)

            bt = BackTester()

            @bt.on(year=2020, month=1, day=1)
            def update()
                series.iloc[:5]         # returns the first 5 rows of the entire ndarray
                oracle_series.iloc[:5]  # returns the first 5 rows of the ndarray after 2020-01-01

            bt.run("2010-01-01", "2024-01-01")
            ```
    """

    def __init__(self, series: pd.Series | pl.Series, past=True):

        if not isinstance(series, (pd.Series, pl.Series)):
            raise ValueError("only pandas or polars OracleSeries are supported")

        self._series = series
        self.past = past

    @classmethod
    def pd_from_csv(cls, path: str, past: bool = True, **kwargs):
        """
        Create an OracleSeries from a CSV file inheriting all the methods and attributes of a Pandas Series.

        Parameters
        ----------
        path : str
            The path to the CSV file.
        past : bool, optional
            If True, the OracleSeries will return only the data before the current date.
            If False, it will return only the data after the current date.
        kwargs :
            Additional keyword arguments to pass to `pd.read

        Returns
        -------
        OracleSeries
            The OracleSeries created from the CSV file.
        """
        return cls(pd.read_csv(path, **kwargs),  past=past)

    @classmethod
    def pl_from_csv(cls, path: str, past: bool = True, **kwargs):
        """
        Create an OracleSeries from a CSV file inheriting all the methods and attributes of a Polars Series.

        Parameters
        ----------
        path : str
            The path to the CSV file.
        past: bool, optional
            If True, the OracleSeries will return only the data before the current date.
            If False, it will return only the data after the current date.
        kwargs :
            Additional keyword arguments to pass to `pl.read

        Returns
        -------
        OracleSeries
            The OracleSeries created from the CSV file.
        """

        return cls(pd.read_csv(path, **kwargs), past=past)

    def _get_filtered_series(self):

        current_datetime = datetime.datetime.now()

        if self.past:
            return self._series[self._series.index <= pd.to_datetime(current_datetime)]
        else:
            return self._series[self._series.index > pd.to_datetime(current_datetime)]

    def __getattr__(self, name: str):

        if name in ['_series', 'past']:
            return object.__getattribute__(self, name)

        attr = getattr(self._get_filtered_series(), name)

        # Special attributes that should be returned directly, not wrapped
        direct_attributes = ['iloc', 'loc', 'at', 'iat']

        if name in direct_attributes:
            return attr
        elif callable(attr):
            def wrapper(*args, **kwargs):
                result = attr(*args, **kwargs)
                return result

            return wrapper
        else:
            return attr

    def pop(self, item: Hashable) -> Any:
        raise NotImplementedError("OracleSeries does not support item popping")

    def __getitem__(self, item):
        return self._get_filtered_df().__getitem__(item)

    def __setitem__(self, key, value):
        return self._get_filtered_df().__setitem__(key, value)

    def __delitem__(self, key):
        raise NotImplementedError("OracleSeries does not support item deletion")

    def __len__(self):
        return self._get_filtered_df().__len__()

    def __iter__(self):
        return self._get_filtered_df().__iter__()

    def __contains__(self, item):
        return self._get_filtered_df().__contains__(item)

    def __reversed__(self):
        return self._get_filtered_df().__reversed__()

    def __missing__(self, key):
        return self._get_filtered_df().__missing__(key)

    def __hash__(self):
        return self._get_filtered_df().__hash__()

    def __repr__(self):
        return self._get_filtered_df().__repr__()

    def __str__(self):
        return self._get_filtered_df().__str__()
