"""
VR Training Assessment Module for ECMO Clinical Decision Support
Scoring VR training sessions, generating performance reports, and statistical analysis.

This module integrates with:
- vr-training/scenarios.yaml for scenario definitions
- vr-training/metrics.md for scoring rubrics
- VR system logs for automated performance data collection
"""

import numpy as np
import pandas as pd
import yaml
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
import json
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict
import warnings


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class DecisionPoint:
    """Individual decision point within a scenario."""
    id: str
    timestamp_min: float
    question: str
    selected_option: str
    correct_option: str
    is_correct: bool
    is_critical: bool
    scoring_weight: int
    time_to_decision_sec: float
    points_awarded: float


@dataclass
class ScenarioPerformance:
    """Performance data for a single VR scenario session."""
    session_id: str
    participant_id: str
    scenario_id: str
    scenario_title: str
    difficulty: str
    ecmo_mode: str

    # Timing metrics
    start_time: datetime
    end_time: datetime
    total_duration_min: float

    # Decision-making metrics
    decision_points: List[DecisionPoint] = field(default_factory=list)
    total_decisions: int = 0
    correct_decisions: int = 0
    decision_accuracy_pct: float = 0.0
    critical_errors: int = 0
    major_errors: int = 0
    minor_errors: int = 0

    # Performance scores
    technical_skill_score: float = 0.0  # 0-100
    clinical_decision_score: float = 0.0  # 0-100
    nirs_interpretation_score: float = 0.0  # 0-100
    complication_management_score: float = 0.0  # 0-100
    communication_score: float = 0.0  # 0-100
    total_score: float = 0.0  # 0-100

    # Specific metrics
    first_attempt_success: bool = False
    scenario_completed: bool = False
    complications_encountered: List[str] = field(default_factory=list)
    interventions_performed: List[str] = field(default_factory=list)

    # Additional data
    notes: str = ""
    assessor_id: Optional[str] = None

    def calculate_totals(self):
        """Calculate aggregate metrics from decision points."""
        if self.decision_points:
            self.total_decisions = len(self.decision_points)
            self.correct_decisions = sum(1 for dp in self.decision_points if dp.is_correct)
            self.decision_accuracy_pct = (self.correct_decisions / self.total_decisions) * 100
            self.critical_errors = sum(1 for dp in self.decision_points
                                      if dp.is_critical and not dp.is_correct)

            # Calculate weighted decision score
            total_weight = sum(dp.scoring_weight for dp in self.decision_points)
            if total_weight > 0:
                self.clinical_decision_score = sum(dp.points_awarded for dp in self.decision_points) / total_weight * 100


@dataclass
class OSCEScore:
    """Objective Structured Clinical Examination scores."""
    participant_id: str
    assessment_date: datetime
    assessor_id: str

    # Station scores (0-20 each)
    pre_cannulation_assessment: float = 0.0
    cannulation_technique: float = 0.0
    circuit_management: float = 0.0
    nirs_monitoring: float = 0.0
    complication_recognition: float = 0.0

    # Total score (0-100)
    total_score: float = 0.0

    # Global rating scale (1-7 each, 6 domains)
    grs_technical_skill: int = 1
    grs_knowledge: int = 1
    grs_judgment: int = 1
    grs_efficiency: int = 1
    grs_communication: int = 1
    grs_professionalism: int = 1
    grs_total: float = 0.0  # 0-100 converted

    def calculate_totals(self):
        """Calculate total scores."""
        self.total_score = (
            self.pre_cannulation_assessment +
            self.cannulation_technique +
            self.circuit_management +
            self.nirs_monitoring +
            self.complication_recognition
        )

        grs_sum = (
            self.grs_technical_skill + self.grs_knowledge +
            self.grs_judgment + self.grs_efficiency +
            self.grs_communication + self.grs_professionalism
        )
        self.grs_total = ((grs_sum - 6) / 36) * 100  # Convert 6-42 to 0-100


