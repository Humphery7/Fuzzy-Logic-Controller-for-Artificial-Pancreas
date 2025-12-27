
import pandas as pd
import glob

controllers = {
    'BB': '/Users/humpheryotuoniyo/Fuzzy-Logic-Controller-for-Artificial-Pancreas/src/results/simglucose_BBController/performance_stats.csv',
    'PID': '/Users/humpheryotuoniyo/Fuzzy-Logic-Controller-for-Artificial-Pancreas/src/results/simglucose_PIDController/performance_stats.csv',
    'Fuzzy': '/Users/humpheryotuoniyo/Fuzzy-Logic-Controller-for-Artificial-Pancreas/src/results/simglucose_FuzzyController/performance_stats.csv'
}

print(f"{'Controller':<10} | {'TIR (70-180)':<15} | {'Hypo (<70)':<15} | {'Hyper (>180)':<15} | {'Risk Index':<15}")
print("-" * 80)

for name, path in controllers.items():
    try:
        df = pd.read_csv(path)
        # Handle the column name with special chars
        tir_col = '70<=BG<=180'
        
        avg_tir = df[tir_col].mean()
        avg_hypo = df['BG<70'].mean()
        avg_hyper = df['BG>180'].mean()
        avg_risk = df['Risk Index'].mean()
        
        print(f"{name:<10} | {avg_tir:>13.2f}% | {avg_hypo:>13.2f}% | {avg_hyper:>13.2f}% | {avg_risk:>13.2f}")
    except Exception as e:
        print(f"Error reading {name}: {e}")
