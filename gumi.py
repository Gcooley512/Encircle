import time
import requests
from bs4 import BeautifulSoup
import urllib.parse
from utils import Tyre
import json


def get_results(tyre_url, api_url, params):
    # initialize an empty list to hold all results and a set to track seen URLs
    all_results = []
    seen_urls = set()

    # create a session since we are making multiple requests to the same server
    session = requests.Session()

    while True:
        # request the page and parse the results
        response = session.get(api_url, params=params)
        if response.status_code == 200:
            # parse the JSON response and extract the HTML content
            soup = BeautifulSoup(response.json()['products'], 'html.parser')

            # find all the product cards
            items = soup.find_all('div', class_='product-card A card-view')

            # we can also find results in "product-card A list-view"
            items += soup.find_all('div', class_='product-card A list-view')

            # logging
            print(f"Page {params.get('page')} - Found {len(items)} items."
                  f" Total results so far: {len(all_results) + len(items)}")

            # check if there are no items found on this page, if so, break the loop
            if len(items) == 0:
                print("No items found on this page.")
                break

            # iterate through the items and extract the data
            for item in items:
                # extract the data-json attribute
                data_json = item.get('data-json')

                # extract the product link
                link = item.find('a', class_='product-link')

                # check if data-json or product link is missing
                if link is None or not data_json:
                    print("Missing data-json or product link, skipping item.")
                    continue

                # parse the JSON data
                try:
                    data = json.loads(data_json)
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON: {e}")
                    continue

                # URL given is relative, so we need to join it with the base url
                item_url = urllib.parse.urljoin(tyre_url, link['href'])

                # create a Tyre object
                tyre = Tyre(
                    url=item_url,
                    brand=data.get('brand'),
                    pattern=data.get('name'),
                    width=data.get('width'),
                    aspect_ratio=data.get('sidewall'),
                    rim_size=data.get('diameter'),
                    load_index=data.get('load_index'),
                    speed_rating=data.get('speed_index'),
                    price=data.get('price')
                )

                # check for duplicates based on the URL and add to results if not seen
                if tyre.url not in seen_urls:
                    seen_urls.add(tyre.url)
                    all_results.append(tyre)
                else:
                    print(f"Duplicate found: {tyre.url}")
        else:
            print(f"Failed to retrieve results. Status code: {response.status_code}")

        # ethical scraping: wait a second before the next request to avoid overwhelming the server
        time.sleep(1)

        # increment the page number for the next request
        params['page'] += 1

    return all_results


def main():
    # set the different URLs and parameters for the search
    api_url = "https://gumi.hu/api/searchAjax"
    tyre_url = "https://gumi.hu/autogumi"
    params = {'page': 1, 'width': 205, 'height': 55, 'diameter': 16}

    results = get_results(tyre_url, api_url, params)
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
