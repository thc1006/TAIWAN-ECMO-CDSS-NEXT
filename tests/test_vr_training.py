"""
Unit Tests for VR Training Assessment (WP3)
Tests scenario loading, performance scoring, statistical analysis, and report generation.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime
import tempfile
import yaml

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'vr-training'))

from assessment import (
    ScenarioLoader,
    VRSessionScorer,
    PerformanceReporter,
    TrainingOutcomeAnalyzer,
    ScenarioPerformance,
    DecisionPoint,
    OSCEScore,
    KnowledgeTest,
    ParticipantProfile
)


# ============================================================================
# SCENARIO LOADER TESTS
# ============================================================================

class TestScenarioLoader:
    """Test VR scenario loading."""

    def test_load_scenarios_from_dict(self, synthetic_vr_scenarios, temp_yaml_file):
        """Test loading scenarios from YAML file."""
        # Write test scenarios to file
        with open(temp_yaml_file, 'w') as f:
            yaml.dump(synthetic_vr_scenarios, f)

        loader = ScenarioLoader(scenarios_path=temp_yaml_file)

        assert len(loader.scenarios) > 0
        assert 'SCN-001' in loader.scenarios

    def test_get_scenario(self, synthetic_vr_scenarios, temp_yaml_file):
        """Test retrieving specific scenario."""
        with open(temp_yaml_file, 'w') as f:
            yaml.dump(synthetic_vr_scenarios, f)

        loader = ScenarioLoader(scenarios_path=temp_yaml_file)
        scenario = loader.get_scenario('SCN-001')

        assert scenario is not None
        assert scenario['id'] == 'SCN-001'
        assert 'decision_points' in scenario

    def test_get_all_scenarios(self, synthetic_vr_scenarios, temp_yaml_file):
        """Test retrieving all scenarios."""
        with open(temp_yaml_file, 'w') as f:
            yaml.dump(synthetic_vr_scenarios, f)

        loader = ScenarioLoader(scenarios_path=temp_yaml_file)
        all_scenarios = loader.get_all_scenarios()

        assert isinstance(all_scenarios, list)
        assert len(all_scenarios) == len(synthetic_vr_scenarios['scenarios'])

    def test_missing_file_warning(self):
        """Test warning when scenario file is missing."""
        loader = ScenarioLoader(scenarios_path='nonexistent.yaml')
        assert len(loader.scenarios) == 0


# ============================================================================
# VR SESSION SCORER TESTS
# ============================================================================

class TestVRSessionScorer:
    """Test VR session scoring."""

    def test_score_session_basic(self, synthetic_vr_log_data, synthetic_vr_scenarios, temp_yaml_file):
        """Test basic session scoring."""
        # Write scenarios to file
        with open(temp_yaml_file, 'w') as f:
            yaml.dump(synthetic_vr_scenarios, f)

        loader = ScenarioLoader(scenarios_path=temp_yaml_file)
        scorer = VRSessionScorer(scenario_loader=loader)

        manual_scores = {
            'technical_skill': 82.0,
            'nirs_interpretation': 75.0,
            'complication_management': 78.0,
            'communication': 85.0
        }

        performance = scorer.score_session(synthetic_vr_log_data, manual_scores)

        assert isinstance(performance, ScenarioPerformance)
        assert performance.session_id == 'VR-2025-001'
        assert performance.participant_id == 'P001'
        assert 0 <= performance.total_score <= 100

    def test_decision_point_scoring(self, synthetic_vr_log_data, synthetic_vr_scenarios, temp_yaml_file):
        """Test decision point scoring."""
        with open(temp_yaml_file, 'w') as f:
            yaml.dump(synthetic_vr_scenarios, f)

        loader = ScenarioLoader(scenarios_path=temp_yaml_file)
        scorer = VRSessionScorer(scenario_loader=loader)

        performance = scorer.score_session(synthetic_vr_log_data)

        # Check decision points were scored
        assert len(performance.decision_points) > 0

        for dp in performance.decision_points:
            assert isinstance(dp, DecisionPoint)
            assert hasattr(dp, 'is_correct')
            assert hasattr(dp, 'points_awarded')

    def test_calculate_totals(self, synthetic_vr_log_data, synthetic_vr_scenarios, temp_yaml_file):
        """Test total metrics calculation."""
        with open(temp_yaml_file, 'w') as f:
            yaml.dump(synthetic_vr_scenarios, f)

        loader = ScenarioLoader(scenarios_path=temp_yaml_file)
        scorer = VRSessionScorer(scenario_loader=loader)

        performance = scorer.score_session(synthetic_vr_log_data)

        # Check totals calculated
        assert performance.total_decisions > 0
        assert performance.correct_decisions <= performance.total_decisions
        assert 0 <= performance.decision_accuracy_pct <= 100

    def test_critical_error_detection(self, synthetic_vr_scenarios, temp_yaml_file):
        """Test critical error detection."""
        # Create log with incorrect critical decision
        vr_log = {
            'session_id': 'TEST-001',
            'participant_id': 'P001',
            'scenario_id': 'SCN-001',
            'scenario_title': 'Test Scenario',
            'difficulty': 'beginner',
            'ecmo_mode': 'VA',
            'start_time': '2025-10-05T09:00:00',
            'end_time': '2025-10-05T09:30:00',
            'total_duration_min': 30.0,
            'first_attempt_success': False,
            'scenario_completed': True,
            'complications_encountered': [],
            'decision_points': [
                {
                    'id': 'DP-001-01',
                    'timestamp_min': 2.0,
                    'selected_option': 'subclavian',  # Wrong answer
                    'time_to_decision_sec': 45.2
                }
            ]
        }

        with open(temp_yaml_file, 'w') as f:
            yaml.dump(synthetic_vr_scenarios, f)

        loader = ScenarioLoader(scenarios_path=temp_yaml_file)
        scorer = VRSessionScorer(scenario_loader=loader)

        performance = scorer.score_session(vr_log)

        # Should detect critical error
        assert performance.critical_errors > 0


# ============================================================================
# PERFORMANCE REPORTER TESTS
# ============================================================================

class TestPerformanceReporter:
    """Test performance report generation."""

    def test_generate_text_report(self, synthetic_vr_log_data, synthetic_vr_scenarios, temp_yaml_file):
        """Test text report generation."""
        with open(temp_yaml_file, 'w') as f:
            yaml.dump(synthetic_vr_scenarios, f)

        loader = ScenarioLoader(scenarios_path=temp_yaml_file)
        scorer = VRSessionScorer(scenario_loader=loader)
        reporter = PerformanceReporter()

        performance = scorer.score_session(synthetic_vr_log_data)
        report = reporter.generate_session_report(performance, output_format='text')

        assert isinstance(report, str)
        assert 'PERFORMANCE REPORT' in report
        assert 'Total Score' in report
        assert performance.participant_id in report

    def test_generate_json_report(self, synthetic_vr_log_data, synthetic_vr_scenarios, temp_yaml_file):
        """Test JSON report generation."""
        with open(temp_yaml_file, 'w') as f:
            yaml.dump(synthetic_vr_scenarios, f)

        loader = ScenarioLoader(scenarios_path=temp_yaml_file)
        scorer = VRSessionScorer(scenario_loader=loader)
        reporter = PerformanceReporter()

        performance = scorer.score_session(synthetic_vr_log_data)
        report = reporter.generate_session_report(performance, output_format='json')

        import json
        data = json.loads(report)
        assert 'session_id' in data
        assert 'total_score' in data

    def test_performance_interpretation(self, synthetic_vr_log_data, synthetic_vr_scenarios, temp_yaml_file):
        """Test performance level interpretation."""
        with open(temp_yaml_file, 'w') as f:
            yaml.dump(synthetic_vr_scenarios, f)

        loader = ScenarioLoader(scenarios_path=temp_yaml_file)
        scorer = VRSessionScorer(scenario_loader=loader)
        reporter = PerformanceReporter()

        # High score
        performance = scorer.score_session(synthetic_vr_log_data)
        performance.total_score = 90

        interpretation = reporter._interpret_performance(performance)
        assert 'EXPERT' in interpretation

        # Low score
        performance.total_score = 40
        interpretation = reporter._interpret_performance(performance)
        assert 'NEEDS IMPROVEMENT' in interpretation

    def test_generate_recommendations(self, synthetic_vr_log_data, synthetic_vr_scenarios, temp_yaml_file):
        """Test recommendation generation."""
        with open(temp_yaml_file, 'w') as f:
            yaml.dump(synthetic_vr_scenarios, f)

        loader = ScenarioLoader(scenarios_path=temp_yaml_file)
        scorer = VRSessionScorer(scenario_loader=loader)
        reporter = PerformanceReporter()

        performance = scorer.score_session(synthetic_vr_log_data)

        # Set low scores
        performance.technical_skill_score = 60
        performance.critical_errors = 2

        recommendations = reporter._generate_recommendations(performance)

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0


# ============================================================================
# STATISTICAL ANALYZER TESTS
# ============================================================================

class TestTrainingOutcomeAnalyzer:
    """Test statistical analysis."""

    def test_compare_groups_basic(self):
        """Test basic group comparison."""
        np.random.seed(42)
        intervention = np.random.normal(78, 12, 50)
        control = np.random.normal(68, 15, 50)

        analyzer = TrainingOutcomeAnalyzer()
        results = analyzer.compare_groups(intervention, control)

        # Check structure
        assert 'intervention' in results
        assert 'control' in results
        assert 'statistical_tests' in results

        # Check descriptive stats
        assert 'mean' in results['intervention']
        assert 'std' in results['intervention']
        assert 'n' in results['intervention']

    def test_compare_groups_statistics(self):
        """Test statistical test results."""
        np.random.seed(42)
        intervention = np.random.normal(78, 12, 50)
        control = np.random.normal(68, 15, 50)

        analyzer = TrainingOutcomeAnalyzer()
        results = analyzer.compare_groups(intervention, control)

        # Check t-test
        assert 't_statistic' in results['statistical_tests']['independent_t_test']
        assert 'p_value' in results['statistical_tests']['independent_t_test']
        assert 'cohens_d' in results['statistical_tests']['independent_t_test']

        # Check Mann-Whitney U
        assert 'u_statistic' in results['statistical_tests']['mann_whitney_u']
        assert 'p_value' in results['statistical_tests']['mann_whitney_u']

    def test_effect_size_interpretation(self):
        """Test Cohen's d interpretation."""
        analyzer = TrainingOutcomeAnalyzer()

        assert analyzer._interpret_cohens_d(0.1) == "negligible"
        assert analyzer._interpret_cohens_d(0.3) == "small"
        assert analyzer._interpret_cohens_d(0.6) == "medium"
        assert analyzer._interpret_cohens_d(1.0) == "large"

    def test_knowledge_retention_analysis(self):
        """Test knowledge retention over time."""
        np.random.seed(42)
        n = 30

        baseline = np.random.normal(60, 10, n)
        post = baseline + np.random.normal(15, 5, n)
        month3 = post - np.random.normal(3, 2, n)
        month6 = month3 - np.random.normal(2, 2, n)

        analyzer = TrainingOutcomeAnalyzer()
        results = analyzer.analyze_knowledge_retention(baseline, post, month3, month6)

        # Check structure
        assert 'timepoint_statistics' in results
        assert 'pairwise_comparisons' in results
        assert 'retention_6month' in results

        # Check timepoints
        assert 'baseline' in results['timepoint_statistics']
        assert 'post_training' in results['timepoint_statistics']
        assert '6_month' in results['timepoint_statistics']

    def test_correlate_vr_with_osce(self):
        """Test correlation between VR and OSCE scores."""
        np.random.seed(42)
        vr_scores = np.random.normal(75, 10, 50)
        # OSCE correlated with VR
        osce_scores = vr_scores + np.random.normal(0, 5, 50)

        analyzer = TrainingOutcomeAnalyzer()
        results = analyzer.correlate_vr_performance_with_osce(vr_scores, osce_scores)

        # Check structure
        assert 'pearson' in results
        assert 'spearman' in results

        # Check correlation is positive and strong
        assert results['pearson']['r'] > 0.5
        assert 'r_squared' in results['pearson']

    def test_learning_curve_fitting(self):
        """Test learning curve model fitting."""
        np.random.seed(42)

        # Simulate learning: exponential improvement
        scenario_numbers = list(range(1, 11))
        scores = [50 + 40 * (1 - np.exp(-0.3 * t)) + np.random.normal(0, 3)
                  for t in scenario_numbers]

        analyzer = TrainingOutcomeAnalyzer()
        results = analyzer.generate_learning_curve(scores, scenario_numbers)

        # Check structure
        if 'model_parameters' in results:
            assert 'asymptotic_performance' in results['model_parameters']
            assert 'learning_rate_lambda' in results['model_parameters']
            assert 'fit_statistics' in results


