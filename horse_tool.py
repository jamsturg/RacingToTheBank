import requests
from typing import Dict, List, Union, Tuple
import math
from datetime import datetime
import logging
import numpy as np
from collections import defaultdict

class EnhancedHorseRacingPredictor:
    def __init__(self):
        self.api_key = '7552b21e-851b-4803-b230-d1637a74f05c'
        self.base_url = 'https://api.puntingform.com.au/v2'
        self.setup_logging()
        
        # Enhanced weighting factors
        self.weight_factors = {
            'time_rating': 0.25,
            'class_rating': 0.20,
            'form_rating': 0.15,
            'track_bias': 0.15,
            'pace_scenario': 0.15,
            'value_rating': 0.10
        }
        
        # Track condition mappings
        self.track_conditions = {
            1: {'name': 'Firm', 'bias': 'Favors horses with good form on firm tracks'},
            2: {'name': 'Good', 'bias': 'Standard track pattern expected'},
            3: {'name': 'Soft', 'bias': 'Advantage to on-pace runners and mud handlers'},
            4: {'name': 'Heavy', 'bias': 'Strong bias towards proven wet trackers and leaders'}
        }

    def setup_logging(self):
        """Configure logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def make_api_request(self, endpoint: str, params: Dict) -> Dict:
        """Enhanced API request handling with retries"""
        MAX_RETRIES = 3
        for attempt in range(MAX_RETRIES):
            try:
                url = f"{self.base_url}/{endpoint}"
                params['apiKey'] = self.api_key
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                self.logger.error(f"API request failed (attempt {attempt + 1}): {str(e)}")
                if attempt == MAX_RETRIES - 1:
                    raise
        return None

    def get_race_data(self, meeting_id: str, race_number: int) -> Dict:
        """Get enhanced race form data"""
        return self.make_api_request('form/form', {
            'meetingId': meeting_id,
            'raceNumber': race_number
        })

    def get_ratings(self, meeting_id: str, race_number: int) -> Dict:
        """Get enhanced ratings data"""
        return self.make_api_request('Ratings/MeetingRatings', {
            'meetingId': meeting_id,
            'raceNumber': race_number
        })

    def calculate_time_score(self, ratings: Dict) -> float:
        """Enhanced time rating calculation"""
        try:
            last_time = float(ratings.get('lastTimeRating', 0))
            best_time = float(ratings.get('bestTimeRating', 0))
            avg_time = float(ratings.get('averageTimeRating', 0))
            
            # Weight recent form more heavily
            weighted_time = (last_time * 0.5) + (best_time * 0.3) + (avg_time * 0.2)
            
            # Normalize to 0-10 scale
            return min(max(weighted_time / 10, 0), 10)
        except (ValueError, TypeError):
            return 0

    def calculate_class_score(self, ratings: Dict) -> float:
        """Enhanced class rating calculation"""
        try:
            class_rating = float(ratings.get('classRating', 0))
            weight_class = float(ratings.get('weightClassRating', 0))
            consistency = float(ratings.get('consistencyRating', 0))
            
            # Weighted combination of class factors
            weighted_class = (
                class_rating * 0.4 +
                weight_class * 0.4 +
                consistency * 0.2
            )
            
            return min(max(weighted_class / 10, 0), 10)
        except (ValueError, TypeError):
            return 0

    def analyze_track_bias(self, barrier: int, run_style: str, track_condition: int, 
                         field_size: int, distance: int) -> float:
        """Enhanced track bias analysis"""
        score = 0
        
        # Distance considerations
        is_sprint = distance <= 1200
        
        # Track condition analysis
        if track_condition >= 3:  # Soft/Heavy
            if run_style.strip() in ['lf', 'mf']:
                score += 0.75 if is_sprint else 0.5
            if barrier <= 4:
                score += 0.75
        else:  # Firm/Good
            if 3 <= barrier <= 6:
                score += 0.5
            if not is_sprint and run_style.strip() in ['mb', 'bm']:
                score += 0.25
        
        # Field size impact
        if field_size > 12:
            if barrier <= 6:
                score += 0.5 if is_sprint else 0.25
        
        # Normalize to 0-10 scale
        return min(score * 2, 10)

    def calculate_pace_pressure(self, pace_map: Dict, run_style: str) -> float:
        """Calculate pace pressure impact"""
        early_speed_count = len(pace_map['early_leaders'])
        
        if run_style in ['lf', 'mf']:
            if early_speed_count <= 2:
                return 8  # Low pressure favors leaders
            elif early_speed_count >= 4:
                return 4  # High pressure compromises leaders
            return 6
        elif run_style in ['mb']:
            if early_speed_count >= 4:
                return 7  # High pressure favors midfield
            return 5
        else:  # Back markers
            if early_speed_count >= 4:
                return 8  # High pressure favors backmarkers
            return 4

    def analyze_race(self, meeting_id: str, race_number: int) -> str:
        try:
            self.logger.info(f"Analyzing race {race_number} at meeting {meeting_id}")
            
            # Fetch race data
            form_data = self.get_race_data(meeting_id, race_number)
            ratings_data = self.get_ratings(meeting_id, race_number)
            
            if not form_data or not ratings_data:
                return "Unable to fetch race data"
            
            # Process race information
            race_info = form_data.get('payLoad', {}).get('raceInfo', {})
            distance = int(race_info.get('distance', 0))
            track_condition = int(race_info.get('trackCondition', 2))
            
            # Process runners
            runners = form_data.get('payLoad', {}).get('runners', [])
            field_size = len(runners)
            
            # Build ratings lookup
            ratings_lookup = {
                rating.get('runnerName'): rating
                for rating in ratings_data.get('payLoad', [])
                if rating.get('raceNo') == race_number
            }
            
            # Analyze pace scenario
            pace_map = self.calculate_pace_scenario(runners, ratings_lookup)
            
            # Score runners
            scored_runners = self.score_runners(
                runners, ratings_lookup, pace_map, 
                field_size, distance, track_condition
            )
            
            # Generate report
            return self.generate_detailed_report(
                scored_runners, pace_map, race_info,
                track_condition, field_size
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing race: {str(e)}")
            return f"Error analyzing race: {str(e)}"

    def score_runners(self, runners: List[Dict], ratings_lookup: Dict, 
                     pace_map: Dict, field_size: int, distance: int, 
                     track_condition: int) -> List[Dict]:
        """Enhanced runner scoring"""
        scored_runners = []
        
        for runner in runners:
            try:
                name = runner.get('name', '')
                ratings = ratings_lookup.get(name, {})
                
                # Calculate component scores
                time_score = self.calculate_time_score(ratings)
                class_score = self.calculate_class_score(ratings)
                form_score = self.analyze_recent_form(runner)
                
                barrier = int(runner.get('barrier', 0))
                run_style = ratings.get('runStyle', '').strip()
                
                bias_score = self.analyze_track_bias(
                    barrier, run_style, track_condition, 
                    field_size, distance
                )
                
                pace_score = self.calculate_pace_pressure(pace_map, run_style)
                value_score = self.calculate_value_rating(ratings)
                
                # Calculate weighted total score
                total_score = (
                    time_score * self.weight_factors['time_rating'] +
                    class_score * self.weight_factors['class_rating'] +
                    form_score * self.weight_factors['form_rating'] +
                    bias_score * self.weight_factors['track_bias'] +
                    pace_score * self.weight_factors['pace_scenario'] +
                    value_score * self.weight_factors['value_rating']
                )
                
                scored_runners.append({
                    'name': name,
                    'total_score': total_score,
                    'component_scores': {
                        'time': time_score,
                        'class': class_score,
                        'form': form_score,
                        'bias': bias_score,
                        'pace': pace_score,
                        'value': value_score
                    },
                    'ratings': ratings,
                    'details': runner
                })
                
            except Exception as e:
                self.logger.error(f"Error scoring runner {name}: {str(e)}")
                continue
        
        return sorted(scored_runners, key=lambda x: x['total_score'], reverse=True)

    def generate_detailed_report(self, scored_runners: List[Dict], pace_map: Dict,
                               race_info: Dict, track_condition: int,
                               field_size: int) -> str:
        """Generate enhanced analysis report"""
        report = ["Advanced Race Analysis", "=" * 50, ""]
        
        # Race Overview
        report.extend([
            "Race Overview:",
            "-" * 30,
            f"Distance: {race_info.get('distance')}m",
            f"Track: {self.track_conditions[track_condition]['name']}",
            f"Field Size: {field_size}",
            f"Track Bias: {self.track_conditions[track_condition]['bias']}",
            ""
        ])
        
        # Pace Analysis
        report.extend([
            "Pace Analysis:",
            "-" * 30,
            f"Early Speed: {len(pace_map['early_leaders'])} front runner(s)",
            f"Pace Pressure: {self.get_pace_pressure_description(pace_map)}",
            f"Likely Leaders: {', '.join(pace_map['early_leaders']) if pace_map['early_leaders'] else 'No clear leader'}",
            ""
        ])
        
        # Top Selections
        report.extend(["Top Selections:", "-" * 30])
        for i, runner in enumerate(scored_runners[:3], 1):
            scores = runner['component_scores']
            report.extend([
                f"\n{i}. {runner['name']}",
                f"Overall Rating: {runner['total_score']:.2f}",
                "Component Scores:",
                f"  Time Rating: {scores['time']:.1f}",
                f"  Class Rating: {scores['class']:.1f}",
                f"  Form Rating: {scores['form']:.1f}",
                f"  Track Bias: {scores['bias']:.1f}",
                f"  Pace Scenario: {scores['pace']:.1f}",
                f"  Value Rating: {scores['value']:.1f}",
                f"Starting Price: ${runner['ratings'].get('fixedOdds', {}).get('current', 'N/A')}",
                "-" * 30
            ])
        
        # Betting Strategy
        report.extend([
            "\nBetting Strategy:",
            self.generate_betting_strategy(scored_runners, pace_map)
        ])
        
        return "\n".join(report)

    def get_pace_pressure_description(self, pace_map: Dict) -> str:
        """Generate pace pressure description"""
        pressure = len(pace_map['early_leaders'])
        if pressure >= 4:
            return "Very Strong - Likely pace collapse"
        elif pressure == 3:
            return "Strong - Favors off-pace runners"
        elif pressure == 2:
            return "Moderate - Balanced pace"
        else:
            return "Slow - Advantage to leaders"

    def generate_betting_strategy(self, scored_runners: List[Dict],
                                pace_map: Dict) -> str:
        """Generate betting strategy recommendations"""
        if not scored_runners:
            return "Insufficient data for betting strategy"
            
        top_score = scored_runners[0]['total_score']
        second_score = scored_runners[1]['total_score'] if len(scored_runners) > 1 else 0
        margin = top_score - second_score
        
        strategies = []
        
        if margin > 3:
            strategies.append("Strong Win Bet - Clear standout selection")
        elif margin > 2:
            strategies.append("Win bet with small saver on second pick")
        elif margin > 1:
            strategies.append("Each-way betting approach recommended")
        else:
            strategies.append("Very competitive race - Consider boxed exotics")
        
        # Exotic betting suggestions
        if len(pace_map['early_leaders']) >= 3:
            strategies.append("Consider including backmarkers in exotics")
        if len(scored_runners) >= 3 and (scored_runners[0]['total_score'] - scored_runners[2]['total_score'] < 2):
            strategies.append("Boxing top 3 selections in trifecta recommended")
            
        return "\n".join(strategies)

def main():
    predictor = EnhancedHorseRacingPredictor()
    
    print("\nHorse Racing Prediction System")
    print("=" * 30)
    
    try:
        meeting_id = input("Enter meeting ID: ")
        race_number = int(input("Enter race number: "))
        
        print("\nAnalyzing race...")
        analysis = predictor.analyze_race(meeting_id, race_number)
        print("\n" + analysis)
        
    except ValueError:
        print("Invalid input. Please enter valid meeting ID and race number.")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()