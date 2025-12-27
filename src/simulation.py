import matplotlib.pyplot as plt
import numpy as np
from patient_model import PatientModel, meals, meal_absorption
from src.controllers.fuzzy_controller import HierarchicalFIS
from src.controllers.pid_controller import PIDController
from tuning import cost_function


def simulate_controller(patient, controller, meals, controller_name="Controller"):
    """
    Run simulation with a given controller.
    
    Args:
        patient: PatientModel instance
        controller: Controller with compute_dose method
        meals: Dictionary of meal times and carb amounts
        controller_name: Name for logging
        
    Returns:
        times, G_trace, doses
    """
    times = np.arange(0, 24, patient.dt)
    doses = np.zeros(len(times))
    G_trace = np.zeros(len(times))
    G_prev, rate_prev = 90, 0
    
    meal_times = sorted(meals.keys())
    
    for i, t in enumerate(times):
        # Calculate meal absorption rate from all meals
        meal_rate = 0
        for mt in meal_times:
            meal_rate += meal_absorption(t, mt, meals[mt], tau=30)
        
        # Get current glucose
        G = G_trace[i-1] if i > 0 else 90
        
        # Calculate glucose rate and acceleration for controllers that need it
        bg_rate = (G - G_prev) / (patient.dt * 60)
        bg_accel = (bg_rate - rate_prev) / (patient.dt * 60)
        
        # Compute insulin dose based on controller type
        if hasattr(controller, 'compute_dose'):
            # Check if it's fuzzy (needs 3 args) or PID (needs 1-2 args)
            try:
                doses[i] = controller.compute_dose(G, bg_rate, bg_accel)
            except TypeError:
                # PID controller only needs glucose
                doses[i] = controller.compute_dose(G, patient.dt)
        
        G_prev, rate_prev = G, bg_rate
        
        # Step patient model forward
        G_trace[i] = patient.step(doses[i], meal_rate)
    
    return times, G_trace, doses


def calculate_metrics(G_trace, doses, times):
    """Calculate performance metrics."""
    metrics = {}
    
    # Time in range (80-140 mg/dL)
    in_range = np.sum((G_trace >= 80) & (G_trace <= 140))
    metrics['time_in_range'] = (in_range / len(G_trace)) * 100
    
    # Time in tight range (70-180 mg/dL)
    tight_range = np.sum((G_trace >= 70) & (G_trace <= 180))
    metrics['time_in_tight_range'] = (tight_range / len(G_trace)) * 100
    
    # Hypoglycemia events (<70 mg/dL)
    metrics['hypo_events'] = np.sum(G_trace < 70)
    
    # Severe hypoglycemia (<54 mg/dL)
    metrics['severe_hypo_events'] = np.sum(G_trace < 54)
    
    # Hyperglycemia (>180 mg/dL)
    metrics['hyper_events'] = np.sum(G_trace > 180)
    
    # Mean glucose
    metrics['mean_glucose'] = np.mean(G_trace)
    
    # Glucose variability (coefficient of variation)
    metrics['glucose_std'] = np.std(G_trace)
    metrics['glucose_cv'] = (metrics['glucose_std'] / metrics['mean_glucose']) * 100
    
    # Total insulin delivered
    metrics['total_insulin'] = np.sum(doses)
    
    # Cost function
    metrics['cost'] = cost_function(G_trace)
    
    return metrics


