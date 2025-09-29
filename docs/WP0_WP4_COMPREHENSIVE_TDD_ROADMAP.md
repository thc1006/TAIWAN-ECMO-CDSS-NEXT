# Taiwan ECMO CDSS - WP0-WP4 綜合TDD實施路線圖
# Comprehensive TDD Implementation Roadmap for Work Packages 0-4

**文件版本**: v1.0
**建立日期**: 2025-09-30
**分析方法**: 6個專業AI代理並行深度分析 (Mesh拓撲群智系統)
**TDD原則**: 測試先行，100%覆蓋率，零任務跳過

---

## 📊 執行摘要 Executive Summary

### 總體統計 Overall Statistics

| 指標 Metric | 數值 Value |
|------------|-----------|
| **總測試案例數** Total Test Cases | **378+** |
| **測試套件數** Test Suites | **40+** |
| **目標覆蓋率** Target Coverage | **≥90% (Critical: 100%)** |
| **實施週期** Implementation Duration | **20 週 (5 months)** |
| **關鍵阻塞問題** Critical Blockers | **3** |
| **技術債務** Technical Debt | **14 項 (3-4 sprints)** |

### 各工作包測試統計 Test Statistics by Work Package

| 工作包 WP | 測試數量 Tests | 覆蓋率目標 Coverage | 工期 Duration | 優先級 Priority | 狀態 Status |
|---------|---------------|-------------------|--------------|----------------|------------|
| **WP0** - 資料字典 Data Dictionary | 78 | 100% | 6 週 | 🔴 Critical | ✅ Plan Ready |
| **WP1** - NIRS模型 Models | 90 | 90% | 4 週 | 🔴 Critical | ✅ Plan Ready |
| **WP2** - 成本效益 Cost-Effectiveness | 80 | 100% | 4 週 | 🟡 High | ✅ Plan Ready |
| **WP3** - VR訓練 Training | 50 | 100% | 4 週 | 🟡 High | ✅ Plan Ready |
| **WP4** - SMART on FHIR | 60 | 100% | 4 週 | 🟢 Medium | ✅ Plan Ready |
| **SQL** - ECMO識別 Identification | 20+ | 90% | 1 週 | 🔴 Critical | ✅ Plan Ready |
| **總計 TOTAL** | **378+** | **≥90%** | **20 週** | - | ✅ All Ready |

---

## 🎯 關鍵發現 Key Findings

### 🚨 Critical Blockers (必須立即處理)

#### 1. **WP0: NIRS資料完全未驗證** (WP0/WP1阻塞)
- **影響**: 核心創新功能缺乏品質控制
- **狀態**: ❌ 無ELSO代碼、無驗證規則、無映射
- **解決**: 78個測試案例，6週實施
- **優先級**: 🔴 P0 - 阻塞WP1模型訓練

#### 2. **SQL: ItemID未驗證** (資料獲取阻塞)
- **影響**: 查詢可能回傳0筆chartevents資料
- **狀態**: ❌ ItemID 227287/227288/227289 需驗證
- **解決**: 執行TEST-0 (`mimic_ecmo_itemids.sql`)
- **優先級**: 🔴 P0 - 必須第1週完成

#### 3. **WP1: 類別不平衡未處理** (模型準確度風險)
- **影響**: 模型偏向多數類別 (死亡率40-60%)
- **狀態**: ❌ 無SMOTE或class_weight實作
- **解決**: 90個測試案例，包含不平衡處理測試
- **優先級**: 🔴 P0 - 影響AUC目標 (≥0.75)

---

## 📅 20週實施時程表 20-Week Implementation Timeline

### 第1階段: 基礎建設 Foundation (Week 1-2)

**Week 1: 緊急修復 Critical Fixes**
- **Day 1-2**: SQL ItemID驗證 (TEST-0)
  - ✅ 執行 `sql/mimic_ecmo_itemids.sql`
  - ✅ 更新 `identify_ecmo.sql` lines 91-96
  - ✅ 驗證20+個SQL測試案例
