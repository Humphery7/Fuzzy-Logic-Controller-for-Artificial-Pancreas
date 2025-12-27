import numpy as np
from scipy.optimize import differential_evolution, minimize


def cost_function(glucose_trace, ref_level=90.0, min_level=80.0):
    err = glucose_trace - ref_level
    err[glucose_trace < min_level] *= 10
    return np.sqrt(np.mean(err ** 2))


def tune_fis(fis, patient, meals, method='DE', bounds=None):
    def objective(params):
        doses = []
        G, _ = patient.simulate(doses, meals)
        return cost_function(G)

    if method == 'DE':
        result = differential_evolution(objective, bounds, maxiter=3, popsize=100)
    else:
        result = minimize(objective, np.zeros(10), method='Nelder-Mead', options={'maxiter': 10})

    return result.x