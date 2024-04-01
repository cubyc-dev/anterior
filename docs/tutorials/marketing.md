---
icon: material/bullseye-arrow
hide:
  - toc
---

# MMM Budget Allocation

In this example, we train a Market Mix Model (MMM) to allocate a marketing budget across two different channels. 
We use a custom data feed to retrieve data from
[PyMC Marketing](https://www.pymc-marketing.io/en/stable/index.html)'s tutorial, and re-train our model every three months.
Lastly, we backtest the model and visualize its predictions and rolling error from 2010 to the present day. 

--- 

## Source

Load PyMC Marketing's tutorial data into an `OracleDataFrame` to fetch historical data on-the-fly during the backtest.

```python linenums="1"
--8<-- "./tutorial_scripts/marketing.py:source"
```

---

## Warp

First, we declare our MMM and initial variables. Then, we declare a function to optimize it with the latest data and collect
logs on the model's expected contribution to sales and that of an equal allocation strategy.
Lastly, using anterior's `BackTester`, we schedule the aforementioned function to run every six months and backtest the whole pipeline.

=== "Step 1"
    Declare the MMM model and initial variables.

    ```python linenums="1" hl_lines="6-13"
    --8<-- "./tutorial_scripts/marketing.py:warp"
    ```

=== "Step 2"
    Define an optimization function with logging.

    ```python linenums="1" hl_lines="16-33"
    --8<-- "./tutorial_scripts/marketing.py:warp"
    ```

=== "Step 3"
    Schedule the optimization function and backtest the pipeline.

    ```python linenums="1" hl_lines="36-38"
    --8<-- "./tutorial_scripts/marketing.py:warp"
    ```
---

## Push

We create a table to compare the MMM's performance with that of an equal allocation strategy on a rolling, six-month basis.

```python linenums="1"
--8<-- "./tutorial_scripts/marketing.py:push"
```

Output:

| date                |   equal_alloc |   mmm_alloc |   percentage_gain |
|---------------------|---------------|-------------|-------------------|
| 2019-01-01 00:00:00 |       2096.76 |     2327.42 |         0.110011  |
| 2019-07-01 00:00:00 |       2124.46 |     2362.46 |         0.112029  |
| 2020-01-01 00:00:00 |       2367.61 |     2500.78 |         0.0562446 |
| 2020-07-01 00:00:00 |       2289.19 |     2425.39 |         0.059496  |
| 2021-01-01 00:00:00 |       2306.23 |     2414.29 |         0.0468537 |
| 2021-07-01 00:00:00 |       2279.21 |     2358.85 |         0.0349413 |
