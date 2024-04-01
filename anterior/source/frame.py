import datetime as datetime
from typing import Hashable

import pandas as pd
import polars as pl


class OracleDataFrame:
    """
    DataFrame that inherits all the methods and attributes of a pandas or polars DataFrame,
    but only returns and modifies data before/after the current date depending on specification.

    Parameters
    ----------
    df : pd.DataFrame | pl.DataFrame
        The DataFrame to use as the data source.
    date_col : str, optional
        The name of the column containing dates. Defaults to the index.
    past : bool, optional
        If True, the OracleDataFrame will return only the data before the current date.
        If False, it will return only the data after the current date.

    Examples
    --------
    !!! Example "OracleDataFrame vs regular DataFrame"

        === "Past"
            ```python hl_lines="6 12-13"
            from pandas import DataFrame
            from anterior import BackTester, RetroDataFrame

            data = ... #  data between 2010 to 2024
            df = DataFrame(data)
            oracle_df = RetroDataFrame(data, past=True)

            bt = BackTester()

            @bt.on(year=2020, month=1, day=1)
            def update()
                df.iloc[:-5]            # returns the last 5 rows of the entire dataset
                oracle_df.iloc[:-5]     # returns the last 5 rows of the dataset before 2020-01-01

            bt.run("2010-01-01", "2024-01-01")
            ```

        === "Future"
            ```python hl_lines="6 12-13"
            from polars import DataFrame
            from anterior import BackTester, RetroDataFrame

            data = ... #  data between 2010 to 2024
            df = DataFrame(data)
            oracle_df = RetroDataFrame(data, past=False)

            bt = BackTester()

            @bt.on(year=2020, month=1, day=1)
            def update()
                df.iloc[:5]             # returns the first 5 rows of the entire dataset
                oracle_df.iloc[:5]      # returns the first 5 rows of the dataset after 2020-01-01

            bt.run("2010-01-01", "2024-01-01")
            ```
    """

    def __init__(self, df: pd.DataFrame | pl.DataFrame, date_col: str = "index", past: bool = True):

        if not isinstance(df, (pd.DataFrame, pl.DataFrame)):
            raise ValueError("only pandas or polars OracleDataFrames are supported")

        self._df = df
        self._date_col = date_col
        self.past = past

    @classmethod
    def pd_from_csv(cls, path: str, date_col="index", past: bool = True, **kwargs):
        """
        Create an OracleDataFrame from a CSV file inheriting all the methods and attributes of a Pandas DataFrame.

        Parameters
        ----------
        path : str
            The path to the CSV file.
        date_col: str, optional
            The name of the column containing dates. Defaults to the index.
        past : bool, optional
            If True, the OracleDataFrame will return only the data before the current date.
            If False, it will return only the data after the current date.
        kwargs :
            Additional keyword arguments to pass to `pd.read

        Returns
        -------
        OracleDataFrame
            The OracleDataFrame created from the CSV file.

        """
        return cls(pd.read_csv(path, **kwargs), date_col=date_col, past=past)

    @classmethod
    def pl_from_csv(cls, path: str, date_col="index", past: bool = True, **kwargs):
        """
        Create an OracleDataFrame from a CSV file inheriting all the methods and attributes of a Polars DataFrame.

        Parameters
        ----------
        path : str
            The path to the CSV file.
        date_col: str, optional
            The name of the column containing dates. Defaults to the index.
        past: bool, optional
            If True, the OracleDataFrame will return only the data before the current date.
            If False, it will return only the data after the current date.
        kwargs :
            Additional keyword arguments to pass to `pl.read

        Returns
        -------
        OracleDataFrame
            The OracleDataFrame created from the CSV file.
        """

        return cls(pd.read_csv(path, **kwargs), date_col=date_col, past=past)

    def _get_filtered_df(self):
        current_datetime = datetime.datetime.now()

        if self.past:
            if self._date_col == "index":
                return self._df[self._df.index <= current_datetime]
            else:
                return self._df[self._df[self._date_col] <= pd.to_datetime(current_datetime)]
        else:
            if self._date_col == "index":
                return self._df[self._df.index > pd.to_datetime(current_datetime)]
            else:
                return self._df[self._df[self._date_col] > pd.to_datetime(current_datetime)]

    def __getattr__(self, name: str):
        if name in ['_df', '_date_col', 'past']:
            return object.__getattribute__(self, name)

        attr = getattr(self._get_filtered_df(), name)

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

    def pop(self, item: Hashable) -> pd.Series | pl.Series:
        raise NotImplementedError("OracleDataFrame does not support item popping")

    def __getitem__(self, item):
        return self._get_filtered_df().__getitem__(item)

    def __setitem__(self, key, value):
        return self._get_filtered_df().__setitem__(key, value)

    def __delitem__(self, key):
        raise NotImplementedError("OracleDataFrame does not support item deletion")

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
