import sys
import requests
import dateutil

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
        params = f"?jurisdiction={self._state_redirect}"+ additional_params
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
            print(f"Keno is not available in '{self._state}', this state uses ACT ")
            self._state = self._states[0]
            return self._state

        return self._state

    # noinspection PyDefaultArgument
    @staticmethod
    def _nested_dict(key=dict, additional_key=""):
        """
        Private Method:
            this function speeds up the look up times for nested dictionaries
        """
        return key.get(additional_key)

    def _transform_time(self, _datetime):
        '''
        Private Method:
            Transforms a date in a datetime object with the correct 
            time information, it also factors in daylight savings
            currently working on adding tz and dst to this function
        '''
        return dateutil.parser.isoparse(_datetime).strftime("%Y-%m-%d %H:%M:%S.%f")

    def _results_selection(self, initial_draw=1, total_draws=1, start_date="2021-02-08", page_size=1, page_number=1):
        """
        Private Method:

            initial_draw: the first game number
            total_draws: how many games you want to select
            start_date: which date you would like to get the games from
            page_size: how many games are on each page
            page_number: if you page size is less then the total draws the games will be split amount multiple pages

            Min adn Max values for a each parameter
            game_number: Min: 0, Max: 999

            Number of Games: Min:1, Max:200

            page_size: Min:1, Max:200

            page_number: Min:1, Max:100
        """

        url = self._get_url(end_point="/v2/info/history",
                            additional_params=f"&starting_game_number={initial_draw}&number_of_games={total_draws}&date={start_date}&page_size={page_size}&page_number={page_number}")
        return dict(requests.get(url).json())

    def game_status(self):
        """
        Public Method:
            Desc: Retrieves information about the current and next game
        """
        url = self._get_url(end_point="/v2/games/kds", additional_params="")
        retrieved = dict(requests.get(url).json())

        status_current = {
            "starting_time": self._transform_time(
                _datetime=self._nested_dict(key=retrieved.get("current"), additional_key="closed")),
            "game_number": self._nested_dict(key=retrieved.get("current"), additional_key="game-number")
        }

        status_selling = {
            "starting_time": self._transform_time(
                _datetime=self._nested_dict(key=retrieved.get("selling"), additional_key="closing")),
            "game_number": self._nested_dict(key=retrieved.get("selling"), additional_key="game-number")
        }

        status = {
            "state": self._state,
            "current_game": status_current,
            "next_game": status_selling
        }

        return status

    def live_draw(self):
        """
        Public Method:
            Desc: Retrieves data from the current draw
        """
        url = self._get_url(end_point="/v2/games/kds", additional_params="")
        retrieved = dict(requests.get(url).json().get("current"))
        status = str(retrieved.get("_type")).split(".")
        status_type = status[-1]

        live_draw = {
            "state": self._state,
            "game_number": retrieved.get("game-number"),
            "status": status_type,
            "started_at": self._transform_time(_datetime=retrieved.get("closed")),
            "is_finished": None,
            "draw_numbers": retrieved.get("draw"),
            "bonus": self._nested_dict(retrieved.get("variants"), additional_key="bonus"),
            "heads": self._nested_dict(retrieved.get("variants"), additional_key="heads-or-tails")["heads"],
            "tails": self._nested_dict(retrieved.get("variants"), additional_key="heads-or-tails")["tails"],
            "result": self._nested_dict(retrieved.get("variants"), additional_key="heads-or-tails")["result"]
        }

        if retrieved.get("_type") == "application/vnd.tabcorp.keno.game.complete":
            live_draw.update({"is_finished": bool(True)})

        else:
            live_draw.update({"is_finished": bool(False)})

        return live_draw

    def jackpot(self):
        """
        Public Method:
            Desc: Retrieves MegaMillions(leveraged) and Regular jackpots
        """
        url = self._get_url(
            end_point="/v2/info/jackpots", additional_params="")
        retrieved = dict(requests.get(url).json())["jackpots"]

        jackpot_regular = {
            "ten_spot": self._nested_dict(key=retrieved.get("ten-spot"), additional_key="base"),
            "nine_spot": self._nested_dict(key=retrieved.get("nine-spot"), additional_key="base"),
            "eight_spot": self._nested_dict(key=retrieved.get("eight-spot"), additional_key="base"),
            "seven_spot": self._nested_dict(key=retrieved.get("seven-spot"), additional_key="base")
        }

        jackpot_leveraged = {
            "ten_spot": self._nested_dict(key=retrieved.get("ten-spot-mm"), additional_key="base"),
            "nine_spot": self._nested_dict(key=retrieved.get("nine-spot-mm"), additional_key="base"),
            "eight_spot": self._nested_dict(key=retrieved.get("eight-spot-mm"), additional_key="base"),
            "seven_spot": self._nested_dict(key=retrieved.get("seven-spot-mm"), additional_key="base")
        }

        jackpot_combined = {
            "state": self._state,
            "regular": jackpot_regular,
            "leveraged": jackpot_leveraged
        }

        return jackpot_combined

    def hot_cold(self):
        """
        Public Method:
            Desc: Retrieves trending numbers which is defined the the official keno
        """
        url = self._get_url(
            end_point="/v2/info/hotCold", additional_params="")
        retrieved = dict(requests.get(url).json())

        hot_cold = {
            "cold": retrieved.get("coldNumbers"),
            "hot": retrieved.get("hotNumbers"),
            "last_updated": retrieved.get("secondsSinceLastReceived"),
            "state": self._state
        }
        return hot_cold