- **Day 3-5**: WP0 Phase 1 開始
  - ✅ 為40個欄位增加ELSO代碼 (8個測試)
  - ✅ 建立欄位驗證規則 (10個測試)

**Week 2: WP0 持續 + 測試基礎設施**
- **WP0 Phase 2**: LOCAL_TO_ELSO映射 (13個測試)
- **測試設定**: pytest, coverage, CI/CD pipeline
- **交付物**: SQL查詢可執行，WP0 36%完成

---

### 第2階段: 資料品質 Data Quality (Week 3-6)

**Week 3-4: WP0 Phase 3 - 代碼整合**
- 整合36個診斷代碼 (ICD-10-CM) - 10個測試
- 整合23個程序代碼 (ICD-10-PCS/CPT/SNOMED/NHI) - 10個測試
- 建立併發症目錄 (ecmo_complications.yaml) - 7個測試
- **交付物**: 59+代碼已連結，WP0 67%完成

**Week 5: WP0 Phase 4 - 進階驗證**
- 跨欄位驗證 (8個測試)
- 資料型別/格式檢查 (4個測試)
- 單位一致性 (3個測試)
- **交付物**: 進階驗證完成，品質報告

**Week 6: WP0 Phase 5 - 風險評分公式**
- SAVE-II 完整實作 (6個測試)
- RESP 完整實作 (6個測試)
- PRESERvE 實作 (5個測試)
- 風險評分整合測試 (3個測試)
- **交付物**: ✅ WP0 100%完成，資料品質 9.0/10

---

### 第3階段: 機器學習模型 ML Models (Week 7-10)

**Week 7: WP1 Phase 1 - 基礎 + 合成資料**
- 測試基礎設施 (pytest-cov, pytest-benchmark)
- 合成資料生成器 (VA-ECMO, VV-ECMO)
- 測試目錄結構建立
- **交付物**: 測試框架就緒

**Week 8: WP1 Phase 2 - 核心單元測試**
- 特徵工程測試 (12個測試)
  - NIRS趨勢計算 (負斜率驗證)
  - 變異性範圍 [0,1]
  - 充足性評分權重 (0.5/0.3/0.2)
- 風險評分測試 (8個測試)
- 模型訓練測試 (15個測試)
  - 基礎訓練 (AUC≥0.70, Brier≤0.20)
  - **類別不平衡處理** (參數化測試)
- 校準測試 (10個測試)
- SHAP可解釋性測試 (10個測試)
- **交付物**: 55個單元測試，覆蓋率≥85%

**Week 9: WP1 Phase 3 - 穩健性測試**
- VA vs VV分離測試 (5個測試)
- E2E管線測試 (3個測試)
- 類別不平衡整合測試 (6個測試)
- 邊緣案例測試 (6個測試)
- **APACHE分層測試** (3個測試)
- **實作**: SMOTE + APACHE評分
- **交付物**: 29個整合測試

**Week 10: WP1 Phase 4 - 驗證**
- 性能基準測試 (6個測試)
- 真實世界驗證 (台灣ECMO registry)
- CI/CD整合 (GitHub Actions)
- **交付物**: ✅ WP1 100%完成，AUC≥0.75驗證

---

### 第4階段: 經濟分析與VR訓練 Economics & VR (Week 11-16)

**Week 11-12: WP2 Phase 1-2 - 成本與QALY**
- 參數驗證測試 (5個測試)
- **成本計算測試** (15個測試)
  - 每日成本: $8,000 (台灣: $5,200)
  - 併發症成本: 出血$25K, 中風$45K, AKI$20K, 感染$15K
- **QALY計算測試** (12個測試)
  - 公式: QALYs = Utility × (預期壽命 - 2年)
  - 折現: 3%年利率
- **ICER計算測試** (10個測試)
  - 公式: (Cost_int - Cost_comp) / (QALY_int - QALY_comp)
  - 分類: <$20K=極具成本效益, $20-50K=成本效益, >$100K=非成本效益
- **交付物**: 42個測試，已驗證計算

