#!/usr/bin/python3
import re
from os import system
import argparse
from requests import Session

# regex-выражения для поиска строк
ANIME_FIND_PATTERN = re.compile(r'<a href="(https://animego\.org/anime/.*)" title="(.*?)">')  # url + title
COUNT_SERIES_PATTERN = re.compile(r'"col-6 col-sm-8 mb-1">(\d+)')  # count series
WATCH_ID_PATTERN = re.compile(r'data-watched-id="(\d+)"')  # episodes ids
DUB_NAME_PATTERN = re.compile(
    r'data-dubbing="(\d+)"><span class="video-player-toggle-item-name text-underline-hover">\s+(.*)')  # dubs
PLAYER_PATTERN = re.compile(r'data-player="(.*)"\s+data-provider="\d+"\s+data-provide-dubbing="(\d+)"')  # video players

EP_PATTERN = re.compile(r'data-id="(\d+)"')  # episodes id
EP_NAME_PATTERN = re.compile(r'data-episode-title="(.*)"')  # episode name

ANIBOOM_PATTERN = re.compile(r"hls:\{src:(.*\.m3u8)")  # aniboom video pattern
# ongoing ep title, ep_num, dub_name
ONGOING_DATA = re.compile(
    r'600">(.*?)</span></span></div><div class="ml-3 text-right"><div class="font-weight-600 text-truncate">(\d+) серия</div><div class="text-gray-dark-6">(\(.*?\))</div>')
# ongoing url anime
ONGOING_URL = re.compile(r'onclick="location\.href=\'(.*?)\'"')

# мобильный юзер-агент обходит блокировку, только это секрет, никому не рассказывайте!
USER_AGENT = {"user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, "
                            "like Gecko) Chrome/94.0.4606.114 Mobile Safari/537.36",
              "x-requested-with": "XMLHttpRequest"}

parser = argparse.ArgumentParser()
parser.add_argument("-p", "--proxy", dest="PROXY", type=str, default="", help="add proxy")
parser.add_argument("-v", "--videoplayer", dest="PLAYER", type=str, default="mpv", help="edit videoplayer. default mpv")
parser.add_argument("-hc", "--headers-command", dest="OS_HEADERS_COMMAND", type=str, default="--http-header-fields",
                    help="edit headers argument name. default --http-header-fields")

args = parser.parse_args()
PROXY = args.PROXY
PLAYER = args.PLAYER
OS_HEADERS_COMMAND = args.OS_HEADERS_COMMAND


