import csv
from time import sleep
from datetime import datetime
from random import random
import streamlit as st
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.microsoft import EdgeChromiumDriverManager

def generate_filename(search_term):
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    stem = '_'.join(search_term.split(' '))
    filename = stem + '_' + timestamp + '.csv'
    return filename

def save_data_to_csv(record, filename, new_file=False):
    header = ['description', 'price', 'rating', 'review_count', 'url']
    if new_file:
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(header)
    else:
        with open(filename, 'a+', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(record)

def create_webdriver() -> webdriver.Edge:
    options = Options()
    options.use_chromium = True
    options.headless = True  # Run headless for performance
    driver = webdriver.Edge(service=Service(EdgeChromiumDriverManager().install()), options=options)
    return driver

def generate_url(search_term, page):
    base_template = 'https://www.amazon.com/s?k={}&ref=nb_sb_noss_1'
    search_term = search_term.replace(' ', '+')
    stem = base_template.format(search_term)
    url_template = stem + '&page={}'
    if page == 1:
        return stem
    else:
        return url_template.format(page)

def extract_card_data(card):
    description = card.find_element(By.XPATH, './/h2/a').text.strip()
    url = card.find_element(By.XPATH, './/h2/a').get_attribute('href')
    try:
        price = card.find_element(By.XPATH, './/span[@class="a-price-whole"]').text
    except Exception:
        price = ""
    try:
        temp = card.find_element(By.XPATH, './/span[contains(@aria-label, "out of")]')
        rating = temp.get_attribute('aria-label')
    except Exception:
        rating = ""
    try:
        temp = card.find_element(By.XPATH, './/span[contains(@aria-label, "out of")]/following-sibling::span')
        review_count = temp.get_attribute('aria-label')
    except Exception:
        review_count = ""
    return description, price, rating, review_count, url

def collect_product_cards_from_page(driver: webdriver.Edge):
    cards = driver.find_elements(By.XPATH, '//div[@data-component-type="s-search-result"]')
    return cards

def sleep_for_random_interval():
    time_in_seconds = random() * 2
    sleep(time_in_seconds)

def run_scraper(search_term, start_page, end_page):
    """Run the Amazon webscraper"""
    filename = generate_filename(search_term)
    save_data_to_csv(None, filename, new_file=True)  # initialize a new file
    driver = create_webdriver()
    num_records_scraped = 0

    for page in range(start_page, end_page + 1):  # iterate from start_page to end_page
        # load the next page
        search_url = generate_url(search_term, page)
        driver.get(search_url)
        sleep_for_random_interval()  # Allow time for the page to load

        # extract product data
        cards = collect_product_cards_from_page(driver)
        for card in cards:
            record = extract_card_data(card)
            if record:
                save_data_to_csv(record, filename)
                num_records_scraped += 1

    # shut down and report results
    driver.quit()
    return filename, num_records_scraped

def main():
    st.title('Amazon Product Scraper')

    search_term = st.text_input('Enter the product name:')
    start_page = st.number_input('Start Page', min_value=1, value=1)
    end_page = st.number_input('End Page', min_value=1, value=1)

    if st.button('Start Scraping'):
        if start_page > end_page:
            st.error('Start page should be less than or equal to end page.')
        elif search_term.strip() == "":
            st.error('Please enter a product name.')
        else:
            with st.spinner('Scraping in progress...'):
                filename, num_records_scraped = run_scraper(search_term, start_page, end_page)
                st.success(f'Scraped {num_records_scraped} records.')
                st.write(f'CSV file saved as: {filename}')
                with open(filename, 'rb') as f:
                    st.download_button(label='Download CSV', data=f.read(), file_name=filename)

if __name__ == '__main__':
    main()