**Week 13-14: WP2 Phase 3 - 進階經濟分析**
- 預算影響分析測試 (8個測試)
- 敏感度分析測試 (6個測試)
- **風險五分位測試** (8個測試)
  - Q1-Q5分層，每層CER計算
- **CEAC曲線測試** (5個測試)
  - 成本效益可接受曲線
  - 淨貨幣效益 (NMB)
- Dashboard元件測試 (10個測試)
- **交付物**: ✅ WP2 100%完成，80個測試通過

**Week 15-16: WP3 - VR訓練協定**
- **Week 15**: 核心評分測試 (28個測試)
  - 加權平均公式: 0.4×技術 + 0.3×溝通 + 0.3×決策
  - 技術評分計算 (7個測試)
  - 溝通評分計算 (5個測試)
  - 決策評分計算 (6個測試)
  - **勝任門檻測試** (5個測試)
    - 總分≥80, 關鍵錯誤=0, 技術≥75
  - 情境進度測試 (5個測試)
- **Week 16**: 進階功能測試 (22個測試)
  - 性能聚合測試 (4個測試)
  - **統計檢定力測試** (5個測試)
    - 樣本數: n=25 (效果量d=0.8)
  - 邊緣案例測試 (4個測試)
  - 整合測試 (2個測試)
- **交付物**: ✅ WP3 100%完成，50個測試，樣本數計算驗證

---

### 第5階段: FHIR整合 FHIR Integration (Week 17-20)

**Week 17: WP4 Phase 1 - OAuth2基礎**
- Discovery階段測試 (5個測試)
- **PKCE實作測試** (7個測試)
  - SHA256 challenge方法
  - code_verifier驗證
- URL建構測試
- Mock伺服器設定
- **交付物**: OAuth2工具函數+測試

**Week 18: WP4 Phase 2 - Token管理**
- **Token交換測試** (8個測試)
  - 授權碼交換
  - code_verifier驗證
- **Refresh Token測試** (6個測試)
  - Token輪替
  - 重用偵測
