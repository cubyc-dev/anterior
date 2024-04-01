# --8<-- [start:source]
import datetime
from io import BytesIO

import pandas as pd
import requests

from anterior.source import OracleDataFrame

_api_key = ...  # Your API key here


def fetch_and_prepare_data(sid):
    url = f"https://api.stlouisfed.org/fred/series/observations?file_type=json" \
          f"&api_key={_api_key}&series_id={sid}"
    df = pd.read_json(BytesIO(bytes(requests.get(url).text, 'utf-8')), typ='series')["observations"]
    df = pd.DataFrame(df)
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    df[sid] = pd.to_numeric(df['value'], errors='coerce')
    return df[[sid]]


series_ids = ["FEDFUNDS", "UNRATE", "CPIAUCSL", "TOTALSA"]
df = pd.concat([fetch_and_prepare_data(sid) for sid in series_ids], axis=1, join='inner')
df['month'], df['year'] = df.index.month, df.index.year

data = OracleDataFrame(df)

# --8<-- [end:source]


# --8<-- [start:warp]
import numpy as np
import xgboost as xgb

from anterior.warp import BackTester

model = xgb.XGBRegressor(objective="reg:squarederror", random_state=7)
logs = []

bt = BackTester()


@bt.do_every(months=1)
def train_model():
    train_data, eval_data = data.iloc[:-1], data.iloc[-1:]
    y_train, y_eval = train_data.pop("TOTALSA"), eval_data.pop("TOTALSA")

    model.fit(train_data, y_train)
    preds = model.predict(eval_data.values).item()

    logs.append({"date": datetime.datetime.now(),
                 "abs_err": np.abs(y_eval - preds).item(),
                 "predicted": preds, "actual": y_eval.item()})


bt.run(start="2010-01-01", end="2024-01-01")

# --8<-- [end:warp]

# --8<-- [start:push]
import seaborn as sns
import matplotlib.pyplot as plt

sns.set()
results = pd.DataFrame.from_records(logs, index="date")
fig, axs = plt.subplots(2, 1, gridspec_kw={"height_ratios": [3, 1]})
sns.lineplot(data=results[["predicted", "actual"]], ax=axs[0])
sns.lineplot(data=results["abs_err"], ax=axs[1], color="#2ca02c")
plt.title("Car Sales Forecast")
plt.tight_layout()
plt.show()
# # --8<-- [end:push]
