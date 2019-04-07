# -*- coding: utf-8 -*-

import time
from datetime import datetime

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.wait import WebDriverWait

SEARCH_URL = 'https://www.autohero.com/de/search/'
DRIVERS_PATH = r'../drivers/geckodriver'
SORT_BY_PRICE_DESC = "2"


def main():

    min_year = 2015
    sort_by = SORT_BY_PRICE_DESC

    driver = init_driver()
    try:
        apply_year_filter(driver, min_year)
        sort(driver, sort_by)
        check_pages(driver, min_year)
    finally:
        driver.close()


def init_driver():
    driver = webdriver.Firefox(executable_path=DRIVERS_PATH)
    driver.get(SEARCH_URL)
    return driver


def apply_year_filter(driver, year):
    print('Applying filter')
    filter_year = driver.find_element_by_css_selector('[data-qa-selector="filter-year"]')
    filter_year.click()

    year_selector = driver.find_element_by_name('yearRange.min')
    year_selector.click()
    Select(year_selector).select_by_visible_text(str(year))

    filter_applied = check_element_ready(By.CSS_SELECTOR, '[data-qa-selector="active-filter"]', driver)
    assert filter_applied, 'Filter applying failed'
    print('Filter applied')


def sort(driver, sort_by):
    print('Applying sorting')

    sort_cars = driver.find_element_by_name('sort')
    Select(sort_cars).select_by_value(sort_by)
    time.sleep(2)
    print('Sorting applied')


def check_pages(driver, min_year):
    print('Checking pages')
    last_price = None
    page_number = 1

    last_price = check_page(driver, min_year, last_price, page_number)
    next_page_icon = driver.find_element_by_css_selector('[aria-label="Next"]')

    while has_next_page(next_page_icon):
        page_number += 1
        next_page_icon.click()
        next_page_locator = '//ul[@class="pagination"]/li[@class="active"]/a[text()="{}"]'.format(page_number)
        next_page_loaded = check_element_ready(By.XPATH, next_page_locator, driver)
        assert next_page_loaded, 'Next page loading failed'
        last_price = check_page(driver, min_year, last_price, page_number)
        next_page_icon = driver.find_element_by_css_selector('[aria-label="Next"]')
    print('Pages are successfully checked')


def has_next_page(next_page_icon):
    next_page_icon_parent = next_page_icon.find_element_by_xpath("./..")
    enabled = 'disabled' not in next_page_icon_parent.get_attribute('Class')
    return enabled


def check_page(driver, min_year, last_price, page_number):
    print('Checking page # {}'.format(page_number))
    search_results = driver.find_element_by_css_selector('[data-qa-selector="ad-items"]')

    all_items = search_results.find_elements_by_css_selector('[data-qa-selector="ad"]')

    current_price = get_price(all_items[0]) if last_price is None else last_price
    for item in all_items:
        price = get_price(item)
        assert current_price >= price, 'prices sorting failed'
        current_price = price
        spec_year = get_year(item)
        assert spec_year >= min_year, 'filter doesn\'t work'
    print('Checking page # {} succeeded'.format(page_number))
    return current_price


def check_element_ready(type, selector, driver):
    delay = 3 # seconds
    try:
        WebDriverWait(driver, delay).until(EC.presence_of_element_located((type, selector)))
        return True
    except TimeoutException:
        print ("Loading took too much time!")
        return False


def get_price(item):
    price_element = item.find_element_by_css_selector('[data-qa-selector="price"]')
    price_with_currency = price_element.text
    space_index = price_with_currency.index(' ')
    price_value_str = price_with_currency[0:space_index]
    price = int(price_value_str.replace('.', ''))
    return price


def get_year(item):
    specs = item.find_element_by_css_selector('[data-qa-selector="spec"]')
    specs_text = specs.text
    specs_date_str = specs_text.replace(u'•\n', '')
    specs_date = datetime.strptime(specs_date_str, '%m/%Y')
    return specs_date.year


main()