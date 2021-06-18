import datetime
import requests
import pandas as pd


class KenoBase:
    def __init__(self, state="NT"):
        self.__state__ = state.upper()
        self.__states__ = ["ACT", 'NSW', "QLD", "VIC", "WA", "NT", "SA", "TAS"]
        self.__base_url__ = "https://api-info-{}.keno.com.au".format(self.__state_redirect__.lower())

    def __get_url__(self, end_point="", additional_params=""):
        end_point = str(end_point)
        params = "?jurisdiction={}".format(self.__state_redirect__) + additional_params
        complete_url = self.__base_url__ + end_point + params

        return str(complete_url)

    @property
    def __state_redirect__(self):
        # Checks state and redirect/ throw error if unavailable or in any way invalid.

        # Check if the state is value is found in the state list if it isn't throw an error and exit app
        if any(x == self.__state__ for x in self.__states__) is False:
            return exit(str("Check state input: '{}' - is invalid").format(self.__state__))

        if self.__state__.upper() == self.__states__[4]:
            print("Keno is not available in WA-Automatically changed to NSW")
            self.__state__ = self.__states__[2]
            return self.__state__

        if self.__state__.upper() == self.__states__[5] or self.__state__.upper() == self.__states__[6] \
                or self.__state__.upper() == self.__states__[7]:
            self.__state__ = self.__states__[0]
            return self.__state__

        else:
            return self.__state__

    # noinspection PyDefaultArgument
    @staticmethod
    def __nested_dict__(key={}, additional_key=""):
        # Simple function to make getting/setting values, efficient and easier to read.
        return key.get(additional_key)

    @staticmethod
    def __transform_time__(_datetime):
        # method made explicit  for Keno's datetime format, changes type(str) to type(datetime)

        time_delta = _datetime.split("T")

        date_dict = {
            "year": int(time_delta[0][0:4]),
            "month": int(time_delta[0][5:7]),
            "day": int(time_delta[0][8:10]),
            "hour": int(time_delta[1][0:2]),
            "minute": int(time_delta[1][3:5]),
            "second": int(time_delta[1][6:8]),
        }

        _datetime = datetime.datetime(date_dict.get("year"), date_dict.get("month"), date_dict.get("day"),
                                      date_dict.get("hour"), date_dict.get("minute"), date_dict.get("second"))
        return _datetime.strftime("%Y-%m-%d %H:%M:%S.%f")

    @staticmethod
    def __custom_range__(start, end, step):
        return range(start, end + 1, step)

    @staticmethod
    def __clamp__(n, minn, maxn):
        return max(min(maxn, n), minn)


