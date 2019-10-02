import time
from typing import Optional

import selenium.common
from colorama import Fore
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

import mapping
from config import MAL_USERNAME, MAL_PASSWORD
from utils import log
import syncHandler


class Driver:
    def __init__(self):
        """ Creates chromedriver with options for the object. """
        log(f"Starting web driver", Fore.CYAN)
        # Setup chrome options
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')

        # Remove unwanted logs
        chrome_options.add_argument("--log-level=3")
        self.driver = webdriver.Chrome(chrome_options = chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        log(f"Web driver started", Fore.GREEN)

    def get(self, url):
        """ Loads a given url with the chromedriver. """
        self.driver.get(url)

    def get_html(self, url = None):
        """ Gets the page source of a given url. """
        if url is not None:
            self.driver.get(url)

        return self.driver.page_source

    def save_screenshot(self):
        return self.driver.save_screenshot('screenshot.png')

    def send_keys(self, selector, keys):
        """ Sends keys to a given element.

        :selector: the css selector to get the target element.
        :keys: The keys to be sent to the target element. """
        element = self.find_element(selector)
        element.send_keys(keys)

    def find_element(self, css_selector):
        """ Finds a single element on a webpage using a css selector.

        :param css_selector: The css selector to locate the target element.
        :return: Single html element that matches the provided css selector.
        """
        self.wait_for(css_selector)
        return self.driver.find_element_by_css_selector(css_selector)

    def find_elements(self, css_selector):
        """ Finds all elements on a webpage that match a given css selector.

        :param css_selector: The css selector to locate the target elements.
        :return: All html elements that match the provided css selector.
        """
        self.wait_for(css_selector)
        return self.driver.find_elements_by_css_selector(css_selector)

    def click(self, css_selector, log_click_error: bool = True):
        """ Sends a click event to the target element using a css selector.

        :param css_selector: The css selector to locate the target element.
        :param log_click_error: Whether or not to log when a click fails.
        """
        try:
            self.wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR, css_selector)))
            ele = self.find_element(css_selector)

            attempts = 0
            while attempts < 5:
                try:
                    attempts += 1
                    ele.click()
                except WebDriverException:
                    time.sleep(1)
                    continue
                break

        except TimeoutException:
            if log_click_error:
                log(f"Failed to click element. {css_selector}")

    def wait_for(self, css_selector):
        """ Waits for an element to be loaded or become visible on the webpage.

        :param css_selector: The css selector to locate the target element.
        """
        self.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, css_selector)))

    def element_exists(self, css_selector):
        """ Checks to see if the element is visible on the webpage.

        :param css_selector: The css selector to locate the target element.
        """
        try:
            self.driver.find_element_by_css_selector(css_selector)
            return True
        except selenium.common.exceptions.NoSuchElementException:
            return False

    def accept_privacy_notices(self):
        # Larger privacy notice
        if self.element_exists('.details_save--1ja7w'):
            self.click('.details_save--1ja7w', False)
        # Click the medium privacy notice
        if self.element_exists('.intro_acceptAll--23PPA'):
            self.click('.intro_acceptAll--23PPA', False)

        # First small privacy notice
        if self.element_exists('button'):
            self.click('button', False)

    def login_myanimelist(self, attempts: int = 1):
        if attempts < 5:
            log(f"Logging into MyAnimeList attempt: {attempts}")
            self.get(f"https://myanimelist.net/login.php?from=%2F")
            self.accept_privacy_notices()

            # Enter login information
            self.send_keys('#loginUserName', MAL_USERNAME)
            self.send_keys('#login-password', MAL_PASSWORD)

            self.click('.pt16 .btn-form-submit')  # Click login button

            if not self.login_successful():
                return self.login_myanimelist(attempts + 1)

            log(f"Logged in successfully as user {MAL_USERNAME}", Fore.GREEN)
            return True

        log(f"MyAnimeList login failed")
        return False

    def login_successful(self):
        log("Checking if login was successful")
        return self.element_exists(".header-profile-link")

    def update_series(self, series: dict) -> Optional[str]:
        log(f"Updating series {series.get('title')} season {series.get('season')}")
        self.get(f"https://myanimelist.net/anime/{series.get('mal_id')}")
        self.accept_privacy_notices()
        plex_watched_episodes = series.get('watched_episodes')

        if self.element_exists('.message'):
            log("Error can't load page with that mal id")
            mapping.add_to_mapping_errors(series.get('tvdb_id'), series.get('title'), series.get('season'))
            return None

        # Click the add to list button if it exists
        if self.element_exists('#showAddtolistAnime'):
            self.click('#showAddtolistAnime')

        # Get the total episodes
        total_episodes = self.find_element('#curEps').text
        total_episodes = int(total_episodes) if total_episodes.isdigit() else None
        status = syncHandler.get_status(plex_watched_episodes, total_episodes)
        # Click the watched status
        self.click(f"#myinfo_status > option:nth-child({status})")

        # Enter episodes seen
        self.send_keys('#myinfo_watchedeps', [Keys.CONTROL, 'a'])
        episodes_seen_value = min(plex_watched_episodes, total_episodes) if total_episodes else plex_watched_episodes
        self.send_keys('#myinfo_watchedeps', episodes_seen_value)

        # Click add or update
        if self.element_exists('.js-anime-add-button'):
            self.click('.js-anime-add-button')
        else:
            self.click('.js-anime-update-button')

        return status

    def quit(self):
        """ Close the driver. """
        self.driver.quit()
