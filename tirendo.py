from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re
import time
from utils import Tyre
import urllib.parse


def get_page_html(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_load_state('networkidle')  # Wait until network is idle
        html = page.content()
        browser.close()
    return html


def collect_list_view(item, base_url, params):
    # find the div with the brand name in
    title_div = item.find('div', class_='product-list-title')

    # find the part in that div where the brand is
    brand_div = title_div.find('div', style=lambda s: s and 'font-weight:bold' in s)
    brand = brand_div.get_text(strip=True)

    # find the link in the title div
    link = title_div.find('a')

    # pattern in same div
    pattern = link.get_text(strip=True)
    item_url = urllib.parse.urljoin(base_url, link['href'])

    # we now need to find load index, speed rating
    size_div = item.find('strong', class_='result-list-prod-size')
    full_text = size_div.get_text(separator=' ', strip=True)

    # regex to find load index and speed rating
    match = re.search(r'\b(\d{2,3})([A-Z])\b', full_text)
    if match:
        load_index, speed_rating = match.groups()
    else:
        load_index, speed_rating = '', ''

    # price is found seperate
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


def collect_card_view(item, base_url, params):
    # find the div with the brand name in
    title_div = item.find('div', class_='advertised-search-list-prod-title')

    # find the part in that div where the brand is
    brand_div = title_div.find('b', attrs={'itemprop': 'brand'})
    brand = brand_div.get_text(strip=True)

    # find the link in the title div
    link = title_div.find('a')

    # pattern in same div
    pattern = link.get_text(strip=True)
    item_url = urllib.parse.urljoin(base_url, link['href'])

    # we now need to find load index, speed rating
    size_div = item.find('strong', class_='result-list-prod-size')
    full_text = size_div.get_text(separator=' ', strip=True)

    # regex to find load index and speed rating
    match = re.search(r'\b(\d{2,3})([A-Z]\b)', full_text)
    if match:
        load_index, speed_rating = match.groups()
    else:
        load_index, speed_rating = '', ''

    # price is found seperate
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
    all_results = []
    seen_urls = set()

    while True:
        try:
            url = search_url + urllib.parse.urlencode(params)
            html = get_page_html(url)
        except TimeoutError:
            print(f"Timeout error occurred while fetching page {params.get('pageNoFull')}. Retrying...")
            time.sleep(5)
            continue

        soup = BeautifulSoup(html, 'html.parser')

        # card view tires are found in "advertised-highlighted advertised-bestseller"
        card_view = soup.find_all('div', class_='advertised-highlighted advertised-bestseller')

        # list view tires are found in "row serp j-sr-item product-item"
        list_view = soup.find_all('div', class_='row serp j-sr-item product-item')

        if len(card_view) == 0 and len(list_view) == 0:
            print("No more items found, ending search.")
            break
        else:
            print(f"Page {params.get('pageNoFull')} - Found {len(card_view)+len(list_view)} items."
                  f" Total results so far: {len(all_results) + len(card_view) + len(list_view)}")

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

        time.sleep(1)

        params['pageNoFull'] += 1

    # write all results to a CSV file
    with open('tyres.csv', 'a') as f:
        # if the file is empty then add headers
        if f.tell() == 0:
            f.write("URL,Brand,Pattern,Width,Aspect Ratio,Rim Size,Load Index,Speed Rating,Price\n")
        for tyre in all_results:
            f.write(tyre.to_csv_row() + "\n")


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

    get_results(base_url, search_url, params)
    print("Results retrieved successfully.")


if __name__ == "__main__":
    main()
