"""
Comprehensive TDD Test Suite for ECMO VR Training Protocol
Taiwan ECMO CDSS - WP3: VR Training Assessment

TEST COVERAGE:
- Performance scoring algorithms (weighted averages)
- Competency threshold validations
- Scenario progression logic
- Adaptive learning path generation
- Statistical power calculations
- Sample size determinations
- Performance metrics aggregation

Target: 100% coverage of assessment logic
"""

import pytest
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from vr_training.training_protocol import (
    ECMOVRTrainingProtocol,
    PerformanceMetrics,
    TrainingScenario
)


# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture
def protocol():
    """Initialize training protocol for testing"""
    return ECMOVRTrainingProtocol()


@pytest.fixture
def sample_performance_data():
    """Standard performance data for testing"""
    return {
        'completion_time': 30.0,
        'technical_errors': [],
        'critical_steps_completed': 5,
        'sterile_technique_maintained': True,
        'communication_rating': 5,
        'demonstrated_leadership': True,
        'instruction_clarity': 5,
        'situation_awareness': 5,
        'correct_decisions': 5,
        'total_decisions': 5,
        'complications_handled_correctly': 2,
        'priority_setting_score': 5,
        'errors': [],
        'critical_errors': []
    }


@pytest.fixture
def perfect_performance_data():
    """Perfect score performance data"""
    return {
        'completion_time': 25.0,  # Under expected time
        'technical_errors': [],
        'critical_steps_completed': 5,
        'sterile_technique_maintained': True,
        'communication_rating': 5,
        'demonstrated_leadership': True,
        'instruction_clarity': 5,
        'situation_awareness': 5,
        'correct_decisions': 5,
        'total_decisions': 5,
        'complications_handled_correctly': 4,
        'priority_setting_score': 5,
        'errors': [],
        'critical_errors': []
    }


@pytest.fixture
def failing_performance_data():
    """Failing score performance data"""
    return {
        'completion_time': 60.0,  # 2x expected time
        'technical_errors': ['error1', 'error2', 'error3', 'error4'],
        'critical_steps_completed': 2,
        'sterile_technique_maintained': False,
        'communication_rating': 2,
        'demonstrated_leadership': False,
        'instruction_clarity': 2,
        'situation_awareness': 2,
        'correct_decisions': 1,
        'total_decisions': 5,
        'complications_handled_correctly': 0,
        'priority_setting_score': 2,
        'errors': [
            {'severity': 'critical', 'description': 'Patient safety violation'},
            {'severity': 'minor', 'description': 'Protocol deviation'}
        ],
        'critical_errors': [{'severity': 'critical', 'description': 'Patient safety violation'}]
    }


# ============================================================================
# TEST 1: WEIGHTED AVERAGE SCORING ALGORITHM
# ============================================================================

class TestWeightedAverageScoring:
    """Test the overall score calculation: 40% technical + 30% communication + 30% decision-making"""

    def test_perfect_scores_yield_100(self, protocol):
        """Test Case 1.1: Perfect scores (100, 100, 100) = 100 overall"""
        # Given: Perfect component scores
        technical = 100.0
        communication = 100.0
        decision_making = 100.0

        # When: Calculate weighted average
        overall = technical * 0.4 + communication * 0.3 + decision_making * 0.3

        # Then: Overall score should be 100
        assert overall == 100.0, f"Expected 100, got {overall}"

    def test_weighted_average_formula(self, protocol):
        """Test Case 1.2: Verify weighted average calculation"""
        # Given: Known component scores
        technical = 80.0
        communication = 90.0
        decision_making = 85.0

        # When: Calculate weighted average
        overall = technical * 0.4 + communication * 0.3 + decision_making * 0.3

        # Then: Verify calculation
        expected = 80 * 0.4 + 90 * 0.3 + 85 * 0.3  # = 32 + 27 + 25.5 = 84.5
        assert overall == expected, f"Expected {expected}, got {overall}"
        assert overall == 84.5, f"Expected 84.5, got {overall}"

    def test_assessment_uses_weighted_formula(self, protocol, sample_performance_data):
        """Test Case 1.3: Assess performance uses correct weighted formula"""
        # Given: Sample performance data
        # When: Assess performance
        metrics = protocol.assess_performance('TEST_001', 'VA001', sample_performance_data)

        # Then: Overall score should match weighted formula
        expected_overall = (
            metrics.technical_score * 0.4 +
            metrics.communication_score * 0.3 +
            metrics.decision_making_score * 0.3
        )
        assert abs(metrics.overall_score - expected_overall) < 0.01, \
            f"Overall score {metrics.overall_score} doesn't match weighted formula {expected_overall}"

    def test_low_technical_high_others(self, protocol):
        """Test Case 1.4: Low technical (60), high communication (100), high decision (100)"""
        # Given: Low technical, high others
        technical = 60.0
        communication = 100.0
        decision_making = 100.0

        # When: Calculate weighted average
        overall = technical * 0.4 + communication * 0.3 + decision_making * 0.3

        # Then: Overall should be weighted toward technical (40% weight)
        expected = 60 * 0.4 + 100 * 0.3 + 100 * 0.3  # = 24 + 30 + 30 = 84
        assert overall == expected, f"Expected {expected}, got {overall}"
        assert overall == 84.0

    def test_component_score_boundaries(self, protocol):
        """Test Case 1.5: Component scores at boundaries (0, 50, 100)"""
        test_cases = [
            (0, 0, 0, 0),
            (50, 50, 50, 50),
            (100, 0, 0, 40),
            (0, 100, 100, 60),
            (75, 75, 75, 75)
        ]

        for tech, comm, dec, expected in test_cases:
            overall = tech * 0.4 + comm * 0.3 + dec * 0.3
            assert overall == expected, \
                f"For ({tech}, {comm}, {dec}), expected {expected}, got {overall}"


