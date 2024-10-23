"""
Advanced Horse Racing Analysis Tool
---------------------------------
Comprehensive racing analysis with form, track conditions, and detailed predictions.
Version: 2.0
"""
pass
import requests
import logging
from datetime import datetime
from typing import Dict, List
import os
import numpy as np
pass
class TrackAnalyzer:
    """Track condition analysis component."""
    def __init__(self):
        self.conditions = {
            'FIRM': {'description': 'Fast track', 'rating': 1},
            'GOOD': {'description': 'Ideal conditions', 'rating': 2},
            'SOFT': {'description': 'Some give in track', 'rating': 3},
            'HEAVY': {'description': 'Significant moisture', 'rating': 4}
        }
    
    def analyze_condition(self, condition: str) -> Dict:
        """Analyze track condition impact."""
        condition = condition.upper()
        if condition in self.conditions:
            return {
                'condition': condition,
                'description': self.conditions[condition]['description'],
                'rating': self.conditions[condition]['rating'],
                'racing_style': self.get_preferred_style(condition),
                'recommendations': self.get_recommendations(condition)
            }
        return {
            'condition': 'UNKNOWN',
            'description': 'Condition not specified',
            'rating': 2,
            'racing_style': 'Versatile',
            'recommendations': ['Consider standard form']
        }
    
    def get_preferred_style(self, condition: str) -> str:
        """Determine preferred racing style for condition."""
        styles = {
            'FIRM': 'Front-runners and on-pace',
            'GOOD': 'All racing styles',
            'SOFT': 'Strong finishers and tractable runners',
            'HEAVY': 'Proven wet-trackers and strong finishers'
        }
        return styles.get(condition.upper(), 'Versatile')
    
    def get_recommendations(self, condition: str) -> List[str]:
        """Get specific recommendations for track condition."""
        recs = {
            'FIRM': [
                'Favor horses with good tactical speed',
                'Inside barriers advantageous',
                'Watch for front-runners'
            ],
            'GOOD': [
                'True form guide conditions',
                'All running styles have chance',
                'Focus on class and fitness'
            ],
            'SOFT': [
                'Consider wet track form',
                'Favor strong finishers',
                'Watch for pattern development'
            ],
            'HEAVY': [
                'Proven wet track form crucial',
                'Fitness very important',
                'Consider weight more carefully'
            ]
        }
        return recs.get(condition.upper(), ['Standard form analysis recommended'])
pass
class FormAnalyzer:
    """Detailed form analysis component."""
    def analyze_form(self, form_string: str, prize_money: float) -> Dict:
        """Analyze recent form and performance."""
        if not form_string:
            return {
                'form_score': 0,
                'consistency': 0,
                'trend': 'Unknown',
                'class_rating': min(20, prize_money / 5000)
            }
        
        positions = []
        for char in form_string:
            if char.isdigit():
                positions.append(int(char))
            elif char.upper() == 'W':
                positions.append(1)
        
        if not positions:
            return {
                'form_score': 0,
                'consistency': 0,
                'trend': 'Unknown',
                'class_rating': min(20, prize_money / 5000)
            }
        
        avg_pos = sum(positions) / len(positions)
        form_score = max(0, 20 - (avg_pos * 2))
        
        pass
        trend = 'Unknown'
        if len(positions) >= 3:
            recent = positions[-3:]
            if all(x <= y for x, y in zip(recent, recent[1:])):
                trend = 'Improving'
            elif all(x >= y for x, y in zip(recent, recent[1:])):
                trend = 'Declining'
            else:
                trend = 'Mixed'
        
        pass
        consistency = 0
        if len(positions) > 1:
            consistency = 100 * (1 - np.std(positions) / max(positions))
        
        pass
        class_rating = min(20, prize_money / 5000)
        
        return {
            'form_score': round(form_score, 2),
            'consistency': round(consistency, 2),
            'trend': trend,
            'class_rating': round(class_rating, 2)
        }
