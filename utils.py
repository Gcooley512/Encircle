import urllib.parse


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
        return f"{self.brand} {self.pattern} {self.width}/{self.aspect_ratio}R{self.rim_size} {self.load_index}{self.speed_rating}- {self.price} - {self.url}"

    def to_csv_row(self):
        return f"{self.url},{self.brand},{self.pattern},{self.width},{self.aspect_ratio},{self.rim_size},{self.load_index},{self.speed_rating},{self.price}"


def build_url(base, path, args_dict):
    url_parts = list(urllib.parse.urlparse(base))
    url_parts[2] = path
    url_parts[4] = urllib.parse.urlencode(args_dict)
    return urllib.parse.urlunparse(url_parts)
