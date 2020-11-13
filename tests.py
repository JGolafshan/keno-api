import src.keno_app as keno


keno = keno.KenoAPI("NSW")

x = keno.historical_data_new(start_date="2020-04-21", end_date="2020-04-25")


print(x)