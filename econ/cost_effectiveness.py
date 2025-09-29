"""
Cost-Effectiveness Analytics for ECMO
Taiwan ECMO CDSS - Health Economics Module

Calculates cost-effectiveness metrics, QALY analysis, and budget impact
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CostParameters:
    """Cost parameters for ECMO economics analysis"""
    # Daily costs (USD)
    ecmo_daily_cost: float = 3500.0  # Daily ECMO circuit and management
    icu_daily_cost: float = 2500.0   # ICU bed daily cost
    physician_daily_cost: float = 800.0  # Specialist physician costs
    nursing_daily_cost: float = 1200.0   # ECMO nursing costs
    
    # Setup costs (one-time)
    cannulation_cost: float = 15000.0   # Cannulation procedure
    decannulation_cost: float = 8000.0  # Decannulation procedure
    
    # Complication costs
    bleeding_cost: float = 25000.0      # Major bleeding episode
    stroke_cost: float = 45000.0        # Stroke/neurologic injury
    aki_cost: float = 20000.0           # Acute kidney injury
    infection_cost: float = 15000.0     # Healthcare-associated infection
    
    # Equipment costs
    circuit_replacement_cost: float = 3000.0  # ECMO circuit change
    dialysis_daily_cost: float = 1500.0       # CRRT if needed
    
    # Taiwan-specific adjustments
    taiwan_cost_multiplier: float = 0.65  # Adjust for Taiwan healthcare costs

@dataclass
class UtilityParameters:
    """Health utility parameters for QALY calculation"""
    # Health state utilities (0-1 scale)
    normal_health: float = 0.90
    ecmo_support: float = 0.20          # Utility while on ECMO
    post_ecmo_good: float = 0.80        # Good neurologic outcome
    post_ecmo_moderate: float = 0.60    # Moderate disability
    post_ecmo_severe: float = 0.30      # Severe disability
    death: float = 0.0
    
    # Life expectancy adjustments (years)
    life_expectancy_reduction: float = 2.0  # Years lost due to critical illness


class ECMOCostEffectivenessAnalyzer:
    """
    ECMO Cost-Effectiveness Analysis
    Performs economic evaluation of ECMO interventions
    """
    
    def __init__(self, cost_params: CostParameters = None, 
                 utility_params: UtilityParameters = None,
                 discount_rate: float = 0.03):
        """
        Initialize cost-effectiveness analyzer
        
        Args:
            cost_params: Cost parameter configuration
            utility_params: Utility parameter configuration
            discount_rate: Annual discount rate for future costs/benefits
        """
        self.cost_params = cost_params or CostParameters()
        self.utility_params = utility_params or UtilityParameters()
        self.discount_rate = discount_rate
        
        logger.info("Initialized ECMO Cost-Effectiveness Analyzer")
    
    def calculate_ecmo_costs(self, patient_data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate total ECMO-related costs per patient
        
        Args:
            patient_data: DataFrame with patient ECMO data
            
        Returns:
            DataFrame with cost calculations
        """
        logger.info(f"Calculating costs for {len(patient_data)} ECMO patients")
        
        costs_df = patient_data.copy()
        
        # Basic ECMO support costs
        costs_df['ecmo_duration_days'] = costs_df.get('ecmo_duration_hours', 120) / 24
        
        # Daily costs
        costs_df['daily_ecmo_cost'] = self.cost_params.ecmo_daily_cost
        costs_df['daily_icu_cost'] = self.cost_params.icu_daily_cost
        costs_df['daily_physician_cost'] = self.cost_params.physician_daily_cost
        costs_df['daily_nursing_cost'] = self.cost_params.nursing_daily_cost
        costs_df['daily_total_cost'] = (
            costs_df['daily_ecmo_cost'] + 
            costs_df['daily_icu_cost'] + 
            costs_df['daily_physician_cost'] + 
            costs_df['daily_nursing_cost']
        )
        
        # Total daily costs
        costs_df['total_daily_costs'] = (
            costs_df['daily_total_cost'] * costs_df['ecmo_duration_days']
        )
        
        # Setup costs
        costs_df['cannulation_cost'] = self.cost_params.cannulation_cost
        costs_df['decannulation_cost'] = np.where(
            costs_df.get('survived_to_discharge', True),
            self.cost_params.decannulation_cost, 0
        )
        
        # Complication costs
        costs_df['complication_costs'] = 0.0
        
        # Major bleeding
        bleeding_rate = 0.15  # 15% major bleeding rate
        costs_df['bleeding_cost'] = np.where(
            np.random.random(len(costs_df)) < bleeding_rate,
            self.cost_params.bleeding_cost, 0
        )
        
        # Stroke/neurologic injury
        stroke_rate = 0.08  # 8% stroke rate
        costs_df['stroke_cost'] = np.where(
            np.random.random(len(costs_df)) < stroke_rate,
            self.cost_params.stroke_cost, 0
        )
        
        # Acute kidney injury
        aki_rate = 0.25  # 25% AKI rate
        costs_df['aki_cost'] = np.where(
            np.random.random(len(costs_df)) < aki_rate,
            self.cost_params.aki_cost, 0
        )
        
        # Infection
        infection_rate = 0.20  # 20% infection rate
        costs_df['infection_cost'] = np.where(
            np.random.random(len(costs_df)) < infection_rate,
            self.cost_params.infection_cost, 0
        )
        
        costs_df['complication_costs'] = (
            costs_df['bleeding_cost'] + 
            costs_df['stroke_cost'] + 
            costs_df['aki_cost'] + 
            costs_df['infection_cost']
        )
        
        # Circuit replacement costs (every 7 days on average)
        costs_df['circuit_replacements'] = np.ceil(costs_df['ecmo_duration_days'] / 7)
        costs_df['circuit_costs'] = (
            costs_df['circuit_replacements'] * self.cost_params.circuit_replacement_cost
        )
        
        # Total costs
        costs_df['total_cost_usd'] = (
            costs_df['total_daily_costs'] + 
            costs_df['cannulation_cost'] + 
            costs_df['decannulation_cost'] + 
            costs_df['complication_costs'] + 
            costs_df['circuit_costs']
        )
        
        # Apply Taiwan cost adjustment
        costs_df['total_cost_usd'] *= self.cost_params.taiwan_cost_multiplier
        
        logger.info(f"Mean ECMO cost: ${costs_df['total_cost_usd'].mean():.0f} USD")
        
        return costs_df
    
    def calculate_qaly_outcomes(self, patient_data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Quality-Adjusted Life Years (QALYs) for ECMO patients
        
        Args:
            patient_data: DataFrame with patient outcomes
            
        Returns:
            DataFrame with QALY calculations
        """
        logger.info(f"Calculating QALYs for {len(patient_data)} patients")
        
        qaly_df = patient_data.copy()
        
        # Determine neurologic outcome categories
        if 'neurologic_outcome' not in qaly_df.columns:
            # Simulate neurologic outcomes based on survival
            survived = qaly_df.get('survived_to_discharge', True)
            outcomes = []
            for surv in survived:
                if not surv:
                    outcomes.append('death')
                else:
                    # Probability distribution for survivors
                    rand = np.random.random()
                    if rand < 0.50:
                        outcomes.append('normal')
                    elif rand < 0.75:
                        outcomes.append('mild_deficit')
                    elif rand < 0.90:
                        outcomes.append('moderate_deficit')
                    else:
                        outcomes.append('severe_deficit')
            qaly_df['neurologic_outcome'] = outcomes
        
        # Map outcomes to utilities
        utility_map = {
            'death': self.utility_params.death,
            'normal': self.utility_params.post_ecmo_good,
            'mild_deficit': self.utility_params.post_ecmo_good,
            'moderate_deficit': self.utility_params.post_ecmo_moderate,
            'severe_deficit': self.utility_params.post_ecmo_severe
        }
        
        qaly_df['post_ecmo_utility'] = qaly_df['neurologic_outcome'].map(utility_map)
        
        # Calculate remaining life expectancy based on age and outcome
        base_life_expectancy = 80 - qaly_df.get('age_years', 60)  # Simplified
        
        # Adjust for critical illness
        qaly_df['adjusted_life_expectancy'] = np.maximum(
            base_life_expectancy - self.utility_params.life_expectancy_reduction,
            0
        )
        
        # Calculate QALYs gained
        qaly_df['qalys_gained'] = (
            qaly_df['post_ecmo_utility'] * qaly_df['adjusted_life_expectancy']
        )
        
        # For patients who died, QALYs = 0
        qaly_df.loc[qaly_df['neurologic_outcome'] == 'death', 'qalys_gained'] = 0
        
        # Discount future QALYs
        if self.discount_rate > 0:
            discount_factor = 1 / (1 + self.discount_rate) ** (
                qaly_df['adjusted_life_expectancy'] / 2
            )  # Mid-point discounting
            qaly_df['discounted_qalys'] = qaly_df['qalys_gained'] * discount_factor
        else:
            qaly_df['discounted_qalys'] = qaly_df['qalys_gained']
        
        logger.info(f"Mean QALYs gained: {qaly_df['qalys_gained'].mean():.2f}")
        
        return qaly_df
    
    def calculate_icer(self, intervention_data: pd.DataFrame, 
                      comparator_data: pd.DataFrame) -> Dict:
        """
        Calculate Incremental Cost-Effectiveness Ratio (ICER)
        
        Args:
            intervention_data: Data for ECMO intervention group
            comparator_data: Data for comparator (standard care) group
            
        Returns:
            Dictionary with ICER analysis results
        """
        logger.info("Calculating ICER for ECMO vs standard care")
        
        # Calculate mean costs and QALYs for each group
        intervention_cost = intervention_data['total_cost_usd'].mean()
        intervention_qaly = intervention_data['discounted_qalys'].mean()
        
        comparator_cost = comparator_data['total_cost_usd'].mean()
        comparator_qaly = comparator_data['discounted_qalys'].mean()
        
        # Calculate incremental values
        incremental_cost = intervention_cost - comparator_cost
        incremental_qaly = intervention_qaly - comparator_qaly
        
        # Calculate ICER
        if incremental_qaly > 0:
            icer = incremental_cost / incremental_qaly
            interpretation = self._interpret_icer(icer)
        else:
            icer = float('inf') if incremental_cost > 0 else float('-inf')
            interpretation = "Dominated" if incremental_cost > 0 else "Dominant"
        
        results = {
            'intervention_cost': intervention_cost,
            'intervention_qaly': intervention_qaly,
            'comparator_cost': comparator_cost,
            'comparator_qaly': comparator_qaly,
            'incremental_cost': incremental_cost,
            'incremental_qaly': incremental_qaly,
            'icer': icer,
            'interpretation': interpretation,
            'cost_effective_50k': icer < 50000 if icer != float('inf') else False,
            'cost_effective_100k': icer < 100000 if icer != float('inf') else False
        }
        
        logger.info(f"ICER: ${icer:,.0f} per QALY gained" if icer != float('inf') else f"ICER: {icer}")
        
        return results
    
    def _interpret_icer(self, icer: float) -> str:
        """Interpret ICER value"""
        if icer < 0:
            return "Cost-saving (dominant)"
        elif icer < 20000:
            return "Very cost-effective"
        elif icer < 50000:
            return "Cost-effective"
        elif icer < 100000:
            return "Moderately cost-effective"
        else:
            return "Not cost-effective"
    
    def budget_impact_analysis(self, population_size: int, 
                              ecmo_utilization_rate: float,
                              years: int = 5) -> Dict:
        """
        Perform budget impact analysis for ECMO program
        
        Args:
            population_size: Target population size
            ecmo_utilization_rate: Proportion receiving ECMO (0-1)
            years: Time horizon for analysis
            
        Returns:
            Dictionary with budget impact results
        """
        logger.info(f"Performing budget impact analysis for {population_size} population over {years} years")
        
        # Estimate annual ECMO cases
        annual_ecmo_cases = population_size * ecmo_utilization_rate
        
        # Generate representative cost data
        np.random.seed(42)
        demo_data = pd.DataFrame({
            'ecmo_duration_hours': np.random.exponential(120, int(annual_ecmo_cases)),
            'survived_to_discharge': np.random.choice([True, False], 
                                                    int(annual_ecmo_cases), 
                                                    p=[0.6, 0.4]),
            'age_years': np.random.normal(55, 15, int(annual_ecmo_cases))
        })
        
        cost_data = self.calculate_ecmo_costs(demo_data)
        qaly_data = self.calculate_qaly_outcomes(cost_data)
        
        # Calculate annual costs
        annual_total_cost = cost_data['total_cost_usd'].sum()
        annual_qalys = qaly_data['discounted_qalys'].sum()
        
        # Project over multiple years
        yearly_results = []
        for year in range(1, years + 1):
            # Apply discount factor
            discount_factor = 1 / (1 + self.discount_rate) ** (year - 1)
            
            yearly_cost = annual_total_cost * discount_factor
            yearly_qalys = annual_qalys * discount_factor
            
            yearly_results.append({
                'year': year,
                'cases': annual_ecmo_cases,
                'total_cost': yearly_cost,
                'total_qalys': yearly_qalys,
                'cost_per_case': yearly_cost / annual_ecmo_cases,
                'qalys_per_case': yearly_qalys / annual_ecmo_cases
            })
        
        # Summary statistics
        total_cost_all_years = sum(r['total_cost'] for r in yearly_results)
        total_qalys_all_years = sum(r['total_qalys'] for r in yearly_results)
        
        budget_impact = {
            'population_size': population_size,
            'utilization_rate': ecmo_utilization_rate,
            'annual_cases': annual_ecmo_cases,
            'time_horizon_years': years,
            'yearly_results': yearly_results,
            'total_program_cost': total_cost_all_years,
            'total_program_qalys': total_qalys_all_years,
            'cost_per_qaly': total_cost_all_years / total_qalys_all_years if total_qalys_all_years > 0 else 0
        }
        
        logger.info(f"Total {years}-year budget impact: ${total_cost_all_years:,.0f}")
        
        return budget_impact
    
    def sensitivity_analysis(self, base_case_data: pd.DataFrame, 
                           parameter_ranges: Dict) -> Dict:
        """
        Perform one-way sensitivity analysis on key parameters
        
        Args:
            base_case_data: Base case patient data
            parameter_ranges: Dictionary of parameter ranges to test
            
        Returns:
            Dictionary with sensitivity analysis results
        """
        logger.info("Performing sensitivity analysis")
        
        sensitivity_results = {}
        base_costs = self.calculate_ecmo_costs(base_case_data)
        base_qalys = self.calculate_qaly_outcomes(base_costs)
        base_icer = base_costs['total_cost_usd'].mean() / base_qalys['discounted_qalys'].mean()
        
        for param, (low, high) in parameter_ranges.items():
            param_results = []
            
            # Test parameter at low, base, and high values
            for value in [low, getattr(self.cost_params, param), high]:
                # Temporarily modify parameter
                original_value = getattr(self.cost_params, param)
                setattr(self.cost_params, param, value)
                
                # Recalculate
                test_costs = self.calculate_ecmo_costs(base_case_data)
                test_qalys = self.calculate_qaly_outcomes(test_costs)
                test_icer = test_costs['total_cost_usd'].mean() / test_qalys['discounted_qalys'].mean()
                
                param_results.append({
                    'parameter_value': value,
                    'icer': test_icer,
                    'change_from_base': (test_icer - base_icer) / base_icer
                })
                
                # Restore original value
                setattr(self.cost_params, param, original_value)
            
            sensitivity_results[param] = param_results
        
        return sensitivity_results
    
    def plot_cost_effectiveness_plane(self, intervention_data: pd.DataFrame,
                                    comparator_data: pd.DataFrame):
        """
        Plot cost-effectiveness plane
        
        Args:
            intervention_data: ECMO intervention data
            comparator_data: Standard care comparator data
        """
        plt.figure(figsize=(10, 8))
        
        # Calculate incremental costs and effects
        int_cost = intervention_data['total_cost_usd'].values
        int_qaly = intervention_data['discounted_qalys'].values
        comp_cost = comparator_data['total_cost_usd'].values
        comp_qaly = comparator_data['discounted_qalys'].values
        
        # For plotting, we'll use mean values with confidence intervals
        inc_cost_mean = int_cost.mean() - comp_cost.mean()
        inc_qaly_mean = int_qaly.mean() - comp_qaly.mean()
        
        # Plot point
        plt.scatter(inc_qaly_mean, inc_cost_mean, s=100, c='red', 
                   label='ECMO vs Standard Care', alpha=0.7)
        
        # Add willingness-to-pay thresholds
        qaly_range = np.linspace(-0.5, max(inc_qaly_mean * 1.5, 1), 100)
        wtp_50k = qaly_range * 50000
        wtp_100k = qaly_range * 100000
        
        plt.plot(qaly_range, wtp_50k, '--', color='orange', label='$50,000/QALY threshold')
        plt.plot(qaly_range, wtp_100k, '--', color='green', label='$100,000/QALY threshold')
        
        # Formatting
        plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        plt.axvline(x=0, color='black', linestyle='-', alpha=0.3)
        
        plt.xlabel('Incremental QALYs')
        plt.ylabel('Incremental Cost ($USD)')
        plt.title('Cost-Effectiveness Plane: ECMO vs Standard Care')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Add quadrant labels
        plt.text(inc_qaly_mean/2, max(inc_cost_mean, wtp_100k.max())*0.8, 
                'More effective\nMore expensive', ha='center', alpha=0.6)
        
        plt.tight_layout()
        plt.savefig('cost_effectiveness_plane.png', dpi=300, bbox_inches='tight')
        plt.show()


def generate_demo_economic_data(n_patients: int = 500) -> pd.DataFrame:
    """Generate demo data for economic analysis"""
    np.random.seed(42)
    
    data = {
        'patient_id': [f'PT{i:04d}' for i in range(n_patients)],
        'age_years': np.random.normal(55, 15, n_patients).clip(18, 85),
        'ecmo_duration_hours': np.random.exponential(120, n_patients).clip(24, 720),
        'survived_to_discharge': np.random.choice([True, False], n_patients, p=[0.6, 0.4]),
        'ecmo_type': np.random.choice(['VA', 'VV'], n_patients, p=[0.6, 0.4])
    }
    
    return pd.DataFrame(data)


if __name__ == "__main__":
    # Demo analysis
    logger.info("ECMO Cost-Effectiveness Analysis Demo")
    
    # Generate demo data
    ecmo_data = generate_demo_economic_data(500)
    
    # Initialize analyzer
    analyzer = ECMOCostEffectivenessAnalyzer()
    
    # Calculate costs and QALYs
    cost_data = analyzer.calculate_ecmo_costs(ecmo_data)
    qaly_data = analyzer.calculate_qaly_outcomes(cost_data)
    
    # Budget impact analysis
    budget_impact = analyzer.budget_impact_analysis(
        population_size=100000,
        ecmo_utilization_rate=0.001,  # 0.1% utilization rate
        years=5
    )
    
    logger.info(f"Budget impact results: {budget_impact}")
    logger.info("Cost-effectiveness analysis complete")