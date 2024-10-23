
import requests
from datetime import datetime, timedelta

class EnhancedHorseRacingPredictor:
    def __init__(self):
        self.base_url = "https://api.racing.com"

    def get_race_meetings(self, date: str, date_format: str = "%Y-%m-%d"):
        try:
            print(f"Attempting to get race meetings for date: {date}")
            url = f"{self.base_url}/api/horse-racing/meeting/{date}"
            print(f"Accessing URL: {url}")
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers)
            print(f"Status code: {response.status_code}")
            print(f"Response headers: {response.headers}")
            print(f"Raw response: {response.text[:1000]}") # Print only first 1000 characters
            if response.status_code == 200 and response.text:
                meetings = response.json().get('meetings', [])
                print(f"Parsed meetings: {meetings[:5]}") # Print only first 5 meetings
                return meetings
            else:
                print(f"Error: Received status code {response.status_code}")
                return []
        except Exception as e:
            print(f"Error in get_race_meetings: {str(e)}")
            import traceback
            traceback.print_exc()
            return []

# Test the class with multiple dates and formats
predictor = EnhancedHorseRacingPredictor()
today = datetime.now()
dates_to_test = [today + timedelta(days=i) for i in range(-1, 3)]  # Test yesterday, today, tomorrow, and the day after

date_formats = ["%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"]

for date_format in date_formats:
    print(f"\nTesting with date format: {date_format}")
    for date in dates_to_test:
        formatted_date = date.strftime(date_format)
        print(f"\nTesting date: {formatted_date}")
        meetings = predictor.get_race_meetings(formatted_date, date_format)
        print(f"Meetings for {formatted_date}: {len(meetings)} found")

# Also test with a known past date
past_date = "2023-10-21"
print(f"\nTesting past date: {past_date}")
meetings = predictor.get_race_meetings(past_date)
print(f"Meetings for {past_date}: {len(meetings)} found")
