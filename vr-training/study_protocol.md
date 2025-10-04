# VR Training Study Protocol for ECMO Clinical Decision Support
## Taiwan ECMO CDSS with NIRS Monitoring Integration

### 1. Study Overview

**Title**: Effectiveness of Virtual Reality Training for ECMO Management: A Randomized Controlled Trial in Taiwan

**Study Design**: Prospective, randomized controlled trial with pre-post assessment

**Study Framework**: ADDIE-based instructional design (Analysis, Design, Development, Implementation, Evaluation)

**Primary Hypothesis**: VR-based ECMO training improves clinical competency and decision-making compared to traditional didactic education

### 2. Study Objectives

#### Primary Objective
Evaluate the effectiveness of VR-based ECMO training on clinical competency scores for ECMO cannulation and management in critical care physicians and perfusionists.

#### Secondary Objectives
1. Assess knowledge retention at 3 and 6 months post-training
2. Evaluate transfer of skills to clinical practice (simulated scenarios)
3. Compare VA vs VV ECMO scenario performance
4. Measure user satisfaction and simulator fidelity
5. Analyze relationship between training performance and NIRS monitoring proficiency

### 3. Study Population

#### Inclusion Criteria
- Critical care physicians (ICU attending, fellows, residents PGY3+)
- Cardiovascular or cardiac surgeons
- Perfusionists with <2 years ECMO experience
- Nurses working in ICU with ECMO capability
- Affiliated with Taiwan medical centers performing ECMO

#### Exclusion Criteria
- >50 ECMO cannulation procedures performed
- Participation in ECMO VR training within past 12 months
- Visual impairment preventing VR headset use
- Motion sickness susceptibility (severe)
- Unable to provide informed consent

#### Sample Size Calculation

**Power Analysis**:
- Primary endpoint: Clinical competency score (0-100 scale)
- Effect size: Cohen's d = 0.6 (medium-large effect)
- Power: 80% (β = 0.20)
- Significance level: α = 0.05 (two-tailed)
- Attrition rate: 15%

**Calculation**:
```
n = 2 × (Z_α/2 + Z_β)² × σ² / δ²
n = 2 × (1.96 + 0.84)² × 15² / (0.6 × 15)²
n = 2 × 7.84 × 225 / 81
n ≈ 44 per group
```

**Total Sample Size**: 100 participants (50 intervention, 50 control, accounting for 15% dropout)

**Stratification Factors**:
- Professional role (physician, perfusionist, nurse)
- Prior ECMO exposure (<5 cases, 5-20 cases, >20 cases)
- Institution (NTUH, CGMH, TVGH, other)

### 4. Randomization and Blinding

#### Randomization
- **Method**: Computer-generated block randomization (block size = 4)
- **Stratification**: By professional role and prior ECMO exposure
- **Allocation concealment**: Sealed, opaque, sequentially numbered envelopes
- **Timing**: After consent and baseline assessment

#### Blinding
- **Participants**: Cannot be blinded to intervention
- **Assessors**: Blinded to group allocation for:
  - Post-test clinical competency assessment
  - Simulated scenario evaluation
  - Follow-up knowledge tests
- **Data analysts**: Blinded until primary analysis complete

### 5. Study Intervention

#### Control Group: Traditional Didactic Training
**Duration**: 4 hours
**Components**:
1. ELSO guideline review lecture (90 min)
2. ECMO circuit demonstration (60 min)
3. Cannulation video review (45 min)
4. Case-based discussion (45 min)

**Materials**: PowerPoint slides, ELSO guidelines, video recordings, mannequin demonstration

#### Intervention Group: VR-Based ECMO Training
**Duration**: 4 hours
**Components**:
1. VR system orientation (15 min)
2. ECMO physiology VR module (30 min)
3. Hands-on VR scenarios (180 min):
   - VA ECMO cannulation (femoral) - 45 min
   - VV ECMO cannulation (bicaval) - 45 min
   - Circuit emergency management - 45 min
   - NIRS-guided optimization - 45 min
4. Debriefing and reflection (15 min)

