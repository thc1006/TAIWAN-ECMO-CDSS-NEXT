# VR Training Metrics for ECMO Clinical Decision Support
## Comprehensive Assessment Framework

### 1. Performance Metrics

#### 1.1 Task Completion Metrics
**Objective**: Measure efficiency and accuracy of VR scenario completion

| Metric | Unit | Description | Target Range | Data Source |
|--------|------|-------------|--------------|-------------|
| **Total scenario time** | minutes | Time from scenario start to completion | 15-45 min (scenario-dependent) | VR system log |
| **Cannulation time** | minutes | Time from skin prep to cannula secured | VA: 8-15 min, VV: 10-18 min | VR system log |
| **Decision time** | seconds | Time to make critical decisions (mean) | <60 sec | VR system log |
| **Setup time** | minutes | Circuit priming and equipment preparation | 5-10 min | VR system log |
| **First-attempt success rate** | % | Successful cannulation on first attempt | >70% | VR system scoring |
| **Scenario completion rate** | % | Scenarios completed without critical failure | >85% | VR system scoring |

#### 1.2 Error and Safety Metrics
**Objective**: Identify critical errors and safety violations

| Metric | Unit | Description | Acceptable Range | Severity |
|--------|------|-------------|------------------|----------|
| **Critical errors** | count | Errors causing patient harm in simulation | 0-1 per scenario | High |
| **Major errors** | count | Errors requiring intervention to prevent harm | 0-2 per scenario | Medium |
| **Minor errors** | count | Technical errors without immediate harm | 0-5 per scenario | Low |
| **Safety violations** | count | Breaches of sterile technique or safety protocols | 0 | High |
| **Error recovery time** | seconds | Time to recognize and correct errors (mean) | <120 sec | VR system log |

**Critical Error Categories**:
1. Wrong cannulation site selected
2. Air embolism introduced to circuit
3. Incorrect anticoagulation dosing (>50% deviation)
4. Failed to recognize oxygenator failure
5. Limb ischemia not addressed within 30 min
6. Catastrophic hemorrhage mismanagement
7. Circuit disconnection not recognized

**Scoring**: Critical errors result in automatic scenario failure

#### 1.3 Technical Skill Metrics
**Objective**: Assess procedural competency using validated checklists

**Cannulation Skill Checklist (0-100 points)**:
- [ ] Pre-procedural timeout performed (5 pts)
- [ ] Appropriate site selection based on indication (10 pts)
- [ ] Sterile technique maintained throughout (10 pts)
- [ ] Ultrasound guidance used appropriately (10 pts)
- [ ] Vessel access obtained safely (15 pts)
- [ ] Guidewire advanced correctly (10 pts)
- [ ] Cannula inserted to appropriate depth (15 pts)
- [ ] Position confirmed (X-ray/echo) (10 pts)
- [ ] Cannula secured appropriately (10 pts)
- [ ] Post-cannulation assessment performed (5 pts)

**Circuit Management Skill Checklist (0-100 points)**:
- [ ] Pre-bypass checklist completed (10 pts)
- [ ] Appropriate initial flow rate selected (15 pts)
- [ ] Sweep gas titrated to target PaCO2 (15 pts)
- [ ] Anticoagulation initiated correctly (15 pts)
- [ ] Circuit pressures monitored (10 pts)
- [ ] Gas exchange adequacy assessed (15 pts)
- [ ] Oxygenator function checked (10 pts)
- [ ] Troubleshooting performed when needed (10 pts)

#### 1.4 Decision-Making Metrics
**Objective**: Evaluate clinical reasoning and NIRS-guided interventions

| Metric | Unit | Description | Target | Method |
|--------|------|-------------|--------|--------|
| **Correct decision rate** | % | Proportion of correct clinical decisions | >80% | Scenario analysis |
| **NIRS interpretation accuracy** | % | Correct interpretation of NIRS trends | >75% | Expert rating |
| **Intervention appropriateness** | 1-5 Likert | Appropriateness of NIRS-guided interventions | ≥4.0 | Expert rating |
| **Diagnostic accuracy** | % | Correct complication diagnosis | >70% | Scenario analysis |
| **Priority setting** | 1-5 Likert | Appropriate prioritization of tasks | ≥4.0 | Expert rating |

