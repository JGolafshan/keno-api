import datetime
import math
import sys
import requests
from flatten_dict import flatten
import cereja as cj


class KenoAPI:
    """
    Has all possible url end points, returns them as a dict.
    To learn more visit the wiki. https://github.com/JGolafshan/KenoAPI/wiki/Keno-API-Functions
    """

    def __init__(self, state="NT"):
        self._state = state.upper()
        self._states = ["ACT", "NSW", "QLD", "VIC", "WA", "NT", "SA", "TAS"]
        self._base_url = f"https://api-info-{self._state_redirect.lower()}.keno.com.au"

    def _get_url(self, end_point="", additional_params=""):
        """
        Private Method:
        concatenates the base URL and the endpoint together along with additional parameters
        """
        end_point = str(end_point)
        params = f"?jurisdiction={self._state_redirect}" + additional_params
        complete_url = self._base_url + end_point + params
        return complete_url

    @property
    def _state_redirect(self):
        """
        Private Method:
            Redirects user input
        """
        if not any(x == self._state for x in self._states):
            sys.exit(f"Check state input: '{self._state}' - is invalid")

        if self._state == self._states[4]:
            print("Keno is not available in WA-Automatically changed to NSW")
            self._state = self._states[2]
            return self._state

        redirect = [self._states[5], self._states[6], self._states[7]]

        if any(x == self._state for x in redirect):
            print(
                f"Keno is not available in '{self._state}', this state uses ACT ")
            self._state = self._states[0]
            return self._state

        return self._state

    @staticmethod
    def _transform_time(_datetime):
        """
        Private Method:
            Transforms a date in a datetime object with the correct
            time information, it also factors in daylight savings
            currently working on adding tz and dst to this function
        """
        try:
            datetime_datatype = datetime.datetime.strptime(_datetime, '%Y-%m-%d %H:%M:%S').replace(
                tzinfo=datetime.timezone.utc)
        except ValueError:
            datetime_datatype = datetime.datetime.strptime(_datetime, '%Y-%m-%d').replace(
                tzinfo=datetime.timezone.utc)
        return datetime_datatype

    @staticmethod
    def _transform_keno_time(_datetime):
        """
        Private Method:
            Transforms a date in a datetime object with the correct
            time information, it also factors in daylight savings
            currently working on adding tz and dst to this function
        """
        return datetime.datetime.strptime(_datetime, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=datetime.timezone.utc)

    @staticmethod
    def _calculate_time_difference(og_date, new_date):
        """
            Private Method:
            Calculates the difference in two dates
        """
        if new_date > og_date:
            time_difference = new_date - og_date
        else:
            time_difference = og_date - new_date

        return time_difference

    def _calculate_valid_game_number(self, date, draw_increase):
        """
        Private Method
        Finds the first draw that is valid on any given day
        returns the first valid game number
        """
        while True:
            results = self._get_results(initial_draw=draw_increase, total_draws=1,
                                        start_date=self._transform_time(date).date(), page_size=100, page_number=1)
            if len(results["items"]) == 0:
                draw_increase += 200
            else:
                return draw_increase

    @staticmethod
    def _json_to_dict(array):
        """
        returns a dict of all the information in a draw, restructured,
         make it easier to use analyzing packages e.g. pandas
        """
        return {
            "_type": array["_type"],
            "closed": array["closed"],
            "game_number": array["game-number"],
            "draw-1": array["draw"][0],
            "draw-2": array["draw"][1],
            "draw-3": array["draw"][2],
            "draw-4": array["draw"][3],
            "draw-5": array["draw"][4],
            "draw-6": array["draw"][5],
            "draw-7": array["draw"][6],
            "draw-8": array["draw"][7],
            "draw-9": array["draw"][8],
            "draw-10": array["draw"][9],
            "draw-11": array["draw"][10],
            "draw-12": array["draw"][11],
            "draw-13": array["draw"][12],
            "draw-14": array["draw"][13],
            "draw-15": array["draw"][14],
            "draw-16": array["draw"][15],
            "draw-17": array["draw"][16],
            "draw-18": array["draw"][17],
            "draw-19": array["draw"][18],
            "draw-20": array["draw"][19],
            "heads-or-tails-results": array["variants"]["heads-or-tails"]["result"],
            "heads-or-tails-heads": array["variants"]["heads-or-tails"]["heads"],
            "heads-or-tails-tails": array["variants"]["heads-or-tails"]["tails"],
            "roulette": array["variants"]["roulette"],
            "bonus": array["variants"]["bonus"]
        }

    def _draw_DA(self, array):
        draws = []
        for item in array["items"]:
            item_data = self._json_to_dict(item)
            draws.append(item_data)
        return draws

    def _get_results(self, initial_draw, total_draws, start_date, page_size, page_number):
        """
        Private Method:
            gets the results of all draws in from an initial draw number and starting date

            initial_draw: the first game number
            total_draws: how many games you want to select
            start_date: which date you would like to get the games from
            page_size: how many games are on each page
            page_number: if you page size is less than the total draws the games will be split amount multiple pages

            Min and Max values for a parameter
                game_number: Min: 0, Max: 999
                Number of Games: Min:1, Max:200
                page_size: Min:1, Max:200
                page_number: Min:1, Max:100
        """

        url = self._get_url(end_point="/v2/info/history",
                            additional_params=f"&starting_game_number={initial_draw}&number_of_games={total_draws}"
                                              f"&date={start_date}&page_size={page_size}&page_number={page_number}")

        with requests.get(url) as response:
            response.raise_for_status()
            retrieved = response.json()
        return retrieved

    def _all_draws_in_day(self, datetime_object):
        """
        Private Method
        returns all the draws in a given day
        """

        SOD = datetime_object.strftime("%Y-%m-%d") + " 00:00:00"
        EOF = (datetime_object + datetime.timedelta(days=1)).strftime("%Y-%m-%d") + " 00:00:00"

        first_game = self.get_specific_historical_game(SOD)
        last_game = self.get_specific_historical_game(EOF)
        last_game_date = self._transform_keno_time(last_game["items"][0]["closed"])
        draw_number = first_game["items"][0]["game-number"]
        data = []
        total_draws_custom = 100

        while last_game_date <= self._transform_keno_time(last_game["items"][0]["closed"]):
            result = self._get_results(initial_draw=draw_number, total_draws=total_draws_custom,
                                       start_date=datetime_object, page_size=100,
                                       page_number=1)

            try:
                last_game_date = self._transform_keno_time(result["items"][-1]["closed"])
                if int(result["items"][0]["game-number"]) + 100 > 999:
                    draw_number = int(result["items"][0]["game-number"]) + 100 - draw_number
                else:
                    draw_number += 100

                data.append(result)
            except IndexError:
                datetime_object = datetime_object + datetime.timedelta(days=1)

        return data

    def live_draw(self):
        """
        Public Method:
            Desc: Retrieves data from the current draw
        """
        url = self._get_url(end_point="/v2/games/kds", additional_params="")
        with requests.get(url) as response:
            response.raise_for_status()
            retrieved = response.json()
            return flatten(retrieved["current"], reducer="underscore")

    def next_draw(self):
        """
        Public Method:
            Desc: Retrieves information about the next game
        """
        url = self._get_url(end_point="/v2/games/kds", additional_params="")
        with requests.get(url) as response:
            response.raise_for_status()
            retrieved = response.json()
            # we move jackpots because it is just bloating the dict.
            del retrieved["selling"]["jackpots"]
            return flatten(retrieved["selling"], reducer="underscore")

    def jackpot(self):
        """
        Public Method:
            Desc: Retrieves MegaMillions(leveraged) and Regular jackpots
        """
        url = self._get_url(end_point="/v2/info/jackpots",
                            additional_params="")
        with requests.get(url) as response:
            response.raise_for_status()
            retrieved = response.json()
            retrieved = flatten(retrieved, reducer="underscore")

            # Delete the next value as we only want the current value.
            remove = [
                "jackpots_ten-spot-mm_next", "jackpots_ten-spot_next",
                "jackpots_nine-spot-mm_next", "jackpots_nine-spot_next",
                "jackpots_eight-spot-mm_next", "jackpots_eight-spot_next",
                "jackpots_seven-spot-mm_next", "jackpots_seven-spot_next",
                "jackpots_zero-spot-mm_base", "jackpots_zero-spot-mm_next",
                "jackpots_zero-spot_base", "jackpots_zero-spot_next"
            ]
            for i in remove:
                del retrieved[i]
            return retrieved

    def hot_cold(self):
        """
        Public Method:
            Desc: Retrieves trending numbers which is defined the official keno
        """
        url = self._get_url(end_point="/v2/info/hotCold", additional_params="")
        with requests.get(url) as response:
            response.raise_for_status()
            retrieved = response.json()
            return retrieved

    def trends(self):
        """
        Public Method:
            Desc: Retrieves the most recent 8 games from the state.
        """
        url = self._get_url(end_point="/v2/info/trends", additional_params="")
        with requests.get(url) as response:
            response.raise_for_status()
            retrieved = response.json()
            return retrieved

    def get_specific_historical_game(self, date):
        """
        gets a specific game given a datetime in the format (YEAR-MONTH-DAY HOUR:MINUTE:SECOND) with a tolerance of
        1 minutes
        returns the json data related to that game
        """
        difference = 999
        results = 0
        draw_increase = self._calculate_valid_game_number(date, draw_increase=0)
        date_object = self._transform_time(date).date()
        last_game_difference = 0

        while difference > 1 * 60:
            try:
                results = self._get_results(initial_draw=draw_increase, total_draws=1,
                                            start_date=date_object, page_size=1, page_number=1)
                redraw_date = self._transform_keno_time(results["items"][0]["closed"])

            except IndexError:
                results = self._get_results(initial_draw=draw_increase, total_draws=1,
                                            start_date=date_object - datetime.timedelta(days=1), page_size=1,
                                            page_number=1)
                redraw_date = self._transform_keno_time(results["items"][0]["closed"])

            # Get the number of games to rebalanced
            difference = self._calculate_time_difference(self._transform_time(date), redraw_date)
            difference = difference.seconds
            game_difference = math.floor(difference / 213)

            if game_difference == last_game_difference:
                break
            else:
                last_game_difference = game_difference

            if draw_increase - game_difference < 0:
                draw_increase = 1000 + draw_increase - game_difference
            else:
                draw_increase -= game_difference
        return results

    def historical(self, start_date, end_date):
        """
        Public Method:
            Desc: Gets all the draws between two dates
        """
        start_date = self._transform_time(start_date)
        end_date = self._transform_time(end_date)
        games = []

        while (end_date - start_date).days > 0:
            start_date = start_date + datetime.timedelta(days=1)

            draws = self._all_draws_in_day(start_date.date())
            games.append(draws)

        single_games = []
        for game in games:
            for sub_game in game:
                single_games.append(self._draw_DA(sub_game))

        flatten_games = cj.flatten(single_games)

        # Remove draws duplicate draws
        unique_draws = []
        for item in flatten_games:
            if item not in unique_draws:
                unique_draws.append(item)

        return unique_draws