**VR Platform**: HTC Vive Pro / Meta Quest 3
**Software**: Custom ECMO training module with NIRS integration
**Supervision**: 1:4 instructor-to-participant ratio

### 6. Training Scenarios (See scenarios.yaml for details)

#### Core Scenarios (All Participants)
1. **VA ECMO Cannulation** - Femoral approach for cardiogenic shock
2. **VV ECMO Cannulation** - Bicaval approach for ARDS
3. **Circuit Emergency** - Oxygenator failure recognition and management
4. **NIRS Monitoring** - Cerebral/somatic NIRS interpretation during ECMO
5. **Weaning Protocol** - Step-wise ECMO flow reduction

#### Advanced Scenarios (Optional)
6. **ECPR** - Emergency cannulation during active CPR
7. **Limb Ischemia** - Recognition and distal perfusion catheter placement
8. **Hemorrhage Management** - Cannula site bleeding control
9. **Multi-organ Support** - ECMO + CRRT integration
10. **Pediatric ECMO** - Size-specific considerations

### 7. Study Endpoints

#### Primary Endpoint
**Clinical Competency Score** (assessed at post-training, 3 months, 6 months)
- Objective Structured Clinical Examination (OSCE) score (0-100)
- Domains (20 points each):
  1. Pre-cannulation assessment and planning
  2. Cannulation technique and safety
  3. Circuit management and troubleshooting
  4. NIRS monitoring and interpretation
  5. Complication recognition and management

#### Secondary Endpoints

**Knowledge Outcomes**:
- ECMO knowledge test score (40-item multiple choice, 0-100 scale)
- ELSO guideline compliance score
- NIRS physiology understanding score

**Performance Outcomes**:
- Simulated scenario completion time (minutes)
- Error rate (critical errors per scenario)
- Decision-making accuracy (% correct decisions)
- NIRS-guided intervention appropriateness

**Clinical Transfer**:
- Supervisor-rated clinical performance (1-5 Likert scale)
- Time to first supervised ECMO cannulation (if applicable)
- Complication rate in first 10 supervised cases (if applicable)

**User Experience**:
- Simulator Sickness Questionnaire (SSQ)
- System Usability Scale (SUS)
- Training satisfaction (5-point Likert)
- Perceived fidelity (5-point Likert)

### 8. Data Collection Schedule

| Timepoint | Intervention | Control | Assessments |
|-----------|-------------|---------|-------------|
| Baseline (T0) | X | X | Demographics, Prior experience, Baseline knowledge test, Pre-training competency OSCE |
| Intervention (T1) | 4h VR | 4h Didactic | Simulator metrics (VR group only) |
| Immediate Post (T2) | X | X | Knowledge test, Post-training competency OSCE, User satisfaction |
| 3 Months (T3) | X | X | Knowledge retention test, Competency OSCE, Clinical performance rating |
| 6 Months (T4) | X | X | Knowledge retention test, Competency OSCE, Clinical performance rating, Clinical outcomes (if applicable) |

### 9. Statistical Analysis Plan

#### Primary Analysis
**Model**: Mixed-effects linear regression
```
Competency_Score ~ Group + Time + Group×Time + (1|Participant) + Stratification_Factors
```

**Primary Comparison**: Group difference in competency score at T2 (immediate post-training)

#### Secondary Analyses
1. **Knowledge retention**: Repeated measures ANOVA with time as within-subject factor
2. **Scenario performance**: Independent t-tests or Mann-Whitney U tests
3. **Subgroup analyses**: Interaction tests by professional role, prior experience
4. **Correlation analyses**: Training metrics vs. clinical competency
5. **NIRS proficiency**: Separate analysis of NIRS-related competency items

#### Effect Size Reporting
- Cohen's d for between-group comparisons
- Partial η² for repeated measures effects
- 95% confidence intervals for all estimates

#### Missing Data
- **Approach**: Multiple imputation (m=20 datasets) under missing at random (MAR) assumption
- **Sensitivity analysis**: Complete case analysis and pattern-mixture models

#### Significance Level
- Primary endpoint: α = 0.05 (two-tailed)
- Secondary endpoints: Bonferroni correction for multiple comparisons