class Anime:
    SEARCH_URL = "https://animego.org/search/anime"

    def __init__(self):
        self.session = Session()
        self.session.headers.update(USER_AGENT)
        self.anime_results = []
        self.series_count = 0
        self._episodes = []
        self.anime_url = ""
        self.__anime_id = ""
        self._videos = []
        self._ongoings = []

    def search(self, pattern: str):
        self.anime_results.clear()
        r = self.session.get("https://animego.org/search/anime", params={"q": pattern})
        anime_urls = re.findall(ANIME_FIND_PATTERN, r.text)
        self.anime_results = anime_urls
        return self.anime_results

    def get_ongoing(self):
        self._ongoings.clear()
        r = self.session.get("https://animego.org/")
        ongoing_data = [list(i) for i in re.findall(ONGOING_DATA, r.text)]
        ongoing_urls = ["https://animego.org" + i for i in re.findall(ONGOING_URL, r.text)]
        [i[0].append(i[-1]) for i in zip(ongoing_data, ongoing_urls)]

        # сортировка онгоингов по названию и номеру серии
        for data in ongoing_data:
            if len(self._ongoings) > 0 and data[0] in [i[0] for i in self._ongoings]:
                for data2 in self._ongoings:
                    if data2[0] == data[0] and int(data2[1]) == int(data2[1]):
                        data2[2] += ", " + data[2]
            else:
                self._ongoings.append(data.copy())
        self._ongoings.sort(key=lambda v: v[0])  # сортировка по алфавиту
        self.anime_results = [i[-1] for i in self._ongoings]
        return self._ongoings

    @staticmethod
    def is_unsupported_player(player: str):
        """:return False if player is kodik"""
        return not ("kodik" in player or "anivod" in player)

    def parse_episodes_count(self, index_choose: int):
        """подсчёт числа эпизодов"""
        if isinstance(self.anime_results[index_choose], tuple):
            self.anime_url = self.anime_results[index_choose][0]
        else:
            self.anime_url = self.anime_results[index_choose]
        self.__anime_id = self.anime_url.split("-")[-1]
        r = self.session.get(self.anime_url)
        self.series_count = re.findall(COUNT_SERIES_PATTERN, r.text)
        if len(self.series_count) > 0:
            return int(self.series_count[0])
        else:
            self.series_count = 1
            return self.series_count

    def parse_players(self, episode_num: int, series_id: str):
        r = self.session.get("https://animego.org/anime/series", params={"dubbing": 2, "provider": 24,
                                                                         "episode": episode_num,
                                                                         "id": series_id}).json()["content"]
        dubs = re.findall(DUB_NAME_PATTERN, r)
        players = re.findall(PLAYER_PATTERN, r)
        results = []
        for dub in dubs:
            result = {
                "dub": dub[1],
                "player":
                    [p[0].replace("amp;", "") for p in players if p[1] == dub[0] and self.is_unsupported_player(p[0])]
            }
            if len(result["player"]) > 0:
                results.append(result)
        self._videos = results

    def parse_series(self):
        """Поиск названий и id эпизодов"""
        r = self.session.get(f"https://animego.org/anime/{self.__anime_id}/player?_allow=true").json()["content"]
        #  доступные эпизоды
        ep_ids = re.findall(EP_PATTERN, r)
        ep_titles = re.findall(EP_NAME_PATTERN, r)
        self._episodes = list(zip(ep_ids, ep_titles))
        return self._episodes

    def choose_episode(self, index_ep: int):
        ep_id = self._episodes[index_ep][0]
        self.parse_players(index_ep, ep_id)
        return self._videos

    def play(self, player: str):
        if "sibnet" in player:
            system(f"{PLAYER} {'https:' + player}")
        elif "aniboom" in player:
            # заголовки обязательно должны начинаться с заглавной буквы для удачного запроса
            r = self.session.get("https:" + player,
                                 headers={"Referer": "https://animego.org/",
                                          "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                                                        "(KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36"})
            r = r.text.replace("&quot;", "").replace("\\", "")
            player = re.findall(ANIBOOM_PATTERN, r)[0]
            system(f'{PLAYER} {OS_HEADERS_COMMAND}="Referer: https://aniboom.one" {player}')
        elif "kodik" in player:
            print("kodik not supported")
            pass


class Menu:

    def __init__(self):
        self.__ACTIONS = {"q": ("[q]uit", self.exit),
                          "b": ("[b]ack next step", self.back_on),
                          "h": ("[h]elp", self.help),
                          "o": ("[o]ngoing print", self.ongoing),
                          "c": ("[c]lear", self.cls)
                          }
        self.anime = Anime()
        self.__back_action = True

    def back_on(self):
        self.__back_action = False

    def back_off(self):
        self.__back_action = True

    @staticmethod
    def cls():
        system("clear")

    @property
    def is_back(self):
        return self.__back_action

    def ongoing(self):
        while self.is_back:
            ongoing_data = self.anime.get_ongoing()
            print(*[f"{i}] {v[0]}, ep: {v[1]}, dub: {v[2]}" for i, v in enumerate(ongoing_data, 1)], sep="\n")
            print("Choose anime:", 1, "-", len(ongoing_data))
            command = input(f"c_o [1-{len(ongoing_data)}] > ")
            if not self.command_wrapper(command) and command.isdigit():
                self.choose_episode(int(command))
        self.back_off()

    def choose_dub(self, result):
        while self.is_back:
            print(*[f"{i}] {r['dub']}" for i, r in enumerate(result, 1)], sep="\n")
            print("Choose dub:", 1, "-", len(result))
            command = input(f"c_d [1-{len(result)}] > ")
            if not self.command_wrapper(command) and command.isdigit():
                command = int(command)
                print("Load player...")
                player = result[command - 1]["player"][0]
                print("Start playing!")
                self.anime.play(player)
            return
        self.back_off()

    def choose_episode(self, num: int):
        self.anime.parse_episodes_count(num - 1)
        episodes = self.anime.parse_series()
        if len(episodes) > 0:
            while self.is_back:
                print(*[f"{i}] {s[1]}" for i, s in enumerate(episodes, 1)], sep="\n")
                print(f"Choose episode: 1-{len(episodes)}")
                command = input(f"c_e [1-{len(episodes)}] > ")
                if not self.command_wrapper(command) and command.isdigit():
                    result = self.anime.choose_episode(int(command) - 1)
                    if len(result) > 0:
                        self.choose_dub(result)
                    else:
                        print("No available dubs")
                        return
            self.back_off()
        else:
            print("""Warning! Episodes not found :(
This anime-title maybe blocked in your country, try using a vpn/proxy and repeat operation
            
""")
            print()
        return

    def choose_anime(self):
        while self.is_back:
            print("Choose anime:", 1, "-", len(self.anime.anime_results))
            command = input(f"c_a [1-{len(self.anime.anime_results)}] > ")
            if not self.command_wrapper(command) and command.isdigit():
                self.choose_episode(int(command))
        self.back_off()

    def find(self, pattern):
        results = self.anime.search(pattern)
        if len(results) > 0:
            print("Found", len(results))
            print(*[f"{i}] {a[1]}" for i, a in enumerate(results, 1)], sep="\n")
            self.choose_anime()
        else:
            print("Not found!")
            return

    def help(self):
        for k, v in self.__ACTIONS.items():
            print(k, v[0])

    def command_wrapper(self, command):
        self.cls()
        if self.__ACTIONS.get(command):
            self.__ACTIONS[command][1]()
            return True
        return False

    def main(self):
        if PROXY:
            print("Check proxy")
            try:
                self.anime.session.get("https://animego.org", proxies=dict(http=PROXY, https=PROXY),
                                       timeout=10)
            except Exception as e:
                print(e)
                print("Failed proxy connect")
                self.exit()
            self.anime.session.proxies.update(dict(http=PROXY, https=PROXY))
            print("Proxy connect success")
        print("Input anime name or USAGE: h for get commands")
        while True:
            command = input("m > ")
            if not self.command_wrapper(command):
                self.find(command)

    @staticmethod
    def exit():
        exit(0)


if __name__ == '__main__':
    try:
        Menu().main()
    except KeyboardInterrupt:
        print("Exit")