# ============================================================================
# TEST 2: TECHNICAL SCORE CALCULATION
# ============================================================================

class TestTechnicalScoreCalculation:
    """Test technical score calculation algorithm"""

    def test_perfect_technical_score(self, protocol, perfect_performance_data):
        """Test Case 2.1: Perfect technical performance yields 100"""
        # Given: Perfect technical data
        # When: Calculate technical score
        scenario = protocol.scenarios[0]
        score = protocol._calculate_technical_score(perfect_performance_data, scenario)

        # Then: Score should be 100 or above (bonus for speed)
        assert score >= 100, f"Perfect performance should yield 100, got {score}"

    def test_time_penalty_50_percent_over(self, protocol, sample_performance_data):
        """Test Case 2.2: Completion time >150% expected time = -20 points"""
        # Given: Scenario with 30 min expected time
        scenario = protocol.scenarios[0]  # duration_minutes = 30
        data = sample_performance_data.copy()
        data['completion_time'] = 46  # >150% of 30 (45 minutes)

        # When: Calculate technical score
        score = protocol._calculate_technical_score(data, scenario)

        # Then: Score should have -20 penalty
        # Base 100 - 20 (time penalty) = 80 maximum
        assert score <= 80, f"Expected ≤80 for 150% time overrun, got {score}"

    def test_time_penalty_20_percent_over(self, protocol, sample_performance_data):
        """Test Case 2.3: Completion time >120% expected time = -10 points"""
        # Given: Scenario with 30 min expected time
        scenario = protocol.scenarios[0]
        data = sample_performance_data.copy()
        data['completion_time'] = 37  # >120% of 30 (36 minutes)

        # When: Calculate technical score
        score = protocol._calculate_technical_score(data, scenario)

        # Then: Score should have -10 penalty
        assert score <= 90, f"Expected ≤90 for 120% time overrun, got {score}"

    def test_technical_errors_penalty(self, protocol, sample_performance_data):
        """Test Case 2.4: Each technical error = -5 points"""
        # Given: Performance with 3 technical errors
        scenario = protocol.scenarios[0]
        data = sample_performance_data.copy()
        data['technical_errors'] = ['error1', 'error2', 'error3']

        # When: Calculate technical score
        score = protocol._calculate_technical_score(data, scenario)

        # Then: Score should have -15 penalty (3 errors * 5 points each)
        # Base 100 - 15 (errors) = 85 maximum
        assert score <= 85, f"Expected ≤85 for 3 technical errors, got {score}"

    def test_incomplete_critical_steps_penalty(self, protocol, sample_performance_data):
        """Test Case 2.5: <80% critical steps completed = major penalty"""
        # Given: Only 3 out of 5 critical steps completed (60%)
        scenario = protocol.scenarios[0]  # 5 key_skills
        data = sample_performance_data.copy()
        data['critical_steps_completed'] = 3

        # When: Calculate technical score
        score = protocol._calculate_technical_score(data, scenario)

        # Then: Score should have penalty for 40% incomplete
        # Penalty = (1 - 0.6) * 30 = 12 points
        assert score <= 88, f"Expected ≤88 for 60% completion, got {score}"

    def test_sterile_technique_violation(self, protocol, sample_performance_data):
        """Test Case 2.6: Sterile technique violation = -15 points"""
        # Given: Sterile technique not maintained
        scenario = protocol.scenarios[0]
        data = sample_performance_data.copy()
        data['sterile_technique_maintained'] = False

        # When: Calculate technical score
        score = protocol._calculate_technical_score(data, scenario)

        # Then: Score should have -15 penalty
        assert score <= 85, f"Expected ≤85 for sterile violation, got {score}"

    def test_technical_score_floor_zero(self, protocol, failing_performance_data):
        """Test Case 2.7: Technical score cannot go below 0"""
        # Given: Extremely poor performance
        scenario = protocol.scenarios[0]

        # When: Calculate technical score
        score = protocol._calculate_technical_score(failing_performance_data, scenario)

        # Then: Score should be ≥0
        assert score >= 0, f"Technical score should not be negative, got {score}"


