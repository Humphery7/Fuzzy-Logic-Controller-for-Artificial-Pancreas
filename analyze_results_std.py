
import csv

controllers = {
    'BB': '/Users/humpheryotuoniyo/Fuzzy-Logic-Controller-for-Artificial-Pancreas/src/results/simglucose_BBController/performance_stats.csv',
    'PID': '/Users/humpheryotuoniyo/Fuzzy-Logic-Controller-for-Artificial-Pancreas/src/results/simglucose_PIDController/performance_stats.csv',
    'Fuzzy': '/Users/humpheryotuoniyo/Fuzzy-Logic-Controller-for-Artificial-Pancreas/src/results/simglucose_FuzzyController/performance_stats.csv'
}

print(f"{'Controller':<10} | {'TIR (70-180)':<15} | {'Hypo (<70)':<15} | {'Hyper (>180)':<15} | {'Risk Index':<15}")
print("-" * 80)

for name, path in controllers.items():
    try:
        tirs, hypos, hypers, risks = [], [], [], []
        with open(path, 'r') as f:
            reader = csv.DictReader(f)
            # Check headers
            # standard simglucose headers: ,70<=BG<=180,BG>180,BG<70,BG>250,BG<50,LBGI,HBGI,Risk Index
            
            for row in reader:
                # Filter out potential empty rows
                if not row['Risk Index']: continue
                
                tirs.append(float(row['70<=BG<=180']))
                hypos.append(float(row['BG<70']))
                hypers.append(float(row['BG>180']))
                risks.append(float(row['Risk Index']))
        
        avg_tir = sum(tirs) / len(tirs)
        avg_hypo = sum(hypos) / len(hypos)
        avg_hyper = sum(hypers) / len(hypers)
        avg_risk = sum(risks) / len(risks)
        
        print(f"{name:<10} | {avg_tir:>13.2f}% | {avg_hypo:>13.2f}% | {avg_hyper:>13.2f}% | {avg_risk:>13.2f}")
    except Exception as e:
        print(f"Error reading {name}: {e}")
