from keno_app import *
from pprint import pprint
import csv
import pandas as pd

pd.set_option('display.max_rows', 4000)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 2000)

base = RealTime("NSW")

hist = base.historical_draws("2021-06-01", "2021-06-03")
data = []



for i in range(0, len(hist)):
    for j in hist[i].get("items"):
        data.append([
            j["game-number"], base.__transform_time__(j["closed"]),
            j["draw"][0], j["draw"][1], j["draw"][2], j["draw"][3], j["draw"][4], j["draw"][5], j["draw"][6],
            j["draw"][7], j["draw"][8], j["draw"][9], j["draw"][10], j["draw"][11], j["draw"][12], j["draw"][13],
            j["draw"][14], j["draw"][15], j["draw"][16], j["draw"][17], j["draw"][18], j["draw"][19],
            j["variants"]["heads-or-tails"]["result"],
            j["variants"]["heads-or-tails"]["heads"],
            j["variants"]["heads-or-tails"]["tails"],
            j["variants"]["roulette"],
            j["variants"]["bonus"]
        ])

df = pd.DataFrame(data,
                  columns=["Game_Number", "Closed",
                           "Draw_1", "Draw_2", "Draw_3", "Draw_4", "Draw_5", "Draw_6", "Draw_7", "Draw_8", "Draw_9",
                           "Draw_10", "Draw_11", "Draw_12", "Draw_13", "Draw_14", "Draw_15", "Draw_16", "Draw_17",
                           "Draw_18", "Draw_19", "Draw_20", "Result", "Heads", "Tails", "Roulette", "Bonus"])

print(df)
