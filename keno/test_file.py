from keno_app import *
from pprint import pprint
import csv
import pandas as pd


base = KenoAPI("NSW")

hist = base.historical_draws("2021-06-01", "2021-06-03")
print(hist)