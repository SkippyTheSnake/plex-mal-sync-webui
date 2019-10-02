from plexapi.video import Show
from driver import Driver
from malList import MalList
import mapping
import config
from plexConnection import PlexConnection
from utils import log
import utils


def update_mal_tvdb_mappings(shows: list):
    log("Updating mal to tvdb mappings")
    for show in shows:
        title = show.title
        tvdbid = show.guid.split('//')[1].rstrip('?lang=en')
        seasons = [str(x.seasonNumber) for x in show.seasons() if x.seasonNumber != 0]
        mapping.update_tvdb_mal_mapping(title, tvdbid, seasons, config.DRIVER)

    mapping.verify_mapping_errors()


def get_status(plex_watched_episodes: int, total_episodes: int) -> str:
    status = '5'  # To watch

    if plex_watched_episodes != 0:
        status = '1'  # Currently Watching

    if total_episodes is not None and 0 < total_episodes <= plex_watched_episodes:
        status = '2'  # Completed

    return status


def process_seasons(show: Show, series_mapping: dict, title: str, mal_list: MalList, tvdb_id: str):
    to_update = []
    for season in [x for x in show.seasons() if x.seasonNumber > 0]:
        mal_id = series_mapping.get(str(season.seasonNumber))

        # When the season is unmapped
        if mal_id is None:
            log(f"Unmapped season for {title} season: {season.seasonNumber}")
            continue

        mal_data = mal_list.get_anime(mal_id) or {}

        total_episodes = mal_data.get('anime_num_episodes')
        mal_watched_eps = mal_data.get('num_watched_episodes') or 0
        plex_watched_eps = len([x for x in season.episodes() if x.isWatched])

        # status = get_status(plex_watched_episodes, total_episodes)

        if len(mal_data) > 0 and plex_watched_eps <= mal_watched_eps or mal_watched_eps == total_episodes:
            continue

        to_update.append({'title'           : title,
                          'season'          : season.seasonNumber,
                          'tvdb_id'         : tvdb_id,
                          'mal_id'          : mal_id,
                          'watched_episodes': plex_watched_eps,
                          'mal_watched_eps' : mal_watched_eps})

    return to_update


def get_to_update(shows: list) -> list:
    log("Getting shows to update")
    tvdbid_mal_mapping = mapping.get_tvdb_mal_mapping()
    mal_list = MalList('SkippyTheSnake')
    to_update = []
    for show in shows:
        title = show.title
        tvdb_id = show.guid.split('//')[1].rstrip('?lang=en')
        series_mapping = tvdbid_mal_mapping.get(tvdb_id)
        # When the series is unmapped
        if series_mapping is None:
            log(f"Unmapped series {title}")
            continue

        to_update.extend(process_seasons(show, series_mapping, title, mal_list, tvdb_id))

    log(f"{len(to_update)} updates required")
    return to_update


def script_init():
    log("Initialising")
    # Start driver
    config.DRIVER = Driver()

    # Ensure mapping file downloads are up to date
    mapping.update_mapping_xml()
    log("Initialisation complete")


def do_sync():
    log("Starting sync")
    script_init()
    plex = PlexConnection(config.SERVER_URL, config.SERVER_TOKEN)
    shows = plex.get_shows("Anime")

    update_mal_tvdb_mappings(shows)

    to_update = get_to_update(shows)

    if len(to_update) > 0:
        logged_in = config.DRIVER.login_myanimelist()

        # If the login fails cancel the sync
        if not logged_in:
            log("Failed to log into MyAnimeList")
            return

        for series in to_update:
            status = config.DRIVER.update_series(series)

            # When the driver failed to load the page because of a MyAnimeList url error
            if status is None:
                continue

            title = series.get('title')
            season_no = series.get('season')
            recent_updates = utils.get_recent_updates()
            watched_eps = series.get('watched_episodes')
            mal_watched_eps = series.get('mal_watched_eps')

            status = {'1': 'Watching', '2': 'Completed', '5': 'To watch'}.get(status)
            eps_change = f" (Ep {mal_watched_eps} → {watched_eps}) " if mal_watched_eps != watched_eps else " "

            recent_updates.append(f"{title} - Season {season_no}{eps_change}({status})")
            config.socketio.emit('recent_updates', {'recent_updates': "\n".join(recent_updates)},
                                 namespace = '/socket')
            utils.save_recent_updates(recent_updates)

        config.DRIVER.quit()
    log("Sync complete")
