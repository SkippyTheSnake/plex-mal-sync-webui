import xml.etree.ElementTree as et
import os
from config import TVDBID_ANIDBID_XML_FILEPATH, TVDBID_ANIDBID_FILEPATH, TVDBID_MALID_FILEPATH, \
    MAPPING_ERRORS_FILEPATH
import urllib.request
import utils
from utils import log
from bs4 import BeautifulSoup
import time
import urllib.parse


def get_anidbid(tvdb_id: str, season: str):
    data = get_tvdb_anidb_mapping().get(tvdb_id) or {}
    return data.get(season)


def update_mapping_xml() -> None:
    if not os.path.exists(TVDBID_ANIDBID_XML_FILEPATH) or not os.path.exists(TVDBID_ANIDBID_FILEPATH):
        download_tvdb_anidb_mapping()

    mapping_file_age = time.time() - os.path.getctime(TVDBID_ANIDBID_XML_FILEPATH)
    if mapping_file_age >= 603_800:
        download_tvdb_anidb_mapping()


def download_tvdb_anidb_mapping() -> None:
    log("Downloading new XML mapping file")
    if os.path.exists(TVDBID_ANIDBID_XML_FILEPATH):
        os.remove(TVDBID_ANIDBID_XML_FILEPATH)

    urllib.request.urlretrieve('https://raw.githubusercontent.com/ScudLee/anime-lists/master/anime-list-full.xml',
                               TVDBID_ANIDBID_XML_FILEPATH)

    log("Parsing new XML data")
    # Parse the xml into json format for easy access
    data = {}
    xml_data = et.parse(TVDBID_ANIDBID_XML_FILEPATH).getroot()
    for anime in list(xml_data):
        # Skip all the specials which have a season number of 0
        # Also some seasons are labelled "a" this is for long series like Dragonball skip these too
        season_number = anime.get('defaulttvdbseason')
        tvdbid, anidbid = anime.get('tvdbid'), anime.get('anidbid')
        if season_number is None or season_number == "0" or not season_number.isdigit() or not tvdbid.isdigit() or not anidbid.isdigit():
            continue

        # Create entry with the tvdbid
        if tvdbid not in data:
            data[tvdbid] = {}

        # Add the anidbid mapping
        data[tvdbid][int(season_number)] = anidbid

    utils.save_json(data, TVDBID_ANIDBID_FILEPATH)


def get_tvdb_anidb_mapping() -> dict:
    """ Load the tvdb id to anidb id mapping xml file.

    :return: xml object containing the mapping data for the tvdb and anidb ids.
    """

    return utils.load_json(TVDBID_ANIDBID_FILEPATH, {})


def get_tvdb_mal_mapping() -> dict:
    return utils.load_json(TVDBID_MALID_FILEPATH, {})


def obtain_malid(anidb_id: str, driver) -> str:
    """ Gets the myanimelist id from the anidb page for the anime.

    :param anidb_id: The anidb id for the anime..
    :return: Returns the myanimelist id as a string.
    """
    url = 'https://anidb.net/anime/' + anidb_id
    soup = BeautifulSoup(driver.get_html(url), 'lxml')

    # Check the two locations for the myanimelist link
    ele = soup.find('a', {'class': 'i_icon i_resource_mal brand'})
    if ele is None:
        ele = soup.find('a', {'class': 'hide mal'})

    return ele.get('href').lstrip('https://myanimelist.net/anime/')


def add_tvdbid_malid_mapping(tvdb_id: str, season: str, mal_id: str) -> None:
    mal_id_mapping = get_tvdb_mal_mapping()
    # Create tvdbid entry if it doesn't already exist
    if tvdb_id not in mal_id_mapping:
        mal_id_mapping[tvdb_id] = {}

    mal_id_mapping.get(tvdb_id)[season] = mal_id

    utils.save_json(mal_id_mapping, TVDBID_MALID_FILEPATH)
    verify_mapping_errors()


def add_to_mapping_errors(tvdb_id: str, title: str, season: str) -> None:
    error_log = utils.load_json(MAPPING_ERRORS_FILEPATH, {})

    if tvdb_id not in error_log:
        error_log[tvdb_id] = {'title': title, 'unmapped_seasons': {}}

    if season not in error_log.get(tvdb_id).get('unmapped_seasons'):
        prop = urllib.parse.quote_plus(f"{title} season {season}")
        search_url = f'https://myanimelist.net/search/all?q={prop}'
        error_log.get(tvdb_id).get('unmapped_seasons')[season] = search_url

    utils.save_json(error_log, MAPPING_ERRORS_FILEPATH)
    verify_mapping_errors()


def update_tvdb_mal_mapping(title: str, tvdbid: str, seasons: list, driver) -> None:
    tvdb_mal_mapping = get_tvdb_mal_mapping()
    log(f"Checking mappings for {title}")
    # Check if series is mapped at all
    if tvdbid not in tvdb_mal_mapping:
        tvdb_mal_mapping[tvdbid] = {}

    series_mapping = tvdb_mal_mapping.get(tvdbid)
    for season in seasons:
        log(f"{title} season {season}")
        mal_id = series_mapping.get(season)

        # Failed to get mal_id from mapping
        if mal_id is None:
            # Get the anidb_id and obtain the mal_id from that
            log(f"Getting mal id for {title} season {season}")
            anidb_id = get_anidbid(tvdbid, season)

            # Failed to find the matching anidb_id
            if anidb_id is None:
                # Add the information to the error log so the user can manually correct it
                print("Unable to find anidb id so this will need to be added manually")
                add_to_mapping_errors(tvdbid, title, season)
                continue

            mal_id = obtain_malid(anidb_id, driver)
            add_tvdbid_malid_mapping(tvdbid, season, mal_id)


def verify_mapping_errors():
    log("Verifying mapping errors")
    mapping_errors = utils.load_json(MAPPING_ERRORS_FILEPATH, {})
    tvdb_mal_mapping = get_tvdb_mal_mapping()

    for tvdbid, data in list(mapping_errors.items()):
        if tvdbid not in tvdb_mal_mapping:
            continue

        series_mapping = tvdb_mal_mapping.get(tvdbid)
        title = data.get('title')
        for season in list(data.get('unmapped_seasons').keys()):
            if series_mapping.get(season) is not None:
                log(f"{title} Season {season} has been mapped. Removing from errors")
                mapping_errors.get(tvdbid).get('unmapped_seasons').pop(season)

        if len(mapping_errors.get(tvdbid).get('unmapped_seasons')) == 0:
            log(f"{title} no longer has any unmapped seasons. Removing from errors")
            del mapping_errors[tvdbid]

    utils.save_json(mapping_errors, MAPPING_ERRORS_FILEPATH)
    log("Mapping errors verified")