@dataclass
class KnowledgeTest:
    """ECMO knowledge test results."""
    participant_id: str
    test_date: datetime
    timepoint: str  # baseline, post, 3month, 6month

    # Domain scores (0-100 each)
    indications_contraindications: float = 0.0
    circuit_physiology: float = 0.0
    cannulation_techniques: float = 0.0
    nirs_monitoring: float = 0.0

    # Total score (0-100)
    total_score: float = 0.0

    # Item-level data
    total_items: int = 40
    correct_items: int = 0

    def calculate_totals(self):
        """Calculate total score."""
        self.total_score = (
            self.indications_contraindications +
            self.circuit_physiology +
            self.cannulation_techniques +
            self.nirs_monitoring
        ) / 4


@dataclass
class ParticipantProfile:
    """Participant demographics and baseline characteristics."""
    participant_id: str
    age: int
    sex: str
    professional_role: str  # physician, perfusionist, nurse
    institution: str
    prior_ecmo_cases: int
    prior_ecmo_cannulations: int
    years_experience: float
    baseline_knowledge_score: float = 0.0
    baseline_osce_score: float = 0.0
    group: str = "control"  # control or intervention


# ============================================================================
# SCENARIO LOADER
# ============================================================================

class ScenarioLoader:
    """Load and parse VR training scenarios from YAML."""

    def __init__(self, scenarios_path: str = "vr-training/scenarios.yaml"):
        self.scenarios_path = Path(scenarios_path)
        self.scenarios = {}
        self.load_scenarios()

    def load_scenarios(self):
        """Load scenarios from YAML file."""
        if not self.scenarios_path.exists():
            warnings.warn(f"Scenarios file not found: {self.scenarios_path}")
            return

        with open(self.scenarios_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if 'scenarios' in data:
            for scenario in data['scenarios']:
                self.scenarios[scenario['id']] = scenario

    def get_scenario(self, scenario_id: str) -> Optional[Dict]:
        """Get scenario definition by ID."""
        return self.scenarios.get(scenario_id)

    def get_all_scenarios(self) -> List[Dict]:
        """Get all scenario definitions."""
        return list(self.scenarios.values())


# ============================================================================
# SCORING ENGINE
# ============================================================================

class VRSessionScorer:
    """Score individual VR training session based on performance metrics."""

    def __init__(self, scenario_loader: Optional[ScenarioLoader] = None):
        self.scenario_loader = scenario_loader or ScenarioLoader()

    def score_session(
        self,
        vr_log_data: Dict[str, Any],
        manual_scores: Optional[Dict[str, float]] = None
    ) -> ScenarioPerformance:
        """
        Score a VR training session.

        Args:
            vr_log_data: Automated VR system log data
            manual_scores: Manual assessor scores (optional)

        Returns:
            ScenarioPerformance object with calculated scores
        """
        # Parse VR log data
        performance = self._parse_vr_log(vr_log_data)

        # Score decision points
        self._score_decision_points(performance, vr_log_data)

        # Add manual scores if provided
        if manual_scores:
            performance.technical_skill_score = manual_scores.get('technical_skill', 0.0)
            performance.nirs_interpretation_score = manual_scores.get('nirs_interpretation', 0.0)
            performance.complication_management_score = manual_scores.get('complication_management', 0.0)
            performance.communication_score = manual_scores.get('communication', 0.0)

        # Calculate totals
        performance.calculate_totals()

        # Calculate overall score (weighted average)
        scenario = self.scenario_loader.get_scenario(performance.scenario_id)
        if scenario and 'assessment_rubric' in scenario:
            performance.total_score = self._calculate_weighted_score(
                performance, scenario['assessment_rubric']
            )
        else:
            # Default equal weighting
            performance.total_score = np.mean([
                performance.technical_skill_score,
                performance.clinical_decision_score,
                performance.nirs_interpretation_score,
                performance.complication_management_score,
                performance.communication_score
            ])

        return performance

    def _parse_vr_log(self, log_data: Dict) -> ScenarioPerformance:
        """Parse VR system log into ScenarioPerformance object."""
        return ScenarioPerformance(
            session_id=log_data.get('session_id', ''),
            participant_id=log_data.get('participant_id', ''),
            scenario_id=log_data.get('scenario_id', ''),
            scenario_title=log_data.get('scenario_title', ''),
            difficulty=log_data.get('difficulty', ''),
            ecmo_mode=log_data.get('ecmo_mode', ''),
            start_time=datetime.fromisoformat(log_data.get('start_time', datetime.now().isoformat())),
            end_time=datetime.fromisoformat(log_data.get('end_time', datetime.now().isoformat())),
            total_duration_min=log_data.get('total_duration_min', 0.0),
            first_attempt_success=log_data.get('first_attempt_success', False),
            scenario_completed=log_data.get('scenario_completed', False),
            complications_encountered=log_data.get('complications_encountered', []),
            interventions_performed=log_data.get('interventions_performed', []),
        )

    def _score_decision_points(self, performance: ScenarioPerformance, log_data: Dict):
        """Score individual decision points from VR log."""
        scenario = self.scenario_loader.get_scenario(performance.scenario_id)
        if not scenario or 'decision_points' not in scenario:
            return

        scenario_decisions = {dp['id']: dp for dp in scenario['decision_points']}
        user_decisions = log_data.get('decision_points', [])

        for decision in user_decisions:
            dp_id = decision.get('id')
            if dp_id not in scenario_decisions:
                continue

            scenario_dp = scenario_decisions[dp_id]
            selected_option = decision.get('selected_option')

            # Determine if correct
            correct_options = [opt['value'] for opt in scenario_dp.get('options', [])
                             if opt.get('correct', False)]
            is_correct = selected_option in correct_options

            # Get scoring weight
            weight = scenario_dp.get('scoring_weight', 10)
            is_critical = scenario_dp.get('critical', False)

            # Calculate points
            points = weight if is_correct else 0

            # Create DecisionPoint object
            dp = DecisionPoint(
                id=dp_id,
                timestamp_min=decision.get('timestamp_min', 0.0),
                question=scenario_dp.get('question', ''),
                selected_option=selected_option,
                correct_option=correct_options[0] if correct_options else '',
                is_correct=is_correct,
                is_critical=is_critical,
                scoring_weight=weight,
                time_to_decision_sec=decision.get('time_to_decision_sec', 0.0),
                points_awarded=points
            )

            performance.decision_points.append(dp)

    def _calculate_weighted_score(
        self,
        performance: ScenarioPerformance,
        rubric: Dict[str, int]
    ) -> float:
        """Calculate weighted total score based on rubric."""
        scores = {
            'technical_skill': performance.technical_skill_score,
            'clinical_decision_making': performance.clinical_decision_score,
            'nirs_interpretation': performance.nirs_interpretation_score,
            'complication_management': performance.complication_management_score,
            'communication': performance.communication_score,
        }

        total_weight = sum(rubric.values())
        weighted_sum = sum(scores.get(key, 0) * weight
                          for key, weight in rubric.items())

        return weighted_sum / total_weight if total_weight > 0 else 0.0


# ============================================================================
# PERFORMANCE REPORTER
# ============================================================================

class PerformanceReporter:
    """Generate performance reports for individual sessions and participants."""

    def generate_session_report(
        self,
        performance: ScenarioPerformance,
        output_format: str = 'text'
    ) -> str:
        """
        Generate performance report for a single VR session.

        Args:
            performance: ScenarioPerformance object
            output_format: 'text', 'json', or 'html'

        Returns:
            Formatted report string
        """
        if output_format == 'json':
            return json.dumps(asdict(performance), indent=2, default=str)

        elif output_format == 'html':
            return self._generate_html_report(performance)

        else:  # text
            return self._generate_text_report(performance)

    def _generate_text_report(self, perf: ScenarioPerformance) -> str:
        """Generate text-based performance report."""
        report = []
        report.append("="*70)
        report.append("VR TRAINING SESSION PERFORMANCE REPORT")
        report.append("="*70)
        report.append(f"Session ID: {perf.session_id}")
        report.append(f"Participant: {perf.participant_id}")
        report.append(f"Scenario: {perf.scenario_title} ({perf.scenario_id})")
        report.append(f"Difficulty: {perf.difficulty.upper()}")
        report.append(f"ECMO Mode: {perf.ecmo_mode}")
        report.append(f"Date: {perf.start_time.strftime('%Y-%m-%d %H:%M')}")
        report.append("")

        # Summary
        report.append("-"*70)
        report.append("SUMMARY")
        report.append("-"*70)
        report.append(f"Total Score: {perf.total_score:.1f}/100")
        report.append(f"Duration: {perf.total_duration_min:.1f} minutes")
        report.append(f"Scenario Completed: {'Yes' if perf.scenario_completed else 'No'}")
        report.append(f"First Attempt Success: {'Yes' if perf.first_attempt_success else 'No'}")
        report.append("")

        # Score breakdown
        report.append("-"*70)
        report.append("SCORE BREAKDOWN")
        report.append("-"*70)
        report.append(f"Technical Skill:            {perf.technical_skill_score:5.1f}/100")
        report.append(f"Clinical Decision-Making:   {perf.clinical_decision_score:5.1f}/100")
        report.append(f"NIRS Interpretation:        {perf.nirs_interpretation_score:5.1f}/100")
        report.append(f"Complication Management:    {perf.complication_management_score:5.1f}/100")
        report.append(f"Communication:              {perf.communication_score:5.1f}/100")
        report.append("")

        # Decision-making performance
        report.append("-"*70)
        report.append("DECISION-MAKING PERFORMANCE")
        report.append("-"*70)
        report.append(f"Total Decisions: {perf.total_decisions}")
        report.append(f"Correct Decisions: {perf.correct_decisions}/{perf.total_decisions} ({perf.decision_accuracy_pct:.1f}%)")
        report.append(f"Critical Errors: {perf.critical_errors}")
        report.append(f"Major Errors: {perf.major_errors}")
        report.append(f"Minor Errors: {perf.minor_errors}")
        report.append("")

        # Decision point details
        if perf.decision_points:
            report.append("-"*70)
            report.append("DECISION POINT DETAILS")
            report.append("-"*70)
            for i, dp in enumerate(perf.decision_points, 1):
                status = "✓ CORRECT" if dp.is_correct else "✗ INCORRECT"
                critical = " [CRITICAL]" if dp.is_critical else ""
                report.append(f"{i}. {dp.question}")
                report.append(f"   Time: {dp.timestamp_min:.1f} min | {status}{critical}")
                report.append(f"   Selected: {dp.selected_option}")
                report.append(f"   Points: {dp.points_awarded:.0f}/{dp.scoring_weight}")
                report.append("")

        # Complications encountered
        if perf.complications_encountered:
            report.append("-"*70)
            report.append("COMPLICATIONS ENCOUNTERED")
            report.append("-"*70)
            for comp in perf.complications_encountered:
                report.append(f"  - {comp}")
            report.append("")

        # Performance interpretation
        report.append("-"*70)
        report.append("INTERPRETATION")
        report.append("-"*70)
        report.append(self._interpret_performance(perf))
        report.append("")

        # Recommendations
        report.append("-"*70)
        report.append("RECOMMENDATIONS")
        report.append("-"*70)
        report.extend(self._generate_recommendations(perf))
        report.append("")

        report.append("="*70)
        report.append(f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("="*70)

        return "\n".join(report)

    def _interpret_performance(self, perf: ScenarioPerformance) -> str:
        """Provide interpretation of performance level."""
        score = perf.total_score

        if score >= 85:
            level = "EXPERT"
            desc = "Excellent performance demonstrating mastery of ECMO management."
        elif score >= 70:
            level = "COMPETENT"
            desc = "Good performance meeting proficiency standards."
        elif score >= 50:
            level = "NOVICE"
            desc = "Developing competency. Additional training recommended."
        else:
            level = "NEEDS IMPROVEMENT"
            desc = "Significant gaps identified. Requires focused remediation."

        return f"Performance Level: {level} ({score:.1f}/100)\n{desc}"

    def _generate_recommendations(self, perf: ScenarioPerformance) -> List[str]:
        """Generate personalized recommendations based on performance."""
        recommendations = []

        # Technical skill
        if perf.technical_skill_score < 70:
            recommendations.append("- Review cannulation technique and procedural steps")
            recommendations.append("- Practice under supervision before independent performance")

        # Clinical decision-making
        if perf.clinical_decision_score < 70:
            recommendations.append("- Review ELSO guidelines for ECMO indications and management")
            recommendations.append("- Participate in case-based discussion sessions")

        if perf.critical_errors > 0:
            recommendations.append(f"- CRITICAL: {perf.critical_errors} critical error(s) identified - immediate review required")
            recommendations.append("- Discuss critical errors with supervisor before next attempt")

        # NIRS interpretation
        if perf.nirs_interpretation_score < 70:
            recommendations.append("- Review NIRS physiology and interpretation guidelines")
            recommendations.append("- Practice NIRS case studies and troubleshooting scenarios")

        # Complication management
        if perf.complication_management_score < 70:
            recommendations.append("- Review ECMO complications and emergency protocols")
            recommendations.append("- Practice circuit emergency scenarios")

        # Time management
        if perf.total_duration_min > 60:
            recommendations.append("- Work on efficiency and time management")
            recommendations.append("- Focus on prioritization of critical tasks")

        if not recommendations:
            recommendations.append("- Continue to maintain high performance standards")
            recommendations.append("- Consider mentoring junior colleagues")
            recommendations.append("- Participate in advanced scenarios if available")

        return recommendations

    def _generate_html_report(self, perf: ScenarioPerformance) -> str:
        """Generate HTML-formatted performance report."""
        # Extract interpretation text and convert newlines to HTML breaks
        interpretation = self._interpret_performance(perf).replace('\n', '<br>')

        # Simplified HTML template
        html = f"""
        <html>
        <head><title>VR Training Report - {perf.participant_id}</title></head>
        <body>
        <h1>VR Training Session Performance Report</h1>
        <h2>Scenario: {perf.scenario_title}</h2>
        <p><strong>Total Score:</strong> {perf.total_score:.1f}/100</p>
        <p><strong>Decision Accuracy:</strong> {perf.decision_accuracy_pct:.1f}%</p>
        <p><strong>Critical Errors:</strong> {perf.critical_errors}</p>
        {interpretation}
        </body>
        </html>
        """
        return html


# ============================================================================
# STATISTICAL ANALYZER
# ============================================================================

class TrainingOutcomeAnalyzer:
    """Statistical analysis of training outcomes."""

    def __init__(self):
        pass

    def compare_groups(
        self,
        intervention_scores: np.ndarray,
        control_scores: np.ndarray,
        alpha: float = 0.05
    ) -> Dict[str, Any]:
        """
        Compare intervention vs control group outcomes.

        Args:
            intervention_scores: OSCE scores for intervention group
            control_scores: OSCE scores for control group
            alpha: Significance level

        Returns:
            Dictionary with statistical test results
        """
        # Descriptive statistics
        results = {
            'intervention': {
                'n': len(intervention_scores),
                'mean': float(np.mean(intervention_scores)),
                'std': float(np.std(intervention_scores, ddof=1)),
                'median': float(np.median(intervention_scores)),
                'iqr': float(np.percentile(intervention_scores, 75) - np.percentile(intervention_scores, 25))
            },
            'control': {
                'n': len(control_scores),
                'mean': float(np.mean(control_scores)),
                'std': float(np.std(control_scores, ddof=1)),
                'median': float(np.median(control_scores)),
                'iqr': float(np.percentile(control_scores, 75) - np.percentile(control_scores, 25))
            }
        }

        # Independent t-test
        t_stat, p_value = stats.ttest_ind(intervention_scores, control_scores)

        # Cohen's d effect size
        pooled_std = np.sqrt(
            ((len(intervention_scores) - 1) * np.var(intervention_scores, ddof=1) +
             (len(control_scores) - 1) * np.var(control_scores, ddof=1)) /
            (len(intervention_scores) + len(control_scores) - 2)
        )
        cohens_d = (np.mean(intervention_scores) - np.mean(control_scores)) / pooled_std

        # Mann-Whitney U test (non-parametric alternative)
        u_stat, p_value_mw = stats.mannwhitneyu(intervention_scores, control_scores, alternative='two-sided')

        results['statistical_tests'] = {
            'independent_t_test': {
                't_statistic': float(t_stat),
                'p_value': float(p_value),
                'significant': p_value < alpha,
                'cohens_d': float(cohens_d),
                'effect_size_interpretation': self._interpret_cohens_d(cohens_d)
            },
            'mann_whitney_u': {
                'u_statistic': float(u_stat),
                'p_value': float(p_value_mw),
                'significant': p_value_mw < alpha
            }
        }

        # Mean difference and 95% CI
        mean_diff = np.mean(intervention_scores) - np.mean(control_scores)
        se_diff = np.sqrt(
            np.var(intervention_scores, ddof=1) / len(intervention_scores) +
            np.var(control_scores, ddof=1) / len(control_scores)
        )
        ci_95 = (mean_diff - 1.96 * se_diff, mean_diff + 1.96 * se_diff)

        results['mean_difference'] = {
            'difference': float(mean_diff),
            'ci_95_lower': float(ci_95[0]),
            'ci_95_upper': float(ci_95[1])
        }

        return results

    def _interpret_cohens_d(self, d: float) -> str:
        """Interpret Cohen's d effect size."""
        abs_d = abs(d)
        if abs_d < 0.2:
            return "negligible"
        elif abs_d < 0.5:
            return "small"
        elif abs_d < 0.8:
            return "medium"
        else:
            return "large"

    def analyze_knowledge_retention(
        self,
        baseline: np.ndarray,
        post_training: np.ndarray,
        month_3: np.ndarray,
        month_6: np.ndarray
    ) -> Dict[str, Any]:
        """
        Analyze knowledge retention over time using repeated measures ANOVA.

        Args:
            baseline: Baseline knowledge scores
            post_training: Immediate post-training scores
            month_3: 3-month follow-up scores
            month_6: 6-month follow-up scores

        Returns:
            Dictionary with repeated measures analysis results
        """
        # Organize data
        data = np.column_stack([baseline, post_training, month_3, month_6])
        n_participants = len(baseline)

        # Calculate means and SDs
        timepoints = ['baseline', 'post_training', '3_month', '6_month']
        results = {
            'timepoint_statistics': {}
        }

        for i, tp in enumerate(timepoints):
            results['timepoint_statistics'][tp] = {
                'mean': float(np.mean(data[:, i])),
                'std': float(np.std(data[:, i], ddof=1)),
                'n': n_participants
            }

        # Pairwise comparisons (post vs baseline, 6mo vs baseline, etc.)
        comparisons = [
            ('post_training', 'baseline', post_training, baseline),
            ('3_month', 'baseline', month_3, baseline),
            ('6_month', 'baseline', month_6, baseline),
            ('6_month', 'post_training', month_6, post_training),
        ]

        results['pairwise_comparisons'] = {}
        for name1, name2, scores1, scores2 in comparisons:
            t_stat, p_value = stats.ttest_rel(scores1, scores2)

            mean_diff = np.mean(scores1 - scores2)
            se_diff = np.std(scores1 - scores2, ddof=1) / np.sqrt(len(scores1))
            ci_95 = (mean_diff - 1.96 * se_diff, mean_diff + 1.96 * se_diff)

            results['pairwise_comparisons'][f'{name1}_vs_{name2}'] = {
                't_statistic': float(t_stat),
                'p_value': float(p_value),
                'mean_difference': float(mean_diff),
                'ci_95': [float(ci_95[0]), float(ci_95[1])]
            }

        # Calculate retention percentage (6 month / post-training * 100)
        retention_pct = (month_6 / post_training) * 100
        results['retention_6month'] = {
            'mean_pct': float(np.mean(retention_pct)),
            'std_pct': float(np.std(retention_pct, ddof=1))
        }

        return results

    def correlate_vr_performance_with_osce(
        self,
        vr_scores: np.ndarray,
        osce_scores: np.ndarray
    ) -> Dict[str, Any]:
        """
        Correlate VR training performance with OSCE scores.

        Args:
            vr_scores: VR scenario total scores
            osce_scores: OSCE total scores

        Returns:
            Correlation analysis results
        """
        # Pearson correlation
        r_pearson, p_pearson = stats.pearsonr(vr_scores, osce_scores)

        # Spearman correlation (non-parametric)
        r_spearman, p_spearman = stats.spearmanr(vr_scores, osce_scores)

        results = {
            'pearson': {
                'r': float(r_pearson),
                'r_squared': float(r_pearson ** 2),
                'p_value': float(p_pearson),
                'interpretation': self._interpret_correlation(r_pearson)
            },
            'spearman': {
                'rho': float(r_spearman),
                'p_value': float(p_spearman),
                'interpretation': self._interpret_correlation(r_spearman)
            }
        }

        return results

    def _interpret_correlation(self, r: float) -> str:
        """Interpret correlation coefficient."""
        abs_r = abs(r)
        if abs_r < 0.3:
            strength = "weak"
        elif abs_r < 0.7:
            strength = "moderate"
        else:
            strength = "strong"

        direction = "positive" if r > 0 else "negative"
        return f"{strength} {direction}"

    def generate_learning_curve(
        self,
        scenario_scores: List[float],
        scenario_numbers: List[int]
    ) -> Dict[str, Any]:
        """
        Fit exponential learning curve model.

        Model: Score(t) = P_asymptote + (P_initial - P_asymptote) * exp(-lambda * t)

        Args:
            scenario_scores: Scores for sequential scenarios
            scenario_numbers: Scenario attempt numbers (1, 2, 3, ...)

        Returns:
            Learning curve parameters and fit statistics
        """
        from scipy.optimize import curve_fit

        def exponential_model(t, P_asymptote, P_initial, lambda_):
            return P_asymptote + (P_initial - P_asymptote) * np.exp(-lambda_ * t)

        # Fit model
        try:
            popt, pcov = curve_fit(
                exponential_model,
                scenario_numbers,
                scenario_scores,
                p0=[90, 50, 0.3],  # Initial guesses
                maxfev=10000
            )

            P_asymptote, P_initial, lambda_ = popt

            # Calculate R-squared
            y_pred = exponential_model(np.array(scenario_numbers), *popt)
            ss_res = np.sum((np.array(scenario_scores) - y_pred) ** 2)
            ss_tot = np.sum((np.array(scenario_scores) - np.mean(scenario_scores)) ** 2)
            r_squared = 1 - (ss_res / ss_tot)

            # Trials to proficiency (80% of asymptote)
            if lambda_ > 0:
                trials_to_proficiency = -np.log(0.2) / lambda_
            else:
                trials_to_proficiency = np.inf

            results = {
                'model_parameters': {
                    'asymptotic_performance': float(P_asymptote),
                    'initial_performance': float(P_initial),
                    'learning_rate_lambda': float(lambda_)
                },
                'fit_statistics': {
                    'r_squared': float(r_squared),
                    'trials_to_proficiency': float(trials_to_proficiency)
                },
                'predicted_scores': y_pred.tolist()
            }

        except Exception as e:
            results = {
                'error': f"Learning curve fitting failed: {str(e)}"
            }

        return results


# ============================================================================
# VISUALIZATION
# ============================================================================

class PerformanceVisualizer:
    """Create visualizations for training performance data."""

    def __init__(self, style: str = 'seaborn-v0_8-darkgrid'):
        plt.style.use('default')
        sns.set_palette("husl")

    def plot_group_comparison(
        self,
        intervention_scores: np.ndarray,
        control_scores: np.ndarray,
        save_path: Optional[str] = None
    ):
        """Create violin plot comparing intervention vs control groups."""
        fig, ax = plt.subplots(figsize=(10, 6))

        data = pd.DataFrame({
            'Score': np.concatenate([intervention_scores, control_scores]),
            'Group': ['Intervention'] * len(intervention_scores) + ['Control'] * len(control_scores)
        })

        sns.violinplot(data=data, x='Group', y='Score', ax=ax)
        sns.swarmplot(data=data, x='Group', y='Score', color='black', alpha=0.5, ax=ax)

        ax.set_ylabel('OSCE Score (0-100)', fontsize=12)
        ax.set_xlabel('Group', fontsize=12)
        ax.set_title('VR Training vs Control Group Performance', fontsize=14, fontweight='bold')
        ax.axhline(y=70, color='red', linestyle='--', label='Competency Threshold')
        ax.legend()

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()

    def plot_knowledge_retention(
        self,
        timepoint_means: List[float],
        timepoint_sds: List[float],
        save_path: Optional[str] = None
    ):
        """Plot knowledge retention over time."""
        fig, ax = plt.subplots(figsize=(10, 6))

        timepoints = ['Baseline', 'Post-Training', '3 Months', '6 Months']
        x_pos = np.arange(len(timepoints))

        ax.errorbar(x_pos, timepoint_means, yerr=timepoint_sds,
                   marker='o', markersize=10, capsize=5, capthick=2, linewidth=2)

        ax.set_xticks(x_pos)
        ax.set_xticklabels(timepoints)
        ax.set_ylabel('Knowledge Test Score (0-100)', fontsize=12)
        ax.set_xlabel('Timepoint', fontsize=12)
        ax.set_title('Knowledge Retention Over Time', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.set_ylim([0, 100])

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()

    def plot_learning_curve(
        self,
        scenario_numbers: List[int],
        scores: List[float],
        predicted_scores: Optional[List[float]] = None,
        save_path: Optional[str] = None
    ):
        """Plot learning curve with optional fitted model."""
        fig, ax = plt.subplots(figsize=(10, 6))

        ax.scatter(scenario_numbers, scores, s=100, alpha=0.6, label='Actual Performance')

        if predicted_scores:
            ax.plot(scenario_numbers, predicted_scores, 'r-', linewidth=2,
                   label='Exponential Learning Curve')

        ax.set_xlabel('Scenario Number', fontsize=12)
        ax.set_ylabel('Performance Score (0-100)', fontsize=12)
        ax.set_title('Learning Curve - VR Training Progression', fontsize=14, fontweight='bold')
        ax.axhline(y=70, color='green', linestyle='--', alpha=0.5, label='Competency Threshold')
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

def example_usage():
    """Demonstrate usage of the VR training assessment module."""

    # Initialize components
    scorer = VRSessionScorer()
    reporter = PerformanceReporter()
    analyzer = TrainingOutcomeAnalyzer()
    visualizer = PerformanceVisualizer()

    # Example VR log data (would come from VR system)
    vr_log_example = {
        'session_id': 'VR-2025-001',
        'participant_id': 'P001',
        'scenario_id': 'SCN-001',
        'scenario_title': 'VA ECMO Cannulation - Femoral Approach',
        'difficulty': 'beginner',
        'ecmo_mode': 'VA',
        'start_time': '2025-10-05T09:00:00',
        'end_time': '2025-10-05T09:38:00',
        'total_duration_min': 38.0,
        'first_attempt_success': True,
        'scenario_completed': True,
        'complications_encountered': ['limb_ischemia'],
        'decision_points': [
            {
                'id': 'DP-001-01',
                'timestamp_min': 2.0,
                'selected_option': 'femoral_percutaneous',
                'time_to_decision_sec': 45.2
            },
            {
                'id': 'DP-001-04',
                'timestamp_min': 18.0,
                'selected_option': 'yes_routinely',
                'time_to_decision_sec': 32.1
            }
        ]
    }

    # Manual assessor scores
    manual_scores = {
        'technical_skill': 82.0,
        'nirs_interpretation': 75.0,
        'complication_management': 78.0,
        'communication': 85.0
    }

    # Score session
    performance = scorer.score_session(vr_log_example, manual_scores)

    # Generate report
    report = reporter.generate_session_report(performance, output_format='text')
    print(report)

    # Example group comparison
    intervention_scores = np.random.normal(78, 12, 50)  # VR group
    control_scores = np.random.normal(68, 15, 50)  # Control group

    comparison = analyzer.compare_groups(intervention_scores, control_scores)
    print("\n\nGroup Comparison:")
    print(json.dumps(comparison, indent=2))

    # Visualize
    # visualizer.plot_group_comparison(intervention_scores, control_scores)


if __name__ == "__main__":
    # Run example
    print("VR Training Assessment Module for ECMO CDSS")
    print("=" * 70)
    example_usage()
