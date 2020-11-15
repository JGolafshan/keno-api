import datetime
import pandas as pd
import requests


class KenoAPI:
    def __init__(self, state="NT"):
        self.state = state.upper()
        self.states = ["ACT", 'NSW', "QLD", "VIC", "WA", "NT", "SA", "TAS"]
        self.base_url = "https://api-info-{}.keno.com.au".format(self.state_redirect.lower())

    def get_url(self, end_point="", additional_params=""):
        end_point = str(end_point)
        params = "?jurisdiction={}".format(self.state_redirect) + additional_params
        complete_url = self.base_url + end_point + params

        return str(complete_url)

    @property
    def state_redirect(self):
        # Checks state and redirect/ throw error if unavailable or in any way invalid.

        # Check if the state is value is found in the state list if it isn't throw an error and exit app
        if any(x == self.state for x in self.states) is False:
            return exit(str("Check state input: '{}' - is invalid").format(self.state))

        if self.state.upper() == self.states[4]:
            print("Keno is not available in WA-Automatically changed to NSW")
            self.state = self.states[2]
            return self.state

        if self.state.upper() == self.states[5] or self.state.upper() == self.states[6] \
                or self.state.upper() == self.states[7]:
            self.state = self.states[0]
            return self.state

        else:
            return self.state

    @staticmethod
    def nested_dict(key={}, additional_key=""):
        # Simple function to make getting/setting values, efficient and easier to read.
        return key.get(additional_key)

    @staticmethod
    def transform_time(_datetime):
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


class RealTime(KenoAPI):
    def __init__(self, state):
        super().__init__(state)

    def game_status(self):
        # Gets current and next game status and returns them as a nested dict.
        url = self.get_url(end_point="/v2/games/kds", additional_params="")
        retrieved = dict(requests.get(url).json())

        status_current = {
            "starting_time": self.transform_time(
                _datetime=self.nested_dict(key=retrieved.get("current"), additional_key="closed")),
            "game_number": self.nested_dict(key=retrieved.get("current"), additional_key="game-number")
        }

        status_selling = {
            "starting_time": self.transform_time(
                _datetime=self.nested_dict(key=retrieved.get("selling"), additional_key="closing")),
            "game_number": self.nested_dict(key=retrieved.get("selling"), additional_key="game-number")
        }

        status = {
            "state": self.state,
            "current_game": status_current,
            "next_game": status_selling
        }

        return status

    def live_draw(self):
        # Gets current live game, returned as dict.
        url = self.get_url(end_point="/v2/games/kds", additional_params="")
        retrieved = dict(requests.get(url).json().get("current"))
        status = str(retrieved.get("_type")).split(".")
        status_type = status[-1]

        live_draw = {
            "state": self.state,
            "game_number": retrieved.get("game-number"),
            "status": status_type,
            "started_at": self.transform_time(_datetime=retrieved.get("closed")),
            "is_finished": None,
            "draw_numbers": retrieved.get("draw"),
            "bonus": self.nested_dict(retrieved.get("variants"), additional_key="bonus"),
            "heads": self.nested_dict(retrieved.get("variants"), additional_key="heads-or-tails")["heads"],
            "tails": self.nested_dict(retrieved.get("variants"), additional_key="heads-or-tails")["tails"],
            "result": self.nested_dict(retrieved.get("variants"), additional_key="heads-or-tails")["result"]
        }

        if retrieved.get("_type") == "application/vnd.tabcorp.keno.game.complete":
            live_draw.update({"is_finished": bool(True)})

        else:
            live_draw.update({"is_finished": bool(False)})

        return live_draw

    def jackpot(self):
        # returns a nested dict. for jackpots
        url = self.get_url(end_point="/v2/info/jackpots", additional_params="")
        retrieved = dict(requests.get(url).json())["jackpots"]

        jackpot_regular = {
            "ten_spot": self.nested_dict(key=retrieved.get("ten-spot"), additional_key="base"),
            "nine_spot": self.nested_dict(key=retrieved.get("nine-spot"), additional_key="base"),
            "eight_spot": self.nested_dict(key=retrieved.get("eight-spot"), additional_key="base"),
            "seven_spot": self.nested_dict(key=retrieved.get("seven-spot"), additional_key="base")
        }

        jackpot_leveraged = {
            "ten_spot": self.nested_dict(key=retrieved.get("ten-spot-mm"), additional_key="base"),
            "nine_spot": self.nested_dict(key=retrieved.get("nine-spot-mm"), additional_key="base"),
            "eight_spot": self.nested_dict(key=retrieved.get("eight-spot-mm"), additional_key="base"),
            "seven_spot": self.nested_dict(key=retrieved.get("seven-spot-mm"), additional_key="base")
        }

        jackpot_combined = {
            "state": self.state,
            "regular": jackpot_regular,
            "leveraged": jackpot_leveraged
        }

        return jackpot_combined

    def hot_cold(self):
        # returns a dict. with hot and cold numbers as well as then it was last updated
        url = self.get_url(end_point="/v2/info/hotCold", additional_params="")
        retrieved = dict(requests.get(url).json())

        hot_cold = {"cold": retrieved.get("coldNumbers"),
                    "hot": retrieved.get("hotNumbers"),
                    "last_updated": retrieved.get("secondsSinceLastReceived"),
                    "state": self.state}
        return hot_cold