# ============================================================================
# DATA MODEL TESTS
# ============================================================================

class TestDataModels:
    """Test data model classes."""

    def test_scenario_performance_calculate_totals(self):
        """Test ScenarioPerformance totals calculation."""
        performance = ScenarioPerformance(
            session_id='TEST-001',
            participant_id='P001',
            scenario_id='SCN-001',
            scenario_title='Test',
            difficulty='beginner',
            ecmo_mode='VA',
            start_time=datetime.now(),
            end_time=datetime.now(),
            total_duration_min=30.0
        )

        # Add decision points
        performance.decision_points = [
            DecisionPoint(
                id='DP1',
                timestamp_min=1.0,
                question='Q1',
                selected_option='A',
                correct_option='A',
                is_correct=True,
                is_critical=False,
                scoring_weight=10,
                time_to_decision_sec=30.0,
                points_awarded=10.0
            ),
            DecisionPoint(
                id='DP2',
                timestamp_min=2.0,
                question='Q2',
                selected_option='B',
                correct_option='A',
                is_correct=False,
                is_critical=True,
                scoring_weight=20,
                time_to_decision_sec=45.0,
                points_awarded=0.0
            )
        ]

        performance.calculate_totals()

        assert performance.total_decisions == 2
        assert performance.correct_decisions == 1
        assert performance.decision_accuracy_pct == 50.0
        assert performance.critical_errors == 1

    def test_osce_score_calculate_totals(self):
        """Test OSCEScore totals calculation."""
        osce = OSCEScore(
            participant_id='P001',
            assessment_date=datetime.now(),
            assessor_id='A001',
            pre_cannulation_assessment=18.0,
            cannulation_technique=16.0,
            circuit_management=17.0,
            nirs_monitoring=15.0,
            complication_recognition=14.0,
            grs_technical_skill=6,
            grs_knowledge=5,
            grs_judgment=6,
            grs_efficiency=5,
            grs_communication=6,
            grs_professionalism=6
        )

        osce.calculate_totals()

        # Total should be sum of station scores
        expected_total = 18 + 16 + 17 + 15 + 14
        assert osce.total_score == expected_total

        # GRS total should be converted to 0-100 scale
        assert 0 <= osce.grs_total <= 100

    def test_knowledge_test_calculate_totals(self):
        """Test KnowledgeTest totals calculation."""
        test = KnowledgeTest(
            participant_id='P001',
            test_date=datetime.now(),
            timepoint='baseline',
            indications_contraindications=75.0,
            circuit_physiology=80.0,
            cannulation_techniques=70.0,
            nirs_monitoring=85.0
        )

        test.calculate_totals()

        # Total should be average of domain scores
        expected = (75 + 80 + 70 + 85) / 4
        assert test.total_score == expected