def run_comparison():
    """Run simulation comparing Fuzzy and PID controllers."""
    print("Running controller comparison simulation...")
    print("=" * 60)
    
    # Create two separate patient models
    patient_fuzzy = PatientModel()
    patient_pid = PatientModel()
    
    # Create controllers with optimized parameters
    fis = HierarchicalFIS(max_dose=1.0)  # Optimized fuzzy: efficient + superior control
    pid = PIDController(Kp=0.05, Ki=0.002, Kd=0.005, target=100.0, max_dose=0.8)  # Baseline PID
    
    # Run simulations
    print("\nRunning Fuzzy Controller simulation...")
    times, G_fuzzy, doses_fuzzy = simulate_controller(patient_fuzzy, fis, meals, "Fuzzy")
    
    print("Running PID Controller simulation...")
    times, G_pid, doses_pid = simulate_controller(patient_pid, pid, meals, "PID")
    
    # Calculate metrics
    print("\n" + "=" * 60)
    print("PERFORMANCE METRICS")
    print("=" * 60)
    
    metrics_fuzzy = calculate_metrics(G_fuzzy, doses_fuzzy, times)
    metrics_pid = calculate_metrics(G_pid, doses_pid, times)
    
    print("\n{:<25} {:>15} {:>15}".format("Metric", "Fuzzy", "PID"))
    print("-" * 60)
    print("{:<25} {:>14.1f}% {:>14.1f}%".format("Time in Range (80-140)", metrics_fuzzy['time_in_range'], metrics_pid['time_in_range']))
    print("{:<25} {:>14.1f}% {:>14.1f}%".format("Time in Range (70-180)", metrics_fuzzy['time_in_tight_range'], metrics_pid['time_in_tight_range']))
    print("{:<25} {:>15d} {:>15d}".format("Hypoglycemia (<70)", metrics_fuzzy['hypo_events'], metrics_pid['hypo_events']))
    print("{:<25} {:>15d} {:>15d}".format("Hyperglycemia (>180)", metrics_fuzzy['hyper_events'], metrics_pid['hyper_events']))
    print("{:<25} {:>14.1f} {:>14.1f}".format("Mean Glucose (mg/dL)", metrics_fuzzy['mean_glucose'], metrics_pid['mean_glucose']))
    print("{:<25} {:>14.1f} {:>14.1f}".format("Glucose Std Dev", metrics_fuzzy['glucose_std'], metrics_pid['glucose_std']))
    print("{:<25} {:>14.1f}% {:>14.1f}%".format("Glucose CV", metrics_fuzzy['glucose_cv'], metrics_pid['glucose_cv']))
    print("{:<25} {:>14.2f} {:>14.2f}".format("Total Insulin (units)", metrics_fuzzy['total_insulin'], metrics_pid['total_insulin']))
    print("{:<25} {:>14.2f} {:>14.2f}".format("Cost Function", metrics_fuzzy['cost'], metrics_pid['cost']))
    
    # Create comparison plots
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Glucose traces
    ax = axes[0, 0]
    ax.plot(times, G_fuzzy, 'b-', label='Fuzzy', linewidth=2)
    ax.plot(times, G_pid, 'r--', label='PID', linewidth=2)
    ax.axhline(100, color='g', ls=':', alpha=0.5, label='Target')
    ax.axhline(80, color='orange', ls='--', alpha=0.5, label='Range (80-140)')
    ax.axhline(140, color='orange', ls='--', alpha=0.5)
    ax.axhline(70, color='red', ls='--', alpha=0.3, label='Hypo threshold')
    ax.set_ylabel('Glucose (mg/dL)', fontsize=11)
    ax.set_xlabel('Time (hours)', fontsize=11)
    ax.set_title('Glucose Control Comparison', fontsize=12, fontweight='bold')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    
    # Insulin doses
    ax = axes[0, 1]
    ax.plot(times, doses_fuzzy, 'b-', label='Fuzzy', linewidth=1.5)
    ax.plot(times, doses_pid, 'r--', label='PID', linewidth=1.5)
    ax.set_ylabel('Insulin Dose (units)', fontsize=11)
    ax.set_xlabel('Time (hours)', fontsize=11)
    ax.set_title('Insulin Delivery Comparison', fontsize=12, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Glucose error over time
    ax = axes[1, 0]
    error_fuzzy = np.abs(G_fuzzy - 100)
    error_pid = np.abs(G_pid - 100)
    ax.plot(times, error_fuzzy, 'b-', label='Fuzzy', linewidth=1.5)
    ax.plot(times, error_pid, 'r--', label='PID', linewidth=1.5)
    ax.set_ylabel('Absolute Error from Target (mg/dL)', fontsize=11)
    ax.set_xlabel('Time (hours)', fontsize=11)
    ax.set_title('Control Error Comparison', fontsize=12, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Performance metrics bar chart
    ax = axes[1, 1]
    metrics_names = ['Time in\nRange (%)', 'Mean\nGlucose', 'Glucose\nStd Dev', 'Total\nInsulin']
    fuzzy_vals = [metrics_fuzzy['time_in_range'], metrics_fuzzy['mean_glucose']/10, 
                  metrics_fuzzy['glucose_std'], metrics_fuzzy['total_insulin']]
    pid_vals = [metrics_pid['time_in_range'], metrics_pid['mean_glucose']/10,
                metrics_pid['glucose_std'], metrics_pid['total_insulin']]
    
    x = np.arange(len(metrics_names))
    width = 0.35
    ax.bar(x - width/2, fuzzy_vals, width, label='Fuzzy', color='blue', alpha=0.7)
    ax.bar(x + width/2, pid_vals, width, label='PID', color='red', alpha=0.7)
    ax.set_ylabel('Value (normalized)', fontsize=11)
    ax.set_title('Performance Metrics Summary', fontsize=12, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(metrics_names, fontsize=9)
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig('controller_comparison.png', dpi=150, bbox_inches='tight')
    print(f"\nPlot saved to: controller_comparison.png")
    plt.show()


if __name__ == "__main__":
    run_comparison()