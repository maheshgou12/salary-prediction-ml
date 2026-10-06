"""FairSalary AI - Model Training Pipeline"""
import json
import time
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import optuna
import pandas as pd
from catboost import CatBoostRegressor
from lightgbm import LGBMRegressor
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor, StackingRegressor, VotingRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from xgboost import XGBRegressor

warnings.filterwarnings('ignore')

# Feature configuration
NUMERICAL_FEATURES = [
    'years_experience',
    'skills_count',
    'previous_salary',
    'interview_score',
]

CATEGORICAL_FEATURES = [
    'education_level',
    'job_role',
    'location',
    'company_size',
]

PROTECTED_ATTRIBUTES = ['gender', 'age']
TARGET = 'salary'
ALL_FEATURES = ['years_experience', 'skills_count', 'previous_salary', 'interview_score',
                'education_level', 'job_role', 'location', 'company_size']


def load_data(data_path: str | Path) -> pd.DataFrame:
    """Load the salary dataset."""
    return pd.read_csv(data_path)


def create_preprocessing_pipeline() -> ColumnTransformer:
    """Create the preprocessing pipeline."""
    numerical_pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler()),
    ])

    categorical_pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('encoder', OneHotEncoder(handle_unknown='ignore', sparse_output=False)),
    ])

    preprocessor = ColumnTransformer([
        ('num', numerical_pipeline, NUMERICAL_FEATURES),
        ('cat', categorical_pipeline, CATEGORICAL_FEATURES),
    ], remainder='drop')

    return preprocessor


def get_base_models() -> Dict[str, Any]:
    """Get dictionary of base models to compare."""
    return {
        'Linear Regression': LinearRegression(),
        'Ridge Regression': Ridge(random_state=42),
        'Random Forest': RandomForestRegressor(random_state=42, n_jobs=-1),
        'XGBoost': XGBRegressor(random_state=42, n_jobs=-1, verbosity=0),
        'LightGBM': LGBMRegressor(random_state=42, n_jobs=-1, verbosity=-1),
        'CatBoost': CatBoostRegressor(random_state=42, verbose=False),
    }


def get_param_grids() -> Dict[str, Dict]:
    """Get hyperparameter grids for GridSearchCV."""
    return {
        'Linear Regression': {},
        'Ridge Regression': {'model__alpha': [0.1, 1.0, 10.0, 100.0]},
        'Random Forest': {
            'model__n_estimators': [100, 200],
            'model__max_depth': [10, 20, None],
            'model__min_samples_split': [2, 5],
            'model__min_samples_leaf': [1, 2],
        },
        'XGBoost': {
            'model__n_estimators': [100, 200],
            'model__max_depth': [4, 6, 8],
            'model__learning_rate': [0.05, 0.1, 0.2],
            'model__subsample': [0.8, 1.0],
        },
        'LightGBM': {
            'model__n_estimators': [100, 200],
            'model__max_depth': [4, 6, 8],
            'model__learning_rate': [0.05, 0.1, 0.2],
            'model__num_leaves': [31, 63],
        },
        'CatBoost': {
            'model__iterations': [100, 200],
            'model__depth': [4, 6, 8],
            'model__learning_rate': [0.05, 0.1, 0.2],
        },
    }


def get_optuna_search_spaces() -> Dict[str, callable]:
    """Get Optuna search spaces for each model."""
    def ridge_space(trial: optuna.Trial) -> Dict:
        return {'alpha': trial.suggest_float('alpha', 0.01, 100.0, log=True)}

    def rf_space(trial: optuna.Trial) -> Dict:
        return {
            'n_estimators': trial.suggest_int('n_estimators', 50, 300),
            'max_depth': trial.suggest_categorical('max_depth', [10, 15, 20, None]),
            'min_samples_split': trial.suggest_int('min_samples_split', 2, 10),
            'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 5),
        }

    def xgb_space(trial: optuna.Trial) -> Dict:
        return {
            'n_estimators': trial.suggest_int('n_estimators', 50, 300),
            'max_depth': trial.suggest_int('max_depth', 3, 10),
            'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
            'subsample': trial.suggest_float('subsample', 0.6, 1.0),
        }

    def lgbm_space(trial: optuna.Trial) -> Dict:
        return {
            'n_estimators': trial.suggest_int('n_estimators', 50, 300),
            'max_depth': trial.suggest_int('max_depth', 3, 10),
            'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
            'num_leaves': trial.suggest_int('num_leaves', 20, 100),
        }

    def catboost_space(trial: optuna.Trial) -> Dict:
        return {
            'iterations': trial.suggest_int('iterations', 50, 300),
            'depth': trial.suggest_int('depth', 3, 10),
            'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
        }

    return {
        'Ridge Regression': ridge_space,
        'Random Forest': rf_space,
        'XGBoost': xgb_space,
        'LightGBM': lgbm_space,
        'CatBoost': catboost_space,
    }


