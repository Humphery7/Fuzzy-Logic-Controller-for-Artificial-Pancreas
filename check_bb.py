
try:
    from simglucose.controller.basal_bolus_ctrller import BBController
    print("Found BBController")
except ImportError:
    print("BBController not found at simglucose.controller.basal_bolus_ctrller")

try:
    import simglucose.controller
    print("Dir of simglucose.controller:", dir(simglucose.controller))
except ImportError:
    print("Could not import simglucose.controller")
