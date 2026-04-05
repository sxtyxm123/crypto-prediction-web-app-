"""
Model Configuration Comparison Tool

This script compares the old vs new model configurations
to show the anti-overfitting improvements.
"""

import json

def calculate_model_params(lstm_units, n_features=30):
    """
    Estimate the number of trainable parameters in the LSTM model.
    
    Args:
        lstm_units: List of LSTM units per layer
        n_features: Number of input features (approximate)
    
    Returns:
        Total parameter count
    """
    total_params = 0
    
    # First LSTM layer (with return_sequences=True)
    # Formula: 4 * (units * (units + input_dim + 1))
    total_params += 4 * (lstm_units[0] * (lstm_units[0] + n_features + 1))
    
    # Second LSTM layer
    # Input is from previous LSTM layer
    total_params += 4 * (lstm_units[1] * (lstm_units[1] + lstm_units[0] + 1))
    
    # Dense output layer
    total_params += lstm_units[1] + 1  # weights + bias
    
    return total_params


def print_comparison():
    """Print a detailed comparison of old vs new configurations."""
    
    print("=" * 80)
    print("MODEL CONFIGURATION COMPARISON - OVERFITTING MITIGATION")
    print("=" * 80)
    print()
    
    # Configuration comparison
    configs = {
        "LSTM Units": {
            "Old": "[64, 32]",
            "New": "[32, 16]",
            "Impact": "50% reduction in model capacity"
        },
        "Dropout Rate": {
            "Old": "0.2 (20%)",
            "New": "0.5 (50%)",
            "Impact": "2.5x more aggressive regularization"
        },
        "L2 Regularization": {
            "Old": "0.01 (kernel + recurrent)",
            "New": "0.02 (kernel + recurrent + bias)",
            "Impact": "2x stronger weight penalty + bias regularization"
        },
        "Batch Size": {
            "Old": "64",
            "New": "128",
            "Impact": "2x more stable gradient estimates"
        },
        "Validation Split": {
            "Old": "0.1 (10%)",
            "New": "0.15 (15%)",
            "Impact": "50% more validation data for monitoring"
        },
        "Early Stopping Patience": {
            "Old": "5 epochs",
            "New": "8 epochs",
            "Impact": "60% more patience for convergence"
        },
        "Batch Normalization": {
            "Old": "None",
            "New": "After each LSTM layer",
            "Impact": "Improved training stability"
        },
        "Learning Rate Reduction": {
            "Old": "None",
            "New": "ReduceLROnPlateau (factor=0.5, patience=3)",
            "Impact": "Adaptive learning for fine-tuning"
        }
    }
    
    print(f"{'Parameter':<30} {'Old Value':<30} {'New Value':<30}")
    print("-" * 90)
    
    for param, values in configs.items():
        print(f"{param:<30} {values['Old']:<30} {values['New']:<30}")
    
    print()
    print("=" * 80)
    print("IMPACT ANALYSIS")
    print("=" * 80)
    print()
    
    for param, values in configs.items():
        print(f"• {param}:")
        print(f"  └─ {values['Impact']}")
        print()
    
    # Parameter count comparison
    old_params = calculate_model_params([64, 32])
    new_params = calculate_model_params([32, 16])
    reduction = ((old_params - new_params) / old_params) * 100
    
    print("=" * 80)
    print("MODEL COMPLEXITY ANALYSIS")
    print("=" * 80)
    print()
    print(f"Old Model Parameters: ~{old_params:,}")
    print(f"New Model Parameters: ~{new_params:,}")
    print(f"Parameter Reduction:  {reduction:.1f}%")
    print()
    print(f"This means the new model has {reduction:.1f}% less capacity to memorize")
    print(f"training data, forcing it to learn more generalizable patterns.")
    print()
    
    # Expected outcomes
    print("=" * 80)
    print("EXPECTED OUTCOMES")
    print("=" * 80)
    print()
    print("✅ Reduced gap between training and validation loss")
    print("✅ More stable predictions across different time periods")
    print("✅ Better generalization to unseen data")
    print("✅ Improved directional accuracy (most important for trading)")
    print("✅ Less sensitivity to noise in the data")
    print()
    print("⚠️  Note: Training may take slightly longer due to:")
    print("   - Larger batch size (128 vs 64)")
    print("   - Batch normalization computations")
    print("   - More epochs before early stopping (8 vs 5 patience)")
    print()
    
    # Trade-offs
    print("=" * 80)
    print("TRADE-OFFS")
    print("=" * 80)
    print()
    print("Pros:")
    print("  ✓ Much better generalization")
    print("  ✓ More robust to market noise")
    print("  ✓ Better long-term performance")
    print("  ✓ More reliable for actual trading")
    print()
    print("Cons:")
    print("  ✗ Slightly lower training accuracy (expected and desired)")
    print("  ✗ May not capture very complex short-term patterns")
    print("  ✗ Training time increased by ~20-30%")
    print()
    
    print("=" * 80)
    print("RECOMMENDATION")
    print("=" * 80)
    print()
    print("Run the training script and compare the training history plots:")
    print()
    print("  python model_training_enhanced.py")
    print()
    print("Then check the generated plots in lstm_models/<SYMBOL>/:")
    print("  • <SYMBOL>_training_history.png  - Shows train/val loss curves")
    print("  • <SYMBOL>_lstm_predictions.png  - Shows prediction quality")
    print()
    print("Look for:")
    print("  1. Training and validation loss curves staying close together")
    print("  2. Overfitting gap (red line) staying near zero")
    print("  3. Predictions following actual trends without being too smooth")
    print()
    print("=" * 80)
    print()


if __name__ == "__main__":
    print_comparison()
