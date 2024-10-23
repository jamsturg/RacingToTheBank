
import re
import csv
from datetime import datetime
from collections import defaultdict

class HorseRacingPredictor:
    def __init__(self, file_path):
        self.file_path = file_path
        self.races = []
        self.horses = []
        self.raw_content = ""

    def load_data(self):
        with open(self.file_path, 'r', encoding='ISO-8859-1') as file:
            self.raw_content = file.read()
        self._extract_races(self.raw_content)
        self._extract_horses(self.raw_content)

    def _extract_races(self, content):
        race_pattern = r'Belmont Park - (.*?) - Race (\d+)\n(.*?)\n\n(.*?)\nRail (.*?)Of \$(.*?) -'
        match = re.search(race_pattern, content, re.DOTALL)
        if match:
            self.races.append({
                'date': match.group(1),
                'number': match.group(2),
                'name': match.group(3),
                'conditions': match.group(4),
                'rail_position': match.group(5),
                'prize_money': match.group(6)
            })
        else:
            print("No race information found.")

    def _extract_horses(self, content):
        horse_pattern = r'(\d+)\s+(\S.*?)\s+(\d+(?:\.\d+)?)\s+(\d+)\s+([\d.]+)\s+(\d+)\s+([\d.]+)\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)'
        matches = re.finditer(horse_pattern, content)
        for match in matches:
            self.horses.append({
                'number': match.group(1),
                'name': match.group(2).strip(),
                'weight': float(match.group(3)),
                'barrier': int(match.group(4)),
                'map_a2e': float(match.group(5)),
                'pfais': int(match.group(6)),
                'pfaip': float(match.group(7)),
                'rating': float(match.group(8)),
                'price': float(match.group(9)),
                'win_percentage': float(match.group(10)),
                'score': 0
            })
        if not self.horses:
            print("No horses found. Check the horse_pattern regex.")

    def calculate_scores(self):
        if not self.horses:
            print("No horses found. Unable to calculate scores.")
            return

        max_weight = max(horse['weight'] for horse in self.horses)
        min_weight = min(horse['weight'] for horse in self.horses)
        weight_range = max_weight - min_weight

        max_rating = max(horse['rating'] for horse in self.horses)
        min_rating = min(horse['rating'] for horse in self.horses)
        rating_range = max_rating - min_rating

        for horse in self.horses:
            score = 0
            
            # Weight score (lower is better)
            if weight_range > 0:
                weight_score = (max_weight - horse['weight']) / weight_range
                score += weight_score * 20
            
            # Barrier score (middle barriers are generally better)
            barrier_score = 10 - abs(7 - horse['barrier'])
            score += barrier_score * 15
            
            # Rating score (higher is better)
            if rating_range > 0:
                rating_score = (horse['rating'] - min_rating) / rating_range
                score += rating_score * 30
            
            # Price score (lower price is generally better)
            price_score = 100 / horse['price']
            score += price_score * 10
            
            # Win percentage score
            score += horse['win_percentage'] * 3
            
            # Map A2E score (not sure what this represents, but we'll include it)
            score += horse['map_a2e'] * 5
            
            horse['score'] = score

            print(f"Debug: {horse['name']} - Weight: {horse['weight']}, Rating: {horse['rating']}, Score: {score:.2f}")

    def get_predictions(self):
        sorted_horses = sorted(self.horses, key=lambda x: x['score'], reverse=True)
        return sorted_horses

    def generate_report(self):
        self.calculate_scores()
        predictions = self.get_predictions()
        
        report = "Horse Racing Prediction Report\n"
        report += "=" * 30 + "\n\n"
        
        for race in self.races:
            report += f"Race {race['number']}: {race['name']}\n"
            report += f"Date: {race['date']}\n"
            report += f"Conditions: {race['conditions']}\n"
            report += f"Rail Position: {race['rail_position']}\n"
            report += f"Prize Money: ${race['prize_money']}\n"
            report += "-" * 30 + "\n"
        
        report += "\nTop 3 Predictions:\n"
        for i, horse in enumerate(predictions[:3], 1):
            report += f"{i}. {horse['name']} (Number: {horse['number']}, Score: {horse['score']:.2f})\n"
            report += f"   Weight: {horse['weight']}kg, Barrier: {horse['barrier']}, Rating: {horse['rating']}, Price: {horse['price']}\n"
            report += f"   Win Percentage: {horse['win_percentage']}%, Map A2E: {horse['map_a2e']}\n\n"
        
        report += "All horses ranked:\n"
        for i, horse in enumerate(predictions, 1):
            report += f"{i}. {horse['name']} (Score: {horse['score']:.2f})\n"
        
        return report

# Usage
predictor = HorseRacingPredictor(r"C:\Users\sulli\OneDrive\Desktop\form.csv")
predictor.load_data()
report = predictor.generate_report()
print(report)

# Save the report to a file
with open('racing_prediction_report.txt', 'w') as f:
    f.write(report)
print("Report saved to racing_prediction_report.txt")
