class InformationNode:
    def __init__(self, name: str, distance_in_km: float, website_link: str,
        map_link: str, categories: str) -> None:
        self.name = name
        self.distance_in_km = distance_in_km
        self.website_link = website_link
        self.map_link = map_link
        self.categories = categories
        pass
    def to_map(self):
        return {
            "name": self.name,
            "distance_in_km": self.distance_in_km,
            "website_link": self.website_link,
            "map_link": self.map_link,
            "categories": self.categories
        }