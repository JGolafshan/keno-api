from pprint import pprint
import requests
import time
import pandas as pd


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
        if self.state == self.states[4]:
            print("Keno is not available in WA-Automaticly changed to NSW")
            self.state = self.states[2]
            return self.state

        if self.state.upper() == self.states[5] or self.states[6] or self.states[7]:
            self.state = self.states[0]
            return self.state
        else:
            return self.state

    @property
    def transfrom_time(self):
        pass

    def game_status(self):
        url = self.get_url(end_point="/v2/games/kds", additonal_parms="")
        retrieved = dict(requests.get(url).json())

        status_current = {"time": retrieved.get("current")["closed"],
                          "game_number": retrieved.get("current")["game-number"],
                          "total_heads": retrieved.get("current")["variants"]["heads-or-tails"]["heads"],
                          "total_tails": retrieved.get("current")["variants"]["heads-or-tails"]["tails"],
                          "result": retrieved.get("current")["variants"]["heads-or-tails"]["result"]
                          }

        if retrieved.get("current")["_type"] == "application/vnd.tabcorp.keno.game.drawing":
            status_current.update({"complete_at": retrieved.get("current")["receivedDrawingAt"]})

        if retrieved.get("current")["_type"] == "application/vnd.tabcorp.keno.game.complete":
            status_current.update({"complete_at": retrieved.get("current")["receivedCompleteAt"]})

        status_selling = {"time": retrieved.get("selling")["closing"],
                          "game_number": retrieved.get("selling")["game-number"],
                          "time_opened": retrieved.get("selling")["opened"],
                          "selling_at": retrieved.get("selling")["receivedSellingAt"]
                          }

        status = {"current_game": status_current,
                  "next_game": status_selling}
        return status

    def jackpot(self):
        url = self.get_url(end_point="/v2/info/jackpots", additonal_parms="")
        retrieved = dict(requests.get(url).json())

        jackpot_list = {"ten_spot": retrieved.get("jackpots")["ten-spot"]["base"],
                        "nine_spot": retrieved.get("jackpots")["nine-spot"]["base"],
                        "eight_spot": retrieved.get("jackpots")["eight-spot"]["base"],
                        "seven_spot": retrieved.get("jackpots")["seven-spot"]["base"],
                        "ten_spot_mm": retrieved.get("jackpots")["ten-spot-mm"]["base"],
                        "nine_spot_mm": retrieved.get("jackpots")["nine-spot-mm"]["base"],
                        "eight_spot_mm": retrieved.get("jackpots")["eight-spot-mm"]["base"],
                        "seven_spot_mm": retrieved.get("jackpots")["seven-spot-mm"]["base"]
                        }
        return jackpot_list

    def hot_cold(self):
        url = self.get_url(end_point="/v2/info/hotCold", additonal_parms="")
        retrieved = dict(requests.get(url).json())

        hot_cold = {"cold_numbers": retrieved.get("coldNumbers"),
                    "hot_numbers": retrieved.get("hotNumbers"),
                    "last_updated": retrieved.get("secondsSinceLastReceived")}
        return hot_cold

    def trends(self):
        pass

    def historical_data(self, date="2020-10-30", start_game=900, number_of_games=20, max_per_page=20):
        # Max values = number_of_games=999, max_per_page=100
        url = self.get_url(end_point="/v2/info/history",
                           additonal_parms="&starting_game_number={}&number_of_games={}&date={}&page_size={}&page_number=1").format(
            start_game, number_of_games, date, max_per_page)

        data = []
        games = dict(requests.get(url).json())
        for item in games["items"]:
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

        data.reverse()
        df = pd.DataFrame(data=data, columns=["game_number", "time",
                                              "ball-1", "ball-2", "ball-3", "ball-4", "ball-5", "ball-6", "ball-7",
                                              "ball-8", "ball-9", "ball-10", "ball-11", "ball-12", "ball-13",
                                              "ball-14", "ball-15", "ball-16", "ball-17", "ball-18", "ball-19",
                                              "ball-20",
                                              "heads", "tails", "winner"
                                              ])
        return df


keno = KenoAPI()
pprint(keno.historical_data())
