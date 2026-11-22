from abc import ABC, abstractmethod
from typing import Dict, Any, List
import pandas as pd

class BaseModel(ABC):
    """Abstract Base Class for all HDIP Machine Learning Models."""

    @abstractmethod
    def train(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Train model and return evaluation metrics dict."""
        pass

    @abstractmethod
    def predict(self, input_params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate prediction with confidence intervals and values."""
        pass

    @abstractmethod
    def explain(self, prediction_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate SHAP or feature-level explanations for prediction."""
        pass
