from keno_app import *
from pprint import pprint
import csv

hist = RealTime("NSW").historical_draws("2021-05-01", "2021-05-02")
pprint(hist)