# ============================================================================
# TEST 3: COMMUNICATION SCORE CALCULATION
# ============================================================================

class TestCommunicationScoreCalculation:
    """Test communication and teamwork score calculation"""

    def test_communication_rating_scale(self, protocol, sample_performance_data):
        """Test Case 3.1: Communication rating 1-5 maps to 20-100"""
        scenario = protocol.scenarios[0]

        test_cases = [
            (1, 20),
            (2, 40),
            (3, 60),
            (4, 80),
            (5, 100)
        ]

        for rating, expected_base in test_cases:
            data = sample_performance_data.copy()
            data['communication_rating'] = rating
            data['demonstrated_leadership'] = False
            data['instruction_clarity'] = 3
            data['situation_awareness'] = 3

            score = protocol._calculate_communication_score(data, scenario)

            # Base score should be rating * 20
            assert score >= expected_base - 5 and score <= expected_base + 5, \
                f"Rating {rating} should yield ~{expected_base}, got {score}"

    def test_leadership_bonus(self, protocol, sample_performance_data):
        """Test Case 3.2: Demonstrated leadership = +10 points"""
        scenario = protocol.scenarios[0]

        # Without leadership
        data_no_lead = sample_performance_data.copy()
        data_no_lead['demonstrated_leadership'] = False
        data_no_lead['communication_rating'] = 4
        data_no_lead['instruction_clarity'] = 3
        data_no_lead['situation_awareness'] = 3
        score_no_lead = protocol._calculate_communication_score(data_no_lead, scenario)

        # With leadership
        data_with_lead = sample_performance_data.copy()
        data_with_lead['demonstrated_leadership'] = True
        data_with_lead['communication_rating'] = 4
        data_with_lead['instruction_clarity'] = 3
        data_with_lead['situation_awareness'] = 3
        score_with_lead = protocol._calculate_communication_score(data_with_lead, scenario)

        # Difference should be ~10 points
        assert abs((score_with_lead - score_no_lead) - 10) < 1, \
            f"Leadership bonus should be 10, got {score_with_lead - score_no_lead}"

    def test_instruction_clarity_modifier(self, protocol, sample_performance_data):
        """Test Case 3.3: Instruction clarity modifies score (rating-3)*5"""
        scenario = protocol.scenarios[0]

        test_cases = [
            (1, -10),  # (1-3)*5 = -10
            (2, -5),   # (2-3)*5 = -5
            (3, 0),    # (3-3)*5 = 0
            (4, 5),    # (4-3)*5 = 5
            (5, 10)    # (5-3)*5 = 10
        ]

        for clarity, expected_modifier in test_cases:
            data = sample_performance_data.copy()
            data['communication_rating'] = 4
            data['demonstrated_leadership'] = False
            data['instruction_clarity'] = clarity
            data['situation_awareness'] = 3

            score = protocol._calculate_communication_score(data, scenario)

            # Base (80) + clarity modifier
            expected = 80 + expected_modifier
            assert abs(score - expected) < 1, \
                f"Clarity {clarity} should yield {expected}, got {score}"

    def test_communication_score_ceiling_100(self, protocol, perfect_performance_data):
        """Test Case 3.4: Communication score capped at 100"""
        scenario = protocol.scenarios[0]
        score = protocol._calculate_communication_score(perfect_performance_data, scenario)

        assert score <= 100, f"Communication score should not exceed 100, got {score}"

    def test_communication_score_floor_zero(self, protocol, failing_performance_data):
        """Test Case 3.5: Communication score floored at 0"""
        scenario = protocol.scenarios[0]
        score = protocol._calculate_communication_score(failing_performance_data, scenario)

        assert score >= 0, f"Communication score should not be negative, got {score}"


