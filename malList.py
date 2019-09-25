import json

import requests
from bs4 import BeautifulSoup


class MalList:
    def __init__(self, username: str):
        """ Loads the list from myanimelist """
        url = f'https://myanimelist.net/animelist/{username}?status=7'
        r = requests.get(url)
        soup = BeautifulSoup(r.content, 'lxml')
        data = json.loads(soup.find('table', {'class', 'list-table'}).get('data-items'))

        self.list_data = {str(x.get('anime_id')): x for x in data}

    def get_list_data(self) -> dict:
        return self.list_data

    def get_anime(self, mal_id: str) -> dict:
        """ Search for anime with matching id from the list.

        :param mal_id: The id of the anime being looked for.
        :return: Dictionary containing the data for the anime.
        """
        return self.list_data.get(mal_id)
