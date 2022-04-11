from math import atan2, cos, radians, sin, sqrt
import requests


__request_uri_format = "https://api.bigdatacloud.net/data/reverse-geocode-client?latitude={latitude}&longitude={longitude}&localityLanguage=en"
__request_headers = {
    "Accept": "application/json"
}


def get_location_by_coordinates(latitude: float, longitude: float):
    request_uri = __request_uri_format.format(
        longitude=longitude, latitude=latitude)
    response = requests.get(request_uri, headers=__request_headers)
    if not response.ok:
        return None

    return __filter_location_props(response.json())


def get_distance(from_coordinates: tuple[float, float], to_coordinates: tuple[float, float]):
    # tuple format: (latitude, longitude)
    R = 6373.0

    lat1 = radians(from_coordinates[0])
    lon1 = radians(from_coordinates[1])
    lat2 = radians(to_coordinates[0])
    lon2 = radians(to_coordinates[1])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return round(R * c, 3)


def get_map_link(coordinates: tuple[float, float]):
    return f'https://www.google.com/maps/place/{coordinates[0]},{coordinates[1]}'


def __filter_location_props(json):
    return {
        "longitude": json["longitude"],
        "latitude": json["latitude"],
        "country_name": json["countryName"],
        "country_code": json["countryCode"],
        "continent": json["continent"],
        "continent_code": json["continentCode"],
        "city": json["city"]
    }
