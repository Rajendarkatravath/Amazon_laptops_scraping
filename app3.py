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

# Define the headers and the data field names
headers = ['description', 'price', 'rating', 'review_count', 'url']

def generate_filename(search_term):
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    stem = '_'.join(search_term.split(' '))
    filename = stem + '_' + timestamp + '.csv'
    return filename

def save_data_to_csv(records, filename, selected_fields, new_file=False):
    if new_file:
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(selected_fields)
            for record in records:
                writer.writerow([record[field] for field in selected_fields])
    else:
        with open(filename, 'a+', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for record in records:
                writer.writerow([record[field] for field in selected_fields])

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

def extract_card_data(card, selected_fields):
    data = {}
    if 'description' in selected_fields:
        data['description'] = card.find_element(By.XPATH, './/h2/a').text.strip()
    if 'url' in selected_fields:
        data['url'] = card.find_element(By.XPATH, './/h2/a').get_attribute('href')
    if 'price' in selected_fields:
        try:
            data['price'] = card.find_element(By.XPATH, './/span[@class="a-price-whole"]').text
        except Exception:
            data['price'] = ""
    if 'rating' in selected_fields:
        try:
            temp = card.find_element(By.XPATH, './/span[contains(@aria-label, "out of")]')
            data['rating'] = temp.get_attribute('aria-label')
        except Exception:
            data['rating'] = ""
    if 'review_count' in selected_fields:
        try:
            temp = card.find_element(By.XPATH, './/span[contains(@aria-label, "out of")]/following-sibling::span')
            data['review_count'] = temp.get_attribute('aria-label')
        except Exception:
            data['review_count'] = ""
    return data

def collect_product_cards_from_page(driver: webdriver.Edge):
    cards = driver.find_elements(By.XPATH, '//div[@data-component-type="s-search-result"]')
    return cards

def sleep_for_random_interval():
    time_in_seconds = random() * 2
    sleep(time_in_seconds)

def run_scraper(search_term, start_page, end_page, selected_fields):
    """Run the Amazon webscraper"""
    filename = generate_filename(search_term)
    save_data_to_csv([], filename, selected_fields, new_file=True)  # initialize a new file
    driver = create_webdriver()
    num_records_scraped = 0
    records = []

    for page in range(start_page, end_page + 1):  # iterate from start_page to end_page
        # load the next page
        search_url = generate_url(search_term, page)
        driver.get(search_url)
        sleep_for_random_interval()  # Allow time for the page to load

        # extract product data
        cards = collect_product_cards_from_page(driver)
        for card in cards:
            record = extract_card_data(card, selected_fields)
            if record:
                records.append(record)
                num_records_scraped += 1
        save_data_to_csv(records, filename, selected_fields)
        records.clear()  # Clear the list to avoid duplicate entries in CSV

    # shut down and report results
    driver.quit()
    return filename, num_records_scraped

def main():
    st.title('Amazon Product Scraper')

    search_term = st.text_input('Enter the product name:')
    start_page = st.number_input('Start Page', min_value=1, value=1)
    end_page = st.number_input('End Page', min_value=1, value=1)

    # Checkbox options for data fields
    selected_fields = []
    if st.checkbox('Description', value=True):
        selected_fields.append('description')
    if st.checkbox('Price', value=True):
        selected_fields.append('price')
    if st.checkbox('Rating', value=True):
        selected_fields.append('rating')
    if st.checkbox('Review Count', value=True):
        selected_fields.append('review_count')
    if st.checkbox('URL', value=True):
        selected_fields.append('url')

    if st.button('Start Scraping'):
        if start_page > end_page:
            st.error('Start page should be less than or equal to end page.')
        elif search_term.strip() == "":
            st.error('Please enter a product name.')
        elif not selected_fields:
            st.error('Please select at least one field to scrape.')
        else:
            with st.spinner('Scraping in progress...'):
                filename, num_records_scraped = run_scraper(search_term, start_page, end_page, selected_fields)
                st.success(f'Scraped {num_records_scraped} records.')
                st.write(f'CSV file saved as: {filename}')
                with open(filename, 'rb') as f:
                    st.download_button(label='Download CSV', data=f.read(), file_name=filename)

if __name__ == '__main__':
    main()
