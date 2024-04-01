---
hide:
  - title
  - header
  - footer
  - navigation
  - toc
  
title: Python's pluggable backtester
description: Schedule, run, and backtest functions with your data
---

<style>
    .cubyc-title h1 {
        font-size: 55px;
        margin-bottom: 10px;

        .gradient-text {
          background-image: linear-gradient(45deg,  var(--md-primary-fg-color), var(--md-accent-fg-color));
          -webkit-background-clip: text;
          background-clip: text;
          color: transparent;
          -webkit-text-fill-color: transparent;
          text-fill-color: transparent;
          background-size: 500% auto;
          animation: textShine 3s ease-in-out infinite alternate;
        }
    }
    @media only screen and (max-width: 1000px) {
    
        .main-container-left {
            display: flex;
            flex-direction: column;
        }
    
        .main-container-right {
            display: flex;
            flex-direction: column-reverse;
        }
    
        .grid-item {
            max-width: 90vw;
        }
    
        .tabbed-set {
            max-width: 90vw;
        }
    
        .cubyc-title {
            max-width: 100%
        }
    }
</style>

<div class="cubyc-title" markdown>

<h1><b>Python's <a class="gradient-text">pluggable</a> backtester</b></h1>

<h2> Schedule your functions today, run them tomorrow... or backtest them yesterday. Always with your data. </h2>

[Start backtesting](site:getting_started){ .md-button .md-button--primary }
[Use cases](site:tutorials/marketing){ .md-button }

</div>

<div class="grid cards" markdown>

-   :fontawesome-solid-plug:{ .middle }  &nbsp; __Schedule, backtest, and plug__   

    ---
    Schedule your functions and backtest them with your own data in a few lines of code.

    [:octicons-arrow-right-24: Features](#schedule-with-ease)

  - :fontawesome-solid-download:{ .middle } &nbsp; __Set up in 5 minutes__ 

    ---
    
    Install Anterior with `pip` and get up
    and running in minutes. 

    [:octicons-arrow-right-24: Quickstart](site:getting_started/concepts)

-   :fontawesome-solid-puzzle-piece:{ .middle } &nbsp; __Domain-agnostic__

    ---

    Backtest anything, from trading bots to marketing campaigns and rolling forecasts.

    [:octicons-arrow-right-24: Tutorials](site:tutorials/marketing)

</div>

---

<div id="reliable" class="main-container-left" markdown>

<div class="grid-item" markdown  style="padding-left: 20%; padding-right: 20%">

<h2 class="gradient-text" markdown> Schedule with ease </h2>

Writing Python schedules doesn't have to be hard! Declare, combine, or attach schedules directly to your functions with Anterior, 
and let time run its course.

[:octicons-arrow-right-24: Learn More](site:getting_started/concepts#schedule-functions)
</div>

<div data-aos="fade-left" class="grid-item tabbed-set" markdown>

=== ":fontawesome-solid-flag:{ .middle } &nbsp; Declare"

    ```python linenums="1" hl_lines="8"
    from anterior import BackTester

    bt = BackTester()

    def func():
        print("I run every 3 hours!")

    bt.every(hours=3).do(my_func)

    bt.run('2010-01-01', '2020-12-31')
    ```

=== ":fontawesome-solid-gears:{ .middle } &nbsp; Combine"

    ```python linenums="1" hl_lines="8-9"
    from anterior import BackTester

    bt = BackTester()

    def func():
        print("I run every 3 hours on weekdays!")

    (bt.every(hours=3) & 
     bt.between(days_of_week="mon-fri")).do(func)
    bt.run('2010-01-01', '2020-12-31')
    ```

=== ":fontawesome-solid-paperclip:{ .middle } &nbsp; Attach"

    ```python linenums="1" hl_lines="5"
    from anterior import BackTester

    bt = BackTester()

    @bt.do_every(hours=3)
    def func():
        print("I run every 3 hours!")


    bt.run('2010-01-01', '2020-12-31')
    ```

</div>

</div>

<div id="reliable" class="main-container-right" markdown>

<div data-aos="fade-right" class="grid-item tabbed-set" markdown>

=== ":fontawesome-solid-play:{ .center } &nbsp; Live"

    ```python linenums="1" hl_lines="10"
    from anterior import BackTester

    fibonacci = [0, 1]

    def hourly_fibonacci():
        fibonacci.append(sum(fibonacci[-2:]))

    bt = BackTester()
    bt.every(hours=1).do(hourly_fibonacci)
    bt.run()
    ```


=== ":fontawesome-solid-backward:{ .center } &nbsp; Backtest"

    ```python linenums="1" hl_lines="10"
    from anterior import BackTester

    fibonacci = [0, 1]

    def hourly_fibonacci():
        fibonacci.append(sum(fibonacci[-2:]))

    bt = BackTester()
    bt.every(hours=1).do(hourly_fibonacci)
    bt.run(start='2010-01-01', end='2020-12-31')
    ```


=== ":fontawesome-solid-arrow-up-right-dots:{ .center } &nbsp; Backfill"

    ```python linenums="1" hl_lines="10"
    from anterior import BackTester

    fibonacci = [0, 1]

    def hourly_fibonacc():
        fibonacci.append(sum(fibonacci[-2:]))

    bt = BackTester()
    bt.every(hours=1).do(hourly_fibonacci)
    bt.run(start='2010-01-01')
    ```

</div>

<div class="grid-item" markdown  style="padding-left: 20%; padding-right: 20%">

<h2 markdown> Consistent results </h2>

Performance decays over time. Anterior's backtester validates your pipelines live or against historical data to ensure consistency and highlight improvement areas.

[:octicons-arrow-right-24: Learn More](site:getting_started/concepts/#run-live-or-backtest-simulations)
</div>

</div>

<div id="reliable" class="main-container-left" markdown>

<div class="grid-item" markdown  style="padding-left: 20%; padding-right: 20%">

<h2 class="gradient-text" markdown> Plug your data </h2>


Slicing and dicing time series is cumbersome.
With Anterior's `Oracle` data structures, you can dynamically access 
your `DataFrame` and `Series` objects on-the-fly during backtests.

[:octicons-arrow-right-24: Learn More](site:getting_started/concepts/#oracle-data)
</div>

<div data-aos="fade-left" class="grid-item tabbed-set" markdown>

=== ":fontawesome-solid-database:{ .center } &nbsp; Source"
  
    ```python linenums="1" hl_lines="3"
    from anterior import BackTester, OracleDataFrame

    df = OracleDataFrame.from_csv("data.csv")
    bt = Backtester()

    @bt.do_every(months=1)
    def hour_update():
        df.iloc[:-1] # last value as of every month

    bt.run(start="2012-01-01", end="2024-01-01")
    ```

=== ":fontawesome-solid-calendar-days:{ .center } &nbsp; Schedule"

    ```python linenums="1" hl_lines="6"
    from anterior import BackTester, OracleDataFrame

    df = OracleDataFrame.from_csv("data.csv")
    bt = Backtester()

    @bt.do_every(months=1)
    def hour_update():
        df.iloc[:-1] # last value as of every month

    bt.run(start="2012-01-01", end="2024-01-01")
    ```

=== ":fontawesome-solid-key:{ .center } &nbsp; Access"

    ```python linenums="1" hl_lines="8"
    from anterior import BackTester, OracleDataFrame

    df = OracleDataFrame.from_csv("data.csv")
    bt = Backtester()

    @bt.do_every(months=1)
    def hour_update():
        df.iloc[:-1] # last value as of every month

    bt.run(start="2012-01-01", end="2024-01-01")
    ```

</div>
</div>