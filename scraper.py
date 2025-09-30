import requests
import csv
from bs4 import BeautifulSoup


class TransfermarktScraper:
    def __init__(self, url):
        self.url = url
        self.soup = None
        self.html = None
        self.browser_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

        self.csv_headers = ['Season', 'Matchday', 'Date', 'Time', 'Home Team', 'Away Team', 'Result', 'Home Goals', 'Away Goals', 'Status', 'Match URL']

    def fetch_page(self):

        try:
            response = requests.get(self.url, headers=self.browser_headers, timeout=10)
            response.raise_for_status()
            self.html = response.text
            self.soup = BeautifulSoup(self.html, 'html.parser')
            print(f"Successfully fetched: {self.url}")

            return True
        except requests.exceptions.RequestException as e:
            print(f"Error fetching page: {e}")
            return False

    def parse_matches(self):

        if not self.soup:
            return []

        matches = []

        season_select = self.soup.find('select', {'name': 'saison_id'})
        if not season_select:
            raise ValueError("Could not find season dropdown in HTML")

        selected_option = season_select.find('option', {'selected': 'selected'})
        if not selected_option:
            raise ValueError("Could not find selected season option in HTML")

        season = int(selected_option.get_text(strip=True))

        current_matchday = None

        tables = self.soup.find_all('table')

        for table in tables:

            current_element = table.find_previous('div', class_='content-box-headline')

            if current_element:
                matchday_text = current_element.get_text(strip=True)

                try:
                    current_matchday = int(matchday_text.split('.')[0])
                except:
                    current_matchday = ''
            else:
                current_matchday = ''

            tbody = table.find('tbody')

            rows = tbody.find_all('tr')

            for row in rows:

                if 'bg_blau_20' in row.get('class', []):
                    continue

                cells = row.find_all('td')
                if len(cells) <= 6:
                    continue

                date_link = cells[0].find('a')
                date = date_link.get_text(strip=True) if date_link else ''

                time_text = cells[1].get_text(strip=True)
                time = time_text if time_text else ''

                home_team_link = cells[2].find('a')
                home_team = home_team_link.get_text(strip=True) if home_team_link else ''

                result_link = cells[4].find('a', class_='ergebnis-link')

                if result_link:
                    result = result_link.get_text(strip=True)
                    match_url = 'https://www.transfermarkt.com' + result_link['href']
                else:
                    result = '-:-'
                    match_url = ''

                away_team_link = cells[6].find('a')
                away_team = away_team_link.get_text(strip=True) if away_team_link else ''

                if result and result != '-:-':
                    status = 'played'
                    goals = result.split(':')
                    home_goals = int(goals[0])
                    away_goals = int(goals[1])
                else:
                    status = 'scheduled'
                    home_goals = None
                    away_goals = None

                matches.append([
                    season,
                    current_matchday,
                    date,
                    time,
                    home_team,
                    away_team,
                    result,
                    home_goals,
                    away_goals,
                    status,
                    match_url
                ])

        return matches

    def save_to_csv(self, headers, rows, filename='results.csv'):
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(headers)
                writer.writerows(rows)
            return True
        except Exception as e:
            print(f"Error creating CSV file: {e}")
            return False


if __name__ == "__main__":
    scraper = TransfermarktScraper('https://www.transfermarkt.com/a-lyga/gesamtspielplan/wettbewerb/LI1?saison_id=2024&spieltagVon=1&spieltagBis=36')

    if scraper.fetch_page():
        matches = scraper.parse_matches()

        scraper.save_to_csv(scraper.csv_headers, matches, 'a_lyga_2025.csv')