**NIRS-Guided Decision Points** (scored individually):
1. Recognition of cerebral desaturation (rScO2 <50%)
2. Identification of differential hypoxia (North-South syndrome)
3. Appropriate response to declining somatic NIRS
4. Recognition of NIRS artifact vs. true signal
5. Integration of NIRS with other hemodynamic parameters

### 2. Knowledge Retention Metrics

#### 2.1 ECMO Knowledge Test
**Format**: 40-item multiple choice examination
**Scoring**: 0-100 scale (2.5 points per item)
**Administration**: Baseline, Immediate post-training, 3 months, 6 months

**Content Domains** (10 items each):
1. **ECMO Indications and Contraindications** (25%)
   - ELSO guideline-based patient selection
   - VA vs VV ECMO indications
   - Absolute and relative contraindications

2. **Circuit Physiology and Management** (25%)
   - Pump flow physiology
   - Gas exchange principles
   - Anticoagulation management
   - Circuit component functions

3. **Cannulation Techniques** (25%)
   - Anatomical considerations
   - Peripheral vs central cannulation
   - Ultrasound-guided techniques
   - Complication prevention

4. **NIRS Monitoring and Interpretation** (25%)
   - NIRS physiology
   - Normal vs abnormal values
   - Troubleshooting low NIRS values
   - Integration with ECMO management

**Psychometric Properties**:
- Cronbach's α ≥ 0.80 (internal consistency)
- Test-retest reliability ≥ 0.85
- Difficulty index: 0.30-0.70 per item
- Discrimination index: ≥0.30 per item

#### 2.2 ELSO Guideline Compliance Score
**Format**: 15-item scenario-based assessment
**Scoring**: 0-100 scale

**Assessed Guideline Components**:
1. Pre-ECMO checklist completion
2. Appropriate mode selection (VA/VV)
3. Cannula size selection
4. Initial ventilator settings on ECMO
5. Anticoagulation protocol adherence
6. Blood gas target ranges
7. Transfusion thresholds
8. Bleeding management protocols
9. Weaning criteria application
10. Daily rounding checklist

#### 2.3 NIRS Physiology Understanding Score
**Format**: 10-item short answer/diagram assessment
**Scoring**: 0-100 scale (10 points per item)

**Topics**:
1. NIRS measurement principles (near-infrared spectroscopy)
2. Cerebral vs somatic NIRS differences
3. Normal NIRS values during ECMO
4. NIRS response to flow changes
5. NIRS in VA vs VV ECMO
6. Differential hypoxia recognition
7. NIRS artifact identification
8. Clinical significance of trends
9. Intervention thresholds
10. Integration with SvO2/ScvO2

### 3. Clinical Competency Scoring Rubrics

#### 3.1 Objective Structured Clinical Examination (OSCE)
**Format**: 5 stations × 20 points = 100 points total
**Duration**: 10 minutes per station
**Assessment**: Live performance with blinded assessor

**Station 1: Pre-Cannulation Assessment (20 points)**
- [ ] Reviews indication and contraindications (5 pts)
- [ ] Assesses patient hemodynamics and labs (5 pts)
- [ ] Selects appropriate ECMO mode and cannulation strategy (5 pts)
- [ ] Identifies potential complications (3 pts)
- [ ] Obtains informed consent elements (2 pts)

**Station 2: Cannulation Technique (20 points)**
- [ ] Demonstrates sterile technique (5 pts)
- [ ] Uses ultrasound guidance appropriately (5 pts)
- [ ] Performs vessel access safely (5 pts)
- [ ] Confirms cannula position (3 pts)
- [ ] Secures cannula appropriately (2 pts)

**Station 3: Circuit Management and Troubleshooting (20 points)**
- [ ] Initiates ECMO with appropriate settings (5 pts)
- [ ] Monitors circuit parameters (pressures, flows) (5 pts)
- [ ] Recognizes circuit emergency (oxygenator failure) (5 pts)
- [ ] Executes emergency circuit change protocol (3 pts)
- [ ] Maintains patient safety during intervention (2 pts)

**Station 4: NIRS Monitoring and Interpretation (20 points)**
- [ ] Interprets NIRS values correctly (5 pts)
- [ ] Identifies abnormal NIRS trends (5 pts)
- [ ] Generates appropriate differential diagnosis (5 pts)
- [ ] Implements evidence-based interventions (3 pts)
- [ ] Re-evaluates after intervention (2 pts)

