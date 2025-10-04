"""
MIMIC-IV ECMO Data Loader for Risk Models
Supports CSV and PostgreSQL sources, stratified splits, preprocessing pipelines.
"""

import os
import gzip
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Tuple, Optional, List, Union
from dataclasses import dataclass
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.impute import SimpleImputer, KNNImputer
import warnings


@dataclass
class DataConfig:
    """Configuration for data loading and preprocessing."""
    # Data source
    data_source: str = 'csv'  # 'csv' or 'postgres'
    mimic_path: Optional[str] = None  # Path to MIMIC-IV files
    postgres_conn: Optional[str] = None  # PostgreSQL connection string

    # SQL query path
    sql_query_path: Optional[str] = None  # Path to extract_ecmo_features.sql

    # CSV file paths (if using pre-extracted features)
    features_csv: Optional[str] = None

    # Train/val/test split
    test_size: float = 0.2
    val_size: float = 0.2  # Fraction of training set
    random_state: int = 42
    stratify_by: List[str] = None  # e.g., ['ecmo_mode', 'survival_to_discharge']

    # Preprocessing
    imputation_strategy: str = 'knn'  # 'median', 'mean', 'knn'
    scaling_method: str = 'robust'  # 'standard', 'robust', 'none'
    handle_outliers: bool = True
    outlier_method: str = 'iqr'  # 'iqr' or 'zscore'

    # Feature selection
    drop_high_missing: bool = True
    missing_threshold: float = 0.5  # Drop features with >50% missing

    def __post_init__(self):
        if self.stratify_by is None:
            self.stratify_by = ['ecmo_mode', 'survival_to_discharge']


