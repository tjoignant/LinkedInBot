import time
import yaml
import datetime
import requests

from random import shuffle

from selenium import webdriver
from selenium.common import exceptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class LinkedInBot:
    def __init__(self, username, password):
        # Google Driver
        self.driver = webdriver.Chrome("./chromedriver")
        # URL Addresses
        self.base_url = "https://www.linkedin.com"
        self.login_url = self.base_url + "/login/"
        self.feed_url = self.base_url + "/feed/"
        # LinkedIn Credentials
        self.username = username
        self.password = password
        # Variables
        self.new_connect_request_cpt = 0
        self.MAX_PAGE_NB = 5

    def login(self):
        # Check Internet Connection
        self._check_internet_status()
        # Login
        self._nav(self.login_url)
        self.driver.find_element_by_id("username").send_keys(self.username)
        self.driver.find_element_by_id("password").send_keys(self.password)
        self.driver.find_element_by_id("password").submit()
        self._sleep(1)
        # Check Login Status
        if self.driver.current_url == self.feed_url:
            print("\n[INFO] {} - Successfully logged-in to LinkedIn".format(self._now()))
        else:
            print("\n[ERROR] {} - Username or password incorrect".format(self._now()))
            self.quit()

    def connect(self, filter_list):
        # For Each Filter
        for filter_text in filter_list:
            # Initialize Variables
            page_nb = 1
            # Search People
            self._search(search_text=filter_text, search_filter="People")
            # Store Current URL
            url = self.driver.current_url
            # Find Each Connect Buttons
            while True:
                connect_button = self._find_element("xpath", "//button[@class='artdeco-button artdeco-button--2 artdeco-button--secondary ember-view'][contains(.,'Connect')]", "connect_button", 1, False)
                # IF Connect Button Found
                if connect_button is not None:
                    request_send = self._send_connection(connect_button)
                    if request_send is False:
                        self.quit()
                    self._sleep(3)
                # ELSE
                else:
                    page_nb = page_nb + 1
                    if page_nb <= self.MAX_PAGE_NB:
                        self._display_next_page(url, filter_text, page_nb)
                    else:
                        break
            # GoTo LinkedIn Feed
            self._nav(self.feed_url)

    def quit(self):
        print("\n[INFO] {} - Number of connection request sent : {}".format(self._now(), self.new_connect_request_cpt))
        print("\n[INFO] {} - Bot is shutting down".format(self._now()))
        self.driver.close()
        quit()

    def build_filter_list(self, config_dict):
        # Initialize Bot Filter Parameters
        finance = config_dict["filters"]["FINANCE"]
        roles = config_dict["filters"]["ROLES"]
        institutions = config_dict["filters"]["INSTITUTIONS"]
        seniorities = config_dict["filters"]["SENIORITIES"]
        locations = config_dict["filters"]["LOCATIONS"]

        # Check Finance Filter
        if finance != "MARKET" and finance != "CORPO" and finance != "AM":
            print('[ERROR] {} - Undefined FINANCE filter (in config.yaml)'.format(self._now()))
            quit()

        # Retrieve Roles List
        roles_list = roles
        if roles[0] == "All" or roles[0] == "ALL":
            roles_list = config_dict["roles"][finance]

        # Retrieve Banks List
        institutions_list = institutions
        if institutions[0] == "All" or institutions[0] == "ALL":
            institutions_list = config_dict["institutions"][finance]

        # Retrieve Seniorities List
        seniorities_list = seniorities
        if seniorities[0] == "All" or seniorities[0] == "ALL":
            seniorities_list = [""]

        # Retrieve Locations List
        locations_list = locations
        if locations[0] == "All" or locations[0] == "ALL":
            locations_list = [""]

        # Shuffle Each List
        shuffle(roles_list)
        shuffle(institutions_list)
        shuffle(seniorities_list)
        shuffle(locations_list)

        # Create Overall Filters List
        filters_list = []
        for role in roles_list:
            for institution in institutions_list:
                for seniority in seniorities_list:
                    for location in locations_list:
                        new_filter = role + ' ' + institution + ' ' + seniority + ' ' + location
                        filters_list.append(new_filter.rstrip())
        return filters_list

    def _display_next_page(self, url, search_text, page_nb):
        # GoTo Next Result Page
        new_ulr = url + "&page=" + str(page_nb)
        print("\n[INFO] {} - Searching for: {} (page {})".format(self._now(), search_text, page_nb))
        self._nav(new_ulr)

    def _send_connection(self, connect_button):
        request_send = True
        try:
            # Click On Connect Button
            connect_button.click()
            # Click On Send Button
            send_button = self._find_element("xpath", "//button[@class='ml1 artdeco-button artdeco-button--3 artdeco-button--primary ember-view'][contains(.,'Send')]", "send_button")
            send_button.click()
            self._sleep(1)
            # Check Connect Button Is Still Accessible
            connect_button.click()
        # EXCEPT Click Interrupted
        except exceptions.ElementClickInterceptedException:
            print("[WARNING] {} - Click on connect_button intercepted".format(self._now()))
            print("[WARNING] {} - Weekly new connection request limit reached".format(self._now()))
            request_send = False
        except exceptions.StaleElementReferenceException:
            print("[INFO] {} - New connection request sent".format(self._now()))
            self.new_connect_request_cpt += 1
        return request_send

    def _search(self, search_text, search_filter="People"):
        # GoTo LinkedIn Feed
        self._nav(self.feed_url)
        # Search Text
        print("\n[INFO] {} - Searching for: {}".format(self._now(), search_text))
        search_bar = self._find_element("xpath", "//input[@class='search-global-typeahead__input always-show-placeholder']", "search_bar")
        search_bar.send_keys(search_text)
        search_bar.send_keys(Keys.ENTER)
        # Filter Results
        if search_filter == "People":
            people_button = self._find_element("xpath", "//button[@class='artdeco-pill artdeco-pill--slate artdeco-pill--2 artdeco-pill--choice ember-view search-reusables__filter-pill-button'][contains(.,'People')]", "people_button")
            people_button.click()
            self._sleep()

    def _find_element(self, find_by, find_string, element_name, max_nb_tries=3, quit_if_not_found=True):
        cpt = 1
        element_found = False
        element = None
        # Try Multiple Times To Find Element
        while not element_found and cpt <= max_nb_tries:
            try:
                if find_by == "xpath":
                    element = WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.XPATH, find_string)))
                    element_found = True
                elif find_by == "class_name":
                    element = WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.CLASS_NAME, find_string)))
                    element_found = True
                else:
                    print("\n[ERROR] {} - Invalid find_by type request".format(self._now()))
                    self.quit()
            # EXCEPT State Element Reference
            except exceptions.StaleElementReferenceException:
                print("[WARNING] {} - connect_button is not attached to the page document, retrying in a couple of seconds".format(self._now()))
                self._sleep()
                cpt = cpt + 1
            # EXCEPT Element Not Found
            except exceptions.TimeoutException:
                if max_nb_tries == 1:
                    print("[WARNING] {} - Couldn't find a {}".format(self._now(), element_name))
                else:
                    self._check_internet_status()
                    print("[WARNING] {} - Couldn't find a {}, retrying in a couple a seconds".format(self._now(), element_name))
                self._sleep()
                cpt = cpt + 1
            # EXCEPT Undefined Exception
            except Exception as e:
                print("[WARNING] {} - Undefined exception: {}".format(self._now(), e))
                self._sleep()
                cpt = cpt + 1
        # IF Element Not Found
        if not element_found and quit_if_not_found == True:
            print("[ERROR] {} - Max number of retries reached".format(self._now()))
            self.quit()
        return element

    def _nav(self, url):
        # GoTo URL
        self.driver.get(url)

    def _check_internet_status(self):
        url = "http://www.kite.com"
        timeout = 5
        cpt = 1
        while True:
            try:
                requests.get(url, timeout=timeout)
                break
            except (requests.ConnectionError, requests.Timeout):
                if cpt > 3:
                    print("[ERROR] {} - Max number of retries reached".format(self._now()))
                    self.quit()
                else:
                    print("[WARNING] {} - Can't connect to internet, retrying in 30s".format(self._now()))
                    cpt = cpt + 1
                    self._sleep(30)

    @staticmethod
    def _sleep(seconds=5):
        time.sleep(seconds)

    @staticmethod
    def _now():
        now = datetime.datetime.now()
        now_str = now.strftime("%d/%m %H:%M")
        return now_str


if __name__ == "__main__":
    # Load Config File
    config_stream = open("config.yaml", "r")
    config_dictionary = yaml.safe_load(config_stream)

    # Initialize Bot Identification Parameters
    USER_EMAIL = config_dictionary["identification"]["USER_EMAIL"]
    USER_PASSWORD = config_dictionary["identification"]["USER_PASSWORD"]

    # Initialize Bot
    bot = LinkedInBot(USER_EMAIL, USER_PASSWORD)

    # Initialize Filter List
    filters = bot.build_filter_list(config_dictionary)

    # Run Bot
    bot.login()
    bot.connect(filter_list=filters)
    bot.quit()
