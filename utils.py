"""
Utils contains common functions used across the project.
The Tyre class is a data structure to hold tyre information.
It has methods to convert the data to a CSV row and to print the tyre information in a readable format.
"""


class Tyre:
    def __init__(self, url, brand, pattern, width, aspect_ratio, rim_size, load_index, speed_rating, price):
        self.url = url
        self.brand = brand
        self.pattern = pattern
        self.width = width
        self.aspect_ratio = aspect_ratio
        self.rim_size = rim_size
        self.load_index = load_index
        self.speed_rating = speed_rating
        self.price = price

    def __str__(self):
        return f"{self.brand} {self.pattern} {self.width}/{self.aspect_ratio}R{self.rim_size} {self.load_index}{self.speed_rating} - {self.price} - {self.url}"

    def to_csv_row(self):
        return f"{self.url},{self.brand},{self.pattern},{self.width},{self.aspect_ratio},{self.rim_size},{self.load_index},{self.speed_rating},{self.price}"
