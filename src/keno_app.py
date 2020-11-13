import datetime
import pandas as pd
import requests
import math


class KenoAPI:
    def __init__(self, state="NT"):
        self.state = state.upper()
        self.states = ["ACT", 'NSW', "QLD", "VIC", "WA", "NT", "SA", "TAS"]
        self.base_url = "https://api-info-{}.keno.com.au".format(self.state_redirect.lower())

    def get_url(self, end_point="", additonal_parms=""):
        end_point = str(end_point)
        params = "?jurisdiction={}".format(self.state_redirect) + additonal_parms
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
    def nested_dict(key={}, additonal_key=""):
        # Simple function to make getting/setting values, efficient and easier to read.
        return key.get(additonal_key)

    @staticmethod
    def transfrom_time(_datetime):
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

    def game_status(self):
        # Gets current and next game status and returns them as a nested dict.
        url = self.get_url(end_point="/v2/games/kds", additonal_parms="")
        retrieved = dict(requests.get(url).json())

        status_current = {
            "starting_time": self.transfrom_time(
                _datetime=self.nested_dict(key=retrieved.get("current"), additonal_key="closed")),
            "game_number": self.nested_dict(key=retrieved.get("current"), additonal_key="game-number")
        }

        status_selling = {
            "starting_time": self.transfrom_time(
                _datetime=self.nested_dict(key=retrieved.get("selling"), additonal_key="closing")),
            "game_number": self.nested_dict(key=retrieved.get("selling"), additonal_key="game-number")
        }

        status = {
            "current_game": status_current,
            "next_game": status_selling
        }

        return status

    def live_draw(self):
        # Gets current live game, returned as dict.
        url = self.get_url(end_point="/v2/games/kds", additonal_parms="")
        retrieved = dict(requests.get(url).json().get("current"))
        status = str(retrieved.get("_type")).split(".")
        status_type = status[-1]

        live_draw = {
            "game_number": retrieved.get("game-number"),
            "status": status_type,
            "started_at": self.transfrom_time(_datetime=retrieved.get("closed")),
            "is_finished": None,
            "draw_numbers": retrieved.get("draw"),
            "bonus": self.nested_dict(retrieved.get("variants"), additonal_key="bonus"),
            "heads": self.nested_dict(retrieved.get("variants"), additonal_key="heads-or-tails")["heads"],
            "tails": self.nested_dict(retrieved.get("variants"), additonal_key="heads-or-tails")["tails"],
            "result": self.nested_dict(retrieved.get("variants"), additonal_key="heads-or-tails")["result"]
        }

        if retrieved.get("_type") == "application/vnd.tabcorp.src.game.complete":
            live_draw.update({"is_finished": bool(True)})

        else:
            live_draw.update({"is_finished": bool(False)})

        return live_draw

    def jackpot(self):
        # returns a nested dict. for jackpots
        url = self.get_url(end_point="/v2/info/jackpots", additonal_parms="")
        retrieved = dict(requests.get(url).json())["jackpots"]

        jackpot_regular = {
            "ten_spot": self.nested_dict(key=retrieved.get("ten-spot"), additonal_key="base"),
            "nine_spot": self.nested_dict(key=retrieved.get("nine-spot"), additonal_key="base"),
            "eight_spot": self.nested_dict(key=retrieved.get("eight-spot"), additonal_key="base"),
            "seven_spot": self.nested_dict(key=retrieved.get("seven-spot"), additonal_key="base")
        }

        jackpot_leveraged = {
            "ten_spot": self.nested_dict(key=retrieved.get("ten-spot-mm"), additonal_key="base"),
            "nine_spot": self.nested_dict(key=retrieved.get("nine-spot-mm"), additonal_key="base"),
            "eight_spot": self.nested_dict(key=retrieved.get("eight-spot-mm"), additonal_key="base"),
            "seven_spot": self.nested_dict(key=retrieved.get("seven-spot-mm"), additonal_key="base")
        }

        jackpot_combined = {
            "regular": jackpot_regular,
            "leveraged": jackpot_leveraged
        }

        return jackpot_combined

    def hot_cold(self):
        # returns a dict. with hot and cold numbers as well as then it was last updated
        url = self.get_url(end_point="/v2/info/hotCold", additonal_parms="")
        retrieved = dict(requests.get(url).json())

        hot_cold = {"cold": retrieved.get("coldNumbers"),
                    "hot": retrieved.get("hotNumbers"),
                    "last_updated": retrieved.get("secondsSinceLastReceived")}
        return hot_cold

    def trends(self, total_games):
        date = datetime.date.today().strftime("%Y-%m-%d")
        trends = self.historical_data(date=date,
                                      start_game=self.game_status().get("current_game").get(
                                          "game_number") - total_games,
                                      number_of_games=total_games, max_per_page=100)

        return trends

    def historical_data_new(self, start_date, end_date):

        def get_daily_info(increase=int(1)):

            def daily_date(_day=increase):
                og_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
                modified_date = og_date + datetime.timedelta(days=_day)
                return modified_date

            def fish_for_number():
                number_list = [0, 100, 200, 300, 400, 500, 600, 700, 800, 900, 999]
                for number in number_list:
                    url = self.get_url(end_point="/v2/info/history",
                                       additonal_parms="&starting_game_number={}&number_of_games={}&date={}&page_size={}&page_number=1").format(
                        number, 1, daily_date(), 1)
                    retrieved = dict(requests.get(url).json())["items"]

                    if len(retrieved) is not 0:
                        return {
                            "game_number": retrieved[0]["game-number"],
                            "closed_time": self.transfrom_time(_datetime=retrieved[0]["closed"])
                        }

            def calculate_first_game():
                first_date = datetime.datetime.strptime(fish_for_number().get("closed_time"), "%Y-%m-%d %H:%M:%S.%f")
                last_date = datetime.datetime(daily_date(increase).year, daily_date(increase).month,
                                              daily_date(increase).day, 12)

                _games = (last_date - first_date).seconds
                _games = int(round(_games / 160, 0))
                return _games

            def calculate_days():
                start = datetime.datetime.strptime(end_date, "%Y-%m-%d")
                end = datetime.datetime.strptime(start_date, "%Y-%m-%d")
                time_delta = abs(end - start).days
                return time_delta

            def calculate_games():
                time = (24 * 60) * 60
                return int(math.ceil(time / 160))

            dict_ = {
                "search_date": daily_date(_day=increase).strftime("%Y-%m-%d"),
                "first_number": fish_for_number().get("game_number"),
                "first_number_date": fish_for_number().get("closed_time"),
                "increase_needed": calculate_first_game(),
                "total_days": calculate_days(),
                "total_games": calculate_games()
            }

            dict_.update({"start_game": int(dict_["first_number"] + dict_["increase_needed"])})
            dict_.update({"total_pages": int(math.ceil(dict_["total_games"] / 100))})
            return dict_

        games = 100
        per_page = 100
        data = []
        for day in range(get_daily_info().get("total_days")):
            info = get_daily_info(increase=day)

            for page in range(1, info.get("total_pages")):
                url_ = self.get_url(end_point="/v2/info/history",
                                    additonal_parms="&starting_game_number={}&number_of_games={}&date={}&page_size={}&page_number={}").format(
                    info.get("start_game"), games, info.get("search_date"), per_page, page)
                games_ = dict(requests.get(url_).json())
                for item in games_["items"]:
                    data.insert(0, [item["game-number"], item["closed"],
                                    item["draw"][0], item["draw"][1], item["draw"][2], item["draw"][3], item["draw"][4],
                                    item["draw"][5], item["draw"][6], item["draw"][7], item["draw"][8], item["draw"][9],
                                    item["draw"][10], item["draw"][11], item["draw"][12], item["draw"][13],
                                    item["draw"][14], item["draw"][15], item["draw"][16], item["draw"][17],
                                    item["draw"][18], item["draw"][19],
                                    item["variants"]["heads-or-tails"]["heads"],
                                    item["variants"]["heads-or-tails"]["tails"],
                                    item["variants"]["heads-or-tails"]["result"]
                                    ])

        df = pd.DataFrame(data=data, columns=[
            "game_number", "time", "ball-1", "ball-2", "ball-3", "ball-4", "ball-5", "ball-6", "ball-7",
            "ball-8",
            "ball-9", "ball-10", "ball-11", "ball-12", "ball-13", "ball-14", "ball-15", "ball-16", "ball-17",
            "ball-18",
            "ball-19", "ball-20", "heads", "tails", "winner"
        ])
        return df