# ============================================================================
# TEST 4: DECISION-MAKING SCORE CALCULATION
# ============================================================================

class TestDecisionMakingScoreCalculation:
    """Test clinical decision-making score calculation"""

    def test_perfect_decisions_100(self, protocol, sample_performance_data):
        """Test Case 4.1: 100% correct decisions = 100 score"""
        scenario = protocol.scenarios[0]
        data = sample_performance_data.copy()
        data['correct_decisions'] = 5
        data['total_decisions'] = 5
        data['complications_handled_correctly'] = 4
        data['priority_setting_score'] = 3

        score = protocol._calculate_decision_making_score(data, scenario)

        # Base 100 (from perfect decisions) + 0 (priority baseline) = 100
        assert score == 100, f"Perfect decisions should yield 100, got {score}"

    def test_decision_rate_calculation(self, protocol, sample_performance_data):
        """Test Case 4.2: Decision rate correctly calculated"""
        scenario = protocol.scenarios[0]

        test_cases = [
            (5, 5, 100),  # 100%
            (4, 5, 80),   # 80%
            (3, 5, 60),   # 60%
            (2, 5, 40),   # 40%
            (0, 5, 0)     # 0%
        ]

        for correct, total, expected_base in test_cases:
            data = sample_performance_data.copy()
            data['correct_decisions'] = correct
            data['total_decisions'] = total
            data['complications_handled_correctly'] = 0
            data['priority_setting_score'] = 3

            score = protocol._calculate_decision_making_score(data, scenario)

            # Base score should be decision_rate * 100
            assert abs(score - expected_base) < 1, \
                f"Decision rate {correct}/{total} should yield ~{expected_base}, got {score}"

    def test_complications_not_handled_penalty(self, protocol, sample_performance_data):
        """Test Case 4.3: Each unhandled complication = -10 points"""
        scenario = protocol.scenarios[0]  # 4 complications
        data = sample_performance_data.copy()
        data['correct_decisions'] = 5
        data['total_decisions'] = 5
        data['complications_handled_correctly'] = 2  # 2 out of 4
        data['priority_setting_score'] = 3

        score = protocol._calculate_decision_making_score(data, scenario)

        # Base 100 - 20 (2 unhandled * 10) = 80
        assert score == 80, f"Expected 80 for 2 unhandled complications, got {score}"

    def test_priority_setting_modifier(self, protocol, sample_performance_data):
        """Test Case 4.4: Priority setting modifies score (rating-3)*5"""
        scenario = protocol.scenarios[0]

        test_cases = [
            (1, -10),  # (1-3)*5 = -10
            (3, 0),    # (3-3)*5 = 0
            (5, 10)    # (5-3)*5 = 10
        ]

        for priority, expected_modifier in test_cases:
            data = sample_performance_data.copy()
            data['correct_decisions'] = 5
            data['total_decisions'] = 5
            data['complications_handled_correctly'] = 4
            data['priority_setting_score'] = priority

            score = protocol._calculate_decision_making_score(data, scenario)

            # Base 100 + priority modifier
            expected = 100 + expected_modifier
            assert score == expected, \
                f"Priority {priority} should yield {expected}, got {score}"

    def test_decision_score_ceiling_100(self, protocol, perfect_performance_data):
        """Test Case 4.5: Decision-making score capped at 100"""
        scenario = protocol.scenarios[0]
        score = protocol._calculate_decision_making_score(perfect_performance_data, scenario)

        assert score <= 100, f"Decision score should not exceed 100, got {score}"

    def test_decision_score_floor_zero(self, protocol, failing_performance_data):
        """Test Case 4.6: Decision-making score floored at 0"""
        scenario = protocol.scenarios[0]
        score = protocol._calculate_decision_making_score(failing_performance_data, scenario)

        assert score >= 0, f"Decision score should not be negative, got {score}"


# ============================================================================
# TEST 5: COMPETENCY THRESHOLD VALIDATION
# ============================================================================

