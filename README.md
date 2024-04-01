# Python's pluggable Backtester

## Schedule your functions today, run them tomorrow... or backtest them yesterday.

Anterior is an open-source Python backtester that lets you schedule and backtest functions. 
It is lightweight, easy to use, and works with your DataFrames and Series data. Check out the
[Documentation](https://docs.cubyc.com/anterior) for more information.

--- 
## Quickstart

### 1. Install

Installation is simple:

```console
pip install anterior
```

Alternatively, to install the latest features, clone this GitHub repository and run the following command inside the downloaded directory:

```console
pip install .
```

### 2. Start backtesting!

You're now ready to run backtests with Anterior. 
The following example shows how to dynamically create a Fibonacci sequence
by computing the next number every hour.

```python
from anterior import BackTester

fibonacci = [0, 1]

def hourly_fibonacci():
    fibonacci.append(sum(fibonacci[-2:]))

bt = BackTester()
bt.every(hours=1).do(hourly_fibonacci)
bt.run(start="2021-01-01", end="2022-01-02")
```