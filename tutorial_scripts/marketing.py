import logging
import warnings

from tabulate import tabulate

warnings.filterwarnings("ignore")
logging.getLogger("pymc").setLevel(logging.CRITICAL)

# --8<-- [start:source]

from anterior.source import OracleDataFrame

url = "https://raw.githubusercontent.com/pymc-labs/pymc-marketing/main/datasets/mmm_example.csv"
data = OracleDataFrame.pd_from_csv(url, parse_dates=["date_week"], date_col="date_week")

# --8<-- [end:source]

# --8<-- [start:warp]

from datetime import datetime
from pymc_marketing import mmm

from anterior.warp import BackTester

model = mmm.DelayedSaturatedMMM(
    date_column="date_week",
    channel_columns=["x1", "x2"],
    control_columns=["event_1", "event_2", "t"],
    adstock_max_lag=8, yearly_seasonality=2)

budget = 0.5
logs = []


def get_budget_allocation():
    features, targets = data[[c for c in data.columns if c != "y"]], data["y"]

    model.fit(features.reset_index(), targets, progressbar=False)

    sigmoid_params = model.compute_channel_curve_optimization_parameters_original_scale()

    opt = model. \
        optimize_channel_budget_for_maximum_contribution(method="sigmoid",
                                                         total_budget=budget,
                                                         parameters=sigmoid_params)

    x1_contribution = mmm.utils.extense_sigmoid(budget / 2, *sigmoid_params["x1"])
    x2_contribution = mmm.utils.extense_sigmoid(budget / 2, *sigmoid_params["x2"])

    logs.append({"date": datetime.now(),
                 "equal_alloc": x1_contribution + x2_contribution,
                 "mmm_alloc": opt["estimated_contribution"]["total"]})


bt = BackTester()
bt.every(months=6).do(get_budget_allocation)
bt.run(start="2019-01-01", end="2021-08-30")
# --8<-- [end:warp]


# --8<-- [start:push]
import pandas as pd

results = pd.DataFrame.from_records(logs, index="date")
results['percentage_gain'] = (results['mmm_alloc'] - results['equal_alloc']) / results['equal_alloc']
print(results)
# --8<-- [end:push]

print(tabulate(results, headers='keys', tablefmt='github'))
