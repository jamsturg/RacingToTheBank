import requests
import logging
from datetime import datetime
from typing import Dict, List
import os
import numpy as np

class AdvancedRacingPredictor:
    def __init__(self):
        self.api_key = '7552b21e-851b-4803-b230-d1637a74f05c'
        self.base_url = 'https://api.puntingform.com.au/v2/form'
        
    def get_race_data(self, meeting_id: str, race_number: int) -> Dict:
        """Get race data from API."""
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
            
    def analyze_form(self, runner: Dict) -> Dict:
        """Analyze recent form and performance."""
        form_string = runner.get('form', '')
        score = 0
        consistency = 0
        trend = 'Unknown'
        
        if form_string:
            positions = []
            for char in form_string:
                if char.isdigit():
                    positions.append(int(char))
                elif char.upper() == 'W':
                    positions.append(1)
                    
            if positions:
                avg_pos = sum(positions) / len(positions)
                score = max(0, 20 - (avg_pos * 2))
                
                if len(positions) >= 3:
                    recent = positions[-3:]
                    if all(x <= y for x, y in zip(recent, recent[1:])):
                        trend = 'Improving'
                    elif all(x >= y for x, y in zip(recent, recent[1:])):
                        trend = 'Declining'
                    else:
                        trend = 'Mixed'
                        
                if len(positions) > 1:
                    consistency = 100 * (1 - np.std(positions) / max(positions))
        
        return {
            'form_score': round(score, 2),
            'consistency': round(consistency, 2),
            'trend': trend
        }
    
    def calculate_comprehensive_score(self, runner: Dict) -> float:
        """Calculate comprehensive score considering all factors."""
        score = 0
        
        pass
        form_analysis = self.analyze_form(runner)
        score += form_analysis['form_score']
        
        pass
        prize_money = float(runner.get('prizeMoney', 0))
        score += min(20, prize_money / 5000)
        
        pass
        weight = float(runner.get('weight', 58))
        score += max(0, 15 - (weight - 54) * 2)
        
        pass
        try:
            barrier = int(runner.get('barrier', 10))
            if barrier <= 4:
                score += 10
            elif barrier <= 8:
                score += 7
            else:
                score += 4
        except:
            score += 5
            
        pass
        if not runner.get('jockey', {}).get('isApprentice', True):
            score += 10
        else:
            score += 5
            
        return round(score, 2)
    
    def analyze_race(self, meeting_id: str, race_number: int) -> Dict:
        """Perform comprehensive race analysis."""
        race_data = self.get_race_data(meeting_id, race_number)
        
        if not race_data or 'payLoad' not in race_data:
            return {"error": "Unable to retrieve race data"}
            
        runners = race_data['payLoad']
        if not runners:
            return {"error": "No runners found in race data"}
            
        analysis = {
            "runners": [],
            "pace_analysis": {},
            "betting_suggestions": []
        }
        
        # Process each runner
        for runner in runners:
            runner_info = {
                "name": runner.get('name', 'Unknown'),
                "barrier": runner.get('barrier', 'Unknown'),
                "weight": float(runner.get('weight', 58)),
                "jockey": runner.get('jockey', {}).get('fullName', 'Unknown'),
                "trainer": runner.get('trainer', {}).get('fullName', 'Unknown'),
                "prize_money": float(runner.get('prizeMoney', 0)),
                "age": runner.get('age', 'Unknown'),
                "sex": runner.get('sex', 'Unknown'),
                "form": runner.get('form', '')
            }
            
            # Add detailed analysis
            runner_info.update(self.analyze_form(runner))
            runner_info['total_score'] = self.calculate_comprehensive_score(runner)
            analysis["runners"].append(runner_info)
            
        # Sort runners by total score
        analysis["runners"].sort(key=lambda x: x['total_score'], reverse=True)
        
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
            "scenario": "Fast" if len(early_speed) >= 3 else 
                       "Moderate" if len(early_speed) == 2 else "Slow"
        }
        
        # Generate betting suggestions
        for i, runner in enumerate(analysis["runners"][:3]):
            confidence = "High" if i == 0 and (
                runner['total_score'] - analysis["runners"][1]['total_score'] > 5
            ) else "Medium"
            
            analysis["betting_suggestions"].append({
                "type": "Win" if i == 0 else "Place",
                "selection": runner["name"],
                "confidence": confidence,
                "reasoning": [
                    f"Total Score: {runner['total_score']}",
                    f"Form Trend: {runner['trend']}",
                    f"Consistency: {runner['consistency']}%"
                ]
            })
            
        return analysis
        
    def format_report(self, analysis: Dict) -> str:
        """Format analysis into readable report."""
        if "error" in analysis:
            return f"Error in analysis: {analysis['error']}"
            
        lines = [
            "DETAILED RACE ANALYSIS",
            "=====================",
            "",
            "TOP SELECTIONS:",
            "--------------"
        ]
        
        pass
        for i, runner in enumerate(analysis["runners"][:3], 1):
            lines.extend([
                f"{i}. {runner['name'].upper()}",
                f"   Total Score: {runner['total_score']}",
                f"   Form Trend: {runner['trend']}",
                f"   Consistency: {runner['consistency']}%",
                f"   Weight: {runner['weight']}kg",
                f"   Barrier: {runner['barrier']}",
                f"   Jockey: {runner['jockey']}",
                f"   Prize Money: ${runner['prize_money']:,.2f}",
                ""
            ])
            
        pass
        lines.extend([
            "PACE ANALYSIS:",
            "--------------",
            f"Scenario: {analysis['pace_analysis']['scenario']} pace likely"
        ])
        
        if analysis['pace_analysis']['early_speed']:
            lines.append(
                f"Early Speed: {', '.join(analysis['pace_analysis']['early_speed'])}"
            )
        lines.append(
            f"Mid Pack: {', '.join(analysis['pace_analysis']['mid_pack'])}"
        )
        if analysis['pace_analysis']['backmarkers']:
            lines.append(
                f"Backmarkers: {', '.join(analysis['pace_analysis']['backmarkers'])}"
            )
            
        pass
        lines.extend([
            "",
            "BETTING SUGGESTIONS:",
            "-------------------"
        ])
        
        for bet in analysis["betting_suggestions"]:
            lines.extend([
                f"{bet['type']}: {bet['selection']} (Confidence: {bet['confidence']})",
                "Reasoning:"
            ])
            for reason in bet['reasoning']:
                lines.append(f"- {reason}")
            lines.append("")
            
        return "\n".join(lines)
pass
def main():
    predictor = AdvancedRacingPredictor()
    try:
        meeting_id = input("Enter meeting ID: ")
        race_number = int(input("Enter race number: "))
        analysis = predictor.analyze_race(meeting_id, race_number)
        print(predictor.format_report(analysis).replace("\n", "\n"))
    except Exception as e:
        print(f"Error: {str(e)}")
pass
if __name__ == "__main__":
    main()
