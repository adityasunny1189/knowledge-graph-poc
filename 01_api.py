import requests

BASE_URL = "https://dblp.org/search/publ/api"

def fetch_coauthor_data(scientist_name):
    params = {
        "q": scientist_name,
        "h": 1000,  # Max results
        "format": "json"
    }
    response = requests.get(BASE_URL, params=params)
    data = response.json()
    print(data)


if __name__ == "__main__":
    scientist = "Andrew Yao"
    fetch_coauthor_data(scientist)
