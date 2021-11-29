import sys
import requests
from flatten_dict import flatten


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

    def _transform_time(self, _datetime):
        """
        Private Method:
            Transforms a date in a datetime object with the correct
            time information, it also factors in daylight savings
            currently working on adding tz and dst to this function
        """
        return None

    def _results_selection(self, initial_draw=1, total_draws=1,
                           start_date="2021-02-08", page_size=1, page_number=1):
        """
        Private Method:

            initial_draw: the first game number
            total_draws: how many games you want to select
            start_date: which date you would like to get the games from
            page_size: how many games are on each page
            page_number: if you page size is less then the total draws the
                        games will be split amount multiple pages

            Min adn Max values for a each parameter
            game_number: Min: 0, Max: 999

            Number of Games: Min:1, Max:200

            page_size: Min:1, Max:200

            page_number: Min:1, Max:100
        """

        url = self._get_url(end_point="/v2/info/history",
                            additional_params=f"""&starting_game_number={initial_draw}&
                            number_of_games={total_draws}&date={start_date}&
                            page_size={page_size}&page_number={page_number}""")
        with requests.get(url) as response:
            response.raise_for_status()
            retrieved = response.json()
            return retrieved

    def game_status(self):
        """
        Public Method:
            Desc: Retrieves information about the current and next game
        """
        url = self._get_url(end_point="/v2/games/kds", additional_params="")
        with requests.get(url) as response:
            response.raise_for_status()
            retrieved = response.json()
            # we move jackpots because it is just bloating the dict.
            del retrieved["selling"]["jackpots"]
            return flatten(retrieved, reducer="underscore")

    def live_draw(self):
        """
        Public Method:
            Desc: Retrieves data from the current draw
        """
        url = self._get_url(end_point="/v2/games/kds", additional_params="")
        with requests.get(url) as response:
            response.raise_for_status()
            retrieved = response.json()
            # we move jackpots because it is just bloating the dict.
            del retrieved["selling"]["jackpots"]
            return flatten(retrieved, reducer="underscore")

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

            # Delete the the next value as we only want the current value.
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
            Desc: Retrieves trending numbers which is defined the the official keno
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

    def historical(self, start, end):
        pass