- **Scope驗證測試** (7個測試)
  - patient/*.read
  - 細粒度權限
- **交付物**: Token管理完整測試

**Week 19: WP4 Phase 3 - FHIR資源存取**
- **FHIR資源存取測試** (10個測試)
  - Patient資源 (人口統計學)
  - Observation資源 (生命徵象: HR, BP, SpO2, lactate)
  - MedicationRequest資源 (抗凝劑, 鎮靜劑, 升壓劑)
- E2E整合測試 (2個場景)
  - 成功路徑: discovery → authorize → token → FHIR
  - 錯誤恢復: 失敗處理流程
- **交付物**: FHIR客戶端實作+測試

**Week 20: WP4 Phase 4 - 安全與部署**
- **安全測試** (10個測試)
  - CSRF保護
  - HTTPS強制執行
  - Token儲存 (server-side, NOT localStorage)
  - 重定向URI白名單
  - 授權碼單次使用
- **錯誤處理測試** (8個測試)
  - 網路失敗
  - 使用者拒絕
  - Token過期
- 生產環境部署
- **交付物**: ✅ WP4 100%完成，60個測試，OAuth2 PKCE安全

---

## 📋 測試覆蓋率目標 Test Coverage Targets

### 整體目標 Overall Targets

```
總覆蓋率 Overall Coverage: ≥90%
  ├─ 行覆蓋率 Line Coverage: ≥90%
  ├─ 分支覆蓋率 Branch Coverage: ≥85%
  ├─ 函數覆蓋率 Function Coverage: ≥95%
  └─ 關鍵路徑 Critical Paths: 100%
```

### 各模組覆蓋率 Module-Specific Coverage

| 模組 Module | 行覆蓋率 Line | 分支覆蓋率 Branch | 函數覆蓋率 Function | 優先級 Priority |
|------------|--------------|------------------|-------------------|----------------|
| **etl/** (資料處理) | 95% | 90% | 100% | 🔴 Critical |
| **nirs/** (ML模型) | 90% | 85% | 95% | 🔴 Critical |
| **econ/** (成本分析) | 100% | 100% | 100% | 🟡 High |
| **vr-training/** (VR) | 100% | 100% | 100% | 🟡 High |
| **smart-fhir/** (新建) | 100% | 100% | 100% | 🟢 Medium |
| **tests/** (測試) | 90% | 85% | 95% | 🟢 Medium |

---

## 🔬 TDD原則實施 TDD Principles Implementation

### 紅綠重構循環 Red-Green-Refactor Cycle

每個實施週期必須遵循:

```python
# 1. 🔴 RED: 寫失敗測試
def test_elso_code_assignment():
    field = data_dict['demographics']['patient_id']
    assert field['elso_code'] == 'PATIENT.ID'  # FAILS initially

# 2. 🟢 GREEN: 最小實作通過測試
data_dict['demographics']['patient_id']['elso_code'] = 'PATIENT.ID'

# 3. ♻️ REFACTOR: 改善程式碼品質
def assign_elso_code(field_name, elso_code):
    """Assign ELSO code to field with validation."""
    validate_elso_code(elso_code)  # Added validation
    data_dict[...][field_name]['elso_code'] = elso_code

# 4. 🔁 REPEAT: 下一個測試案例
```

### 測試先行檢查清單 Test-First Checklist

每個功能開發前:
- [ ] 測試案例已編寫 (Test case written)
- [ ] 測試執行且失敗 (Test runs and fails)
- [ ] 實作最小程式碼 (Minimal code implemented)
- [ ] 測試通過 (Test passes)
- [ ] 程式碼重構 (Code refactored)
- [ ] 所有測試仍通過 (All tests still pass)
- [ ] 程式碼審查完成 (Code review completed)
- [ ] CI/CD管線通過 (CI/CD pipeline passes)

### 零任務跳過政策 Zero Task Skip Policy

**絕對禁止**:
- ❌ 實作沒有測試的功能
- ❌ 跳過失敗的測試 (使用 `@pytest.mark.skip`)
- ❌ 降低覆蓋率門檻
- ❌ 合併未通過測試的PR
- ❌ 部署未驗證的程式碼

**必須執行**:
- ✅ 每個PR必須增加測試
- ✅ 覆蓋率不得下降
- ✅ 所有測試必須通過
- ✅ 回歸測試每日執行
- ✅ 性能測試每週執行

---

## 🚀 CI/CD管線設定 CI/CD Pipeline Configuration

### GitHub Actions Workflow

```yaml
name: TDD Pipeline
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-benchmark

    - name: Run WP0 tests (Data Dictionary)
      run: pytest tests/etl/ -v --cov=etl --cov-report=xml

    - name: Run WP1 tests (NIRS Models)
      run: pytest tests/nirs/ -v --cov=nirs --cov-report=xml

    - name: Run WP2 tests (Cost-Effectiveness)
      run: pytest tests/econ/ -v --cov=econ --cov-report=xml

    - name: Run WP3 tests (VR Training)
      run: pytest tests/vr-training/ -v --cov=vr_training --cov-report=xml

    - name: Run WP4 tests (SMART on FHIR)
      run: pytest tests/smart-fhir/ -v --cov=smart_fhir --cov-report=xml

    - name: Check coverage threshold
      run: |
        coverage report --fail-under=90

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
```

### 品質門檻 Quality Gates

所有PR必須通過:
1. ✅ 所有測試通過 (378+ tests pass)
2. ✅ 覆蓋率 ≥90%
3. ✅ 無安全漏洞 (Bandit scan)
4. ✅ 程式碼風格 (Black, isort, flake8)
5. ✅ 型別檢查 (mypy, 85%+ coverage)
6. ✅ 文件更新 (docstrings, README)
7. ✅ 變更日誌更新 (CHANGELOG.md)

---

## 📊 進度追蹤儀表板 Progress Tracking Dashboard

### Streamlit監控應用程式

```python
import streamlit as st
import pandas as pd

# 測試覆蓋率儀表板
st.title("Taiwan ECMO CDSS - TDD Progress Dashboard")

# 總體進度
total_tests = 378
tests_passed = st.session_state.get('tests_passed', 0)
st.metric("Test Pass Rate", f"{tests_passed}/{total_tests}", f"{tests_passed/total_tests*100:.1f}%")

# 各WP進度
wp_progress = pd.DataFrame({
    'WP': ['WP0', 'WP1', 'WP2', 'WP3', 'WP4', 'SQL'],
    'Tests Total': [78, 90, 80, 50, 60, 20],
    'Tests Passed': [0, 0, 0, 0, 0, 0],  # Updated by test runs
    'Coverage': [0, 0, 0, 0, 0, 0]
})

st.dataframe(wp_progress)
st.bar_chart(wp_progress.set_index('WP')['Coverage'])
```

### 每週檢查點 Weekly Checkpoints

每週五執行:
1. 執行完整測試套件 (pytest tests/ -v)
2. 生成覆蓋率報告 (coverage html)
3. 更新進度儀表板
4. 識別阻塞問題
5. 調整下週計畫

---

## 🎯 驗收標準 Acceptance Criteria

### Phase 1 完成標準 (Week 1-2)
- [ ] SQL ItemID已驗證 (TEST-0通過)
- [ ] SQL查詢<30秒完成
- [ ] WP0 Phase 1-2完成 (36%)
- [ ] 測試基礎設施就緒 (pytest, coverage, CI/CD)

### Phase 2 完成標準 (Week 3-6)
- [ ] WP0 100%完成 (78/78測試通過)
- [ ] 資料品質分數 ≥9.0/10
- [ ] 40/40欄位有ELSO代碼
- [ ] 59+臨床代碼已整合
- [ ] 風險評分公式100%完成

### Phase 3 完成標準 (Week 7-10)
- [ ] WP1 100%完成 (90/90測試通過)
- [ ] AUC-ROC ≥0.75 (VA-ECMO, VV-ECMO)
- [ ] Brier score <0.15
- [ ] SMOTE不平衡處理已實作
- [ ] APACHE分層性能驗證
- [ ] SHAP可解釋性功能完整

### Phase 4 完成標準 (Week 11-16)
- [ ] WP2 100%完成 (80/80測試通過)
- [ ] WP3 100%完成 (50/50測試通過)
- [ ] 所有經濟公式已驗證
- [ ] VR訓練評分演算法已驗證
- [ ] 統計檢定力計算正確 (n=25, d=0.8)

### Phase 5 完成標準 (Week 17-20)
- [ ] WP4 100%完成 (60/60測試通過)
- [ ] OAuth2 PKCE安全實作
- [ ] FHIR R4資源存取功能
- [ ] 所有安全測試通過
- [ ] 生產環境部署完成

### 最終驗收標準 Final Acceptance
- [ ] **378+測試全部通過** (100% pass rate)
- [ ] **覆蓋率 ≥90%** (Critical paths: 100%)
- [ ] **零已知阻塞問題** (All critical issues resolved)
- [ ] **技術債務 <5項** (From 14 items)
- [ ] **臨床驗證通過** (Clinical expert review)
- [ ] **監管審查通過** (IRB approval for prospective studies)
- [ ] **文件100%完整** (User guide, API docs, maintenance guide)

---

## 📚 文件交付清單 Documentation Deliverables

### 已建立文件 Documents Created

1. **WP0_TDD_TEST_PLAN.md** (933行)
   - 78個測試案例規格
   - 5個實施階段
   - 複雜度分析與風險評估

2. **wp1_tdd_test_plan.md** (14,000+字)
   - 90個測試案例
   - 架構分析
   - 接受標準與指標閾值

3. **wp1_tdd_executive_summary.md**
   - WP1執行摘要
   - 關鍵差距識別
   - 4週實施路線圖

4. **wp2_tdd_test_plan.md** (13,450行)
   - 80個測試案例
   - 已驗證計算範例
   - pytest與coverage配置

5. **WP3_TDD_Test_Plan.md**
   - 50個測試案例
   - 評分演算法詳細說明
   - 統計檢定力計算

6. **wp4/tdd_test_plan.md** (60+測試)
7. **wp4/architecture.md** (系統設計)
8. **wp4/SUMMARY.md** (執行摘要)
9. **wp4/README.md** (快速導覽)

10. **tests/sql/test_ecmo_identification.sql** (933行)
11. **tests/sql/test_fixtures.sql** (330行)
12. **tests/sql/README_TDD_PLAN.md** (600+行)

13. **WP0_WP4_COMPREHENSIVE_TDD_ROADMAP.md** (本文件)

### 待建立文件 Documents To Be Created

- [ ] **系統整合測試計畫** (System Integration Test Plan)
- [ ] **使用者驗收測試計畫** (UAT Plan)
- [ ] **性能測試計畫** (Performance Test Plan)
- [ ] **安全測試計畫** (Security Test Plan)
- [ ] **監管提交文件** (Regulatory Submission Docs)

---

## 🔗 跨WP依賴關係 Cross-WP Dependencies

### 依賴圖 Dependency Graph

```
SQL (Week 1) ──────┐
                   ├──> WP0 (Week 1-6) ──────> WP1 (Week 7-10)
                   │                              │
                   │                              ├──> WP2 (Week 11-14)
                   │                              │
                   └──────────────────────────────┤
                                                  ├──> WP3 (Week 15-16)
                                                  │
                                                  └──> WP4 (Week 17-20)
```

### 關鍵路徑 Critical Path

```
[SQL ItemID] → [WP0 ELSO codes] → [WP1 Features] → [WP1 Models] → [WP2/WP3/WP4 Parallel]
   Week 1         Week 1-6            Week 7-8       Week 9-10       Week 11-20
   1週             6週                 2週            2週              10週
```

**總關鍵路徑**: Week 1 → Week 10 (10週)
**後續並行工作**: Week 11-20 (10週，WP2/WP3/WP4可並行)

---

## 🎓 團隊能力需求 Team Competency Requirements

### 角色與技能 Roles and Skills

| 角色 Role | 數量 Count | 核心技能 Core Skills | 優先WP Priority |
|----------|-----------|-------------------|----------------|
| **資料工程師** Data Engineer | 2 | SQL, ETL, ELSO standards, PostgreSQL | WP0, SQL |
| **機器學習工程師** ML Engineer | 2 | Python, scikit-learn, SHAP, calibration | WP1 |
| **健康經濟學家** Health Economist | 1 | QALY, ICER, CEAC, R/Python | WP2 |
| **VR開發人員** VR Developer | 1 | Unity/Unreal, 性能評估算法 | WP3 |
| **後端工程師** Backend Engineer | 1 | Node.js, OAuth2, FHIR, Express | WP4 |
| **測試工程師** Test Engineer | 2 | pytest, Jest, TDD, CI/CD | All WPs |
| **DevOps工程師** DevOps Engineer | 1 | GitHub Actions, Docker, monitoring | Infrastructure |
| **臨床顧問** Clinical Advisor | 1 | ECMO expertise, clinical validation | All WPs |
| **專案經理** Project Manager | 1 | Agile, risk management, reporting | Coordination |

**總人力**: 12人 (Full-time equivalent)

---

## 💰 成本估算 Cost Estimation

### 人力成本 Labor Costs (20 weeks)

| 角色 Role | 人數 Count | 週薪 Weekly Rate (NTD) | 總成本 Total (NTD) |
|----------|-----------|----------------------|------------------|
| 資料工程師 | 2 | 60,000 | 2,400,000 |
| ML工程師 | 2 | 70,000 | 2,800,000 |
| 健康經濟學家 | 1 | 65,000 | 1,300,000 |
| VR開發人員 | 1 | 60,000 | 1,200,000 |
| 後端工程師 | 1 | 65,000 | 1,300,000 |
| 測試工程師 | 2 | 55,000 | 2,200,000 |
| DevOps工程師 | 1 | 60,000 | 1,200,000 |
| 臨床顧問 | 1 | 50,000 | 1,000,000 |
| 專案經理 | 1 | 55,000 | 1,100,000 |
| **小計** | **12** | - | **NTD 14,500,000** |

### 基礎設施成本 Infrastructure Costs

| 項目 Item | 每月成本 Monthly (NTD) | 5個月總成本 Total (NTD) |
|----------|----------------------|----------------------|
| CI/CD (GitHub Actions) | 5,000 | 25,000 |
| 雲端運算 (AWS/Azure) | 20,000 | 100,000 |
| 資料庫 (PostgreSQL RDS) | 15,000 | 75,000 |
| 監控 (Datadog/New Relic) | 10,000 | 50,000 |
| MIMIC-IV存取 | 0 (免費研究用) | 0 |
| **小計** | **50,000** | **NTD 250,000** |

### 總預算 Total Budget

```
人力成本:     NTD 14,500,000
基礎設施成本:  NTD    250,000
緩衝 (15%):   NTD  2,212,500
───────────────────────────
總計:         NTD 16,962,500 (~NTD 17M)
```

**備註**: 與原先估計 NTD 8-12M 相比偏高，主要因為:
1. 完整20週實施 (原估12個月的前5個月)
2. 12人全職團隊 (高品質TDD需要充足人力)
3. 零任務跳過政策 (100%覆蓋率目標)

---

## 🎯 風險管理 Risk Management

### 高風險項目 High Risk Items

| 風險 Risk | 影響 Impact | 機率 Probability | 緩解策略 Mitigation |
|----------|-----------|----------------|------------------|
| **ItemID驗證失敗** | 🔴 Critical | 🟡 Medium | Week 1立即執行TEST-0，預備替代方案 |
| **WP1 AUC<0.75** | 🔴 High | 🟡 Medium | SMOTE+APACHE分層，擴充特徵集，調參 |
| **測試開發延誤** | 🟡 High | 🟡 Medium | 並行開發測試+實作，每日站會追蹤 |
| **人力短缺** | 🟡 High | 🟢 Low | 提前招募，交叉訓練，外包測試工程 |
| **技術債務累積** | 🟡 Medium | 🟡 Medium | 每Sprint重構時間，程式碼審查強制執行 |

### 應變計畫 Contingency Plans

1. **ItemID失敗**: 使用替代識別方法 (procedures + medications only)
2. **WP1 AUC不達標**: 延長1-2週調參，或接受0.72-0.75範圍
3. **測試延誤**: 降低非關鍵路徑覆蓋率目標至85%
4. **預算超支**: 削減WP3/WP4範圍，優先完成WP0/WP1

---

## 📈 成功指標 Success Metrics

### 技術指標 Technical Metrics

| 指標 Metric | 基線 Baseline | 目標 Target | 測量頻率 Frequency |
|------------|-------------|-----------|-----------------|
| 測試通過率 | 0% | 100% | 每次提交 |
| 程式碼覆蓋率 | 5.9% | ≥90% | 每日 |
| AUC-ROC (VA) | Unknown | ≥0.75 | Week 10 |
| AUC-ROC (VV) | Unknown | ≥0.75 | Week 10 |
| Brier score | Unknown | <0.15 | Week 10 |
| SQL查詢時間 | Unknown | <30s | Week 1 |
| ELSO對齊度 | 45% | 100% | Week 6 |

### 流程指標 Process Metrics

| 指標 Metric | 目標 Target | 測量方式 Measurement |
|------------|-----------|------------------|
| Sprint速度 | 穩定±10% | Jira burndown |
| 缺陷密度 | <1 bug/KLOC | Bug tracking |
| 程式碼審查時間 | <24小時 | GitHub PR metrics |
| CI/CD成功率 | >95% | GitHub Actions |
| 文件覆蓋率 | 100% | Docstring檢查 |

### 臨床指標 Clinical Metrics (長期)

| 指標 Metric | 基線 Baseline | 目標 Target | 時間點 Timeline |
|------------|-------------|-----------|--------------|
| 模型採用率 | 0% | >70% | 6個月 |
| 臨床醫師滿意度 | N/A | >85% | 6個月 |
| 預測準確度 | 68% (APACHE) | ≥75% | 驗證研究 |

---

## 📞 利益相關者溝通 Stakeholder Communication

### 每週報告 Weekly Reports (每週五)

**報告對象**: 專案贊助者、臨床顧問、開發團隊
**內容**:
1. 本週完成的測試數量 (vs 計畫)
2. 覆蓋率變化趨勢
3. 阻塞問題與解決方案
4. 下週優先事項
5. 預算使用狀況

### 每月展示 Monthly Demos (每月最後一週)

**展示內容**:
- 功能展示 (working software)
- 測試儀表板 (coverage, pass rate)
- 臨床場景演練
- 下個月目標

### 關鍵里程碑溝通 Milestone Communications

- **Week 2**: SQL驗證完成 + WP0啟動
- **Week 6**: WP0完成 (100% ELSO對齊)
- **Week 10**: WP1完成 (AUC≥0.75驗證)
- **Week 14**: WP2完成 (經濟分析驗證)
- **Week 16**: WP3完成 (VR訓練驗證)
- **Week 20**: WP4完成 (FHIR整合上線)

---

## 🎉 總結 Conclusion

### 準備就緒狀態 Readiness Status

✅ **完全就緒**: 所有6個工作包的TDD測試計畫已完成
✅ **完全就緒**: 378+測試案例已定義，覆蓋率目標已設定
✅ **完全就緒**: 20週實施時程表已制定，依賴關係已分析
✅ **完全就緒**: 預算估算已完成 (NTD 17M)
✅ **完全就緒**: 風險管理計畫已建立
✅ **準備就緒**: 群智記憶系統已儲存所有分析結果

### 下一步行動 Next Actions

**立即執行 (Week 1, Day 1)**:
1. 召集專案啟動會議
2. 確認團隊資源 (12人)
3. 設定開發環境 (GitHub, CI/CD)
4. **執行TEST-0** (SQL ItemID驗證) ← 🚨 最高優先級
5. 開始WP0 Phase 1測試開發

**本週完成 (Week 1)**:
1. SQL ItemID驗證並更新查詢
2. WP0 Phase 1 (18個測試)
3. 測試基礎設施就緒
4. 第一次每週報告

---

**文件版本**: v1.0
**最後更新**: 2025-09-30
**狀態**: ✅ 完整且可執行
**審核狀態**: 待臨床顧問與專案贊助者審核
**記憶系統**: 所有分析結果已儲存於 coordination namespace

---

## 附錄: 群智分析記憶索引 Appendix: Swarm Memory Index

所有分析結果已儲存於Claude Flow記憶系統:

```bash
# 查詢所有WP分析結果
npx claude-flow@alpha memory query "wp" --namespace coordination

# 檢索特定WP
npx claude-flow@alpha memory retrieve "wp0/summary" --namespace coordination
npx claude-flow@alpha memory retrieve "wp1/summary" --namespace coordination
npx claude-flow@alpha memory retrieve "wp2/summary" --namespace coordination
npx claude-flow@alpha memory retrieve "wp3/summary" --namespace coordination
npx claude-flow@alpha memory retrieve "wp4/summary" --namespace coordination
npx claude-flow@alpha memory retrieve "sql/summary" --namespace coordination

# 匯出完整記憶
npx claude-flow@alpha memory export wp_backup.json --namespace coordination
```

**記憶儲存狀態**:
- ✅ wp0/summary (211 bytes)
- ✅ wp1/summary (259 bytes)
- ✅ wp2/summary (222 bytes)
- ✅ wp3/summary (232 bytes)
- ✅ wp4/summary (230 bytes)
- ✅ sql/summary (272 bytes)

---

**END OF ROADMAP**