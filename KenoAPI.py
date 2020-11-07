import datetime
import pandas as pd
import requests


class KenoAPI:
    def __init__(self, state="NT"):
        self.state = state
        self.states = ["ACT", 'NSW', "QLD", "VIC", "WA", "NT", "SA", "TAS"]
        self.base_url = "https://api-info-{}.keno.com.au".format(self.state_redirect.lower())

    def get_url(self, end_point="", additonal_parms=""):
        end_point = str(end_point)
        params = "?jurisdiction={}".format(self.state_redirect.upper()) + additonal_parms
        complete_url = self.base_url + end_point + params

        return str(complete_url)

    @property
    def state_redirect(self):
        if self.state.upper() == self.states[4]:
            print("Keno is not available in WA-Automaticly changed to NSW")
            self.state = self.states[2]
            return self.state

        if self.state.upper() == self.states[5] or self.state.upper() == self.states[6] or self.state.upper() == \
                self.states[7]:
            self.state = self.states[0]
            return self.state
        else:
            return self.state

    def nested_dict(self, key=dict(), additonal_key=""):
        return key.get(additonal_key)

    def transfrom_time(self, _datetime):
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

        if retrieved.get("_type") == "application/vnd.tabcorp.keno.game.complete":
            live_draw.update({"is_finished": bool(True)})

        else:
            live_draw.update({"is_finished": bool(False)})

        return live_draw

    def jackpot(self):
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
        url = self.get_url(end_point="/v2/info/hotCold", additonal_parms="")
        retrieved = dict(requests.get(url).json())

        hot_cold = {"cold": retrieved.get("coldNumbers"),
                    "hot": retrieved.get("hotNumbers"),
                    "last_updated": retrieved.get("secondsSinceLastReceived")}
        return hot_cold

    def trends(self):
        pass

    def historical_data(self, date="2020-10-30", start_game=600, number_of_games=20, max_per_page=20):
        # Max values = number_of_games=999, max_per_page=100
        url = self.get_url(end_point="/v2/info/history",
                           additonal_parms="&starting_game_number={}&number_of_games={}&date={}&page_size={}&page_number=1").format(
            start_game, number_of_games, date, max_per_page)

        data = []
        games = dict(requests.get(url).json())
        for item in games["items"]:
            data.insert(0, [item["game-number"], self.transfrom_time(_datetime=item["closed"]),
                            item["draw"][0], item["draw"][1], item["draw"][2], item["draw"][3], item["draw"][4],
                            item["draw"][5], item["draw"][6], item["draw"][7], item["draw"][8], item["draw"][9],
                            item["draw"][10], item["draw"][11], item["draw"][12], item["draw"][13],
                            item["draw"][14], item["draw"][15], item["draw"][16], item["draw"][17],
                            item["draw"][18], item["draw"][19],
                            item["variants"]["heads-or-tails"]["heads"],
                            item["variants"]["heads-or-tails"]["tails"],
                            item["variants"]["heads-or-tails"]["result"]
                            ])

        data.reverse()
        df = pd.DataFrame(data=data, columns=[
            "game_number", "time", "ball-1", "ball-2", "ball-3", "ball-4", "ball-5", "ball-6", "ball-7", "ball-8",
            "ball-9", "ball-10", "ball-11", "ball-12", "ball-13", "ball-14", "ball-15", "ball-16", "ball-17", "ball-18",
            "ball-19", "ball-20", "heads", "tails", "winner"
        ])
        return df
