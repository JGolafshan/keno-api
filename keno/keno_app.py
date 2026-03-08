#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Date: 03/08/2025
Author: Joshua David Golafshan
"""

import math
import logging
import datetime
import requests
import cereja as cj
from flatten_dict import flatten
from keno.utils import _transform_time, _calculate_time_difference, _transform_keno_time

logger = logging.getLogger(__name__)


class KenoAPI:
    """
    Has all possible url end points, returns them as a dict.
    To learn more, visit the wiki. https://github.com/JGolafshan/KenoAPI/wiki/Keno-API-Functions
    """

    def __init__(self, state: str = "NT"):
        self._state = state.upper()
        self.session = requests.Session()
        self._base_url = f"https://api-info-{self._state_redirect.lower()}.keno.com.au"

    def _get_url(self, end_point: str = "", additional_params: str = ""):
        """
        Private Method:
        concatenates the base URL and the endpoint together along with additional parameters
        """
        end_point = str(end_point)
        params = f"?jurisdiction={self._state_redirect}" + additional_params
        complete_url = self._base_url + end_point + params
        return complete_url

    def _request(self, endpoint: str, params: str = ""):
        """
        Private Method:
        returns the JSON data from the endpoint
        """

        url = self._get_url(endpoint, params)
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    @property
    def _state_redirect(self):
        """
        Private Method:
            Redirects user input
        """
        states = {"ACT", "NSW", "QLD", "VIC", "WA", "NT", "SA", "TAS"}

        if self._state not in states:
            raise ValueError(f"Invalid state: {self._state}")

        if self._state == "WA":
            logger.warning("Keno is not available in WA. Automatically using NSW.")
            return "NSW"

        if self._state in {"NT", "SA", "TAS"}:
            logger.warning(f"Keno is not available in {self._state}. Using ACT.")
            return "ACT"

        return self._state

    def _calculate_valid_game_number(self, date: str, draw_increase: int):
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
    def _json_to_dict(array: dict):
        """
        returns a dict of all the information in a draw, restructured,
        make it easier to use analyzing packages e.g. pandas
        """
        draws = {f"draw-{i + 1}": num for i, num in enumerate(array["draw"])}

        return {
            "_type": array["_type"],
            "closed": array["closed"],
            "game_number": array["game-number"],
            **draws,
            "heads-or-tails-results": array["variants"]["heads-or-tails"]["result"],
            "heads-or-tails-heads": array["variants"]["heads-or-tails"]["heads"],
            "heads-or-tails-tails": array["variants"]["heads-or-tails"]["tails"],
            "roulette": array["variants"]["roulette"],
            "bonus": array["variants"]["bonus"]
        }

    def _draw_DA(self, array: dict):
        draws = []
        for item in array["items"]:
            item_data = self._json_to_dict(item)
            draws.append(item_data)
        return draws

    def _get_results(self, initial_draw: int, total_draws: int, start_date: str, page_size: int, page_number: int):
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
        data = self._request(
            endpoint="/v2/info/history",
            params=f"&starting_game_number={initial_draw}&number_of_games={total_draws}"
                   f"&date={start_date}&page_size={page_size}&page_number={page_number}"
        )

        return data

    def _all_draws_in_day(self, datetime_object):
        """
        Private Method
        returns all the draws in a given day
        """

        SOD = datetime_object.strftime("%Y-%m-%d") + " 00:00:00"
        EOF = (datetime_object + datetime.timedelta(days=1)).strftime("%Y-%m-%d") + " 00:00:00"

        first_game = self.get_specific_historical_game(SOD)
        last_game = self.get_specific_historical_game(EOF)
        last_game_date = _transform_keno_time(last_game["items"][0]["closed"])
        draw_number = first_game["items"][0]["game-number"]
        data = []
        total_draws_custom = 100

        while last_game_date <= _transform_keno_time(last_game["items"][0]["closed"]):
            result = self._get_results(initial_draw=draw_number, total_draws=total_draws_custom,
                                       start_date=datetime_object, page_size=100,
                                       page_number=1)

            try:
                last_game_date = _transform_keno_time(result["items"][-1]["closed"])
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

        data = self._request(endpoint="/v2/games/kds", params="")
        return flatten(data["current"], reducer="underscore")

    def next_draw(self):
        """
        Public Method:
            Desc: Retrieves information about the next game
        """
        data = self._request(endpoint="/v2/games/kds", params="")

        del data["selling"]["jackpots"]
        return data["selling"]

    def jackpot(self):
        """
        Public Method:
            Desc: Retrieves MegaMillions(leveraged) and Regular jackpots
        """

        data = self._request(endpoint="/v2/info/jackpots", params="")
        return data["jackpots"]

    def hot_cold(self):
        """
        Public Method:
            Desc: Retrieves trending numbers which is defined the official keno
        """
        data = self._request(endpoint="/v2/info/hotCold", params="")
        for key in ["_type", "_href"]:
            data.pop(key, None)

        return data

    def trends(self):
        """
        Public Method:
            Desc: Retrieves the most recent 8 games from the state.
        """
        data = self._request(endpoint="/v2/info/trends", params="")
        return data

    def get_specific_historical_game(self, date: str):
        """
        gets a specific game given a datetime in the format (YEAR-MONTH-DAY HOUR:MINUTE:SECOND) with a tolerance of
        1 minutes
        returns the json data related to that game
        """
        difference = 999
        results = 0
        draw_increase = self._calculate_valid_game_number(date, draw_increase=0)
        date_object = _transform_time(date).date()
        last_game_difference = 0

        while difference > 1 * 60:
            try:
                results = self._get_results(initial_draw=draw_increase, total_draws=1,
                                            start_date=date_object, page_size=1, page_number=1)
                redraw_date = _transform_keno_time(results["items"][0]["closed"])

            except IndexError:
                results = self._get_results(initial_draw=draw_increase, total_draws=1,
                                            start_date=date_object - datetime.timedelta(days=1), page_size=1,
                                            page_number=1)
                redraw_date = _transform_keno_time(results["items"][0]["closed"])

            # Get the number of games to rebalanced
            difference = _calculate_time_difference(_transform_time(date), redraw_date)
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

    def historical(self, start_date: str, end_date: str):
        """
        Public Method:
            Desc: Gets all the draws between two dates
        """
        start_date = _transform_time(start_date)
        end_date = _transform_time(end_date)
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
