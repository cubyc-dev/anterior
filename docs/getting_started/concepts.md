---
icon: material/lightbulb
---

# Anterior 101

This guide will introduce you to the core concepts of Anterior and show you how to use them in your projects.

---

## Backtesting

The `BackTester` is the main anterior class, serving as the base class to schedule functions to run live or in backtest
simulations.

### Schedule Functions

Write or attach simple deterministic schedules to your functions using the with any of five scheduling primitives:
`after`, `between`, `cron`, `every`, and `on`.

???+ example "Simple schedules"

    === "After"
    
        ```python hl_lines="5 12"
        from anterior.warp import BackTester
    
        bt = BackTester()
        
        @bt.after(seconds=5)
        def decorated_func():
            print("I run after 5 seconds from the start of the backtest")
    
        def declared_func():
            print("I run after 10 days from the start of the backtest")
        
        bt.after(days=10).do(process.declared_func)
        ```

    === "Between"
    
        ```python hl_lines="5 12"
        from anterior.warp import BackTester
    
        bt = BackTester()
        
        @bt.between(days_of_week="mon-fri")
        def decorated_func():
            print("I run between Monday and Friday")
    
        def declared_func():
            print("I run between January and June")

        bt.between(months=(1, 6)).do(process.argument_func)
        ```
    
    === "Cron"
    
        ```python hl_lines="5 12"
        from anterior.warp import BackTester
    
        bt = BackTester()
        
        @schedules.cron("0 0 1 1 *")
        def decorated_func():
            print("I run every year on January 1st")

        def declared_func():
            print("I run every 5 minutes")
        
        bt.cron("*/5 * * * *").do(process.declared_func)
        ```
    === "Every"
    
        ```python hl_lines="5 12"
        from anterior.warp import BackTester
    
        bt = BackTester()
        
        @bt.cron("0 0 1 1 *")
        def decorated_func():
            print("I run every 15 minutes")

        def declared_func():
            print("I run every hour")
        
        bt.cron("*/5 * * * *").do(process.argument_func)
        ```
    
    === "On"
    
        ```python hl_lines="5 12"
        from anterior.warp import BackTester
    
        bt = BackTester()
        
        @bt.on("2023-05-20 10:00")
        def decorated_func():
            print("I run on May 20th, 2023 at 10 AM")

        def declared_func():
            print("I run on January 1st, 2024 at midnight")
        
        bt.on(year=2024, month=1, day=1).do(process.declared_func)
        ```

You can also or attach conditional schedules to your functions using the `when` and `once` methods.
These methods allow you to run a function when or once a non-deterministic condition function is met.

???+ example "Conditional schedules"

    === "When"
    
        ```python hl_lines="11"
        import random
        from anterior.warp import BackTester
     
        def conditional_func():
            return random.randint(0, 1)

        def executable_func():
            print("I run when conditional_func returns 1")
    
        bt = BackTester()
        bt.when(conditional_func).do(executable_func)
        ```
    
    === "Once"
    
        ```python hl_lines="11"
        import random
        from anterior.warp import BackTester
     
        def conditional_func():
            return random.randint(0, 1)

        def executable_func():
            print("I run once when the conditional function returns 1, but only once")
    
        bt = BackTester()
        bt.once(conditional_func).do(executable_func)
        ```

Simple and conditional schedules can be combined using the `&` and `|` operators, representing logical `AND` and `OR`
respectively.

???+ example "Combined schedules"

    === "And"
    
        ```python hl_lines="13-14"
        from anterior.warp import BackTester

        def conditional_func():
            return random.randint(0, 1)

        def func1():
            print("I run between Monday and Friday when the conditional function returns 1")

        def func2():
            print("I run every hour on January 1st, 2024")

        bt = BackTester()
        (bt.between(days_of_week="mon-fri") | bt.when(conditional_func)).do(func1)
        (bt.on(year=2024, month=1, day=1) & bt.every(hours=1)).do(func2)
        ```

    === "Or"
    
        ```python hl_lines="13-14"
        from anterior.warp import BackTester

        def conditional_func():
            return random.randint(0, 1)

        def func1():
            print("I run between 9:00 AM and 12:00 PM or when the conditional function returns 1")

        def func2():
            print("I run on January 1st, 2024 or January 5th, 2024")

        bt = BackTester()
        (bt.between(hours=(9, 12)) | bt.when(conditional_func)).do(func1)
        (bt.on(year=2024, month=1, day=1) | bt.on(year=2024, month=1, day=5)).do(func2)
        ```

