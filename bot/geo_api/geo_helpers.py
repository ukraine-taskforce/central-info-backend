import requests


__request_uri_format = "https://api.bigdatacloud.net/data/reverse-geocode-client?latitude={latitude}&longitude={longitude}&localityLanguage=en"
__request_headers = {
    "Accept": "application/json"
}


def get_location_by_coordinates(longitude: float, latitude: float):
    request_uri = __request_uri_format.format(
        longitude=longitude, latitude=latitude)
    response = requests.get(request_uri, headers=__request_headers)
    if not response.ok:
        return None

    return __filter_location_props(response.json())


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
