"""
Utility functions for cryptocurrency price prediction system.

This module provides common utilities for:
- Configuration management
- Logging setup
- Data validation
- Error handling
- File operations
"""

import os
import json
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
import pandas as pd
from pathlib import Path


class ConfigManager:
    """Manages configuration loading and validation."""
    
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to configuration JSON file
        """
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            return config
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e}")
    
    def get(self, section: str, key: Optional[str] = None, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            section: Configuration section name
            key: Optional key within section
            default: Default value if not found
            
        Returns:
            Configuration value or default
        """
        if section not in self.config:
            return default
        
        if key is None:
            return self.config[section]
        
        return self.config[section].get(key, default)


class LoggerSetup:
    """Sets up logging for the application."""
    
    @staticmethod
    def setup_logger(
        name: str,
        log_dir: str = "logs",
        level: str = "INFO",
        console: bool = True,
        file_logging: bool = True
    ) -> logging.Logger:
        """
        Set up logger with file and console handlers.
        
        Args:
            name: Logger name
            log_dir: Directory for log files
            level: Logging level
            console: Enable console logging
            file_logging: Enable file logging
            
        Returns:
            Configured logger instance
        """
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, level.upper()))
        
        # Remove existing handlers
        logger.handlers = []
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        if console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        # File handler
        if file_logging:
            os.makedirs(log_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = os.path.join(log_dir, f"{name}_{timestamp}.log")
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        return logger


class DataValidator:
    """Validates data integrity and format."""
    
    @staticmethod
    def validate_dataframe(
        df: pd.DataFrame,
        required_columns: List[str],
        min_rows: int = 1
    ) -> bool:
        """
        Validate DataFrame has required columns and minimum rows.
        
        Args:
            df: DataFrame to validate
            required_columns: List of required column names
            min_rows: Minimum number of rows required
            
        Returns:
            True if valid
            
        Raises:
            ValueError: If validation fails
        """
        if df is None or df.empty:
            raise ValueError("DataFrame is None or empty")
        
        if len(df) < min_rows:
            raise ValueError(f"DataFrame has {len(df)} rows, minimum {min_rows} required")
        
        missing_cols = set(required_columns) - set(df.columns)
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        return True
    
    @staticmethod
    def validate_date_range(start_date: str, end_date: str) -> bool:
        """
        Validate date range is logical.
        
        Args:
            start_date: Start date string (YYYY-MM-DD)
            end_date: End date string (YYYY-MM-DD)
            
        Returns:
            True if valid
            
        Raises:
            ValueError: If validation fails
        """
        try:
            start = pd.Timestamp(start_date)
            end = pd.Timestamp(end_date)
        except Exception as e:
            raise ValueError(f"Invalid date format: {e}")
        
        if start >= end:
            raise ValueError(f"Start date {start_date} must be before end date {end_date}")
        
        if end > pd.Timestamp.now():
            raise ValueError(f"End date {end_date} cannot be in the future")
        
        return True
    
    @staticmethod
    def validate_symbol(symbol: str, valid_symbols: List[str]) -> bool:
        """
        Validate cryptocurrency symbol.
        
        Args:
            symbol: Symbol to validate
            valid_symbols: List of valid symbols
            
        Returns:
            True if valid
            
        Raises:
            ValueError: If validation fails
        """
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Symbol must be a non-empty string")
        
        if symbol not in valid_symbols:
            raise ValueError(f"Invalid symbol {symbol}. Valid symbols: {valid_symbols}")
        
        return True


class RetryHandler:
    """Handles retry logic for API calls and operations."""
    
    @staticmethod
    def retry_with_backoff(
        func,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0,
        logger: Optional[logging.Logger] = None
    ):
        """
        Retry function with exponential backoff.
        
        Args:
            func: Function to retry
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay in seconds
            backoff_factor: Multiplier for delay after each retry
            logger: Optional logger for retry messages
            
        Returns:
            Function result if successful
            
        Raises:
            Last exception if all retries fail
        """
        delay = initial_delay
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return func()
            except Exception as e:
                last_exception = e
                
                if attempt < max_retries:
                    if logger:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries + 1} failed: {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                    time.sleep(delay)
                    delay *= backoff_factor
                else:
                    if logger:
                        logger.error(f"All {max_retries + 1} attempts failed")
        
        raise last_exception


class FileManager:
    """Manages file operations safely."""
    
    @staticmethod
    def ensure_directory(path: str) -> str:
        """
        Ensure directory exists, create if necessary.
        
        Args:
            path: Directory path
            
        Returns:
            Absolute path to directory
        """
        abs_path = os.path.abspath(path)
        os.makedirs(abs_path, exist_ok=True)
        return abs_path
    
    @staticmethod
    def safe_file_path(directory: str, filename: str) -> str:
        """
        Create safe file path preventing directory traversal.
        
        Args:
            directory: Base directory
            filename: File name
            
        Returns:
            Safe absolute file path
            
        Raises:
            ValueError: If path is unsafe
        """
        # Normalize paths
        base_dir = os.path.abspath(directory)
        file_path = os.path.abspath(os.path.join(base_dir, filename))
        
        # Ensure file path is within base directory
        if not file_path.startswith(base_dir):
            raise ValueError(f"Unsafe file path: {filename}")
        
        return file_path
    
    @staticmethod
    def get_file_size_mb(file_path: str) -> float:
        """
        Get file size in megabytes.
        
        Args:
            file_path: Path to file
            
        Returns:
            File size in MB
        """
        if not os.path.exists(file_path):
            return 0.0
        
        size_bytes = os.path.getsize(file_path)
        return size_bytes / (1024 * 1024)


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def print_section_header(title: str, width: int = 60):
    """
    Print formatted section header.
    
    Args:
        title: Section title
        width: Total width of header
    """
    print("\n" + "=" * width)
    print(f"{title:^{width}}")
    print("=" * width)


def print_metrics(metrics: Dict[str, float], title: str = "Metrics"):
    """
    Print formatted metrics.
    
    Args:
        metrics: Dictionary of metric names and values
        title: Title for metrics section
    """
    print(f"\n{title}:")
    for name, value in metrics.items():
        if isinstance(value, float):
            print(f"  {name}: {value:.4f}")
        else:
            print(f"  {name}: {value}")