### Run live or backtest simulations

Once you have scheduled your functions, you can run them live and stop them at any time, or backtest and backfill them
over a specified time period.

???+ example "Run, Stop, Backtest & Backfill"

    === "Run"

        ```python hl_lines="12"
        from anterior import BackTester

        bt = MyBackTester()

        counter = 0

        @bt.every(hours=1)
        def update():
            global counter
            counter += 1

        bt.run()                                            # run a live process 
        ...
        process.stop()                                      # stop the live process
        process.run(start="2020-01-01", end="2024-01-01")   # specify start and end dates to backtest
        process.run(start="2020-01-01")                     # specify only the start date to backfill
        ```
    
    === "Stop"

        ```python hl_lines="14"
        from anterior import BackTester

        bt = MyBackTester()

        counter = 0

        @bt.every(hours=1)
        def update():
            global counter
            counter += 1

        bt.run()                                            # run a live process 
        ...
        process.stop()                                      # stop the live process
        process.run(start="2020-01-01", end="2024-01-01")   # specify start and end dates to backtest
        process.run(start="2020-01-01")                     # specify only the start date to backfill
        ```
    
    === "Backtest"

        ```python hl_lines="15"
        from anterior import BackTester

        bt = MyBackTester()

        counter = 0

        @bt.every(hours=1)
        def update():
            global counter
            counter += 1

        bt.run()                                            # run a live process 
        ...
        process.stop()                                      # stop the live process
        process.run(start="2020-01-01", end="2024-01-01")   # specify start and end dates to backtest
        process.run(start="2020-01-01")                     # specify only the start date to backfill
        ```
    
    === "Backfill"
    
        ```python hl_lines="16"
        from anterior import BackTester

        bt = MyBackTester()

        counter = 0

        @bt.every(hours=1)
        def update():
            global counter
            counter += 1

        bt.run()                                            # run a live process 
        ...
        process.stop()                                      # stop the live process
        process.run(start="2020-01-01", end="2024-01-01")   # specify start and end dates to backtest
        process.run(start="2020-01-01")                     # specify only the start date to backfill
        ```

---

## Oracle data

The `OracleDataFrame` and `OracleSeries` classes inherit all the methods and attributes of a pandas or
polars `DataFrame` and `Series`, depending on the specification.
However, they simplify historical data access by only returning data before the simulated time.

???+ example "Oracle data usage"

    === "OracleDataFrame"
    
        ```python hl_lines="4"
        import pandas as pd
        from anterior import BackTester, OracleDataFrame
        
        df = OracleDataFrame(pd.read_csv("data.csv"))   # data between 2020-01-01 and 2024-01-01
    
        bt = BackTester()
    
        @bt.do_every(hours=1)
        def hour_update():
            df.iloc[-1]     # last value as of every simulated hour
    
        @bt.do_every(days=1)
        def day_update():
            df.iloc[-2:]    # last 2 value2 as of every simulated day
    
        @bt.do_on("2023-01-01")
        def day_update():
            df.iloc[-5:]    # last 5 values as of simulated January 1st, 2023
    
        bt.run(start="2023-01-01", end="2024-01-01")
        ```

    === "OracleSeries"
    
        ```python hl_lines="4"
        import pandas as pd
        from anterior import BackTester, OracleSeries
        
        df = OracleSeries(pd.read_csv("data.csv"))  # data between 2020-01-01 and 2024-01-01
    
        bt = BackTester()
    
        @bt.do_every(hours=1)
        def hour_update():
            df.iloc[-1]     # last value as of every simulated hour
    
        @bt.do_every(days=1)
        def day_update():
            df.iloc[-1:2]   # last 2 value as of every simulated day
    
        @bt.do_on("2023-01-01")
        def day_update():
            df.iloc[-5:]    # last 5 values as of simulated January 1st, 2023
    
        bt.run(start="2020-01-01", end="2024-01-01")
        ```