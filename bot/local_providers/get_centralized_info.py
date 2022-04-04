response = {
    "data": [
        {
            "ID": "HU01",
            "Country": "Hungary",
            "Category": "Entry steps",
            "Hyperlink": "https://ukrainehelp.hu/en/#crossing",
            "ISOCountryCode": "HU"
        },
        {
            "ID": "HU02",
            "Country": "Hungary",
            "Category": "Health care",
            "Hyperlink": "https://ukrainehelp.hu/#medical",
            "ISOCountryCode": "HU"
        },
        {
            "ID": "HU03",
            "Country": "Hungary",
            "Category": "Health care",
            "Hyperlink": "https://ukrainehelp.hu/#medical",
            "ISOCountryCode": "HU"
        },
        {
            "ID": "HU04",
            "Country": "Hungary",
            "Category": "Entry steps",
            "Hyperlink": "https://ukrainehelp.hu/en/#crossing",
            "ISOCountryCode": "HU"
        },
        {
            "ID": "HU05",
            "Country": "Hungary",
            "Category": "Health care",
            "Hyperlink": "https://ukrainehelp.hu/#medical",
            "ISOCountryCode": "HU"
        },
        {
            "ID": "HU06",
            "Country": "Hungary",
            "Category": "Health care",
            "Hyperlink": "https://ukrainehelp.hu/#medical",
            "ISOCountryCode": "HU"
        }
    ]
}


def get_centralized_info(country: str, category: str, page_size: int, page: int):
    # stub instead of HTTP request or manual DB fetch here
    items_count = len(response["data"])
    start_from = page * page_size
    end_at = min(items_count - 1, start_from + page_size)
    can_load_more = end_at + 1 < items_count
    return response["data"][start_from:end_at], can_load_more