### 10. Ethical Considerations

#### Ethics Approval
- Institutional Review Board approval from all participating institutions
- Clinical trial registration (ClinicalTrials.gov)

#### Informed Consent
- Written informed consent from all participants
- Voluntary participation with right to withdraw
- No impact on employment or clinical privileges

#### Data Protection
- De-identified data storage
- HIPAA/GDPR-equivalent compliance (Taiwan Personal Data Protection Act)
- Secure REDCap database

#### Safety Monitoring
- VR-related adverse events (simulator sickness, discomfort)
- Real-time monitoring during VR sessions
- Withdrawal criteria: severe simulator sickness, participant request

### 11. Timeline and Milestones

| Phase | Duration | Activities |
|-------|----------|------------|
| Preparation | Month 1-2 | IRB approval, VR system setup, Assessor training |
| Recruitment | Month 3-6 | Participant enrollment, Baseline assessment |
| Intervention | Month 7-10 | VR and control group training sessions |
| Immediate Follow-up | Month 7-10 | Post-training assessments |
| 3-Month Follow-up | Month 10-13 | Retention testing, Clinical performance evaluation |
| 6-Month Follow-up | Month 13-16 | Final assessments, Clinical outcome collection |
| Analysis & Reporting | Month 17-20 | Statistical analysis, Manuscript preparation, Dissemination |

### 12. Budget Considerations (Taiwan Context)

**Major Cost Categories**:
- VR hardware (4 stations × NT$50,000 = NT$200,000)
- VR software development/licensing (NT$500,000)
- Personnel (research coordinators, assessors) (NT$800,000)
- Participant incentives (NT$300,000)
- Data management (REDCap, statistical software) (NT$100,000)
- **Total Estimated Budget**: NT$2,000,000 (~USD $65,000)

### 13. Quality Assurance

#### Training Standardization
- Identical didactic materials for control group
- Standardized VR scenario progression
- Instructor training and certification
- Fidelity checklists for both interventions

#### Assessment Reliability
- Inter-rater reliability testing (κ > 0.80)
- Regular calibration meetings for OSCE assessors
- Video recording of OSCE sessions for quality review

#### Data Quality
- Real-time data validation in REDCap
- Monthly data quality audits
- Source data verification (10% random sample)

### 14. Dissemination Plan

**Target Audiences**:
- Critical care medicine community
- Medical education researchers
- ELSO organization
- Taiwan ICU Society

**Planned Outputs**:
1. Primary outcomes manuscript (target: *Critical Care Medicine*, *Intensive Care Medicine*)
2. VR methodology paper (target: *Simulation in Healthcare*)
3. Conference presentations (SCCM, ESICM, Taiwan Critical Care Conference)
4. VR training module open-source release (GitHub)
5. Policy brief for Taiwan Ministry of Health and Welfare

### 15. Study Limitations

**Known Limitations**:
1. Cannot blind participants to intervention
2. Simulator fidelity may not fully replicate clinical environment
3. Short-term follow-up (6 months) may not capture long-term skill retention
4. Clinical outcome data dependent on participant ECMO exposure
5. Single-country study may limit generalizability

**Mitigation Strategies**:
1. Blinded outcome assessors
2. High-fidelity VR with expert input
3. Extended follow-up substudy planned
4. Supervisor ratings as proxy for clinical performance
5. Multi-center design within Taiwan

---

## References to ELSO Guidelines

This study protocol incorporates the following ELSO guidelines:
- ELSO General Guidelines for ECMO Centers (2022)
- ELSO Adult Cardiac Failure Supplement (2021)
- ELSO Adult Respiratory Failure Supplement (2021)
- ELSO Anticoagulation Guidelines (2020)

## Alignment with Taiwan Clinical Context

**Taiwan-Specific Considerations**:
- National Health Insurance (NHI) reimbursement policies for ECMO
- Language: Training available in Mandarin and English
- Regional ECMO referral networks (Northern, Central, Southern Taiwan)
- Integration with existing Taiwan ECMO quality registry
- Collaboration with Taiwan Society of Critical Care Medicine