class HistoricalData(KenoAPI):
    def __init__(self, state=None, start_date=None, end_date=None):
        super().__init__(state)
        self.start_date = start_date
        self.end_date = end_date
        self.data = []

    # ------------- Callable Methods -------------

    def recent_trends(self, look_back=None):
        current_game = RealTime(state=self.state).game_status().get("current_game")
        get_date = datetime.datetime.now().strftime("%Y-%m-%d")
        get_game_number = current_game.get("game_number")
        start_game = get_game_number - look_back

        url = self.get_url(end_point="/v2/info/history",
                           additional_params="&starting_game_number={}&number_of_games={}&date={}&page_size=100&page_number=1").format(
            start_game, int(look_back), get_date)
        games_ = requests.get(url).json()
        print(url)

        if len(games_["items"]) == 0:
            exit("Could Not find anything")

        else:
            self.data = self.__append_data(selected_data=games_)
            return self.__df_conversion(selected_data=self.data)

    def historical_data(self):
        pass

    # ------------- Private Methods -------------

    def __append_data(self, selected_data):
        for item in selected_data["items"]:
            self.data.insert(0, [item["game-number"], item["closed"],
                                 item["draw"][0], item["draw"][1], item["draw"][2], item["draw"][3], item["draw"][4],
                                 item["draw"][5], item["draw"][6], item["draw"][7], item["draw"][8], item["draw"][9],
                                 item["draw"][10], item["draw"][11], item["draw"][12], item["draw"][13],
                                 item["draw"][14], item["draw"][15], item["draw"][16], item["draw"][17],
                                 item["draw"][18], item["draw"][19],
                                 item["variants"]["heads-or-tails"]["heads"],
                                 item["variants"]["heads-or-tails"]["tails"],
                                 item["variants"]["heads-or-tails"]["result"]
                                 ])
        return self.data

    def __df_conversion(self, selected_data):
        return pd.DataFrame(data=selected_data, columns=[
            "game_number", "time", "ball-1", "ball-2", "ball-3", "ball-4", "ball-5", "ball-6", "ball-7",
            "ball-8",
            "ball-9", "ball-10", "ball-11", "ball-12", "ball-13", "ball-14", "ball-15", "ball-16", "ball-17",
            "ball-18",
            "ball-19", "ball-20", "heads", "tails", "winner"
        ])


app = HistoricalData(state="nsw", start_date=None, end_date=None)

print(app.recent_trends(look_back=5))
