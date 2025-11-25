import requests

def test_restcountries():
    url = "https://restcountries.com/v3.1/all"
    fields = "name,cca2,cca3,capital,region,subregion,languages,currencies,population,continents,flags"
    print(f"Testing RestCountries with fields: {fields}")
    try:
        response = requests.get(url, params={'fields': fields}, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code != 200:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

def test_geodata():
    branches = ["master", "main"]
    for branch in branches:
        url = f"https://raw.githubusercontent.com/dr5hn/countries-states-cities-database/{branch}/cities.json"
        print(f"Testing GeoData URL: {url}")
        try:
            response = requests.head(url, timeout=10)
            print(f"Status: {response.status_code}")
        except Exception as e:
            print(f"Exception: {e}")

if __name__ == "__main__":
    test_restcountries()
    test_geodata()
