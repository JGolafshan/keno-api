import sys
import requests
import dateutil

class KenoBase:
    '''
    Methods that are to be inherented to 'KenoAPI' class.
    Do not use this class, instead use 'KenoAPI''.
    '''

    def __init__(self, state="NT"):
        self.__state__ = state.upper()
        self.__states__ = ["ACT", "NSW", "QLD", "VIC", "WA", "NT", "SA", "TAS"]
        self.__base_url__ = "https://api-info-{}.keno.com.au".format(self.__state_redirect__.lower())

    def __get_url__(self, end_point="", additional_params=""):
        '''
        Private Method:
        concatenates the base URL and the endpoint together along with additional parameters
        '''
        end_point = str(end_point)
        params = "?jurisdiction={}".format(self.__state_redirect__) + additional_params
        complete_url = self.__base_url__ + end_point + params

        return str(complete_url)

    @property
    def __state_redirect__(self):
        '''
        Private Method:
        redirects user input
        '''
        if any(x == self.__state__ for x in self.__states__) is False:
            return sys.exit(str("Check state input: '{}' - is invalid").format(self.__state__))

        if self.__state__ == self.__states__[4]:
            print("Keno is not available in WA-Automatically changed to NSW")
            self.__state__ = self.__states__[2]
            return self.__state__

        redirect = [self.__states__[5], self.__states__[6], self.__states__[7]]

        if any(x == self.__state__ for x in redirect) is True:
            print(str("Keno is not available in '{}', this state uses ACT ").format(self.__state__))
            self.__state__ = self.__states__[0]
            return self.__state__

        return self.__state__

    # noinspection PyDefaultArgument
    @staticmethod
    def __nested_dict__(key=dict, additional_key=""):
        '''
        Private Method:    
        this function speeds up the look up times for nested dictionaries
        '''
        return key.get(additional_key)

    def __transform_time__(self, _datetime):
        pass
        '''
        Private Method:
        Transfroms a date in a datetime object with the correct 
        time information, it also factors in daylight savings
        
        currently working on adding tz and dst to this function
        '''
        return dateutil.parser.isoparse(_datetime).strftime("%Y-%m-%d %H:%M:%S.%f")

    def __results_selection__(self, initial_draw=1, total_draws=1, start_date="2021-02-08", page_size=1, page_number=1):
        '''
        Private Method:
            
            initial_draw: the first game number
            total_draws: how many games you want to select
            start_date: which date you would like to get the games from
            page_size: how many games are on each page
            page_number: if you page size is less then the total draws the games will be split amont muliple pages
        
            Min adn Max values for a each parameter 
            game_number: Min: 0, Max: 999
            
            Number of Games: Min:1, Max:200
            
            page_size: Min:1, Max:200
            
            page_number: Min:1, Max:100
        '''

        url = self.__get_url__(end_point="/v2/info/history", additional_params="&starting_game_number={}&number_of_games={}&date={}&page_size={}&page_number={}").format(
            initial_draw, total_draws, start_date, page_size, page_number)
        return dict(requests.get(url).json())

class KenoAPI(KenoBase):
    '''
    Has all possible url end points.
    To learn more vist the wiki. https://github.com/JGolafshan/KenoAPI/wiki/Keno-API-Functions
    '''

    def __init__(self, state):
        super().__init__(state)

    def game_status(self):
        '''
        Public Method:
            Desc: Retrieves information about the current and next game
        '''
        url = self.__get_url__(end_point="/v2/games/kds", additional_params="")
        retrieved = dict(requests.get(url).json())

        status_current = {
            "starting_time": self.__transform_time__(_datetime=self.__nested_dict__(key=retrieved.get("current"), additional_key="closed")),
            "game_number": self.__nested_dict__(key=retrieved.get("current"), additional_key="game-number")
        }

        status_selling = {
            "starting_time": self.__transform_time__(_datetime=self.__nested_dict__(key=retrieved.get("selling"), additional_key="closing")),
            "game_number": self.__nested_dict__(key=retrieved.get("selling"), additional_key="game-number")
        }

        status = {
            "state": self.__state__,
            "current_game": status_current,
            "next_game": status_selling
        }

        return status

    def live_draw(self):
        '''
        Public Method:
            Desc: Retrieves data from the current draw
        '''
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
        '''
        Public Method:
            Desc: Retrieves MegaMillions(leveraged) and Regular jackpots
        '''
        url = self.__get_url__(
            end_point="/v2/info/jackpots", additional_params="")
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
        '''
        Public Method:
            Desc: Retrieves trending numbers which is defined the the offical keno
        '''
        url = self.__get_url__(
            end_point="/v2/info/hotCold", additional_params="")
        retrieved = dict(requests.get(url).json())

        hot_cold = {
            "cold": retrieved.get("coldNumbers"),
            "hot": retrieved.get("hotNumbers"),
            "last_updated": retrieved.get("secondsSinceLastReceived"),
            "state": self.__state__
        }
        return hot_cold

