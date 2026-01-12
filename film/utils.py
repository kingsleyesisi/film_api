import requests 
import json 

def getfilms(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        return [
            {
                'title': film.get('title'),
                'release_date': film.get('release_date'),
                'comment_count': 0
            }
            for film in data
        ]
    except requests.RequestException as e:
        return f"Error: {e}"

if __name__ == "__main__":
    url = "https://swapi.info/api/films/"
    films = getfilms(url)
    print(films)