**Station 5: Complication Recognition and Management (20 points)**
- [ ] Recognizes complication promptly (5 pts)
- [ ] Prioritizes interventions appropriately (5 pts)
- [ ] Executes management plan (5 pts)
- [ ] Communicates with team effectively (3 pts)
- [ ] Documents critical actions (2 pts)

**Scoring Rubric per Item**:
- Full points: Performed correctly without prompting
- Half points: Performed with minor errors or prompting
- Zero points: Not performed or critical errors

**Pass/Fail Threshold**: ≥70/100 (70%)

#### 3.2 Global Rating Scale (GRS)
**Format**: 7-point Likert scale for 6 domains
**Assessor**: Blinded expert observer

| Domain | Score 1-2 (Novice) | Score 3-5 (Competent) | Score 6-7 (Expert) |
|--------|-------------------|----------------------|-------------------|
| **Overall technical skill** | Multiple errors, unsafe | Few errors, generally safe | No errors, efficient |
| **Knowledge of procedure** | Inadequate understanding | Good understanding | Complete mastery |
| **Clinical judgment** | Poor decisions | Appropriate decisions | Excellent decisions |
| **Efficiency/time management** | Very slow, inefficient | Reasonable pace | Fast and efficient |
| **Communication** | Poor team communication | Adequate communication | Excellent communication |
| **Professional behavior** | Unprofessional | Professional | Exemplary |

**Total GRS Score**: Sum of 6 domains (6-42 scale)
**Conversion to 100-point scale**: (Total - 6) / 36 × 100

### 4. User Experience and Satisfaction Metrics

#### 4.1 Simulator Sickness Questionnaire (SSQ)
**Purpose**: Monitor VR-related adverse effects
**Timing**: Pre-VR, Immediately post-VR, 30 min post-VR
**Format**: 16-item questionnaire, 0-3 severity scale

**Symptom Categories**:
- **Nausea** (7 items): General discomfort, increased salivation, sweating, nausea, difficulty concentrating, stomach awareness, burping
- **Oculomotor** (7 items): General discomfort, fatigue, headache, eyestrain, difficulty focusing, difficulty concentrating, blurred vision
- **Disorientation** (7 items): Difficulty focusing, nausea, fullness of head, blurred vision, dizzy (eyes open), dizzy (eyes closed), vertigo

**Scoring**: Total score = sum × 3.74
**Interpretation**:
- 0-5: Negligible symptoms
- 5-10: Minimal symptoms
- 10-15: Significant symptoms (monitor)
- >15: Severe symptoms (discontinue VR)

#### 4.2 System Usability Scale (SUS)
**Purpose**: Evaluate VR system usability
**Timing**: Post-training session
**Format**: 10-item questionnaire, 1-5 Likert scale

**Items** (odd items positive, even items negative):
1. I think I would like to use this VR system frequently
2. I found the VR system unnecessarily complex
3. I thought the VR system was easy to use
4. I think I would need support to use this VR system
5. I found the various functions in this VR system were well integrated
6. I thought there was too much inconsistency in this VR system
7. I would imagine that most people would learn to use this VR system quickly
8. I found the VR system very cumbersome to use
9. I felt very confident using the VR system
10. I needed to learn a lot of things before I could get going with this VR system

**Scoring**: Convert to 0-100 scale
- Score 68+: Above average usability
- Score 50-67: Average usability
- Score <50: Below average usability

#### 4.3 Training Satisfaction Survey
**Format**: 20-item questionnaire, 1-5 Likert scale

**Domains** (4 items each):
1. **Content Relevance**: Training matched clinical needs
2. **Learning Effectiveness**: Felt improvement in skills/knowledge
3. **Engagement**: Training was interesting and motivating
4. **Fidelity**: Simulation realism and accuracy
5. **Instructor Quality**: Support and feedback quality

**Scoring**: Mean score per domain and overall (1-5 scale)
**Benchmark**: ≥4.0 considered satisfactory

#### 4.4 Perceived Fidelity Scale
**Format**: 15-item questionnaire, 1-5 Likert scale

**Assessed Fidelity Components**:
1. Visual realism of ECMO equipment
2. Haptic feedback accuracy
3. Anatomical accuracy of cannulation
4. Physiological response realism
5. NIRS monitor accuracy
6. Circuit emergency realism
7. Team interaction realism
8. Clinical environment immersion
9. Patient response realism
10. Equipment interaction naturalness