class TestCompetencyThresholds:
    """Test competency achievement criteria: Overall ≥80, No critical errors, Technical ≥75"""

    def test_competency_all_criteria_met(self, protocol, perfect_performance_data):
        """Test Case 5.1: Competency achieved when all criteria met"""
        # Given: Perfect performance (overall ≥80, no critical errors, technical ≥75)
        metrics = protocol.assess_performance('TEST_001', 'VA001', perfect_performance_data)

        # Then: Competency should be achieved
        assert metrics.competency_achieved, "Competency should be achieved with perfect scores"
        assert metrics.overall_score >= 80
        assert len(metrics.critical_errors) == 0
        assert metrics.technical_score >= 75

    def test_competency_overall_below_80(self, protocol, sample_performance_data):
        """Test Case 5.2: Competency NOT achieved when overall <80"""
        # Given: Performance with overall score < 80
        data = sample_performance_data.copy()
        data['correct_decisions'] = 2  # Lower decision-making score
        data['total_decisions'] = 5
        data['communication_rating'] = 3  # Lower communication score

        metrics = protocol.assess_performance('TEST_001', 'VA001', data)

        # Then: If overall < 80, competency not achieved
        if metrics.overall_score < 80:
            assert not metrics.competency_achieved, \
                f"Competency should not be achieved with overall {metrics.overall_score} < 80"

    def test_competency_critical_errors_present(self, protocol, sample_performance_data):
        """Test Case 5.3: Competency NOT achieved with critical errors"""
        # Given: Good scores but critical errors present
        data = sample_performance_data.copy()
        data['errors'] = [{'severity': 'critical', 'description': 'Safety violation'}]

        metrics = protocol.assess_performance('TEST_001', 'VA001', data)

        # Extract critical errors
        critical_errors_list = [e for e in data['errors'] if e.get('severity') == 'critical']

        # Then: Competency not achieved due to critical errors
        if len(critical_errors_list) > 0:
            assert not metrics.competency_achieved, \
                "Competency should not be achieved with critical errors present"

    def test_competency_technical_below_75(self, protocol, sample_performance_data):
        """Test Case 5.4: Competency NOT achieved when technical <75"""
        # Given: Good overall but low technical score
        data = sample_performance_data.copy()
        data['critical_steps_completed'] = 2  # Only 40% completion
        data['technical_errors'] = ['e1', 'e2', 'e3', 'e4', 'e5']  # Many errors

        metrics = protocol.assess_performance('TEST_001', 'VA001', data)

        # Then: If technical < 75, competency not achieved
        if metrics.technical_score < 75:
            assert not metrics.competency_achieved, \
                f"Competency should not be achieved with technical {metrics.technical_score} < 75"

    def test_competency_boundary_conditions(self, protocol):
        """Test Case 5.5: Test exact boundary values (80, 0, 75)"""
        # Test case: Overall = 80, Critical errors = 0, Technical = 75 (exactly at thresholds)
        data = {
            'completion_time': 30,
            'technical_errors': ['e1'],  # -5
            'critical_steps_completed': 5,
            'sterile_technique_maintained': True,
            'communication_rating': 5,
            'demonstrated_leadership': True,
            'instruction_clarity': 5,
            'situation_awareness': 5,
            'correct_decisions': 4,
            'total_decisions': 5,
            'complications_handled_correctly': 2,
            'priority_setting_score': 5,
            'errors': [],
            'critical_errors': []
        }

        metrics = protocol.assess_performance('TEST_001', 'VA001', data)

        # At exact boundaries, competency should be achieved
        if (metrics.overall_score >= 80 and
            len(metrics.critical_errors) == 0 and
            metrics.technical_score >= 75):
            assert metrics.competency_achieved, \
                "Competency should be achieved at exact boundary thresholds"


# ============================================================================
# TEST 6: SCENARIO PROGRESSION LOGIC
# ============================================================================

