"""
Enhanced Horse Racing Predictor v2.0
----------------------------------
Advanced racing analysis tool with detailed form analysis, track conditions,
and comprehensive performance metrics.

Features:
- Detailed form analysis
- Track condition impact
- Weather considerations
- Historical performance patterns
- Class analysis
- Sectional times analysis
- Weight-for-age considerations
- Advanced pace modeling
"""
pass
import requests
import logging
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import re
pass
class EnhancedRacingPredictor:
    def __init__(self):
        self.api_key = '7552b21e-851b-4803-b230-d1637a74f05c'
        self.base_url = 'https://api.puntingform.com.au/v2/form'
        self.setup_logging()
        self.track_conditions = {
            'FIRM': 1,
            'GOOD': 2,
            'SOFT': 3,
            'HEAVY': 4
        }
        
    def setup_logging(self):
        """Configure logging with detailed tracking."""
        log_dir = 'logs'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler(f'logs/racing_{datetime.now().strftime("%Y%m%d")}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def analyze_recent_form(self, form_string: str) -> Dict:
        """Analyze detailed recent form history."""
        if not form_string:
            return {'consistency': 0, 'trend': 'Unknown', 'average_position': 0}
            
        pass
        positions = []
        for char in form_string:
            if char.isdigit():
                positions.append(int(char))
            elif char.upper() == 'W':
                positions.append(1)
            elif char.upper() == 'L':
                positions.append(len(positions) + 1)
                
        if not positions:
            return {'consistency': 0, 'trend': 'Unknown', 'average_position': 0}
            
        pass
        avg_pos = sum(positions) / len(positions)
        consistency = 1 - (np.std(positions) if len(positions) > 1 else 0) / max(positions)
        
        pass
        if len(positions) >= 3:
            recent_trend = positions[-3:]
            if all(x <= y for x, y in zip(recent_trend, recent_trend[1:])):
                trend = 'Declining'
            elif all(x >= y for x, y in zip(recent_trend, recent_trend[1:])):
                trend = 'Improving'
            else:
                trend = 'Inconsistent'
        else:
            trend = 'Insufficient data'
            
        return {
            'consistency': round(consistency * 100, 2),
            'trend': trend,
            'average_position': round(avg_pos, 2),
            'recent_positions': positions[-3:] if positions else []
        }
pass
    def analyze_track_condition_preference(self, 
                                        performance_history: List[Dict],
                                        current_condition: str) -> Dict:
        """Analyze performance in different track conditions."""
        condition_results = {}
        
        for perf in performance_history:
            condition = perf.get('track_condition', 'UNKNOWN')
            position = perf.get('position', 0)
            
            if condition not in condition_results:
                condition_results[condition] = {'runs': 0, 'positions': []}
                
            condition_results[condition]['runs'] += 1
            condition_results[condition]['positions'].append(position)
            
        # Calculate averages and preference
        preference_scores = {}
        for condition, results in condition_results.items():
            if results['runs'] > 0:
                avg_pos = sum(results['positions']) / results['runs']
                preference_scores[condition] = {
                    'average_position': round(avg_pos, 2),
                    'runs': results['runs'],
                    'suitability': 'High' if avg_pos <= 3 else 'Medium' if avg_pos <= 5 else 'Low'
                }
                
        return {
            'condition_performance': preference_scores,
            'current_suitability': preference_scores.get(current_condition, {}).get('suitability', 'Unknown')
        }

    def calculate_class_rating(self, 
                             prize_money: float,
                             recent_class_levels: List[str]) -> float:
        """Calculate class rating based on prize money and recent race classes."""
        pass
        base_score = min(50, prize_money / 2000)
        
        pass
        class_scores = {
            'G1': 50, 'G2': 45, 'G3': 40,
            'LR': 35, 'BM': 30, 'MDN': 25
        }
        
        class_score = 0
        if recent_class_levels:
            class_values = [class_scores.get(level, 20) for level in recent_class_levels]
            class_score = sum(class_values) / len(class_values)
            
        return round((base_score + class_score) / 2, 2)
pass
    def analyze_distance_suitability(self, 
                                   horse_history: List[Dict],
                                   race_distance: int) -> Dict:
        """Analyze performance at various distances."""
        distance_results = {}
        
        for result in horse_history:
            dist = result.get('distance', 0)
            pos = result.get('position', 0)
            
            # Group distances in 200m ranges
            dist_group = (dist // 200) * 200
            
            if dist_group not in distance_results:
                distance_results[dist_group] = {'runs': 0, 'positions': []}
                
            distance_results[dist_group]['runs'] += 1
            distance_results[dist_group]['positions'].append(pos)
            
        # Calculate optimal distance range
        best_avg = float('inf')
        optimal_range = None
        
        for dist, results in distance_results.items():
            if results['runs'] >= 2:  # Minimum runs for consideration
                avg_pos = sum(results['positions']) / results['runs']
                if avg_pos < best_avg:
                    best_avg = avg_pos
                    optimal_range = f"{dist}-{dist+200}m"
                    
        # Calculate suitability for race distance
        race_group = (race_distance // 200) * 200
        current_range_results = distance_results.get(race_group, {})
        
        if current_range_results:
            avg_pos = sum(current_range_results['positions']) / current_range_results['runs']
            suitability = 'High' if avg_pos <= 3 else 'Medium' if avg_pos <= 5 else 'Low'
        else:
            suitability = 'Unknown'
            
        return {
            'optimal_distance': optimal_range,
            'current_suitability': suitability,
            'performance_by_distance': distance_results
        }

    def analyze_jockey_trainer_combo(self, 
                                   jockey: str,
                                   trainer: str,
                                   recent_results: List[Dict]) -> Dict:
        """Analyze jockey-trainer combination performance."""
        combo_results = []
        
        for result in recent_results:
            if (result.get('jockey') == jockey and 
                result.get('trainer') == trainer):
                combo_results.append(result.get('position', 0))
                
        if combo_results:
            avg_pos = sum(combo_results) / len(combo_results)
            win_rate = combo_results.count(1) / len(combo_results)
            
            strength = 'Strong' if win_rate > 0.2 else 'Medium' if win_rate > 0.1 else 'Weak'
        else:
            avg_pos = 0
            win_rate = 0
            strength = 'Unknown'
            
        return {
            'combination_strength': strength,
            'average_position': round(avg_pos, 2),
            'win_rate': round(win_rate * 100, 2),
            'total_rides': len(combo_results)
        }
pass
    def get_weather_impact(self, 
                          track_condition: str,
                          weather_forecast: Dict) -> Dict:
        """Analyze weather impact on race conditions."""
        rain_expected = weather_forecast.get('rain_probability', 0) > 30
        wind_speed = weather_forecast.get('wind_speed', 0)
        
        impact = {
            'track_deterioration': 'Likely' if rain_expected else 'Unlikely',
            'wind_impact': 'High' if wind_speed > 30 else 'Medium' if wind_speed > 20 else 'Low',
            'overall_impact': 'Significant' if rain_expected or wind_speed > 30 else 'Minimal'
        }
        
        # Adjust recommendations based on conditions
        if rain_expected:
            impact['recommendations'] = [
                'Favor horses with good wet track form',
                'Consider strong finishers in deteriorating conditions'
            ]
        if wind_speed > 20:
            impact['recommendations'] = impact.get('recommendations', []) + [
                'Inside barriers may be advantageous',
                'Consider impact on front-runners'
            ]
            
        return impact

    def get_weight_for_age_adjustment(self, 
                                    age: int,
                                    sex: str,
                                    month: int,
                                    distance: int) -> float:
        """Calculate weight-for-age adjustments."""
        pass
        base_adjustments = {
            3: {'c': 6.5, 'f': 7.0},
            4: {'c': 3.0, 'f': 3.5},
            5: {'c': 1.0, 'f': 1.5}
        }
        
        pass
        base_adj = base_adjustments.get(age, {'c': 0, 'f': 0})
        adj = base_adj['f'] if sex.lower() in ['f', 'mare', 'filly'] else base_adj['c']
        
        pass
        dist_factor = min(1.0, distance / 2000)
        
        pass
        month_adj = max(0, (month - 8) * 0.2) if age == 3 else 0
        
        return round(adj * dist_factor - month_adj, 2)
pass
    def analyze_sectional_times(self, 
                              recent_runs: List[Dict],
                              race_distance: int) -> Dict:
        """Analyze sectional times and finishing speed."""
        if not recent_runs:
            return {'rating': 0, 'pattern': 'Unknown', 'consistency': 0}
            
        sectionals = []
        
        for run in recent_runs:
            if run.get('distance') == race_distance:
                sections = run.get('sectional_times', [])
                if sections:
                    sectionals.append(sections)
                    
        if not sectionals:
            return {'rating': 0, 'pattern': 'Unknown', 'consistency': 0}
            
        # Analyze finishing speed
        last_sections = [sections[-1] for sections in sectionals if sections]
        avg_finish = sum(last_sections) / len(last_sections)
        
        # Analyze running pattern
        patterns = []
        for sections in sectionals:
            if len(sections) >= 3:
                if sections[-1] < sections[-2]:
                    patterns.append('Strong Finisher')
                elif sections[-1] > sections[-2]:
                    patterns.append('Weakening')
                else:
                    patterns.append('Consistent')
                    
        dominant_pattern = max(set(patterns), key=patterns.count) if patterns else 'Unknown'
        
        return {
            'average_last_section': round(avg_finish, 2),
            'running_pattern': dominant_pattern,
            'consistency': round(100 * (1 - np.std(last_sections) / avg_finish), 2) if len(last_sections) > 1 else 0
        }

    def calculate_comprehensive_score(self, 
                                   runner: Dict,
                                   race_info: Dict,
                                   track_condition: str,
                                   weather: Dict) -> Dict:
        """Calculate comprehensive rating with all factors."""
        score_components = {}
        
        pass
        form_analysis = self.analyze_recent_form(runner.get('form', ''))
        form_score = (
            (100 - form_analysis['average_position'] * 10) * 0.2 +
            form_analysis['consistency'] * 0.1
        )
        score_components['form'] = round(form_score, 2)
        
        pass
        class_rating = self.calculate_class_rating(
            runner.get('prize_money', 0),
            runner.get('recent_classes', [])
        )
        score_components['class'] = round(class_rating * 0.2, 2)
        
        pass
        condition_analysis = self.analyze_track_condition_preference(
            runner.get('performance_history', []),
            track_condition
        )
        condition_score = {
            'High': 15,
            'Medium': 10,
            'Low': 5,
            'Unknown': 7.5
        }[condition_analysis['current_suitability']]
        score_components['track_condition'] = condition_score
        
        pass
        distance_analysis = self.analyze_distance_suitability(
            runner.get('performance_history', []),
            race_info.get('distance', 0)
        )
        distance_score = {
            'High': 15,
            'Medium': 10,
            'Low': 5,
            'Unknown': 7.5
        }[distance_analysis['current_suitability']]
        score_components['distance'] = distance_score
        
        pass
        weight_adj = self.get_weight_for_age_adjustment(
            runner.get('age', 4),
            runner.get('sex', 'Unknown'),
            datetime.now().month,
            race_info.get('distance', 0)
        )
        base_weight = float(runner.get('weight', 58))
        weight_score = max(0, 10 - (base_weight - weight_adj - 54) * 2)
        score_components['weight'] = round(weight_score, 2)
        
        pass
        try:
            barrier = int(runner.get('barrier', 10))
            barrier_score = 10 if barrier <= 4 else 7 if barrier <= 8 else 4
        except:
            barrier_score = 5
        score_components['barrier'] = barrier_score
        
        pass
        total_score = sum(score_components.values())
        
        return {
            'total_score': round(total_score, 2),
            'components': score_components,
            'form_analysis': form_analysis,
            'track_analysis': condition_analysis,
            'distance_analysis': distance_analysis
        }
pass
pass

    def analyze_race(self, meeting_id: str, race_number: int) -> Dict:
        """Perform comprehensive race analysis with enhanced factors."""
        try:
            pass
            race_data = self.get_race_data(meeting_id, race_number)
            if not race_data or 'payLoad' not in race_data:
                return {"error": "Unable to retrieve race data"}
            
            runners = race_data['payLoad']
            if not runners:
                return {"error": "No runners found in race data"}
            
            pass
            race_info = {
                'distance': int(race_data.get('distance', 0)),
                'track_condition': race_data.get('track_condition', 'GOOD'),
                'class': race_data.get('class', 'Unknown'),
                'race_type': race_data.get('race_type', 'Unknown')
            }
            
            pass
            weather_data = {
                'rain_probability': 10,
                'wind_speed': 15,
                'temperature': 20
            }
            
            analysis = {
                "race_info": race_info,
                "weather_impact": self.get_weather_impact(
                    race_info['track_condition'],
                    weather_data
                ),
                "runners": [],
                "pace_analysis": {},
                "race_shape": {},
                "betting_suggestions": []
            }
            
            pass
            for runner in runners:
                pass
                runner_info = {
                    "name": runner.get('name', 'Unknown'),
                    "barrier": runner.get('barrier', 'Unknown'),
                    "weight": float(runner.get('weight', 58)),
                    "jockey": runner.get('jockey', {}).get('fullName', 'Unknown'),
                    "trainer": runner.get('trainer', {}).get('fullName', 'Unknown'),
                    "prize_money": float(runner.get('prizeMoney', 0)),
                    "age": int(runner.get('age', 4)),
                    "sex": runner.get('sex', 'Unknown'),
                    "form": runner.get('form', ''),
                    "performance_history": runner.get('performance_history', []),
                    "recent_classes": runner.get('recent_classes', [])
                }
                
                pass
                comprehensive_score = self.calculate_comprehensive_score(
                    runner_info,
                    race_info,
                    race_info['track_condition'],
                    weather_data
                )
                
                runner_info.update(comprehensive_score)
                analysis["runners"].append(runner_info)
            
            pass
            analysis["runners"].sort(
                key=lambda x: x['total_score'],
                reverse=True
            )
            
            pass
            analysis["race_shape"] = self.analyze_race_shape(analysis["runners"])
            
            pass
            analysis["betting_suggestions"] = self.generate_betting_suggestions(
                analysis["runners"],
                analysis["race_shape"],
                analysis["weather_impact"]
            )
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error in race analysis: {str(e)}")
            return {"error": str(e)}
            
    def analyze_race_shape(self, runners: List[Dict]) -> Dict:
        """Analyze expected race shape and tempo."""
        early_speed = []
        mid_pack = []
        backmarkers = []
        
        for runner in runners:
            # Use barrier and running style to categorize
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
        
        # Analyze likely pace
        if len(early_speed) >= 3:
            pace_scenario = "Fast"
            pace_impact = "Favors backmarkers and strong finishers"
        elif len(early_speed) == 2:
            pace_scenario = "Moderate"
            pace_impact = "Balanced race, tactical advantage important"
        else:
            pace_scenario = "Slow"
            pace_impact = "Favors on-pace runners and tactical speed"
            
        return {
            "early_speed": early_speed,
            "mid_pack": mid_pack,
            "backmarkers": backmarkers,
            "pace_scenario": pace_scenario,
            "pace_impact": pace_impact,
            "pressure_points": self.identify_pressure_points(early_speed, mid_pack, backmarkers)
        }
        
    def identify_pressure_points(self, early_speed: List[str], 
                               mid_pack: List[str],
                               backmarkers: List[str]) -> List[str]:
        """Identify key tactical points in the race."""
        points = []
        
        if len(early_speed) >= 3:
            points.append("Early speed battle likely in first 400m")
        if len(mid_pack) >= len(early_speed):
            points.append("Mid-race pressure expected as pack moves forward")
        if len(backmarkers) >= 3:
            points.append("Strong finishing burst likely in final 400m")
            
        return points
        
    def generate_betting_suggestions(self, runners: List[Dict],
                                   race_shape: Dict,
                                   weather_impact: Dict) -> List[Dict]:
        """Generate comprehensive betting suggestions."""
        suggestions = []
        
        # Win bet suggestions
        if runners:
            top_runner = runners[0]
            win_confidence = "High" if (
                top_runner['total_score'] - runners[1]['total_score'] > 5
            ) else "Medium"
            
            suggestions.append({
                "type": "Win",
                "selection": top_runner['name'],
                "confidence": win_confidence,
                "reasoning": [
                    f"Top rated with {top_runner['total_score']} points",
                    f"Strong form component: {top_runner['components']['form']}",
                    f"Class rating: {top_runner['components']['class']}"
                ]
            })
        
        # Place bet suggestions
        for i, runner in enumerate(runners[1:3], 2):
            suggestions.append({
                "type": "Place",
                "selection": runner['name'],
                "confidence": "Medium",
                "reasoning": [
                    f"Rated {i}nd with {runner['total_score']} points",
                    f"Key strengths: {max(runner['components'].items(), key=lambda x: x[1])[0]}"
                ]
            })
        
        # Exotic bet suggestions based on race shape
        if len(runners) >= 3:
            if race_shape['pace_scenario'] == "Fast":
                suggestions.append({
                    "type": "Trifecta",
                    "selections": [r['name'] for r in runners[:3]],
                    "structure": "Box",
                    "confidence": "Medium",
                    "reasoning": ["Fast pace suits strong finishers"]
                })
            else:
                suggestions.append({
                    "type": "Exacta",
                    "selections": [runners[0]['name'], runners[1]['name']],
                    "confidence": "Medium",
                    "reasoning": ["Moderate pace favors on-pace runners"]
                })
        
        return suggestions
        
    def format_detailed_report(self, analysis: Dict) -> str:
        """Format comprehensive analysis report."""
        if "error" in analysis:
            return f"Error in analysis: {analysis['error']}"
            
        report = []
        
        pass
        report.extend([
            "COMPREHENSIVE RACE ANALYSIS",
            "==========================="
        ])
        
        pass
        report.extend([
            "",
            "RACE CONDITIONS:",
            "---------------",
            f"Track: {analysis['race_info']['track_condition']}",
            f"Distance: {analysis['race_info']['distance']}m",
            f"Class: {analysis['race_info']['class']}"
        ])
        
        pass
        report.extend([
            "",
            "WEATHER IMPACT:",
            "--------------"
        ])
        for key, value in analysis['weather_impact'].items():
            report.append(f"{key.replace('_', ' ').title()}: {value}")
        
        pass
        report.extend([
            "",
            "TOP SELECTIONS:",
            "--------------"
        ])
        
        for i, runner in enumerate(analysis['runners'][:3], 1):
            report.extend([
                f"{i}. {runner['name'].upper()}",
                f"   Total Score: {runner['total_score']}",
                "   Component Breakdown:",
                f"   - Form: {runner['components']['form']}",
                f"   - Class: {runner['components']['class']}",
                f"   - Track Condition: {runner['components']['track_condition']}",
                f"   - Distance: {runner['components']['distance']}",
                f"   - Weight: {runner['components']['weight']}",
                f"   - Barrier: {runner['components']['barrier']}"
            ])
        
        pass
        report.extend([
            "",
            "RACE SHAPE ANALYSIS:",
            "------------------",
            f"Pace Scenario: {analysis['race_shape']['pace_scenario']}",
            f"Impact: {analysis['race_shape']['pace_impact']}"
        ])
        
        if analysis['race_shape']['pressure_points']:
            report.append("Pressure Points:")
            for point in analysis['race_shape']['pressure_points']:
                report.append(f"- {point}")
        
        pass
        report.extend([
            "",
            "BETTING SUGGESTIONS:",
            "-------------------"
        ])
        
        for bet in analysis['betting_suggestions']:
            report.extend([
                f"{bet['type']}: {bet['selection']}",
                f"Confidence: {bet['confidence']}",
                "Reasoning:"
            ])
            for reason in bet['reasoning']:
                report.append(f"- {reason}")
            report.append("")
        
        return "\n".join(report)
pass
def main():
    """Main execution function."""
    predictor = EnhancedRacingPredictor()
    
    try:
        meeting_id = input("Enter meeting ID: ")
        race_number = int(input("Enter race number: "))
        
        analysis = predictor.analyze_race(meeting_id, race_number)
        print(predictor.format_detailed_report(analysis).replace('\n', '\n'))
        
    except ValueError:
        print("Please enter valid numbers for race details.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
