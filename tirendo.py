from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re
import time
from utils import Tyre
import urllib.parse


def get_page_html(url):
    # Use Playwright to fetch the page content and wait for network idle to ensure all content is loaded
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_load_state('networkidle')  # Wait until network is idle
        html = page.content()
        browser.close()
    return html


def collect_list_view(item, base_url, params) -> Tyre:
    """
    The collect_list_view function extracts tyre information from all items in the list view of the search results page.
    Since the location of some data is different in the list view, we need to handle it separately from the card view.

    :param item: HTML element representing a single tyre item in the list view
    :param base_url: Site base URL to join with relative URLs found in the item
    :param params: Different search parameters used to filter the results, such as width, profile, and size
    :return: Tyre object containing the extracted information
    """
    # find the div containing the brand name
    title_div = item.find('div', class_='product-list-title')

    # find the text in that div where the brand is, which is in a div with style "font-weight:bold"
    brand_div = title_div.find('div', style=lambda s: s and 'font-weight:bold' in s)
    brand = brand_div.get_text(strip=True)

    # find the url in the title div
    link = title_div.find('a')

    # the model name is in the link text
    pattern = link.get_text(strip=True)

    # the URL is relative, so we need to join it with the base URL
    item_url = urllib.parse.urljoin(base_url, link['href'])

    # we now need to find load index and speed rating
    size_div = item.find('strong', class_='result-list-prod-size')

    # text is extracted with separator=' ' to ensure that the load index and speed rating can be located with regex
    full_text = size_div.get_text(separator=' ', strip=True)

    # regex to find load index and speed rating
    # we are looking for 2 or 3 digits followed by a single uppercase letter
    match = re.search(r'\b(\d{2,3})([A-Z])\b', full_text)
    if match:
        load_index, speed_rating = match.groups()
    else:
        # if not found, set to empty strings
        load_index, speed_rating = '', ''

    # price is found in a separate location
    price = item.find('span', class_='search-list-price', attrs={'itemprop': 'price'}).get('content')

    # create a Tyre object
    tyre = Tyre(
        url=item_url,
        brand=brand,
        pattern=pattern,
        width=params.get('width'),
        aspect_ratio=params.get('profile'),
        rim_size=params.get('size'),
        load_index=load_index,
        speed_rating=speed_rating,
        price=price
    )

    return tyre


def collect_card_view(item, base_url, params) -> Tyre:
    """
    The collect_card_view function extracts tyre information from all items in the card view of the search results page.
    Since the location of some data is different in the card view, we need to handle it separately from the list view.

    :param item: HTML element representing a single tyre item in the list view
    :param base_url: Site base URL to join with relative URLs found in the item
    :param params: Different search parameters used to filter the results, such as width, profile, and size
    :return: Tyre object containing the extracted information
    """
    # find the div containing the brand name
    title_div = item.find('div', class_='advertised-search-list-prod-title')

    # find the text in that div where the brand is, which is in a <b> tag with itemprop="brand"
    brand_div = title_div.find('b', attrs={'itemprop': 'brand'})
    brand = brand_div.get_text(strip=True)

    # find the url in the title div
    link = title_div.find('a')

    # the model name is in the link text
    pattern = link.get_text(strip=True)

    # the URL is relative, so we need to join it with the base URL
    item_url = urllib.parse.urljoin(base_url, link['href'])

    # we now need to find load index, speed rating
    size_div = item.find('strong', class_='result-list-prod-size')

    # text is extracted with separator=' ' to ensure that the load index and speed rating can be located with regex
    full_text = size_div.get_text(separator=' ', strip=True)

    # regex to find load index and speed rating
    # we are looking for 2 or 3 digits followed by a single uppercase letter
    match = re.search(r'\b(\d{2,3})([A-Z]\b)', full_text)
    if match:
        load_index, speed_rating = match.groups()
    else:
        # if not found, set to empty strings
        load_index, speed_rating = '', ''

    # price is found in a separate location
    price = item.find('span', class_='advertised-formatted-price', attrs={'itemprop': 'price'}).get('content')

    # create a Tyre object
    tyre = Tyre(
        url=item_url,
        brand=brand,
        pattern=pattern,
        width=params.get('width'),
        aspect_ratio=params.get('profile'),
        rim_size=params.get('size'),
        load_index=load_index,
        speed_rating=speed_rating,
        price=price
    )

    return tyre


def get_results(base_url, search_url, params):
    # initialize an empty list to hold all results and a set to track seen URLs
    all_results = []
    seen_urls = set()

    # loop through pages until no more results are found using a while loop
    while True:
        # a try except block to handle any potential errors when fetching the page
        try:
            url = search_url + urllib.parse.urlencode(params)
            html = get_page_html(url)
        except TimeoutError:
            print(f"Timeout error occurred while fetching page {params.get('pageNoFull')}. Retrying...")
            time.sleep(5)
            continue

        # parse the HTML with BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        # card view tires are found in "advertised-highlighted advertised-bestseller"
        card_view = soup.find_all('div', class_='advertised-highlighted advertised-bestseller')

        # list view tires are found in "row serp j-sr-item product-item"
        list_view = soup.find_all('div', class_='row serp j-sr-item product-item')

        # check if there are no items found on this page, if so, break the loop
        if len(card_view) == 0 and len(list_view) == 0:
            print("No more items found, ending search.")
            break
        else:
            # if there are items found, log the number of items found and the total results so far
            print(f"Page {params.get('pageNoFull')} - Found {len(card_view)+len(list_view)} items."
                  f" Total results so far: {len(all_results) + len(card_view) + len(list_view)}")

        # loop through the items in card view and list view, collect the data and add to results if not seen
        # we use the seen_urls set to track which URLs have already been added to the results
        for item in card_view:
            tyre = collect_card_view(item, base_url, params)
            if tyre.url not in seen_urls:
                seen_urls.add(tyre.url)
                all_results.append(tyre)
            else:
                print(f"Duplicate tyre found: {tyre.url}")

        for item in list_view:
            tyre = collect_list_view(item, base_url, params)
            if tyre.url not in seen_urls:
                seen_urls.add(tyre.url)
                all_results.append(tyre)
            else:
                print(f"Duplicate tyre found: {tyre.url}")

        # ethical scraping: wait a second before the next request to avoid overwhelming the server
        time.sleep(1)

        # increment the page number for the next request
        params['pageNoFull'] += 1

    return all_results


def main():
    base_url = "https://www.tirendo.fr/"
    search_url = "https://www.tirendo.fr/search?"
    params = {
        "width": 205,
        "profile": 55,
        "size": 16,
        "pageNoFull": 1,
        "itemsPerPage": 50
    }

    results = get_results(base_url, search_url, params)
    print("Results retrieved successfully.")

    # write all results to a CSV file
    with open('tyres.csv', 'a') as f:
        # if the file is empty then add headers
        if f.tell() == 0:
            f.write("URL,Brand,Pattern,Width,Aspect Ratio,Rim Size,Load Index,Speed Rating,Price\n")
        for tyre in results:
            f.write(tyre.to_csv_row() + "\n")


if __name__ == "__main__":
    main()