# ============================================================================
# EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_decision_points(self, synthetic_vr_scenarios, temp_yaml_file):
        """Test handling of session with no decision points."""
        vr_log = {
            'session_id': 'TEST-001',
            'participant_id': 'P001',
            'scenario_id': 'SCN-001',
            'scenario_title': 'Test',
            'difficulty': 'beginner',
            'ecmo_mode': 'VA',
            'start_time': '2025-10-05T09:00:00',
            'end_time': '2025-10-05T09:30:00',
            'total_duration_min': 30.0,
            'first_attempt_success': True,
            'scenario_completed': True,
            'decision_points': []  # Empty
        }

        with open(temp_yaml_file, 'w') as f:
            yaml.dump(synthetic_vr_scenarios, f)

        loader = ScenarioLoader(scenarios_path=temp_yaml_file)
        scorer = VRSessionScorer(scenario_loader=loader)

        performance = scorer.score_session(vr_log)

        assert performance.total_decisions == 0
        assert performance.decision_accuracy_pct == 0.0

    def test_all_wrong_answers(self, synthetic_vr_scenarios, temp_yaml_file):
        """Test scoring with all incorrect answers."""
        vr_log = {
            'session_id': 'TEST-001',
            'participant_id': 'P001',
            'scenario_id': 'SCN-001',
            'scenario_title': 'Test',
            'difficulty': 'beginner',
            'ecmo_mode': 'VA',
            'start_time': '2025-10-05T09:00:00',
            'end_time': '2025-10-05T09:30:00',
            'total_duration_min': 30.0,
            'first_attempt_success': False,
            'scenario_completed': True,
            'decision_points': [
                {
                    'id': 'DP-001-01',
                    'timestamp_min': 2.0,
                    'selected_option': 'subclavian',  # Wrong
                    'time_to_decision_sec': 45.2
                }
            ]
        }

        with open(temp_yaml_file, 'w') as f:
            yaml.dump(synthetic_vr_scenarios, f)

        loader = ScenarioLoader(scenarios_path=temp_yaml_file)
        scorer = VRSessionScorer(scenario_loader=loader)

        performance = scorer.score_session(vr_log)

        assert performance.decision_accuracy_pct == 0.0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
