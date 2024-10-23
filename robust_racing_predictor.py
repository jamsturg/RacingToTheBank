import requests
import logging
from datetime import datetime
from typing import Dict, List
import os

class RobustRacingPredictor:
    def __init__(self):
        self.api_key = '7552b21e-851b-4803-b230-d1637a74f05c'
        self.base_url = 'https://api.puntingform.com.au/v2/form'
        
    def get_race_data(self, meeting_id: str, race_number: int) -> Dict:
        try:
            url = f"{self.base_url}/form"
            params = {
                'meetingId': meeting_id,
                'raceNumber': race_number,
                'apiKey': self.api_key
            }
            response = requests.get(url, params=params)
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            print(f"Error getting race data: {str(e)}")
            return None
    
    def analyze_race(self, meeting_id: str, race_number: int) -> Dict:
        race_data = self.get_race_data(meeting_id, race_number)
        
        if not race_data or 'payLoad' not in race_data:
            return {"error": "Unable to retrieve race data"}
        
        runners = race_data['payLoad']
        if not runners:
            return {"error": "No runners found in race data"}
        
        analysis = {"runners": [], "predictions": [], "pace_analysis": {}}
        
        for runner in runners:
            runner_info = {
                "name": runner.get('name', 'Unknown'),
                "barrier": runner.get('barrier', 'Unknown'),
                "weight": float(runner.get('weight', 58)),
                "jockey": runner.get('jockey', {}).get('fullName', 'Unknown'),
                "trainer": runner.get('trainer', {}).get('fullName', 'Unknown'),
                "prize_money": float(runner.get('prizeMoney', 0)),
                "age": runner.get('age', 'Unknown'),
                "sex": runner.get('sex', 'Unknown')
            }
            
            # Calculate score
            score = 0
            score += min(20, runner_info["prize_money"] / 5000)  # Prize money factor
            score += max(0, 15 - (runner_info["weight"] - 54) * 2)  # Weight factor
            
            try:
                barrier = int(runner_info["barrier"])
                if barrier <= 4:
                    score += 10
                elif barrier <= 8:
                    score += 7
                else:
                    score += 4
            except:
                score += 5
            
            runner_info["score"] = round(score, 2)
            analysis["runners"].append(runner_info)
        
        # Sort runners by score
        analysis["runners"].sort(key=lambda x: x["score"], reverse=True)
        
        # Generate predictions
        total_runners = len(analysis["runners"])
        for i, runner in enumerate(analysis["runners"]):
            confidence = round(100 * (total_runners - i) / total_runners)
            analysis["predictions"].append({
                "position": i + 1,
                "name": runner["name"],
                "score": runner["score"],
                "confidence": confidence
            })
        
        # Pace analysis
        early_speed = []
        mid_pack = []
        backmarkers = []
        
        for runner in analysis["runners"]:
            try:
                barrier = int(runner["barrier"])
                if barrier <= 4 and runner["weight"] < 58:
                    early_speed.append(runner["name"])
                elif barrier <= 8:
                    mid_pack.append(runner["name"])
                else:
                    backmarkers.append(runner["name"])
            except:
                mid_pack.append(runner["name"])
        
        analysis["pace_analysis"] = {
            "early_speed": early_speed,
            "mid_pack": mid_pack,
            "backmarkers": backmarkers,
            "scenario": "Fast" if len(early_speed) >= 3 else "Moderate" if len(early_speed) == 2 else "Slow"
        }
        
        return analysis
    
    def format_report(self, analysis: Dict) -> str:
        if "error" in analysis:
            return f"Error in analysis: {analysis['error']}"
        
        lines = [
            "RACE ANALYSIS REPORT",
            "===================",
            "",
            "TOP SELECTIONS:",
            "--------------"
        ]
        
        for pred in analysis["predictions"][:3]:
            lines.extend([
                f"{pred['position']}. {pred['name']}",
                f"   Score: {pred['score']}",
                f"   Confidence: {pred['confidence']}%"
            ])
        
        lines.extend([
            "",
            "PACE ANALYSIS:",
            "--------------",
            f"Scenario: {analysis['pace_analysis']['scenario']} pace likely"
        ])
        
        if analysis['pace_analysis']['early_speed']:
            lines.append(f"Early Speed: {', '.join(analysis['pace_analysis']['early_speed'])}")
        lines.append(f"Mid Pack: {', '.join(analysis['pace_analysis']['mid_pack'])}")
        if analysis['pace_analysis']['backmarkers']:
            lines.append(f"Backmarkers: {', '.join(analysis['pace_analysis']['backmarkers'])}")
        
        return "\n".join(lines)

def main():
    predictor = RobustRacingPredictor()
    try:
        meeting_id = input("Enter meeting ID: ")
        race_number = int(input("Enter race number: "))
        analysis = predictor.analyze_race(meeting_id, race_number)
        print(predictor.format_report(analysis).replace("\n", "\n"))
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
