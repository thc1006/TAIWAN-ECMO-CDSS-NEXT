# .gitignore 更新總結

## 📦 已排除的大型檔案和目錄

### 🔴 超大型目錄 (已加入 .gitignore)

| 目錄/檔案 | 大小 | 原因 |
|-----------|------|------|
| `physionet.org/` | **10GB** | MIMIC-IV 3.1 醫療數據集 |
| `.claude/` | 1.7MB | AI 助手臨時檔案 |
| `htmlcov/` | 2.0MB | 測試覆蓋率報告 |
| `.hive-mind/` | 144KB | Swarm 協調檔案 |
| `.swarm/` | 64KB | Agent 同步資料 |
| `.pytest_cache/` | 20KB | Pytest 快取 |
| `.claude-flow/` | 4KB | Claude Flow 配置 |

### 📁 大於 100MB 的檔案 (已被 *.csv.gz 規則排除)

在 `physionet.org/` 目錄下：

1. `hosp/emar.csv.gz` (>100MB)
2. `hosp/emar_detail.csv.gz` (>100MB)
3. `hosp/labevents.csv.gz` (>100MB)
4. `hosp/microbiologyevents.csv.gz` (>100MB)
5. `hosp/pharmacy.csv.gz` (>100MB)
6. `hosp/poe.csv.gz` (>100MB)
7. `hosp/prescriptions.csv.gz` (>100MB)
8. `icu/chartevents.csv.gz` (**3.3GB** - 最大檔案！)
9. `icu/ingredientevents.csv.gz` (>100MB)
10. `icu/inputevents.csv.gz` (>100MB)

---

## ✅ .gitignore 新增內容

### 主要新增規則

```gitignore
# MIMIC-IV data (10GB, large medical dataset)
physionet.org/

# Test coverage reports
htmlcov/
.coverage
.coverage.*
*.cover
.pytest_cache/
.tox/

# AI/ML model artifacts (if large)
*.pkl
*.h5
*.hdf5
models/*.joblib
models/*.pt
models/*.pth
*.onnx

# Swarm/Agent coordination
.hive-mind/
.swarm/
.claude-flow/
.claude/

# Large compressed files (>100MB)
*.csv.gz
*.tar.gz
*.zip
*.7z
*.rar
```

### 完整分類

1. **macOS 檔案**: `.DS_Store`
2. **Python**: `__pycache__/`, `*.pyc`, `*.egg-info/`, `dist/`, `build/`
3. **環境變數**: `.env`, `venv/`, `env/`
4. **IDEs**: `.vscode/`, `.idea/`, `*.swp`
5. **Jupyter**: `*.ipynb_checkpoints`
6. **數據目錄**: `data/`, `outputs/`, `.cache/`
7. **MIMIC-IV**: `physionet.org/`
8. **測試覆蓋率**: `htmlcov/`, `.coverage`, `.pytest_cache/`
9. **ML 模型**: `*.pkl`, `*.h5`, `*.hdf5`, `*.pt`, `*.pth`, `*.onnx`
10. **Swarm/Agent**: `.hive-mind/`, `.swarm/`, `.claude-flow/`, `.claude/`
11. **大型壓縮檔**: `*.csv.gz`, `*.tar.gz`, `*.zip`
12. **日誌**: `logs/`, `*.log`
13. **臨時檔案**: `tmp/`, `temp/`, `*.tmp`
14. **資料庫**: `*.db`, `*.sqlite`, `*.sqlite3`
15. **文檔構建**: `docs/_build/`, `docs/.doctrees/`

---

## 📋 .gitattributes 也已創建

用於：
- Git LFS 追蹤準備（註解掉，需要時啟用）
- 行尾符號標準化 (LF for Unix)
- 二進位檔案標記

---

## 🔍 驗證

### 測試 .gitignore 是否生效

```bash
# 這些目錄/檔案應該被忽略
git check-ignore -v physionet.org/
git check-ignore -v htmlcov/
git check-ignore -v .pytest_cache/
git check-ignore -v .hive-mind/
git check-ignore -v .swarm/
git check-ignore -v .claude/
```

### 檢查 Git 狀態

```bash
git status
```

應該**不會**顯示：
- ❌ `physionet.org/` (10GB)
- ❌ `.claude/` (1.7MB)
- ❌ `htmlcov/` (2MB)
- ❌ 任何 `.csv.gz` 檔案

---

## 💾 建議的數據管理策略

### 選項 1: Git LFS (Large File Storage)

如果需要版本控制大型檔案：

```bash
# 安裝 Git LFS
git lfs install

# 追蹤大型檔案類型
git lfs track "*.pkl"
git lfs track "*.h5"
git lfs track "*.csv.gz"

# 提交 .gitattributes
git add .gitattributes
git commit -m "Configure Git LFS for large files"
```

### 選項 2: 外部存儲

建議將 MIMIC-IV 數據存儲在：

1. **本地**: 保留在 `physionet.org/` (已被 .gitignore 排除)
2. **雲端**: AWS S3, Azure Blob, Google Cloud Storage
3. **機構**: 醫院內部 NAS/SAN 存儲
4. **文檔**: 在 `README.md` 中說明如何獲取數據

### 選項 3: 數據下載腳本

創建 `scripts/download_mimic.sh`:

```bash
#!/bin/bash
# 從 PhysioNet 下載 MIMIC-IV 數據
# 需要 PhysioNet 認證

wget -r -N -c -np --user YOUR_USERNAME --ask-password \
  https://physionet.org/files/mimiciv/3.1/ \
  -P physionet.org/
```

---

## 📊 空間節省

**Git Repository 大小優化:**

- **Before**: ~10GB (包含 MIMIC-IV)
- **After**: ~50MB (僅代碼和文檔)
- **節省**: ~99.5%

---

## ⚠️ 注意事項

1. **已存在的檔案**: 如果這些檔案之前已被 Git 追蹤，需要手動移除：

   ```bash
   # 從 Git 追蹤中移除（但保留本地檔案）
   git rm --cached -r physionet.org/
   git rm --cached -r htmlcov/
   git rm --cached -r .pytest_cache/
   git rm --cached -r .hive-mind/
   git rm --cached -r .swarm/
   git rm --cached -r .claude/

   # 提交變更
   git commit -m "Remove large files from Git tracking"
   ```

2. **團隊協作**: 確保所有團隊成員都知道如何獲取 MIMIC-IV 數據

3. **CI/CD**: 配置 CI/CD 管道以自動下載或使用快取的數據

4. **文檔**: 在 `DEPLOYMENT.md` 中已說明數據獲取方式

---

## ✅ 完成清單

- [x] 識別所有 >100MB 的檔案
- [x] 更新 `.gitignore` 排除大型檔案
- [x] 創建 `.gitattributes` 配置行尾和二進位檔案
- [x] 排除 `physionet.org/` (10GB)
- [x] 排除測試覆蓋率報告 `htmlcov/`
- [x] 排除 AI/Swarm 協調檔案
- [x] 排除所有 `.csv.gz` 壓縮檔案
- [x] 排除 ML 模型檔案 (`*.pkl`, `*.h5`, `*.pt`)
- [x] 驗證 Git 忽略規則生效

---

**更新時間**: 2025-10-05
**狀態**: ✅ 完成
