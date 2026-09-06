import time

import requests
from bs4 import BeautifulSoup
import urllib.parse
from utils import Tyre, build_url
import json

"""
We want to use BeautifulSoup to find all tyres with the size 205/55R16
We can create a template of the url to search these tyres


We want to request the search page and identify how many results there are
these should all have their urls added to a list
to find where the results are in the page we can look in ""product-card A card-view"" class
These card views contain json data with all the information we need to create a dictionary of the results "data-json"

all the necessary information we need to create a dictionary of the results is as follows:
    - URL
    - Brand
    - Pattern (not sure what this means or if it is listed)
    - width
    - Aspect ratio
    - Rim size
    - Load index
    - Speed rating
    - Price
We can create a class for these items and then add functionality in this class to add to a database or to a csv file
"""


def get_results(base_url, path, args_dict):
    # construct the full url
    full_url = build_url(base_url, path, args_dict)
    print(f"Requesting URL: {full_url}")

    # request the page and parse the results
    response = requests.get(full_url)
    if response.status_code == 200:
        # if there are results, parse the page and extract the data
        results = []
        items = []
        soup = BeautifulSoup(response.content, 'html.parser')

        # find all the product cards

        # since these product cards are the same on each page, we only need to check them on the first page
        if args_dict.get('page') == '1':
            items += soup.find_all('div', class_='product-card A card-view')

        # we can also find results in "product-card A list-view"
        items += soup.find_all('div', class_='product-card A list-view')

        # iterate through the items and extract the data
        for item in items:
            data_json = item.get('data-json')
            # URL given is relative, so we need to join it with the base url
            # TODO if none then error will occur, use ".get('href')"
            item_url = urllib.parse.urljoin(base_url, item.find('a', class_='product-link')['href'])

            # extract the data from the json and create a Tyre object
            if data_json:
                data = json.loads(data_json)

                tyre = Tyre(
                    url=item_url,
                    brand=data.get('brand', ''),
                    pattern=data.get('category', ''),
                    width=data.get('width', ''),
                    aspect_ratio=data.get('sidewall', ''),
                    rim_size=data.get('diameter', ''),
                    load_index=data.get('load_index', ''),
                    speed_rating=data.get('speed_index', ''),
                    price=data.get('price', '')
                )
                results.append(tyre)
        print(f"Found {len(items)} items.")

        return results
    else:
        print(f"Failed to retrieve results. Status code: {response.status_code}")
        return []


def get_all_results(base_url, path, args_dict, max_pages=20):
    all_results = []
    seen_urls = set()
    page = 1

    while page <= max_pages:
        args_dict['page'] = str(page)
        page_results = get_results(base_url, path, args_dict)

        for tyre in page_results:
            if tyre.url not in seen_urls:
                seen_urls.add(tyre.url)
                all_results.append(tyre)

        page += 1
        # polite to avoid overwhelming the server
        time.sleep(1)

    # output these results to csv TODO change this to not w mode
    with open('tyres.csv', 'w') as f:
        f.write("URL,Brand,Pattern,Width,Aspect Ratio,Rim Size,Load Index,Speed Rating,Price\n")
        for tyre in all_results:
            f.write(tyre.to_csv_row() + "\n")
    return all_results


def main():
    base_url = "https://gumi.hu/"
    path = "/autogumi"
    args_dict = {'width': '205', 'height': '55', 'diameter': '16', 'page': '1'}
    results = get_all_results(base_url, path, args_dict)
    print("Results retrieved successfully.")
    print("Results:")
    for tyre in results:
        print(tyre)


if __name__ == "__main__":
    main()

