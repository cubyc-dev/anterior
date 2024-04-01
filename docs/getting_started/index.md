# Quickstart 

## 1. Install `anterior`

Installation is simple:

```console
pip install anterior
```

Alternatively, to install the latest features, clone Anterior's [GitHub repo](https://github.com/cubyc-team/anterior) 
and run:

```console
python setup.py install
```

---

## 2. Start backtesting!

You're now ready to run backtests with Anterior.

!!! example "Your first backtest"
    ```python
    from anterior import BackTester

    bt = BackTester()

    counter = 0

    def hello_world():
        counter += 1
        print(f"Hello, hour {counter}!")

    bt.every(hours=1).do(hello_world)

    process.run(start='2023-01-01', end='2023-01-10')
    print(counter)
    ```

