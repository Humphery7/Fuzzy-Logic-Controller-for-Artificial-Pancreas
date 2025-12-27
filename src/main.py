from simglucose.simulation.user_interface import simulate
from controllers.pid_controller import PIDController
from controllers.fuzzy_controller import HierarchicalFuzzyController


print("Select Controller for Comparison Experiment:")
print("[1] BBController (Clinical Baseline)")
print("[2] PIDController (Classical Control)")
print("[3] HierarchicalFuzzyController (Your Contribution)")

selection = input(">>> ")

if selection == '1':
    # Default simglucose controller is usually Basal-Bolus if None is passed
    # attempting to verify or use a placeholder if needed, but passing None typically works for default
    ctrller = None 
    print("Selected: BBController (Clinical Baseline)")
elif selection == '2':
    ctrller = PIDController()
    print("Selected: PIDController (Classical Control)")
elif selection == '3':
    ctrller = HierarchicalFuzzyController(init_state=0)
    print("Selected: HierarchicalFuzzyController (Your Contribution)")
else:
    print("Invalid selection, defaulting to Fuzzy Controller")
    ctrller = HierarchicalFuzzyController(init_state=0)

simulate(controller=ctrller)