**Scoring**: Mean fidelity score (1-5 scale)
**Target**: ≥3.5 for acceptable fidelity

### 5. Teamwork and Communication Metrics

#### 5.1 Team Performance Metrics
**Context**: Applicable to multi-user VR scenarios

| Metric | Unit | Description | Target | Method |
|--------|------|-------------|--------|--------|
| **Teamwork score** | 0-100 | Overall team coordination | ≥75 | T-NOTECHS scale |
| **Leadership score** | 0-100 | Team leader effectiveness | ≥75 | ANTS scale |
| **Communication latency** | seconds | Response time to team communication | <15 sec | VR log analysis |
| **Task delegation** | 1-5 Likert | Appropriateness of task distribution | ≥4.0 | Expert rating |
| **Closed-loop communication** | % | Proportion of read-back confirmations | ≥80% | Audio analysis |

#### 5.2 T-NOTECHS (Team Non-Technical Skills) Scale
**Format**: 5 categories × 4 behaviors = 20 items
**Scoring**: 1-5 Likert per item, converted to 0-100

**Categories**:
1. **Cooperation**: Team building, supporting others, conflict solving
2. **Leadership**: Use of authority, maintaining standards, planning
3. **Situation awareness**: Gathering information, recognizing issues, anticipating
4. **Decision making**: Identifying options, balancing risks, re-evaluating
5. **Task management**: Planning, prioritizing, providing standards, identifying resources

### 6. Clinical Transfer Metrics

#### 6.1 Supervisor-Rated Clinical Performance
**Format**: 10-item assessment by clinical supervisor
**Timing**: 3 months and 6 months post-training
**Scoring**: 1-5 Likert scale per item

**Assessed Domains**:
1. Pre-ECMO patient assessment quality
2. Cannulation technique (if performed)
3. Circuit management knowledge
4. NIRS interpretation in clinical practice
5. Complication recognition speed
6. Evidence-based decision making
7. Team communication
8. Adherence to protocols
9. Overall ECMO clinical competency
10. Readiness for independent practice

**Total Score**: Sum / 50 × 100 (0-100 scale)

#### 6.2 Clinical Outcome Metrics (if applicable)
**Note**: Only for participants who perform ECMO cannulation during follow-up

| Metric | Unit | Description | Benchmark | Data Source |
|--------|------|-------------|-----------|-------------|
| **Time to first supervised ECMO** | days | Days from training to first supervised case | N/A | Clinical records |
| **First cannulation success rate** | % | Successful first cannulation attempt | >70% | Procedure reports |
| **Complication rate (first 10 cases)** | % | Complications in first 10 supervised cases | <15% | Adverse event reports |
| **Supervisor confidence rating** | 1-5 Likert | Supervisor confidence in trainee ability | ≥4.0 | Supervisor survey |
| **Readiness for independence** | 1-5 Likert | Trainee readiness for unsupervised practice | ≥4.0 | Competency committee |

### 7. Advanced Analytics Metrics

#### 7.1 Learning Curve Analysis
**Method**: Exponential decay model fit to performance over repeated scenarios

**Model**: Performance(t) = P_asymptote + (P_initial - P_asymptote) × e^(-λt)

**Metrics**:
- **Learning rate (λ)**: Speed of skill acquisition (higher = faster learning)
- **Asymptotic performance (P_asymptote)**: Maximum achievable performance
- **Trials to proficiency**: Number of scenarios to reach 80% of asymptote

#### 7.2 Eye-Tracking Metrics (if available)
**Hardware**: Eye-tracking integrated VR headset

| Metric | Unit | Description | Clinical Relevance |
|--------|------|-------------|--------------------|
| **Fixation duration** | ms | Mean fixation time on critical areas | Attention allocation |
| **Saccade rate** | per second | Eye movement frequency | Visual search efficiency |
| **Gaze transition rate** | per minute | Transitions between monitors/patient | Situational awareness |
| **Time to first fixation** | seconds | Time to notice critical changes | Vigilance |
| **Proportion of time on NIRS** | % | Time spent monitoring NIRS display | NIRS utilization |

#### 7.3 Motion Capture Metrics (if available)
**Hardware**: Hand tracking sensors