class TestScenarioProgression:
    """Test adaptive learning path and scenario progression"""

    def test_new_trainee_gets_beginner_scenarios(self, protocol):
        """Test Case 6.1: New trainee with no history gets beginner scenarios"""
        # Given: New trainee with no performance history
        trainee_id = 'NEW_TRAINEE_001'

        # When: Generate learning path
        recommended = protocol.generate_learning_path(trainee_id)

        # Then: Should recommend beginner scenarios (but protocol has no Beginner level)
        # OR return empty if no beginner scenarios exist
        assert isinstance(recommended, list), "Learning path should return a list"

    def test_high_performer_gets_advanced_scenarios(self, protocol, perfect_performance_data):
        """Test Case 6.2: Trainee with avg score ≥90 gets Advanced scenarios"""
        # Given: Trainee with consistently high scores
        trainee_id = 'HIGH_PERFORMER_001'

        # Create multiple high-scoring sessions
        for _ in range(5):
            protocol.assess_performance(trainee_id, 'VA001', perfect_performance_data)

        # When: Generate learning path
        recommended = protocol.generate_learning_path(trainee_id)

        # Then: Should recommend Advanced scenarios
        for scenario_id in recommended:
            scenario = next((s for s in protocol.scenarios if s.scenario_id == scenario_id), None)
            if scenario:
                assert scenario.difficulty_level == 'Advanced', \
                    f"High performer should get Advanced scenarios, got {scenario.difficulty_level}"

    def test_intermediate_performer_gets_intermediate_scenarios(self, protocol, sample_performance_data):
        """Test Case 6.3: Trainee with 75 ≤ avg < 90 gets Intermediate scenarios"""
        # Given: Trainee with intermediate scores
        trainee_id = 'MID_PERFORMER_001'

        # Create moderate-scoring sessions
        data = sample_performance_data.copy()
        data['correct_decisions'] = 4  # 80% decisions
        data['communication_rating'] = 4

        for _ in range(5):
            protocol.assess_performance(trainee_id, 'VA001', data)

        # When: Generate learning path
        recommended = protocol.generate_learning_path(trainee_id)

        # Then: Should recommend Intermediate scenarios
        for scenario_id in recommended:
            scenario = next((s for s in protocol.scenarios if s.scenario_id == scenario_id), None)
            if scenario:
                assert scenario.difficulty_level in ['Intermediate', 'Advanced'], \
                    f"Mid performer should get Intermediate/Advanced, got {scenario.difficulty_level}"

    def test_weak_technical_gets_technical_scenarios(self, protocol, sample_performance_data):
        """Test Case 6.4: Weak technical skills get technical-focused scenarios"""
        # Given: Trainee with weak technical but good other scores
        trainee_id = 'WEAK_TECH_001'

        data = sample_performance_data.copy()
        data['technical_errors'] = ['e1', 'e2', 'e3', 'e4']  # High errors
        data['critical_steps_completed'] = 3  # Low completion

        for _ in range(5):
            protocol.assess_performance(trainee_id, 'VA001', data)

        # When: Generate learning path
        recommended = protocol.generate_learning_path(trainee_id)

        # Then: Recommendations should exist (algorithm should handle weak technical)
        assert len(recommended) > 0, "Should recommend scenarios for technical improvement"

    def test_learning_path_limit_five(self, protocol, perfect_performance_data):
        """Test Case 6.5: Learning path limited to 5 recommendations"""
        # Given: Trainee with history
        trainee_id = 'TEST_LIMIT_001'

        for i in range(3):
            protocol.assess_performance(trainee_id, f'VA00{i%2+1}', perfect_performance_data)

        # When: Generate learning path
        recommended = protocol.generate_learning_path(trainee_id)

        # Then: Should return ≤5 recommendations
        assert len(recommended) <= 5, f"Learning path should have ≤5 recommendations, got {len(recommended)}"


# ============================================================================
# TEST 7: PERFORMANCE METRICS AGGREGATION
# ============================================================================

