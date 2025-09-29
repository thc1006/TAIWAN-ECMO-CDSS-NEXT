"""
VR Training Protocol and Metrics for ECMO Team Training
Taiwan ECMO CDSS - Virtual Reality Training Module

Standardized protocols for ECMO team training with performance assessment
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TrainingScenario:
    """VR training scenario definition"""
    scenario_id: str
    title: str
    description: str
    ecmo_type: str  # VA or VV
    difficulty_level: str  # Beginner, Intermediate, Advanced
    duration_minutes: int
    learning_objectives: List[str]
    key_skills: List[str]
    assessment_criteria: List[str]
    complications: List[str]

@dataclass
class PerformanceMetrics:
    """Performance metrics for VR training assessment"""
    trainee_id: str
    scenario_id: str
    session_date: datetime
    completion_time_minutes: float
    technical_score: float  # 0-100
    communication_score: float  # 0-100
    decision_making_score: float  # 0-100
    overall_score: float  # 0-100
    errors_count: int
    critical_errors: List[str]
    areas_for_improvement: List[str]
    competency_achieved: bool

class ECMOVRTrainingProtocol:
    """
    ECMO VR Training Protocol Manager
    Manages training scenarios, assessment, and progress tracking
    """
    
    def __init__(self):
        """Initialize VR training protocol system"""
        self.scenarios = self._initialize_scenarios()
        self.performance_data = []
        logger.info("ECMO VR Training Protocol system initialized")
    
    def _initialize_scenarios(self) -> List[TrainingScenario]:
        """Initialize standard ECMO training scenarios"""
        
        scenarios = [
            # VA-ECMO Scenarios
            TrainingScenario(
                scenario_id="VA001",
                title="Emergency VA-ECMO Cannulation",
                description="Patient in cardiogenic shock requiring emergency VA-ECMO support",
                ecmo_type="VA",
                difficulty_level="Intermediate",
                duration_minutes=30,
                learning_objectives=[
                    "Rapid assessment of VA-ECMO candidacy",
                    "Proper cannulation site selection",
                    "Sterile cannulation technique",
                    "Initial ECMO parameter setting"
                ],
                key_skills=[
                    "Ultrasound-guided vessel access",
                    "Cannula positioning",
                    "Circuit priming",
                    "Team communication",
                    "Crisis resource management"
                ],
                assessment_criteria=[
                    "Time to cannulation <60 minutes",
                    "Proper sterile technique maintained",
                    "Appropriate initial flow settings",
                    "Effective team communication",
                    "Recognition of complications"
                ],
                complications=[
                    "Arterial dissection",
                    "Limb ischemia",
                    "Cannula malposition",
                    "Circuit air embolism"
                ]
            ),
            
            TrainingScenario(
                scenario_id="VA002", 
                title="Post-Cardiotomy VA-ECMO",
                description="Failure to wean from cardiopulmonary bypass requiring ECMO support",
                ecmo_type="VA",
                difficulty_level="Advanced",
                duration_minutes=45,
                learning_objectives=[
                    "Recognize failure to wean from CPB",
                    "Transition from CPB to ECMO",
                    "Manage post-operative bleeding",
                    "Optimize hemodynamics on ECMO"
                ],
                key_skills=[
                    "Central cannulation technique",
                    "Coagulation management",
                    "Hemodynamic optimization",
                    "Multi-disciplinary coordination"
                ],
                assessment_criteria=[
                    "Smooth transition from CPB",
                    "Bleeding control achieved",
                    "Appropriate ECMO flows",
                    "Team coordination during crisis"
                ],
                complications=[
                    "Excessive bleeding",
                    "Tamponade",
                    "LV distension", 
                    "Arrhythmias"
                ]
            ),
            
            # VV-ECMO Scenarios
            TrainingScenario(
                scenario_id="VV001",
                title="Severe ARDS VV-ECMO Initiation",
                description="COVID-19 ARDS patient requiring VV-ECMO for respiratory support",
                ecmo_type="VV",
                difficulty_level="Intermediate",
                duration_minutes=35,
                learning_objectives=[
                    "ARDS severity assessment",
                    "VV-ECMO candidacy evaluation", 
                    "Dual-lumen cannula placement",
                    "Lung-protective ventilation on ECMO"
                ],
                key_skills=[
                    "Bicaval cannulation",
                    "Chest imaging interpretation",
                    "Ventilator management",
                    "Infection control protocols"
                ],
                assessment_criteria=[
                    "Appropriate candidate selection",
                    "Successful cannula positioning",
                    "Adequate oxygenation achieved",
                    "Lung rest ventilation settings"
                ],
                complications=[
                    "Cannula malposition",
                    "Recirculation", 
                    "Bleeding at access site",
                    "Ventilator-associated complications"
                ]
            ),
            
            TrainingScenario(
                scenario_id="VV002",
                title="Bridge to Lung Transplant",
                description="End-stage pulmonary fibrosis patient requiring bridge to transplantation",
                ecmo_type="VV",
                difficulty_level="Advanced", 
                duration_minutes=40,
                learning_objectives=[
                    "Transplant candidate assessment",
                    "Long-term ECMO management",
                    "Ambulation on ECMO",
                    "Psychological support strategies"
                ],
                key_skills=[
                    "Ambulatory ECMO setup",
                    "Patient mobilization",
                    "Family counseling",
                    "Multidisciplinary care planning"
                ],
                assessment_criteria=[
                    "Successful ambulatory setup",
                    "Patient safety maintained",
                    "Family education provided",
                    "Transplant readiness achieved"
                ],
                complications=[
                    "Circuit disconnection",
                    "Patient falls",
                    "Psychological distress",
                    "Device malfunction"
                ]
            ),
            
            # Complication Management Scenarios
            TrainingScenario(
                scenario_id="COMP001",
                title="ECMO Circuit Emergency",
                description="Multiple circuit alarms requiring immediate intervention",
                ecmo_type="Both",
                difficulty_level="Advanced",
                duration_minutes=20,
                learning_objectives=[
                    "Rapid alarm interpretation",
                    "Emergency troubleshooting",
                    "Circuit component replacement",
                    "Crisis communication"
                ],
                key_skills=[
                    "Alarm management",
                    "Emergency procedures",
                    "Equipment troubleshooting",
                    "Staff coordination"
                ],
                assessment_criteria=[
                    "Rapid problem identification",
                    "Appropriate corrective actions",
                    "Patient safety maintained",
                    "Clear communication"
                ],
                complications=[
                    "Oxygenator failure",
                    "Pump malfunction",
                    "Air in circuit",
                    "Massive hemolysis"
                ]
            ),
            
            TrainingScenario(
                scenario_id="WEAN001", 
                title="ECMO Weaning and Decannulation",
                description="Successful patient recovery requiring ECMO discontinuation",
                ecmo_type="Both",
                difficulty_level="Intermediate",
                duration_minutes=30,
                learning_objectives=[
                    "Weaning readiness assessment",
                    "Systematic flow reduction",
                    "Decannulation technique",
                    "Post-decannulation monitoring"
                ],
                key_skills=[
                    "Hemodynamic assessment",
                    "Echocardiographic evaluation",
                    "Surgical decannulation",
                    "Vascular closure techniques"
                ],
                assessment_criteria=[
                    "Appropriate weaning protocol",
                    "Successful decannulation",
                    "Hemostasis achieved",
                    "Continued patient stability"
                ],
                complications=[
                    "Weaning failure",
                    "Bleeding at cannula sites",
                    "Hemodynamic instability",
                    "Vascular complications"
                ]
            )
        ]
        
        logger.info(f"Initialized {len(scenarios)} ECMO VR training scenarios")
        return scenarios
    
    def get_scenarios_by_difficulty(self, difficulty: str) -> List[TrainingScenario]:
        """Get scenarios filtered by difficulty level"""
        return [s for s in self.scenarios if s.difficulty_level == difficulty]
    
    def get_scenarios_by_ecmo_type(self, ecmo_type: str) -> List[TrainingScenario]:
        """Get scenarios filtered by ECMO type"""
        return [s for s in self.scenarios if s.ecmo_type == ecmo_type or s.ecmo_type == "Both"]
    
    def assess_performance(self, trainee_id: str, scenario_id: str, 
                          performance_data: Dict) -> PerformanceMetrics:
        """
        Assess trainee performance in VR training scenario
        
        Args:
            trainee_id: Unique trainee identifier
            scenario_id: Training scenario identifier  
            performance_data: Dictionary with performance measurements
            
        Returns:
            PerformanceMetrics object with assessment results
        """
        logger.info(f"Assessing performance for trainee {trainee_id} in scenario {scenario_id}")
        
        scenario = next((s for s in self.scenarios if s.scenario_id == scenario_id), None)
        if not scenario:
            raise ValueError(f"Scenario {scenario_id} not found")
        
        # Calculate component scores
        technical_score = self._calculate_technical_score(performance_data, scenario)
        communication_score = self._calculate_communication_score(performance_data, scenario)
        decision_making_score = self._calculate_decision_making_score(performance_data, scenario)
        
        # Overall score (weighted average)
        overall_score = (
            technical_score * 0.4 + 
            communication_score * 0.3 + 
            decision_making_score * 0.3
        )
        
        # Identify errors and areas for improvement
        errors_count, critical_errors = self._identify_errors(performance_data, scenario)
        areas_for_improvement = self._identify_improvement_areas(performance_data, scenario)
        
        # Determine competency achievement
        competency_achieved = (
            overall_score >= 80 and 
            len(critical_errors) == 0 and
            technical_score >= 75
        )
        
        metrics = PerformanceMetrics(
            trainee_id=trainee_id,
            scenario_id=scenario_id,
            session_date=datetime.now(),
            completion_time_minutes=performance_data.get('completion_time', 0),
            technical_score=technical_score,
            communication_score=communication_score,
            decision_making_score=decision_making_score,
            overall_score=overall_score,
            errors_count=errors_count,
            critical_errors=critical_errors,
            areas_for_improvement=areas_for_improvement,
            competency_achieved=competency_achieved
        )
        
        self.performance_data.append(metrics)
        
        logger.info(f"Assessment complete. Overall score: {overall_score:.1f}")
        
        return metrics
    
    def _calculate_technical_score(self, data: Dict, scenario: TrainingScenario) -> float:
        """Calculate technical skill score"""
        score = 100.0
        
        # Time-based deductions
        expected_time = scenario.duration_minutes
        actual_time = data.get('completion_time', expected_time)
        if actual_time > expected_time * 1.5:
            score -= 20
        elif actual_time > expected_time * 1.2:
            score -= 10
        
        # Technical errors
        technical_errors = data.get('technical_errors', [])
        score -= len(technical_errors) * 5
        
        # Critical technical steps completed
        steps_completed = data.get('critical_steps_completed', 0)
        total_steps = len(scenario.key_skills)
        if total_steps > 0:
            completion_rate = steps_completed / total_steps
            if completion_rate < 0.8:
                score -= (1 - completion_rate) * 30
        
        # Sterile technique maintenance
        if not data.get('sterile_technique_maintained', True):
            score -= 15
        
        return max(score, 0)
    
    def _calculate_communication_score(self, data: Dict, scenario: TrainingScenario) -> float:
        """Calculate communication and teamwork score"""
        score = 100.0
        
        # Team communication effectiveness
        communication_rating = data.get('communication_rating', 5)  # 1-5 scale
        score = communication_rating * 20
        
        # Leadership demonstration
        if data.get('demonstrated_leadership', False):
            score += 10
        
        # Clear instruction giving
        instruction_clarity = data.get('instruction_clarity', 5)  # 1-5 scale
        score += (instruction_clarity - 3) * 5
        
        # Situation awareness
        situation_awareness = data.get('situation_awareness', 5)  # 1-5 scale
        score += (situation_awareness - 3) * 5
        
        return min(max(score, 0), 100)
    
    def _calculate_decision_making_score(self, data: Dict, scenario: TrainingScenario) -> float:
        """Calculate clinical decision-making score"""
        score = 100.0
        
        # Appropriate decisions made
        correct_decisions = data.get('correct_decisions', 0)
        total_decisions = data.get('total_decisions', 1)
        decision_rate = correct_decisions / total_decisions if total_decisions > 0 else 0
        score = decision_rate * 100
        
        # Response to complications
        complications_handled = data.get('complications_handled_correctly', 0)
        total_complications = len(scenario.complications)
        if total_complications > 0 and complications_handled < total_complications:
            score -= (total_complications - complications_handled) * 10
        
        # Priority setting
        priority_score = data.get('priority_setting_score', 5)  # 1-5 scale
        score += (priority_score - 3) * 5
        
        return min(max(score, 0), 100)
    
    def _identify_errors(self, data: Dict, scenario: TrainingScenario) -> Tuple[int, List[str]]:
        """Identify errors made during training"""
        all_errors = data.get('errors', [])
        critical_errors = [e for e in all_errors if e.get('severity') == 'critical']
        
        critical_error_descriptions = [e.get('description', '') for e in critical_errors]
        
        return len(all_errors), critical_error_descriptions
    
    def _identify_improvement_areas(self, data: Dict, scenario: TrainingScenario) -> List[str]:
        """Identify areas needing improvement"""
        areas = []
        
        if data.get('technical_score', 100) < 80:
            areas.append("Technical skills require additional practice")
        
        if data.get('communication_rating', 5) < 4:
            areas.append("Team communication and leadership skills")
        
        if data.get('completion_time', 0) > scenario.duration_minutes * 1.3:
            areas.append("Time management and efficiency")
        
        if not data.get('sterile_technique_maintained', True):
            areas.append("Sterile technique and infection control")
        
        if len(data.get('critical_errors', [])) > 0:
            areas.append("Critical error recognition and prevention")
        
        return areas
    
    def generate_learning_path(self, trainee_id: str) -> List[str]:
        """
        Generate personalized learning path based on performance history
        
        Args:
            trainee_id: Trainee identifier
            
        Returns:
            List of recommended scenario IDs
        """
        trainee_performance = [p for p in self.performance_data if p.trainee_id == trainee_id]
        
        if not trainee_performance:
            # New trainee - start with beginner scenarios
            return [s.scenario_id for s in self.get_scenarios_by_difficulty("Beginner")]
        
        # Analyze recent performance
        recent_performance = sorted(trainee_performance, key=lambda x: x.session_date)[-5:]
        avg_score = np.mean([p.overall_score for p in recent_performance])
        
        # Determine next difficulty level
        if avg_score >= 90:
            next_level = "Advanced"
        elif avg_score >= 75:
            next_level = "Intermediate"
        else:
            next_level = "Beginner"
        
        # Identify weak areas
        weak_areas = []
        if np.mean([p.technical_score for p in recent_performance]) < 75:
            weak_areas.append("technical")
        if np.mean([p.communication_score for p in recent_performance]) < 75:
            weak_areas.append("communication")
        if np.mean([p.decision_making_score for p in recent_performance]) < 75:
            weak_areas.append("decision_making")
        
        # Recommend scenarios
        recommended_scenarios = []
        available_scenarios = self.get_scenarios_by_difficulty(next_level)
        
        # Prioritize based on weak areas
        for scenario in available_scenarios:
            if "technical" in weak_areas and "technique" in scenario.title.lower():
                recommended_scenarios.append(scenario.scenario_id)
            elif "communication" in weak_areas and "team" in ' '.join(scenario.key_skills).lower():
                recommended_scenarios.append(scenario.scenario_id)
            elif "decision_making" in weak_areas and "emergency" in scenario.title.lower():
                recommended_scenarios.append(scenario.scenario_id)
        
        # Add general scenarios if no specific weaknesses
        if not recommended_scenarios:
            recommended_scenarios = [s.scenario_id for s in available_scenarios[:3]]
        
        return recommended_scenarios[:5]  # Limit to 5 recommendations
    
    def generate_competency_report(self, trainee_id: str) -> Dict:
        """
        Generate comprehensive competency report for trainee
        
        Args:
            trainee_id: Trainee identifier
            
        Returns:
            Dictionary with competency assessment
        """
        trainee_performance = [p for p in self.performance_data if p.trainee_id == trainee_id]
        
        if not trainee_performance:
            return {"error": "No performance data found for trainee"}
        
        # Calculate statistics
        total_sessions = len(trainee_performance)
        competent_sessions = len([p for p in trainee_performance if p.competency_achieved])
        competency_rate = competent_sessions / total_sessions if total_sessions > 0 else 0
        
        avg_scores = {
            'overall': np.mean([p.overall_score for p in trainee_performance]),
            'technical': np.mean([p.technical_score for p in trainee_performance]),
            'communication': np.mean([p.communication_score for p in trainee_performance]),
            'decision_making': np.mean([p.decision_making_score for p in trainee_performance])
        }
        
        # Identify scenarios completed
        scenarios_completed = list(set([p.scenario_id for p in trainee_performance]))
        scenarios_passed = list(set([p.scenario_id for p in trainee_performance if p.competency_achieved]))
        
        # Progress tracking
        performance_trend = self._calculate_performance_trend(trainee_performance)
        
        # Common error patterns
        all_errors = []
        for p in trainee_performance:
            all_errors.extend(p.critical_errors)
        
        error_frequency = {}
        for error in all_errors:
            error_frequency[error] = error_frequency.get(error, 0) + 1
        
        report = {
            'trainee_id': trainee_id,
            'report_date': datetime.now().isoformat(),
            'summary': {
                'total_sessions': total_sessions,
                'competency_rate': competency_rate,
                'scenarios_completed': len(scenarios_completed),
                'scenarios_passed': len(scenarios_passed)
            },
            'average_scores': avg_scores,
            'scenarios': {
                'completed': scenarios_completed,
                'passed': scenarios_passed,
                'remaining': [s.scenario_id for s in self.scenarios if s.scenario_id not in scenarios_completed]
            },
            'performance_trend': performance_trend,
            'common_errors': dict(sorted(error_frequency.items(), key=lambda x: x[1], reverse=True)[:5]),
            'recommendations': self.generate_learning_path(trainee_id),
            'competency_status': 'Competent' if competency_rate >= 0.8 else 'Developing'
        }
        
        return report
    
    def _calculate_performance_trend(self, performance_history: List[PerformanceMetrics]) -> str:
        """Calculate performance trend over time"""
        if len(performance_history) < 3:
            return "Insufficient data"
        
        # Sort by date
        sorted_performance = sorted(performance_history, key=lambda x: x.session_date)
        
        # Calculate trend in overall scores
        recent_scores = [p.overall_score for p in sorted_performance[-5:]]
        earlier_scores = [p.overall_score for p in sorted_performance[:-5] if len(sorted_performance) > 5]
        
        if not earlier_scores:
            return "Improving" if len(recent_scores) >= 2 and recent_scores[-1] > recent_scores[0] else "Stable"
        
        recent_avg = np.mean(recent_scores)
        earlier_avg = np.mean(earlier_scores)
        
        if recent_avg > earlier_avg + 5:
            return "Improving"
        elif recent_avg < earlier_avg - 5:
            return "Declining"
        else:
            return "Stable"
    
    def export_training_data(self, filepath: str):
        """Export all training data to file"""
        training_data = {
            'scenarios': [
                {
                    'scenario_id': s.scenario_id,
                    'title': s.title,
                    'description': s.description,
                    'ecmo_type': s.ecmo_type,
                    'difficulty_level': s.difficulty_level,
                    'duration_minutes': s.duration_minutes,
                    'learning_objectives': s.learning_objectives,
                    'key_skills': s.key_skills,
                    'assessment_criteria': s.assessment_criteria,
                    'complications': s.complications
                } for s in self.scenarios
            ],
            'performance_data': [
                {
                    'trainee_id': p.trainee_id,
                    'scenario_id': p.scenario_id,
                    'session_date': p.session_date.isoformat(),
                    'completion_time_minutes': p.completion_time_minutes,
                    'technical_score': p.technical_score,
                    'communication_score': p.communication_score,
                    'decision_making_score': p.decision_making_score,
                    'overall_score': p.overall_score,
                    'errors_count': p.errors_count,
                    'critical_errors': p.critical_errors,
                    'areas_for_improvement': p.areas_for_improvement,
                    'competency_achieved': p.competency_achieved
                } for p in self.performance_data
            ]
        }
        
        with open(filepath, 'w') as f:
            json.dump(training_data, f, indent=2)
        
        logger.info(f"Training data exported to {filepath}")


def generate_demo_training_data() -> ECMOVRTrainingProtocol:
    """Generate demonstration training data"""
    protocol = ECMOVRTrainingProtocol()
    
    # Simulate training sessions for demo trainees
    demo_trainees = ['TRAINEE_001', 'TRAINEE_002', 'TRAINEE_003']
    
    np.random.seed(42)  # For reproducible demo data
    
    for trainee in demo_trainees:
        # Simulate multiple training sessions
        for i in range(np.random.randint(3, 8)):
            scenario_id = np.random.choice([s.scenario_id for s in protocol.scenarios])
            
            # Simulate performance data
            performance_data = {
                'completion_time': np.random.normal(30, 5),
                'technical_errors': ['error1', 'error2'][:np.random.randint(0, 3)],
                'critical_steps_completed': np.random.randint(3, 6),
                'sterile_technique_maintained': np.random.choice([True, False], p=[0.8, 0.2]),
                'communication_rating': np.random.randint(3, 6),
                'demonstrated_leadership': np.random.choice([True, False], p=[0.6, 0.4]),
                'instruction_clarity': np.random.randint(3, 6),
                'situation_awareness': np.random.randint(3, 6),
                'correct_decisions': np.random.randint(2, 5),
                'total_decisions': 5,
                'complications_handled_correctly': np.random.randint(0, 3),
                'priority_setting_score': np.random.randint(3, 6),
                'errors': [{'severity': 'minor', 'description': 'Minor error'}],
                'critical_errors': []
            }
            
            # Add occasional critical errors
            if np.random.random() < 0.1:
                performance_data['critical_errors'] = [{'severity': 'critical', 'description': 'Critical safety violation'}]
            
            protocol.assess_performance(trainee, scenario_id, performance_data)
    
    return protocol


if __name__ == "__main__":
    logger.info("ECMO VR Training Protocol Demo")
    
    # Initialize training protocol
    protocol = generate_demo_training_data()
    
    # Display scenarios
    logger.info(f"Available scenarios: {len(protocol.scenarios)}")
    for scenario in protocol.scenarios:
        logger.info(f"- {scenario.scenario_id}: {scenario.title} ({scenario.ecmo_type}, {scenario.difficulty_level})")
    
    # Generate competency reports
    for trainee in ['TRAINEE_001', 'TRAINEE_002', 'TRAINEE_003']:
        report = protocol.generate_competency_report(trainee)
        logger.info(f"\nTrainee {trainee} Competency Report:")
        logger.info(f"- Overall Score: {report['average_scores']['overall']:.1f}")
        logger.info(f"- Competency Rate: {report['summary']['competency_rate']:.1%}")
        logger.info(f"- Status: {report['competency_status']}")
        logger.info(f"- Trend: {report['performance_trend']}")
    
    # Export training data
    protocol.export_training_data('ecmo_vr_training_data.json')
    
    logger.info("VR Training Protocol demonstration complete")