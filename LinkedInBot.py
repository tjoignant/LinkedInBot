import time
import yaml
import datetime

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
        self.login_url = self.base_url + "/login"
        self.feed_url = self.base_url + "/feed"
        # LinkedIn Credentials
        self.username = username
        self.password = password
        # Variables
        self.new_connect_request_cpt = 0
        self.MAX_PAGE_NB = 10

    def login(self):
        # Login
        self._nav(self.login_url)
        self.driver.find_element_by_id('username').send_keys(self.username)
        self.driver.find_element_by_id('password').send_keys(self.password)
        self.driver.find_element_by_id('password').submit()
        self._sleep()
        # Check Login Status
        if self.driver.current_url != self.base_url + "/checkpoint/lg/login-submit":
            print('\n[INFO] {} - Successfully logged-in to LinkedIn'.format(self._now()))
        else:
            print('\n[ERROR] {} - Username or password incorrect\n'.format(self._now()))
            quit()

    def connect(self, filter_list):
        # For Each Filter
        for filter_text in filter_list:
            # Initialize Variables
            page_nb = 1
            nb_page_connections = 0
            # Search People
            self._search(search_text=filter_text, search_filter='People')
            self._sleep()
            # Store Current URL
            url = self.driver.current_url
            # Find All Action Buttons
            while True:
                # TRY To Find First Connect Button On The Page
                try:
                    connect_button = WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.XPATH, "//button[@class='artdeco-button artdeco-button--2 artdeco-button--secondary ember-view'][contains(.,'Connect')]")))
                    self._send_connection(connect_button)
                    nb_page_connections = nb_page_connections + 1
                # EXCEPT Click Interrupted
                except exceptions.ElementClickInterceptedException:
                    print('[WARNING] {} - Click On Button Intercepted'.format(self._now()))
                    break
                # EXCEPT Element Not Found
                except exceptions.TimeoutException:
                    page_nb = page_nb + 1
                    if page_nb <= self.MAX_PAGE_NB:
                        self._display_next_page(url, filter_text, page_nb)
                    else:
                        break
            # Return To Feed
            self._nav(self.feed_url)

    def quit(self):
        print('\n[INFO] {} - Number of connection request sent : {}'.format(self._now(), self.new_connect_request_cpt))
        self._sleep()
        print('\n[INFO] {} - Bot is shutting down'.format(self._now()))
        self.driver.close()

    def buildFilterList(self, finance, roles, banks, seniorities, locations):
        # Load Filters
        filter_stream = open("filters.yaml", 'r')
        filter_dictionary = yaml.safe_load(filter_stream)

        # Retrieve Roles List
        if roles[0] == 'All' or roles[0] == 'ALL':
            if finance == 'MARKET':
                roles_list = filter_dictionary['MARKET_ROLES_LIST']
            elif finance == 'CORPORATE':
                roles_list = filter_dictionary['CORPO_ROLES_LIST']
            else:
                roles_list = ['']
                print('[ERROR] {} - Undefined FINANCE filter (in config.yaml)'.format(self._now()))
                quit()
        else:
            roles_list = roles

        # Retrieve Banks List
        if banks[0] == 'All' or banks[0] == 'ALL':
            if finance == 'MARKET':
                banks_list = filter_dictionary['MARKET_INSTITUTIONS_LIST']
            elif finance == 'CORPO':
                banks_list = filter_dictionary['CORPO_INSTITUTIONS_LIST']
            else:
                banks_list = filter_dictionary['AM_INSTITUTIONS_LIST']
        else:
            banks_list = banks

        # Retrieve Seniorities List
        if seniorities[0] == 'All' or seniorities[0] == 'ALL':
            seniorities_list = ['']
        else:
            seniorities_list = seniorities

        # Retrieve Locations List
        if locations[0] == 'All' or locations[0] == 'ALL':
            locations_list = ['']
        else:
            locations_list = locations

        # Create Overall Filters List
        filters_list = []
        for role in roles_list:
            for bank in banks_list:
                for seniority in seniorities_list:
                    for location in locations_list:
                        new_filter = role + ' ' + bank + ' ' + seniority + ' ' + location
                        filters_list.append(new_filter.rstrip())
        return filters_list

    def _display_next_page(self, url, search_text, page_nb):
        # GoTo Next Page
        new_ulr = url + "&page=" + str(page_nb)
        self._nav(new_ulr)
        print('\n[INFO] {} - Searching "{}" (page {})'.format(self._now(), search_text, page_nb))
        self._sleep()

    def _send_connection(self, connect_button):
        # Click On "Connect" Button
        connect_button.click()
        self._sleep()
        # Click On "Send" Button
        self.driver.find_element_by_class_name('ml1').click()
        self._sleep()
        # Update Counter
        self.new_connect_request_cpt += 1
        print('[INFO] {} - New connection request sent'.format(self._now()))

    def _search(self, search_text, search_filter='People'):
        # GoTo LinkedIn "Feed"
        self._nav(self.feed_url)
        # Search Text
        print('\n[INFO] {} - Searching "{}"'.format(self._now(), search_text))
        search = self.driver.find_element_by_class_name('search-global-typeahead__input')
        search.send_keys(search_text)
        search.send_keys(Keys.ENTER)
        self._sleep()
        # Filter Results
        if search_filter == "People":
            self.driver.find_element_by_xpath("//button[text()='People']").click()
            self._sleep()

    def _nav(self, url):
        # GoTo URL
        self._sleep()
        self.driver.get(url)
        self._sleep()

    @staticmethod
    def _sleep(seconds=5):
        time.sleep(seconds)

    @staticmethod
    def _now():
        now = datetime.datetime.now()
        now_str = now.strftime("%d/%m %H:%M")
        return now_str


if __name__ == '__main__':
    # Load Config Parameters
    config_stream = open("config.yaml", 'r')
    config_dictionary = yaml.safe_load(config_stream)

    # Initialize Bot Identification Parameters
    USER_EMAIL = config_dictionary['identification']['USER_EMAIL']
    USER_PASSWORD = config_dictionary['identification']['USER_PASSWORD']

    # Initialize Bot Filter Parameters
    FINANCE = config_dictionary['filters']['FINANCE']
    ROLES = config_dictionary['filters']['ROLES']
    BANKS = config_dictionary['filters']['INSTITUTIONS']
    SENIORITIES = config_dictionary['filters']['SENIORITIES']
    LOCATIONS = config_dictionary['filters']['LOCATIONS']

    # Initialize Bot
    bot = LinkedInBot(USER_EMAIL, USER_PASSWORD)

    # Initialize Filter List
    filters = bot.buildFilterList(FINANCE, ROLES, BANKS, SENIORITIES, LOCATIONS)

    # Run Bot
    bot.login()
    bot.connect(filter_list=filters)
    bot.quit()