class MIMICDataLoader:
    """
    Load and preprocess MIMIC-IV ECMO data for risk modeling.

    Supports:
    - Loading from compressed CSV files
    - Loading from PostgreSQL database
    - Stratified train/validation/test splits
    - Preprocessing pipeline with imputation and scaling
    - Integration with extract_ecmo_features.sql output
    """

    def __init__(self, config: DataConfig):
        self.config = config
        self.raw_data = None
        self.processed_data = {}
        self.preprocessing_stats = {}
        self.feature_columns = None
        self.target_column = 'survival_to_discharge'

        # Preprocessing components
        self.scalers = {}  # Separate scalers for VA and VV
        self.imputers = {}  # Separate imputers for VA and VV

    def load_from_csv(self, csv_path: str) -> pd.DataFrame:
        """
        Load ECMO features from CSV file (supports gzip compression).

        Args:
            csv_path: Path to CSV file (can be .csv or .csv.gz)

        Returns:
            DataFrame with ECMO features
        """
        path = Path(csv_path)

        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        print(f"Loading data from: {csv_path}")

        if path.suffix == '.gz':
            with gzip.open(csv_path, 'rt') as f:
                df = pd.read_csv(f, low_memory=False)
        else:
            df = pd.read_csv(csv_path, low_memory=False)

        print(f"Loaded {len(df)} records with {len(df.columns)} columns")
        return df

    def load_from_postgres(self, query_file: str, conn_string: str) -> pd.DataFrame:
        """
        Load ECMO features from PostgreSQL using SQL query.

        Args:
            query_file: Path to SQL query file (e.g., extract_ecmo_features.sql)
            conn_string: PostgreSQL connection string

        Returns:
            DataFrame with ECMO features
        """
        try:
            import psycopg2
            from sqlalchemy import create_engine
        except ImportError:
            raise ImportError("PostgreSQL support requires psycopg2 and sqlalchemy: "
                            "pip install psycopg2-binary sqlalchemy")

        # Read SQL query
        with open(query_file, 'r') as f:
            query = f.read()

        print(f"Executing SQL query from: {query_file}")

        # Create engine and execute query
        engine = create_engine(conn_string)
        df = pd.read_sql_query(query, engine)

        print(f"Loaded {len(df)} records with {len(df.columns)} columns")
        return df

    def load_mimic_tables(self, table_paths: Dict[str, str]) -> Dict[str, pd.DataFrame]:
        """
        Load multiple MIMIC-IV tables from compressed CSV files.

        Args:
            table_paths: Dictionary mapping table names to file paths

        Returns:
            Dictionary of DataFrames
        """
        tables = {}

        for table_name, path in table_paths.items():
            print(f"Loading {table_name}...")
            tables[table_name] = self.load_from_csv(path)

        return tables

    def parse_ecmo_episodes(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Parse and validate ECMO episode data.

        Args:
            df: Raw ECMO features DataFrame

        Returns:
            Validated DataFrame with proper types
        """
        # Make a copy to avoid modifying original
        df = df.copy()

        # Parse datetime columns
        datetime_cols = ['ecmo_start_time', 'ecmo_end_time']
        for col in datetime_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')

        # Ensure required columns exist
        required_cols = ['subject_id', 'hadm_id', 'ecmo_mode']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        # Standardize ECMO mode
        if 'ecmo_mode' in df.columns:
            df['ecmo_mode'] = df['ecmo_mode'].str.upper()
            valid_modes = ['VA', 'VV', 'VAV', 'VVA']
            invalid_modes = ~df['ecmo_mode'].isin(valid_modes)
            if invalid_modes.any():
                warnings.warn(f"Found {invalid_modes.sum()} records with invalid ECMO mode. "
                            f"Valid modes: {valid_modes}")
                df = df[~invalid_modes]

        # Ensure target exists
        if self.target_column not in df.columns:
            raise ValueError(f"Target column '{self.target_column}' not found in data")

        # Convert target to binary
        df[self.target_column] = df[self.target_column].astype(int)

        print(f"\nData Summary:")
        print(f"  Total episodes: {len(df)}")
        print(f"  ECMO modes:")
        for mode, count in df['ecmo_mode'].value_counts().items():
            print(f"    {mode}: {count}")
        print(f"  Outcome distribution:")
        for outcome, count in df[self.target_column].value_counts().items():
            label = 'Survived' if outcome == 1 else 'Died'
            print(f"    {label}: {count} ({count/len(df)*100:.1f}%)")

        return df

    def identify_feature_columns(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        """
        Identify feature columns by type.

        Returns:
            Dictionary categorizing features
        """
        # Columns to exclude from features
        exclude_cols = [
            'subject_id', 'hadm_id', 'stay_id', 'episode_num',
            'ecmo_start_time', 'ecmo_end_time', 'ecmo_run_id',
            'primary_icd10', 'primary_diagnosis_desc',
            'discharge_location', 'hospital_expire_flag',
            self.target_column, 'death_on_ecmo', 'death_24h_post_ecmo'
        ]

        # Categorical columns (need encoding)
        categorical_cols = [
            'ecmo_mode', 'sex', 'race', 'age_group', 'diagnosis_category'
        ]

        # Numeric feature columns
        numeric_cols = [
            col for col in df.columns
            if col not in exclude_cols + categorical_cols
            and df[col].dtype in ['int64', 'float64']
        ]

        # Binary complication flags
        binary_cols = [
            col for col in numeric_cols
            if df[col].dropna().isin([0, 1]).all()
        ]

        continuous_cols = [col for col in numeric_cols if col not in binary_cols]

        feature_dict = {
            'continuous': continuous_cols,
            'binary': binary_cols,
            'categorical': [col for col in categorical_cols if col in df.columns],
            'exclude': exclude_cols,
            'all_features': numeric_cols + [col for col in categorical_cols if col in df.columns]
        }

        print(f"\nFeature Categories:")
        print(f"  Continuous: {len(feature_dict['continuous'])}")
        print(f"  Binary: {len(feature_dict['binary'])}")
        print(f"  Categorical: {len(feature_dict['categorical'])}")
        print(f"  Total features: {len(feature_dict['all_features'])}")

        return feature_dict

    def handle_missing_data(self, df: pd.DataFrame, feature_cols: List[str]) -> pd.DataFrame:
        """
        Handle missing data in features.

        Args:
            df: DataFrame with features
            feature_cols: List of feature column names

        Returns:
            DataFrame with missing data handled
        """
        df = df.copy()

        # Calculate missing percentages
        missing_pct = df[feature_cols].isnull().mean()

        # Drop features with too many missing values
        if self.config.drop_high_missing:
            high_missing = missing_pct[missing_pct > self.config.missing_threshold].index.tolist()
            if high_missing:
                print(f"\nDropping {len(high_missing)} features with >{self.config.missing_threshold*100}% missing:")
                for col in high_missing[:10]:  # Show first 10
                    print(f"  {col}: {missing_pct[col]*100:.1f}% missing")
                if len(high_missing) > 10:
                    print(f"  ... and {len(high_missing)-10} more")

                feature_cols = [col for col in feature_cols if col not in high_missing]

        # Store preprocessing stats
        self.preprocessing_stats['missing_percentages'] = missing_pct.to_dict()
        self.preprocessing_stats['dropped_features'] = high_missing if self.config.drop_high_missing else []

        return df, feature_cols

    def handle_outliers(self, df: pd.DataFrame, feature_cols: List[str]) -> pd.DataFrame:
        """
        Handle outliers in continuous features.

        Args:
            df: DataFrame with features
            feature_cols: List of feature column names

        Returns:
            DataFrame with outliers handled
        """
        if not self.config.handle_outliers:
            return df

        df = df.copy()

        for col in feature_cols:
            if col not in df.columns:
                continue

            data = df[col].dropna()
            if len(data) == 0:
                continue

            if self.config.outlier_method == 'iqr':
                # IQR method
                Q1 = data.quantile(0.25)
                Q3 = data.quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 3 * IQR
                upper_bound = Q3 + 3 * IQR
            else:
                # Z-score method
                mean = data.mean()
                std = data.std()
                lower_bound = mean - 4 * std
                upper_bound = mean + 4 * std

            # Clip outliers
            df[col] = df[col].clip(lower=lower_bound, upper=upper_bound)

        return df

    def create_stratified_splits(
        self,
        df: pd.DataFrame,
        feature_cols: List[str]
    ) -> Dict[str, Tuple[pd.DataFrame, pd.DataFrame]]:
        """
        Create stratified train/validation/test splits by ECMO mode.

        Args:
            df: Full dataset
            feature_cols: List of feature column names

        Returns:
            Dictionary with splits for each ECMO mode
        """
        splits = {}

        for mode in ['VA', 'VV']:
            df_mode = df[df['ecmo_mode'] == mode].copy()

            if len(df_mode) < 20:
                warnings.warn(f"Insufficient data for {mode} mode: {len(df_mode)} samples. Skipping.")
                continue

            # Get features and target
            X = df_mode[feature_cols].copy()
            y = df_mode[self.target_column].copy()

            # Store metadata
            metadata_cols = ['subject_id', 'hadm_id', 'stay_id', 'ecmo_mode']
            metadata = df_mode[[col for col in metadata_cols if col in df_mode.columns]]

            # Create stratified splits
            try:
                # First split: train+val vs test
                X_trainval, X_test, y_trainval, y_test, meta_trainval, meta_test = train_test_split(
                    X, y, metadata,
                    test_size=self.config.test_size,
                    stratify=y,
                    random_state=self.config.random_state
                )

                # Second split: train vs val
                val_size_adjusted = self.config.val_size / (1 - self.config.test_size)
                X_train, X_val, y_train, y_val, meta_train, meta_val = train_test_split(
                    X_trainval, y_trainval, meta_trainval,
                    test_size=val_size_adjusted,
                    stratify=y_trainval,
                    random_state=self.config.random_state
                )

                splits[mode] = {
                    'train': (X_train, y_train, meta_train),
                    'val': (X_val, y_val, meta_val),
                    'test': (X_test, y_test, meta_test)
                }

                print(f"\n{mode} ECMO - Data Splits:")
                print(f"  Train: {len(X_train)} samples ({y_train.mean()*100:.1f}% survival)")
                print(f"  Val:   {len(X_val)} samples ({y_val.mean()*100:.1f}% survival)")
                print(f"  Test:  {len(X_test)} samples ({y_test.mean()*100:.1f}% survival)")

            except ValueError as e:
                warnings.warn(f"Failed to create stratified split for {mode}: {e}")
                continue

        return splits

    def create_preprocessing_pipeline(self, mode: str) -> Tuple[SimpleImputer, StandardScaler]:
        """
        Create preprocessing pipeline for a specific ECMO mode.

        Args:
            mode: 'VA' or 'VV'

        Returns:
            Tuple of (imputer, scaler)
        """
        # Create imputer
        if self.config.imputation_strategy == 'knn':
            imputer = KNNImputer(n_neighbors=5)
        elif self.config.imputation_strategy == 'median':
            imputer = SimpleImputer(strategy='median')
        elif self.config.imputation_strategy == 'mean':
            imputer = SimpleImputer(strategy='mean')
        else:
            raise ValueError(f"Unknown imputation strategy: {self.config.imputation_strategy}")

        # Create scaler
        if self.config.scaling_method == 'standard':
            scaler = StandardScaler()
        elif self.config.scaling_method == 'robust':
            scaler = RobustScaler()
        elif self.config.scaling_method == 'none':
            scaler = None
        else:
            raise ValueError(f"Unknown scaling method: {self.config.scaling_method}")

        return imputer, scaler

    def fit_preprocessing(
        self,
        X_train: pd.DataFrame,
        mode: str
    ) -> pd.DataFrame:
        """
        Fit preprocessing pipeline on training data.

        Args:
            X_train: Training features
            mode: ECMO mode ('VA' or 'VV')

        Returns:
            Transformed training features
        """
        # Create pipeline
        imputer, scaler = self.create_preprocessing_pipeline(mode)

        # Fit and transform imputer
        X_imputed = pd.DataFrame(
            imputer.fit_transform(X_train),
            columns=X_train.columns,
            index=X_train.index
        )

        # Fit and transform scaler
        if scaler is not None:
            X_scaled = pd.DataFrame(
                scaler.fit_transform(X_imputed),
                columns=X_imputed.columns,
                index=X_imputed.index
            )
        else:
            X_scaled = X_imputed

        # Store fitted components
        self.imputers[mode] = imputer
        self.scalers[mode] = scaler

        return X_scaled

    def transform_preprocessing(
        self,
        X: pd.DataFrame,
        mode: str
    ) -> pd.DataFrame:
        """
        Transform data using fitted preprocessing pipeline.

        Args:
            X: Features to transform
            mode: ECMO mode ('VA' or 'VV')

        Returns:
            Transformed features
        """
        if mode not in self.imputers:
            raise ValueError(f"Preprocessing pipeline not fitted for mode: {mode}")

        # Transform with imputer
        X_imputed = pd.DataFrame(
            self.imputers[mode].transform(X),
            columns=X.columns,
            index=X.index
        )

        # Transform with scaler
        if self.scalers[mode] is not None:
            X_scaled = pd.DataFrame(
                self.scalers[mode].transform(X_imputed),
                columns=X_imputed.columns,
                index=X_imputed.index
            )
        else:
            X_scaled = X_imputed

        return X_scaled

    def load_and_prepare(self) -> Dict[str, Dict]:
        """
        Complete data loading and preparation pipeline.

        Returns:
            Dictionary with preprocessed splits for each ECMO mode
        """
        print("="*60)
        print("ECMO Data Loading and Preparation")
        print("="*60)

        # Step 1: Load raw data
        if self.config.data_source == 'csv':
            if self.config.features_csv:
                self.raw_data = self.load_from_csv(self.config.features_csv)
            else:
                raise ValueError("features_csv path must be specified for CSV data source")
        elif self.config.data_source == 'postgres':
            if not self.config.sql_query_path or not self.config.postgres_conn:
                raise ValueError("sql_query_path and postgres_conn must be specified for postgres data source")
            self.raw_data = self.load_from_postgres(
                self.config.sql_query_path,
                self.config.postgres_conn
            )
        else:
            raise ValueError(f"Unknown data source: {self.config.data_source}")

        # Step 2: Parse and validate ECMO episodes
        self.raw_data = self.parse_ecmo_episodes(self.raw_data)

        # Step 3: Identify feature columns
        feature_dict = self.identify_feature_columns(self.raw_data)

        # Step 4: Handle missing data
        self.raw_data, feature_cols = self.handle_missing_data(
            self.raw_data,
            feature_dict['all_features']
        )
        self.feature_columns = feature_cols

        # Step 5: Handle outliers
        self.raw_data = self.handle_outliers(self.raw_data, feature_dict['continuous'])

        # Step 6: Create stratified splits
        splits = self.create_stratified_splits(self.raw_data, self.feature_columns)

        # Step 7: Preprocess each split
        processed_splits = {}

        for mode, mode_splits in splits.items():
            print(f"\nPreprocessing {mode} ECMO data...")

            # Fit preprocessing on training data
            X_train_processed = self.fit_preprocessing(mode_splits['train'][0], mode)

            # Transform validation and test data
            X_val_processed = self.transform_preprocessing(mode_splits['val'][0], mode)
            X_test_processed = self.transform_preprocessing(mode_splits['test'][0], mode)

            processed_splits[mode] = {
                'train': {
                    'X': X_train_processed,
                    'y': mode_splits['train'][1],
                    'metadata': mode_splits['train'][2]
                },
                'val': {
                    'X': X_val_processed,
                    'y': mode_splits['val'][1],
                    'metadata': mode_splits['val'][2]
                },
                'test': {
                    'X': X_test_processed,
                    'y': mode_splits['test'][1],
                    'metadata': mode_splits['test'][2]
                }
            }

        self.processed_data = processed_splits

        print("\n" + "="*60)
        print("Data preparation complete!")
        print("="*60)

        return processed_splits

    def save_processed_data(self, output_dir: str):
        """
        Save processed data splits to disk.

        Args:
            output_dir: Directory to save processed data
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        for mode, splits in self.processed_data.items():
            mode_dir = output_path / mode.lower()
            mode_dir.mkdir(exist_ok=True)

            for split_name, split_data in splits.items():
                # Save features
                split_data['X'].to_csv(
                    mode_dir / f"{split_name}_features.csv",
                    index=False
                )

                # Save target
                pd.Series(split_data['y'], name=self.target_column).to_csv(
                    mode_dir / f"{split_name}_target.csv",
                    index=False
                )

                # Save metadata
                split_data['metadata'].to_csv(
                    mode_dir / f"{split_name}_metadata.csv",
                    index=False
                )

        print(f"\nProcessed data saved to: {output_dir}")

    def get_feature_names(self) -> List[str]:
        """Get list of feature column names."""
        return self.feature_columns


# Utility functions

def load_preprocessed_data(
    data_dir: str,
    mode: str,
    split: str
) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    """
    Load preprocessed data splits from disk.

    Args:
        data_dir: Directory containing processed data
        mode: ECMO mode ('VA' or 'VV')
        split: Data split ('train', 'val', or 'test')

    Returns:
        Tuple of (features, target, metadata)
    """
    data_path = Path(data_dir) / mode.lower()

    X = pd.read_csv(data_path / f"{split}_features.csv")
    y = pd.read_csv(data_path / f"{split}_target.csv").squeeze()
    metadata = pd.read_csv(data_path / f"{split}_metadata.csv")

    return X, y, metadata


# Example usage
if __name__ == '__main__':
    # Example configuration
    config = DataConfig(
        data_source='csv',
        features_csv='path/to/ecmo_features.csv',
        test_size=0.2,
        val_size=0.2,
        imputation_strategy='knn',
        scaling_method='robust',
        handle_outliers=True
    )

    # Load and prepare data
    loader = MIMICDataLoader(config)
    processed_data = loader.load_and_prepare()

    # Access processed data
    va_train_X = processed_data['VA']['train']['X']
    va_train_y = processed_data['VA']['train']['y']

    print(f"\nVA training features shape: {va_train_X.shape}")
    print(f"Feature names: {loader.get_feature_names()[:10]}...")