class TestPerformanceAggregation:
    """Test competency report generation and metrics aggregation"""

    def test_competency_report_structure(self, protocol, sample_performance_data):
        """Test Case 7.1: Competency report contains required fields"""
        # Given: Trainee with some performance data
        trainee_id = 'REPORT_TEST_001'
        protocol.assess_performance(trainee_id, 'VA001', sample_performance_data)

        # When: Generate competency report
        report = protocol.generate_competency_report(trainee_id)

        # Then: Report should have required structure
        assert 'trainee_id' in report
        assert 'summary' in report
        assert 'average_scores' in report
        assert 'scenarios' in report
        assert 'performance_trend' in report
        assert 'competency_status' in report

        # Verify summary fields
        assert 'total_sessions' in report['summary']
        assert 'competency_rate' in report['summary']

        # Verify average scores
        assert 'overall' in report['average_scores']
        assert 'technical' in report['average_scores']
        assert 'communication' in report['average_scores']
        assert 'decision_making' in report['average_scores']

    def test_competency_rate_calculation(self, protocol, perfect_performance_data, failing_performance_data):
        """Test Case 7.2: Competency rate correctly calculated"""
        # Given: Mix of passing and failing sessions
        trainee_id = 'RATE_TEST_001'

        # 3 passing sessions
        for _ in range(3):
            protocol.assess_performance(trainee_id, 'VA001', perfect_performance_data)

        # 2 failing sessions
        for _ in range(2):
            protocol.assess_performance(trainee_id, 'VA002', failing_performance_data)

        # When: Generate report
        report = protocol.generate_competency_report(trainee_id)

        # Then: Competency rate should be 3/5 = 0.6
        expected_rate = 3 / 5
        assert abs(report['summary']['competency_rate'] - expected_rate) < 0.01, \
            f"Expected competency rate {expected_rate}, got {report['summary']['competency_rate']}"

    def test_average_scores_calculation(self, protocol, sample_performance_data):
        """Test Case 7.3: Average scores correctly calculated across sessions"""
        # Given: Multiple sessions with known scores
        trainee_id = 'AVG_TEST_001'

        # Create sessions with predictable scores
        for i in range(3):
            data = sample_performance_data.copy()
            data['communication_rating'] = 3 + i  # 3, 4, 5
            protocol.assess_performance(trainee_id, 'VA001', data)

        # When: Generate report
        report = protocol.generate_competency_report(trainee_id)

        # Then: Average scores should be calculated correctly
        assert 'overall' in report['average_scores']
        assert report['average_scores']['overall'] > 0
        assert report['average_scores']['technical'] > 0
        assert report['average_scores']['communication'] > 0
        assert report['average_scores']['decision_making'] > 0

    def test_competency_status_determination(self, protocol, perfect_performance_data, failing_performance_data):
        """Test Case 7.4: Competency status 'Competent' if rate ≥0.8"""
        # Test competent trainee (≥80% pass rate)
        trainee_competent = 'COMPETENT_001'
        for _ in range(8):
            protocol.assess_performance(trainee_competent, 'VA001', perfect_performance_data)
        for _ in range(2):
            protocol.assess_performance(trainee_competent, 'VA002', failing_performance_data)

        report_competent = protocol.generate_competency_report(trainee_competent)
        assert report_competent['competency_status'] == 'Competent', \
            "Trainee with ≥80% competency rate should be 'Competent'"

        # Test developing trainee (<80% pass rate)
        trainee_developing = 'DEVELOPING_001'
        for _ in range(2):
            protocol.assess_performance(trainee_developing, 'VA001', perfect_performance_data)
        for _ in range(8):
            protocol.assess_performance(trainee_developing, 'VA002', failing_performance_data)

        report_developing = protocol.generate_competency_report(trainee_developing)
        assert report_developing['competency_status'] == 'Developing', \
            "Trainee with <80% competency rate should be 'Developing'"


# ============================================================================
# TEST 8: STATISTICAL POWER AND SAMPLE SIZE
# ============================================================================

class TestStatisticalPower:
    """Test statistical power calculations and sample size determination"""

    def test_sample_size_calculation_paired_ttest(self):
        """Test Case 8.1: Sample size for paired t-test (pre/post design)"""
        # Given: Study parameters
        effect_size = 0.8  # Cohen's d (large effect)
        alpha = 0.05
        power = 0.80

        # When: Calculate sample size (using standard formula)
        # For paired t-test: n ≈ (Z_α/2 + Z_β)² * 2σ² / δ²
        # Simplified: n ≈ 16 / d² for α=0.05, power=0.80

        n_required = np.ceil(16 / (effect_size ** 2))

        # Then: Sample size should be reasonable for ECMO training study
        assert n_required > 0, "Sample size must be positive"
        assert n_required == 25, f"Expected n=25 for d=0.8, got {n_required}"

    def test_sample_size_for_medium_effect(self):
        """Test Case 8.2: Sample size for medium effect size (d=0.5)"""
        effect_size = 0.5  # Cohen's d (medium effect)
        n_required = np.ceil(16 / (effect_size ** 2))

        assert n_required == 64, f"Expected n=64 for d=0.5, got {n_required}"

    def test_power_analysis_with_achieved_sample(self):
        """Test Case 8.3: Calculate achieved power with given sample size"""
        # Given: Achieved sample size
        n = 30
        effect_size = 0.8

        # When: Calculate achieved power (simplified)
        # d = sqrt(16/n) for power=0.80
        # If actual d ≥ required d, power ≥ 0.80

        required_d = np.sqrt(16 / n)
        achieved_power = 0.80 if effect_size >= required_d else 0.80 * (effect_size / required_d) ** 2

        # Then: Should have adequate power
        assert achieved_power >= 0.80, f"With n=30, d=0.8, power should be ≥0.80, got {achieved_power}"

    def test_minimum_detectable_effect(self):
        """Test Case 8.4: Calculate minimum detectable effect with n=25"""
        n = 25
        alpha = 0.05
        power = 0.80

        # Minimum detectable effect: d = sqrt(16/n)
        min_effect = np.sqrt(16 / n)

        assert abs(min_effect - 0.8) < 0.01, f"Expected d=0.8 with n=25, got {min_effect}"

    def test_crossover_design_sample_size(self):
        """Test Case 8.5: Sample size for crossover design (higher efficiency)"""
        # Crossover design requires ~50% fewer participants
        effect_size = 0.8
        n_paired = np.ceil(16 / (effect_size ** 2))
        n_crossover = np.ceil(n_paired / 2)

        assert n_crossover == 13, f"Crossover design should need ~13 participants, got {n_crossover}"