def evaluate_model(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Calculate regression metrics."""
    return {
        'MAE': mean_absolute_error(y_true, y_pred),
        'RMSE': np.sqrt(mean_squared_error(y_true, y_pred)),
        'R2': r2_score(y_true, y_pred),
    }


def train_and_evaluate(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    model_name: str,
    model: Any,
    param_grid: Dict,
    preprocessor: ColumnTransformer,
    use_optuna: bool = True,
    n_trials: int = 30,
) -> Dict[str, Any]:
    """Train a model with cross-validation and evaluate on test set."""
    pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('model', model),
    ])

    # Cross-validation
    cv_scores = cross_val_score(
        pipeline, X_train, y_train,
        cv=5, scoring='neg_mean_absolute_error', n_jobs=-1
    )
    cv_mae = -cv_scores.mean()
    cv_std = cv_scores.std()

    # Hyperparameter tuning
    best_pipeline = pipeline
    best_params = {}

    if use_optuna and model_name in get_optuna_search_spaces():
        search_space = get_optuna_search_spaces()[model_name]

        def objective(trial: optuna.Trial) -> float:
            params = search_space(trial)
            trial_pipeline = Pipeline([
                ('preprocessor', preprocessor),
                ('model', model.set_params(**params)),
            ])
            cv_scores = cross_val_score(
                trial_pipeline, X_train, y_train,
                cv=3, scoring='neg_mean_absolute_error', n_jobs=-1
            )
            return -cv_scores.mean()

        study = optuna.create_study(direction='minimize', sampler=optuna.samplers.TPESampler(seed=42))
        study.optimize(objective, n_trials=n_trials, show_progress_bar=False)

        best_params = study.best_params
        best_pipeline = Pipeline([
            ('preprocessor', preprocessor),
            ('model', model.set_params(**best_params)),
        ])
        best_pipeline.fit(X_train, y_train)
    elif param_grid:
        grid_search = GridSearchCV(
            pipeline, param_grid,
            cv=3, scoring='neg_mean_absolute_error',
            n_jobs=-1, verbose=0
        )
        grid_search.fit(X_train, y_train)
        best_pipeline = grid_search.best_estimator_
        best_params = grid_search.best_params_
    else:
        best_pipeline.fit(X_train, y_train)

    # Test evaluation
    y_pred = best_pipeline.predict(X_test)
    metrics = evaluate_model(y_test.values, y_pred)

    return {
        'model_name': model_name,
        'pipeline': best_pipeline,
        'best_params': best_params,
        'cv_mae': cv_mae,
        'cv_std': cv_std,
        'test_metrics': metrics,
    }


def create_stacking_ensemble(
    base_models: List[Tuple[str, Any]],
    preprocessor: ColumnTransformer,
    X_train: pd.DataFrame,
    y_train: pd.Series,
) -> Pipeline:
    """Create a Stacking Ensemble with Ridge meta-learner."""
    estimators = [(name, Pipeline([
        ('preprocessor', preprocessor),
        ('model', model),
    ])) for name, model in base_models]

    stacking = StackingRegressor(
        estimators=estimators,
        final_estimator=Ridge(alpha=1.0),
        cv=5,
        n_jobs=-1,
    )

    stacking.fit(X_train, y_train)
    return stacking


def create_voting_ensemble(
    base_models: List[Tuple[str, Any]],
    preprocessor: ColumnTransformer,
    X_train: pd.DataFrame,
    y_train: pd.Series,
) -> Pipeline:
    """Create a Voting Ensemble."""
    estimators = [(name, Pipeline([
        ('preprocessor', preprocessor),
        ('model', model),
    ])) for name, model in base_models]

    voting = VotingRegressor(estimators=estimators, n_jobs=-1)
    voting.fit(X_train, y_train)
    return voting


def run_training(
    data_path: str | Path = 'ml/data/raw/salary_data.csv',
    model_dir: str | Path = 'ml/models',
    use_mlflow: bool = True,
    optuna_trials: int = 30,
) -> Dict[str, Any]:
    """Run the complete training pipeline."""
    model_dir = Path(model_dir)
    model_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    df = load_data(data_path)

    # Prepare features and target (EXCLUDE protected attributes)
    X = df[ALL_FEATURES].copy()
    y = df[TARGET].copy()

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Preprocessing
    preprocessor = create_preprocessing_pipeline()

    # Setup MLflow
    if use_mlflow:
        import mlflow
        import mlflow.sklearn
        mlflow.set_tracking_uri('file:./mlruns')
        mlflow.set_experiment('fairsalary-salary-prediction')

    # Model comparison
    models = get_base_models()
    param_grids = get_param_grids()

    results = []
    best_model_info = None
    best_mae = float('inf')

    print("Training models...")
    print("-" * 60)

    for name, model in models.items():
        print(f"\nTraining {name}...")
        start_time = time.time()

        result = train_and_evaluate(
            X_train, y_train, X_test, y_test,
            name, model, param_grids[name], preprocessor,
            use_optuna=True,
            n_trials=optuna_trials,
        )

        training_time = time.time() - start_time
        result['training_time'] = training_time

        results.append(result)

        test_mae = result['test_metrics']['MAE']
        print(f"  CV MAE: ${result['cv_mae']:,.0f} ± ${result['cv_std']:,.0f}")
        print(f"  Test MAE: ${test_mae:,.0f}")
        print(f"  Test RMSE: ${result['test_metrics']['RMSE']:,.0f}")
        print(f"  Test R²: {result['test_metrics']['R2']:.4f}")
        print(f"  Training time: {training_time:.1f}s")

        # Log to MLflow
        if use_mlflow:
            try:
                mlflow.set_experiment('fairsalary-salary-prediction')
                with mlflow.start_run(run_name=name):
                    mlflow.log_params(best_params)
                    mlflow.log_metrics({
                        'cv_mae': result['cv_mae'],
                        'cv_std': result['cv_std'],
                        'test_mae': metrics['MAE'],
                        'test_rmse': metrics['RMSE'],
                        'test_r2': metrics['R2'],
                        'training_time_seconds': training_time,
                    })
                    mlflow.sklearn.log_model(
                        result['pipeline'],
                        artifact_path='model',
                        registered_model_name=f'FairSalary_{name.replace(" ", "_")}',
                    )
            except Exception as e:
                print(f"  MLflow logging failed for {name}: {e}")

        if test_mae < best_mae:
            best_mae = test_mae
            best_model_info = result

    # Create ensembles from top 3 models
    print("\n" + "=" * 60)
    print("CREATING ENSEMBLES")
    print("=" * 60)

    sorted_results = sorted(results, key=lambda x: x['test_metrics']['MAE'])
    top_3_models = [(r['model_name'], r['pipeline'].named_steps['model']) for r in sorted_results[:3]]
    print(f"Top 3 models for ensembling: {[m[0] for m in top_3_models]}")

    # Stacking Ensemble
    print("\nTraining Stacking Ensemble...")
    start_time = time.time()
    try:
        stacking_model = create_stacking_ensemble(top_3_models, preprocessor, X_train, y_train)
        stacking_time = time.time() - start_time

        y_pred_stack = stacking_model.predict(X_test)
        stack_metrics = {
            'MAE': mean_absolute_error(y_test.values, y_pred_stack),
            'RMSE': np.sqrt(mean_squared_error(y_test.values, y_pred_stack)),
            'R2': r2_score(y_test.values, y_pred_stack),
        }

        stack_result = {
            'model_name': 'Stacking Ensemble',
            'pipeline': stacking_model,
            'best_params': {},
            'cv_mae': 0,
            'cv_std': 0,
            'test_metrics': stack_metrics,
            'training_time': stacking_time,
        }
        results.append(stack_result)

        print(f"  Test MAE: ${stack_metrics['MAE']:,.0f}")
        print(f"  Test RMSE: ${stack_metrics['RMSE']:,.0f}")
        print(f"  Test R2: {stack_metrics['R2']:.4f}")
        print(f"  Training time: {stacking_time:.1f}s")

        if stack_metrics['MAE'] < best_mae:
            best_mae = stack_metrics['MAE']
            best_model_info = stack_result
    except Exception as e:
        print(f"  Stacking failed: {e}")

    # Voting Ensemble
    print("\nTraining Voting Ensemble...")
    start_time = time.time()
    try:
        voting_model = create_voting_ensemble(top_3_models, preprocessor, X_train, y_train)
        voting_time = time.time() - start_time

        y_pred_vote = voting_model.predict(X_test)
        vote_metrics = {
            'MAE': mean_absolute_error(y_test.values, y_pred_vote),
            'RMSE': np.sqrt(mean_squared_error(y_test.values, y_pred_vote)),
            'R2': r2_score(y_test.values, y_pred_vote),
        }

        vote_result = {
            'model_name': 'Voting Ensemble',
            'pipeline': voting_model,
            'best_params': {},
            'cv_mae': 0,
            'cv_std': 0,
            'test_metrics': vote_metrics,
            'training_time': voting_time,
        }
        results.append(vote_result)

        print(f"  Test MAE: ${vote_metrics['MAE']:,.0f}")
        print(f"  Test RMSE: ${vote_metrics['RMSE']:,.0f}")
        print(f"  Test R2: {vote_metrics['R2']:.4f}")
        print(f"  Training time: {voting_time:.1f}s")

        if vote_metrics['MAE'] < best_mae:
            best_mae = vote_metrics['MAE']
            best_model_info = vote_result
    except Exception as e:
        print(f"  Voting failed: {e}")

    # Save best model
    assert best_model_info is not None
    best_pipeline = best_model_info['pipeline']
    model_path = Path(model_dir) / 'best_model.joblib'
    joblib.dump(best_pipeline, model_path)
    print(f"\nBest model ({best_model_info['model_name']}) saved to {model_path}")

    # Save results summary
    summary = {
        'best_model': best_model_info['model_name'],
        'best_params': best_model_info['best_params'],
        'test_metrics': best_model_info['test_metrics'],
        'training_time': best_model_info.get('training_time', 0),
        'all_results': [
            {
                'model': r['model_name'],
                'cv_mae': r['cv_mae'],
                'cv_std': r['cv_std'],
                'test_mae': r['test_metrics']['MAE'],
                'test_rmse': r['test_metrics']['RMSE'],
                'test_r2': r['test_metrics']['R2'],
                'training_time': r.get('training_time', 0),
                'best_params': r['best_params'],
            }
            for r in results
        ],
    }

    summary_path = Path(model_dir) / 'training_summary.json'
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"Training summary saved to {summary_path}")

    # Save detailed results CSV
    results_df = pd.DataFrame([
        {
            'model': r['model_name'],
            'cv_mae': r['cv_mae'],
            'cv_std': r['cv_std'],
            'test_mae': r['test_metrics']['MAE'],
            'test_rmse': r['test_metrics']['RMSE'],
            'test_r2': r['test_metrics']['R2'],
            'training_time_seconds': r.get('training_time', 0),
            'best_params': json.dumps(r['best_params']),
        }
        for r in results
    ])
    results_csv_path = Path(model_dir) / 'results.csv'
    results_df.to_csv(results_csv_path, index=False)
    print(f"Results CSV saved to {results_csv_path}")

    # Print comparison table
    print("\n" + "=" * 100)
    print("MODEL COMPARISON")
    print("=" * 100)
    print(f"{'Model':<25} {'CV MAE':>12} {'Test MAE':>12} {'Test RMSE':>12} {'Test R²':>8} {'Time(s)':>8}")
    print("-" * 100)
    for r in results:
        m = r['test_metrics']
        t = r.get('training_time', 0)
        print(f"{r['model_name']:<25} ${r['cv_mae']:>10,.0f} ${m['MAE']:>10,.0f} ${m['RMSE']:>10,.0f} {m['R2']:>8.4f} {t:>8.1f}")

    # Ensemble verdict
    print("\n" + "=" * 60)
    print("ENSEMBLE VERDICT")
    print("=" * 60)
    base_best = min([r for r in results if 'Ensemble' not in r['model_name']], key=lambda x: x['test_metrics']['MAE'])
    stack_result = next((r for r in results if r['model_name'] == 'Stacking Ensemble'), None)
    vote_result = next((r for r in results if r['model_name'] == 'Voting Ensemble'), None)

    if stack_result and stack_result['test_metrics']['MAE'] < base_best['test_metrics']['MAE']:
        print(f"[OK] Stacking Ensemble beats best base model ({base_best['model_name']})")
    else:
        print(f"[NO] Stacking Ensemble does NOT beat best base model ({base_best['model_name']})")

    if vote_result and vote_result['test_metrics']['MAE'] < base_best['test_metrics']['MAE']:
        print(f"[OK] Voting Ensemble beats best base model ({base_best['model_name']})")
    else:
        print(f"[NO] Voting Ensemble does NOT beat best base model ({base_best['model_name']})")

    return summary


if __name__ == '__main__':
    run_training()