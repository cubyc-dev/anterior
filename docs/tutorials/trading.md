---

icon: material/finance

---

[//]: # ()
[//]: # (# Algorithmic Trading Bot)

[//]: # ()
[//]: # ()
[//]: # ( This tutorial implements a simple moving average crossover, buying when the symbol when its current price)

[//]: # ( is greater than the long moving average, and selling when its current price is less than)

[//]: # (the long moving average.)

[//]: # ()
[//]: # ()
[//]: # (For advanced trading schedules, data feeds, and util functions, check out the cubyc_finance library, see:)

[//]: # (    -  https://github.com/cubyc-team/cubyc-finance)

[//]: # ()
[//]: # (For more information on moving average crossover strategies, see:)

[//]: # (    - https://www.investopedia.com/terms/m/movingaverage.asp)

[//]: # ()
[//]: # (For more information on the yfinance library, see:)

[//]: # (    - https://pypi.org/project/yfinance/)

[//]: # ()
[//]: # (--- )

[//]: # (## Source)

[//]: # ()
[//]: # (To source our data from PyMC Marketing, we declare a custom data feed `PyMCDatafeed` which inherits from `DataFeed`.)

[//]: # (This class will be used to dynamically source and cache the data from PyMC Marketing for any given `channel`, and)

[//]: # ()
[//]: # (=== "Step 1")

[//]: # ()
[//]: # (    ```python hl_lines="6 9")

[//]: # (    --8<-- "tutorial_scripts/trading.py:datafeed")

[//]: # (    ```)

[//]: # ()
[//]: # ()
[//]: # (=== "Step 2")

[//]: # ()
[//]: # (    ```python hl_lines="1-4 11-15")

[//]: # (    --8<-- "tutorial_scripts/trading.py:datafeed")

[//]: # (    ```)

[//]: # ()
[//]: # (### Warp)

[//]: # ()
[//]: # (=== "Step 1")

[//]: # (    )
[//]: # (    Define Process)

[//]: # ()
[//]: # (    ```python hl_lines="1 4-9")

[//]: # (    --8<-- "tutorial_scripts/trading.py:process")

[//]: # (    ```)

[//]: # ()
[//]: # ()
[//]: # (=== "Step 2")

[//]: # ()
[//]: # (    Logic for buying, selling and utility functions)

[//]: # ()
[//]: # (    ```python hl_lines="11-26")

[//]: # (    --8<-- "tutorial_scripts/trading.py:process")

[//]: # (    ```)

[//]: # ()
[//]: # (=== "Step 3")

[//]: # ()
[//]: # (    Set up your trading bot's initial state, and schedule the `update` method to run on weekdays at 10:00 AM.)

[//]: # ()
[//]: # (    ```python hl_lines="28-32")

[//]: # (    --8<-- "tutorial_scripts/trading.py:process")

[//]: # (    ```)

[//]: # ()
[//]: # ()
[//]: # (=== "Step 4")

[//]: # ()
[//]: # (    Fill out the `update` method to buy or sell the symbol based on the moving average crossover strategy.)

[//]: # ()
[//]: # (    ```python hl_lines="34-50")

[//]: # (    --8<-- "tutorial_scripts/trading.py:process")

[//]: # (    ```)

# Coming soon!