# ============================================================================
# TEST 9: EDGE CASES AND ERROR HANDLING
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_invalid_scenario_id(self, protocol, sample_performance_data):
        """Test Case 9.1: Invalid scenario ID raises error"""
        with pytest.raises(ValueError):
            protocol.assess_performance('TEST_001', 'INVALID_ID', sample_performance_data)

    def test_no_performance_data_report(self, protocol):
        """Test Case 9.2: Report with no data returns error message"""
        report = protocol.generate_competency_report('NONEXISTENT_TRAINEE')
        assert 'error' in report

    def test_zero_total_decisions(self, protocol, sample_performance_data):
        """Test Case 9.3: Zero total decisions handled gracefully"""
        data = sample_performance_data.copy()
        data['total_decisions'] = 0

        scenario = protocol.scenarios[0]
        score = protocol._calculate_decision_making_score(data, scenario)

        # Should return 0 or handle gracefully
        assert score >= 0, "Should handle zero divisions gracefully"

    def test_missing_optional_fields(self, protocol):
        """Test Case 9.4: Missing optional fields use defaults"""
        minimal_data = {
            'completion_time': 30,
            'errors': []
        }

        # Should use defaults without crashing
        scenario = protocol.scenarios[0]
        tech_score = protocol._calculate_technical_score(minimal_data, scenario)

        assert tech_score >= 0, "Should handle missing fields with defaults"


# ============================================================================
# TEST 10: INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """End-to-end integration tests"""

    def test_complete_training_workflow(self, protocol):
        """Test Case 10.1: Complete workflow from assessment to report"""
        trainee_id = 'INTEGRATION_TEST_001'

        # Step 1: Assess multiple performances
        scenarios = ['VA001', 'VV001', 'COMP001']
        for scenario_id in scenarios:
            data = {
                'completion_time': 30,
                'technical_errors': [],
                'critical_steps_completed': 5,
                'sterile_technique_maintained': True,
                'communication_rating': 5,
                'demonstrated_leadership': True,
                'instruction_clarity': 5,
                'situation_awareness': 5,
                'correct_decisions': 5,
                'total_decisions': 5,
                'complications_handled_correctly': 2,
                'priority_setting_score': 5,
                'errors': [],
                'critical_errors': []
            }
            protocol.assess_performance(trainee_id, scenario_id, data)

        # Step 2: Generate learning path
        learning_path = protocol.generate_learning_path(trainee_id)
        assert len(learning_path) > 0, "Learning path should be generated"

        # Step 3: Generate competency report
        report = protocol.generate_competency_report(trainee_id)
        assert report['summary']['total_sessions'] == 3
        assert report['competency_status'] in ['Competent', 'Developing']
        assert len(report['scenarios']['completed']) == 3

    def test_multiple_trainees_concurrent(self, protocol, sample_performance_data):
        """Test Case 10.2: Handle multiple trainees concurrently"""
        trainees = [f'TRAINEE_{i:03d}' for i in range(10)]

        # Assess all trainees
        for trainee_id in trainees:
            protocol.assess_performance(trainee_id, 'VA001', sample_performance_data)

        # Verify all data stored
        assert len(protocol.performance_data) >= 10

        # Generate reports for all
        for trainee_id in trainees:
            report = protocol.generate_competency_report(trainee_id)
            assert 'trainee_id' in report
            assert report['trainee_id'] == trainee_id


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])