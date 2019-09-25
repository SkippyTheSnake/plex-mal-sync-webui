from typing import Optional
from utils import log
from plexapi.server import PlexServer


class PlexConnection(PlexServer):
    def __init__(self, server_url: str, server_token: str) -> None:
        """ Connects to plex server with the given url and token.

        :param server_url: The url to the target plex server.
        :param server_token: The token for the target server.
        """
        log("Connecting to plex server")
        super().__init__(server_url, server_token)
        log("Plex connection established")

    def get_shows(self, library: str) -> Optional[list]:
        """ Gets all the shows in a given library.

        :param library: The name of the target library.
        :return: A list of Show objects from the target library.
        """
        log(f"Getting shows for library {library}")
        if library in [x.title for x in self.library.sections()]:
            return self.library.section(library).all()

        return None