class KenoAPI(KenoBase):
    def __init__(self, state):
        super().__init__(state)

    def __results_selection__(self, initial_draw=1, total_draws=1, start_date="2021-02-08",
                              page_size=1, page_number=1):
        # game_number Max: 9999
        # Number of Games: Min:1, Max:200
        # page_size: Min:1, Max:200
        # page_number: Min:1, Max:100
        url = self.__get_url__(end_point="/v2/info/history", additional_params="&starting_game_number={}&number_of_"
                                                                               "games={}&date={}&page_size={"
                                                                               "}&page_number={}").format(
            initial_draw, total_draws, start_date, page_size, page_number)
        return dict(requests.get(url).json())

    def __results_narrowed__(self, date):
        number = 100
        increase = bool
        found = False

        while found is False:
            try:
                selection = self.__results_selection__(number, 1, date, 1, 1)
                if "keno.game.complete" in selection.get("items")[0].get("_type"):
                    found = True
                    retrieved_date = self.__transform_time__(selection.get("items")[0].get("closed"))
                    retrieved_date = datetime.datetime.strptime(retrieved_date, "%Y-%m-%d %H:%M:%S.%f")
                    start_date = datetime.datetime.strptime(date, "%Y-%m-%d")

                    # These two if statements check how many games we are from the first game
                    if retrieved_date < start_date:
                        time_delta = start_date - retrieved_date
                        increase = True

                    if retrieved_date > start_date:
                        time_delta = retrieved_date - start_date
                        increase = False

                    return ({
                        "date": datetime.datetime.strptime(date, "%Y-%m-%d").date(),
                        "increase": increase,
                        "initial_draw": number,
                        "retry_at": round(time_delta / datetime.timedelta(seconds=160), 0),
                        "start": 0
                    })

            except (IndexError, TypeError):
                number = number + 100
                continue

    def __data_frame__(self, keno_data):
        pd.set_option('display.max_rows', 999999)
        pd.set_option('display.max_columns', 999999)
        pd.set_option('display.width', 999999)
        list_result = []
        for i in range(0, len(keno_data)):
            for j in keno_data[i].get("items"):
                list_result.append([
                    j["game-number"], self.__transform_time__(j["closed"]),
                    j["draw"][0], j["draw"][1], j["draw"][2], j["draw"][3], j["draw"][4], j["draw"][5], j["draw"][6],
                    j["draw"][7], j["draw"][8], j["draw"][9], j["draw"][10], j["draw"][11], j["draw"][12],
                    j["draw"][13],
                    j["draw"][14], j["draw"][15], j["draw"][16], j["draw"][17], j["draw"][18], j["draw"][19],
                    j["variants"]["heads-or-tails"]["result"],
                    j["variants"]["heads-or-tails"]["heads"],
                    j["variants"]["heads-or-tails"]["tails"],
                    j["variants"]["roulette"],
                    j["variants"]["bonus"]
                ])

        return pd.DataFrame(list_result,
                            columns=["Game_Number", "Closed",
                                     "Draw_1", "Draw_2", "Draw_3", "Draw_4", "Draw_5", "Draw_6", "Draw_7", "Draw_8",
                                     "Draw_9",
                                     "Draw_10", "Draw_11", "Draw_12", "Draw_13", "Draw_14", "Draw_15", "Draw_16",
                                     "Draw_17",
                                     "Draw_18", "Draw_19", "Draw_20", "Result", "Heads", "Tails", "Roulette", "Bonus"])

    def game_status(self):
        # Gets current and next game status and returns them as a nested dict.
        url = self.__get_url__(end_point="/v2/games/kds", additional_params="")
        retrieved = dict(requests.get(url).json())

        status_current = {
            "starting_time": self.__transform_time__(
                _datetime=self.__nested_dict__(key=retrieved.get("current"), additional_key="closed")),
            "game_number": self.__nested_dict__(key=retrieved.get("current"), additional_key="game-number")
        }

        status_selling = {
            "starting_time": self.__transform_time__(
                _datetime=self.__nested_dict__(key=retrieved.get("selling"), additional_key="closing")),
            "game_number": self.__nested_dict__(key=retrieved.get("selling"), additional_key="game-number")
        }

        status = {
            "state": self.__state__,
            "current_game": status_current,
            "next_game": status_selling
        }

        return status

    def live_draw(self):
        # Gets current live game, returned as dict.
        url = self.__get_url__(end_point="/v2/games/kds", additional_params="")
        retrieved = dict(requests.get(url).json().get("current"))
        status = str(retrieved.get("_type")).split(".")
        status_type = status[-1]

        live_draw = {
            "state": self.__state__,
            "game_number": retrieved.get("game-number"),
            "status": status_type,
            "started_at": self.__transform_time__(_datetime=retrieved.get("closed")),
            "is_finished": None,
            "draw_numbers": retrieved.get("draw"),
            "bonus": self.__nested_dict__(retrieved.get("variants"), additional_key="bonus"),
            "heads": self.__nested_dict__(retrieved.get("variants"), additional_key="heads-or-tails")["heads"],
            "tails": self.__nested_dict__(retrieved.get("variants"), additional_key="heads-or-tails")["tails"],
            "result": self.__nested_dict__(retrieved.get("variants"), additional_key="heads-or-tails")["result"]
        }

        if retrieved.get("_type") == "application/vnd.tabcorp.keno.game.complete":
            live_draw.update({"is_finished": bool(True)})

        else:
            live_draw.update({"is_finished": bool(False)})

        return live_draw

    def jackpot(self):
        # returns a nested dict. for jackpots
        url = self.__get_url__(end_point="/v2/info/jackpots", additional_params="")
        retrieved = dict(requests.get(url).json())["jackpots"]

        jackpot_regular = {
            "ten_spot": self.__nested_dict__(key=retrieved.get("ten-spot"), additional_key="base"),
            "nine_spot": self.__nested_dict__(key=retrieved.get("nine-spot"), additional_key="base"),
            "eight_spot": self.__nested_dict__(key=retrieved.get("eight-spot"), additional_key="base"),
            "seven_spot": self.__nested_dict__(key=retrieved.get("seven-spot"), additional_key="base")
        }

        jackpot_leveraged = {
            "ten_spot": self.__nested_dict__(key=retrieved.get("ten-spot-mm"), additional_key="base"),
            "nine_spot": self.__nested_dict__(key=retrieved.get("nine-spot-mm"), additional_key="base"),
            "eight_spot": self.__nested_dict__(key=retrieved.get("eight-spot-mm"), additional_key="base"),
            "seven_spot": self.__nested_dict__(key=retrieved.get("seven-spot-mm"), additional_key="base")
        }

        jackpot_combined = {
            "state": self.__state__,
            "regular": jackpot_regular,
            "leveraged": jackpot_leveraged
        }

        return jackpot_combined

    def hot_cold(self):
        # returns a dict. with hot and cold numbers as well as then it was last updated
        url = self.__get_url__(end_point="/v2/info/hotCold", additional_params="")
        retrieved = dict(requests.get(url).json())

        hot_cold = {"cold": retrieved.get("coldNumbers"),
                    "hot": retrieved.get("hotNumbers"),
                    "last_updated": retrieved.get("secondsSinceLastReceived"),
                    "state": self.__state__}
        return hot_cold

    def historical_draws(self, start_date, end_date):
        start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
        timestamp = start_date
        results = []

        while timestamp <= end_date:
            base_test = self.__results_narrowed__(str(timestamp))

            if base_test.get("increase") is False and base_test.get("retry_at") > base_test.get("initial_draw"):
                base_test["date"] -= datetime.timedelta(days=1)
                base_test["start"] = 999 - (base_test.get("retry_at") + base_test.get("initial_draw"))

            else:
                base_test["start"] = base_test.get("retry_at") + base_test.get("initial_draw")

            for num in self.__custom_range__(0, 999, 180):
                if (num + base_test.get("start")) >= 999:
                    num = (num + base_test.get("start")) - 999

                returned_data = self.__results_selection__(self.__clamp__(base_test.get("start") + num, 0, 999), 180,
                                                           base_test.get("date").strftime("%Y-%m-%d"), 180, 1)
                results.append(returned_data)

            timestamp += datetime.timedelta(days=1)
        return self.__data_frame__(keno_data=results)