| Metric | Unit | Description | Skill Indicator |
|--------|------|-------------|-----------------|
| **Hand tremor** | mm | Hand steadiness during cannulation | Procedural confidence |
| **Movement efficiency** | arbitrary units | Economy of motion | Technical skill |
| **Instrument trajectory** | smoothness index | Smoothness of cannula advancement | Expertise level |
| **Bimanual coordination** | correlation coefficient | Two-hand coordination | Dexterity |

### 8. Data Collection and Storage

#### 8.1 Automated VR Metrics
**Collection**: Real-time logging by VR system
**Storage**: PostgreSQL database with timestamped events
**Export**: CSV/JSON for analysis

**Logged Events**:
- Scenario start/end timestamps
- Decision points and selections
- Error occurrences (type, severity, timestamp)
- Vital sign/parameter changes
- User actions (cannula placement, settings adjustments)
- Intervention outcomes

#### 8.2 Manual Assessment Data
**Collection**: REDCap electronic data capture
**Quality control**: Double data entry for OSCE scores
**Storage**: HIPAA-compliant secure server

**Forms**:
- OSCE scoring sheets (per station)
- Knowledge tests (automated scoring)
- Satisfaction surveys
- Supervisor ratings
- Clinical outcome reports

### 9. Statistical Analysis of Metrics

#### 9.1 Primary Metric Analysis
**Outcome**: OSCE score (0-100)
**Model**: Mixed-effects linear regression
```
OSCE_Score ~ Group + Time + Group×Time + (1|Participant) + Covariates
```

**Covariates**:
- Baseline OSCE score
- Professional role
- Prior ECMO experience
- Institution

#### 9.2 Secondary Metric Analyses
1. **Knowledge retention**: Repeated measures ANOVA
2. **VR performance metrics**: Independent t-tests (VR group only, pre-post)
3. **User satisfaction**: Mann-Whitney U tests (between groups)
4. **Clinical transfer**: Logistic regression (binary outcomes)

#### 9.3 Correlation Analyses
**Research Questions**:
- Do VR performance metrics predict OSCE scores?
- Does simulator sickness affect learning outcomes?
- Is NIRS interpretation accuracy associated with clinical competency?

**Method**: Pearson/Spearman correlations with Bonferroni correction

### 10. Benchmarking and Quality Indicators

#### 10.1 Individual Performance Benchmarks

| Metric | Novice (<10 cases) | Competent (10-50 cases) | Expert (>50 cases) |
|--------|-------------------|------------------------|-------------------|
| **OSCE score** | 50-69 | 70-84 | 85-100 |
| **Cannulation time (VA)** | >15 min | 10-15 min | <10 min |
| **Critical errors** | 2-3 per scenario | 1 per scenario | 0 per scenario |
| **Knowledge test** | 60-74 | 75-89 | 90-100 |
| **NIRS accuracy** | 50-69% | 70-84% | 85-100% |

#### 10.2 Training Program Quality Indicators

**Process Indicators**:
- Participant completion rate: >85%
- Simulator uptime: >95%
- Assessor inter-rater reliability: κ > 0.80

**Outcome Indicators**:
- Mean OSCE improvement: ≥15 points (VR group)
- Knowledge retention at 6 months: ≥80% of immediate post-test
- User satisfaction: ≥4.0/5.0

**Safety Indicators**:
- Severe simulator sickness rate: <5%
- Adverse event rate: <1%

---

## Appendix A: Metric Collection Timeline

| Timepoint | Performance | Knowledge | Competency | Satisfaction | Clinical |
|-----------|------------|-----------|------------|--------------|----------|
| Baseline | - | Test 1 | OSCE 1 | - | - |
| During VR | VR logs | - | - | SSQ | - |
| Post-training | - | Test 2 | OSCE 2 | SUS, Satisfaction | - |
| 3 months | - | Test 3 | OSCE 3 | - | Supervisor rating |
| 6 months | - | Test 4 | OSCE 4 | - | Supervisor rating, Clinical outcomes |

## Appendix B: Metric Prioritization

**Tier 1 (Essential)**:
- OSCE score (primary endpoint)
- Knowledge test score
- Critical error rate
- Scenario completion time
- User satisfaction

**Tier 2 (Important)**:
- NIRS interpretation accuracy
- Individual skill checklist scores
- Simulator sickness (safety)
- Clinical supervisor ratings

**Tier 3 (Exploratory)**:
- Eye-tracking metrics
- Motion capture metrics
- Teamwork scores
- Learning curve parameters
