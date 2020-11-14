import datetime
import pandas as pd
import requests
import math


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
            print("Keno is not available in WA-Automaticly changed to NSW")
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

        if retrieved.get("_type") == "application/vnd.tabcorp.src.game.complete":
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

    # ------------- Callable Methods -------------

    def recent_trends(self, total_games):
        pass

    def historical_data(self):
        for day in range(self.__calculate_days()):
            print(self.__increment_date(increase=day))

    # ------------- Private Methods -------------

    def __increment_date(self, increase):
        og_date = datetime.datetime.strptime(self.start_date, "%Y-%m-%d")
        modified_date = og_date + datetime.timedelta(days=increase)
        return modified_date

    def __fish_game_number(self):
        pass

    def __calculate_first_game(self):
        pass

    def __calculate_days(self):
        start = datetime.datetime.strptime(self.end_date, "%Y-%m-%d")
        end = datetime.datetime.strptime(self.start_date, "%Y-%m-%d")
        time_delta = abs(end - start).days
        return time_delta

    def __calculate_games(self):
        # apply more programmatic style to getting the time difference between games
        time = (24 * 60) * 60
        return int(math.ceil(time / 160))

    def __df_conversion(self):
        pass


keno = HistoricalData(state="nsw", start_date="2020-03-20", end_date="2020-04-20")

print(keno.historical_data())