pass
class AdvancedRacingPredictor:
    """Main racing prediction and analysis class."""
    def __init__(self):
        self.api_key = '7552b21e-851b-4803-b230-d1637a74f05c'
        self.base_url = 'https://api.puntingform.com.au/v2/form'
        self.track_analyzer = TrackAnalyzer()
        self.form_analyzer = FormAnalyzer()
        
    def get_race_data(self, meeting_id: str, race_number: int) -> Dict:
        """Get comprehensive race data."""
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
    
    def calculate_comprehensive_score(self, runner: Dict, track_analysis: Dict) -> Dict:
        """Calculate detailed score with all factors."""
        # Get form analysis
        form_analysis = self.form_analyzer.analyze_form(
            runner.get('form', ''),
            float(runner.get('prizeMoney', 0))
        )
        
        # Base score components
        score_components = {
            'form': form_analysis['form_score'],
            'class': form_analysis['class_rating'],
            'weight': 0,
            'barrier': 0,
            'jockey': 0,
            'track_condition': 0
        }
        
        # Weight factor (max 15 points)
        weight = float(runner.get('weight', 58))
        score_components['weight'] = max(0, 15 - (weight - 54) * 2)
        
        # Barrier factor (max 10 points)
        try:
            barrier = int(runner.get('barrier', 10))
            if barrier <= 4:
                score_components['barrier'] = 10
            elif barrier <= 8:
                score_components['barrier'] = 7
            else:
                score_components['barrier'] = 4
        except:
            score_components['barrier'] = 5
        
        # Jockey factor (max 15 points)
        if not runner.get('jockey', {}).get('isApprentice', True):
            score_components['jockey'] = 10
        else:
            score_components['jockey'] = 5
        
        # Track condition adjustment
        if track_analysis['condition'] != 'UNKNOWN':
            score_components['track_condition'] = (
                10 if track_analysis['racing_style'] == 'All racing styles'
                else 7
            )
        
        # Calculate total score
        total_score = sum(score_components.values())
        
        return {
            'total_score': round(total_score, 2),
            'components': {k: round(v, 2) for k, v in score_components.items()},
            'form_analysis': form_analysis
        }
    
    def analyze_race(self, meeting_id: str, race_number: int) -> Dict:
        """Perform comprehensive race analysis."""
        race_data = self.get_race_data(meeting_id, race_number)
        
        if not race_data or 'payLoad' not in race_data:
            return {"error": "Unable to retrieve race data"}
        
        runners = race_data['payLoad']
        if not runners:
            return {"error": "No runners found in race data"}
        
        pass
        track_condition = race_data.get('track_condition', 'GOOD')
        track_analysis = self.track_analyzer.analyze_condition(track_condition)
        
        analysis = {
            "track_analysis": track_analysis,
            "runners": [],
            "pace_analysis": {},
            "betting_suggestions": []
        }
        
        pass
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
            
            pass
            score_analysis = self.calculate_comprehensive_score(runner, track_analysis)
            runner_info.update(score_analysis)
            analysis["runners"].append(runner_info)
        
        pass
        analysis["runners"].sort(key=lambda x: x['total_score'], reverse=True)
        
        pass
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
        
        pass
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
                    f"Form Trend: {runner['form_analysis']['trend']}",
                    f"Class Rating: {runner['components']['class']}",
                    f"Track Condition: Suited" if runner['components']['track_condition'] >= 7
                    else "Track Condition: Acceptable"
                ]
            })
        
        return analysis
    
    def format_report(self, analysis: Dict) -> str:
        """Format comprehensive analysis report."""
        if "error" in analysis:
            return f"Error in analysis: {analysis['error']}"
        
        lines = [
            "COMPREHENSIVE RACE ANALYSIS",
            "=========================",
            "",
            "TRACK ANALYSIS:",
            "--------------",
            f"Condition: {analysis['track_analysis']['condition']}",
            f"Description: {analysis['track_analysis']['description']}",
            f"Preferred Style: {analysis['track_analysis']['racing_style']}",
            "",
            "Recommendations:",
        ]
        
        for rec in analysis['track_analysis']['recommendations']:
            lines.append(f"- {rec}")
        
        lines.extend([
            "",
            "TOP SELECTIONS:",
            "--------------"
        ])
        
        for i, runner in enumerate(analysis["runners"][:3], 1):
            lines.extend([
                f"{i}. {runner['name'].upper()}",
                f"   Total Score: {runner['total_score']}",
                "   Component Breakdown:",
                f"   - Form: {runner['components']['form']}",
                f"   - Class: {runner['components']['class']}",
                f"   - Weight: {runner['components']['weight']}",
                f"   - Barrier: {runner['components']['barrier']}",
                f"   - Jockey: {runner['components']['jockey']}",
                f"   - Track Condition: {runner['components']['track_condition']}",
                f"   Form Trend: {runner['form_analysis']['trend']}",
                f"   Consistency: {runner['form_analysis']['consistency']}%",
                f"   Weight: {runner['weight']}kg",
                f"   Barrier: {runner['barrier']}",
                f"   Jockey: {runner['jockey']}",
                ""
            ])
        
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

def main():
    predictor = AdvancedRacingPredictor()
    try:
        meeting_id = input("Enter meeting ID: ")
        race_number = int(input("Enter race number: "))
        analysis = predictor.analyze_race(meeting_id, race_number)
        print(predictor.format_report(analysis).replace("\n", "\n"))
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
