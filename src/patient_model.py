# import numpy as np
# from scipy.integrate import odeint
#
# class PatientModel:
#     def __init__(self, initial_glucose=90.0, insulin_sensitivity=0.02):
#         self.G = initial_glucose
#         self.I = 0.0
#         self.Si = insulin_sensitivity
#         self.t = 0.0
#         self.dt = 5 / 60
#
#     def dynamics(self, state, t, insulin_dose, meal_rate=0):
#         """
#         Glucose-insulin dynamics based on simplified Bergman minimal model.
#
#         Args:
#             state: [G, I] - glucose (mg/dL) and insulin (mU/L)
#             t: time
#             insulin_dose: insulin dose (units)
#             meal_rate: glucose appearance rate from meals (mg/dL per minute)
#
#         Returns:
#             [dG/dt, dI/dt]
#         """
#         G, I = state
#
#         # Model parameters (physiologically realistic)
#         p1 = 0.028      # Glucose effectiveness (1/min) - glucose self-regulation
#         Gb = 90.0       # Basal glucose (mg/dL)
#         p2 = 0.025      # Insulin sensitivity (1/min per mU/L) - REDUCED from 0.02
#         p3 = 0.000013   # Insulin-dependent glucose uptake (1/min per mU/L)
#         n = 0.2         # Insulin clearance rate (1/min)
#
#         # Glucose dynamics
#         # dG/dt = -p1*(G-Gb) - p3*G*I + meal_rate
#         # Negative term: glucose returns to baseline
#         # Insulin effect: proportional to both glucose level and insulin
#         # Meal effect: direct glucose appearance
#         dGdt = -p1 * (G - Gb) - p3 * G * I + meal_rate
#
#         # Insulin dynamics
#         # dI/dt = -n*I + gamma*insulin_dose
#         # Insulin decays exponentially
#         # Insulin dose adds to plasma insulin
#         gamma = 20.0  # Insulin appearance rate (mU/L per unit) - REDUCED from 50
#         dIdt = -n * I + gamma * insulin_dose
#
#         return [dGdt, dIdt]
#
#     def step(self, insulin_dose, meal_rate=0):
#         state0 = [self.G, self.I]
#         sol = odeint(self.dynamics, state0, [0, self.dt], args=(insulin_dose, meal_rate))
#         self.G, self.I = sol[-1]
#         self.t += self.dt
#         return self.G
#
#     def simulate(self, insulin_doses, meal_schedule):
#
#         times = np.arange(0, 24, self.dt)
#         G_trace = np.zeros(len(times))
#         I_trace = np.zeros(len(times))
#         state0 = [self.G, self.I]
#
#         for i, t in enumerate(times):
#             meal_rate = meal_schedule.get(t, 0)
#             sol = odeint(self.dynamics, state0, [0, self.dt], args=(insulin_doses[i] if i < len(insulin_doses) else 0, meal_rate))
#             state0 = sol[-1]
#             G_trace[i] = state0[0]
#             I_trace[i] = state0[1]
#             self.t = t + self.dt
#
#         return G_trace, I_trace
#
#
# def meal_absorption(t, meal_time, carbs, tau=45):
#
#     if t < meal_time:
#         return 0
#
#     dt_minutes = (t - meal_time) * 60  # Convert to minutes
#
#     # Exponential absorption: fast initially, then tapers off
#     # Carb-to-glucose conversion: ~3-4 mg/dL per gram for average person
#     # For 50g meal: should raise glucose by ~150-200 mg/dL total if no insulin
#     # But this is spread over time via exponential decay
#
#     glucose_per_gram = 3.5  # mg/dL per gram of carbs (total rise)
#     total_glucose_rise = carbs * glucose_per_gram
#
#     # Exponential decay: most absorption in first 30-60 min
#     # Scale factor to ensure integral over time equals total rise
#     # For exponential: integral from 0 to inf of (A/tau)*exp(-t/tau) = A
#     rate = (total_glucose_rise / tau) * np.exp(-dt_minutes / tau)
#
#     return rate
#
#
# # Realistic meal schedule with carbohydrate amounts
# # Format: {time_in_hours: carbs_in_grams}
# meals = {
#     7.0: 50,   # 7am breakfast: 50g carbs (e.g., oatmeal, fruit)
#     12.0: 60,  # 12pm lunch: 60g carbs (e.g., sandwich, side)
#     18.0: 70   # 6pm dinner: 70g carbs (e.g., pasta, vegetables)
# }

















# patient_model.py
import numpy as np
from scipy.integrate import odeint

class PatientModel:
    """
    Bergman Minimal Model (3-state):
      States:
        G : plasma glucose (mg/dL)
        X : remote insulin action (1/min but converted internally)
        I : plasma insulin (mU/L)

    Public API kept the same:
      - step(insulin_dose, meal_rate) -> returns updated G
      - simulate(insulin_doses, meal_schedule) -> (G_trace, I_trace)
    """

    def __init__(self, initial_glucose=90.0, initial_insulin=15.0, dt_hours=5/60):
        # state (public)
        self.G = initial_glucose   # mg/dL
        self.X = 0.0               # remote insulin action (dimensionless)
        self.I = initial_insulin   # mU/L

        # basal values
        self.Gb = 90.0    # basal glucose mg/dL
        self.Ib = initial_insulin  # basal insulin mU/L

        # time step in hours (kept for compatibility with your simulation code)
        self.dt = dt_hours
        self.t = 0.0

        # Bergman parameters (per minute). We'll convert to per hour inside dynamics
        self._p1_per_min = 0.028      # glucose effectiveness (1/min)
        self._p2_per_min = 0.025      # insulin action decay (1/min)
        self._p3_per_min = 5.0e-05    # insulin sensitivity term (1/min per mU/L) - Increased to reveal controller differences
        self._n_per_min  = 0.2        # insulin clearance (1/min)

        # insulin appearance scaling: converts units -> mU/L per unit
        # gamma is mU/L per unit of insulin delivered (appearance). This is a tuning/scaling parameter.
        # We will convert to per-hour inside dynamics consistent with other rate conversions.
        self.gamma_mU_per_unit = 20.0

    def dynamics(self, state, t, insulin_dose_units_per_step, meal_rate_mg_per_dL_per_min):
        """
        state: [G, X, I]
        t: time (in hours) — odeint will march over an interval in hours
        insulin_dose_units_per_step: insulin units delivered during the current step (units per step)
        meal_rate_mg_per_dL_per_min: glucose appearance rate from meals in mg/dL per MINUTE
        """

        G, X, I = state

        # Convert per-minute parameters to per-hour because t (and dt) are in hours
        p1 = self._p1_per_min * 60.0
        p2 = self._p2_per_min * 60.0
        p3 = self._p3_per_min * 60.0
        n  = self._n_per_min  * 60.0

        # Convert meal_rate (mg/dL per minute) -> mg/dL per hour for consistency
        meal_rate_per_hour = meal_rate_mg_per_dL_per_min * 60.0

        # Convert insulin dose (units delivered over the step) -> appearance rate (mU/L per hour)
        # insulin_dose_units_per_step is units given during the step of length dt hours
        # units per minute = insulin_dose / (dt_hours * 60)
        # mU/L per minute = gamma * units_per_minute
        # convert to per hour -> multiply by 60
        dt_minutes = self.dt * 60.0 if self.dt > 0 else 1.0
        if dt_minutes <= 0:
            dt_minutes = 1.0
        units_per_minute = insulin_dose_units_per_step / dt_minutes
        u_mU_per_min = self.gamma_mU_per_unit * units_per_minute
        u_mU_per_hour = u_mU_per_min * 60.0

        # Bergman Minimal Model equations (converted to per-hour rates)
        # dG/dt = - (p1 + X) * G + p1 * Gb + D(t)
        dGdt = - (p1 + X) * G + p1 * self.Gb + meal_rate_per_hour

        # dX/dt = -p2 * X + p3 * (I - Ib)
        dXdt = - p2 * X + p3 * (I - self.Ib)

        # dI/dt = -n * (I - Ib) + u(t)
        dIdt = - n * (I - self.Ib) + u_mU_per_hour

        return [dGdt, dXdt, dIdt]

    def step(self, insulin_dose, meal_rate=0):
        """
        Advance the model by one time step (self.dt hours).
        insulin_dose: units delivered during the step (units)
        meal_rate: mg/dL per minute (same units your meal_absorption returns)
        Returns updated glucose value (self.G).
        """
        state0 = [self.G, self.X, self.I]
        # integrate over small interval [0, dt] where ode expects time in hours
        sol = odeint(self.dynamics, state0, [0.0, self.dt], args=(insulin_dose, meal_rate))
        self.G, self.X, self.I = sol[-1]
        self.t += self.dt
        return self.G

    def simulate(self, insulin_doses, meal_schedule):
        """
        Simulate over 24 hours using internal dt (hours).
        insulin_doses: array-like of insulin units per step. If shorter than time vector, zeros are used.
        meal_schedule: dict {time_in_hours: carbs_in_grams}
        Returns: (G_trace, I_trace)
        """
        times = np.arange(0, 24, self.dt)
        G_trace = np.zeros(len(times))
        X_trace = np.zeros(len(times))
        I_trace = np.zeros(len(times))

        state0 = [self.G, self.X, self.I]
        meal_times = sorted(meal_schedule.keys())

        for i, t in enumerate(times):
            # compute meal_rate at this time (sum of contributions from all meals)
            meal_rate = 0.0
            for mt in meal_times:
                # use provided helper meal_absorption which returns mg/dL per minute
                meal_rate += meal_absorption(t, mt, meal_schedule[mt], tau=45)

            insulin_dose = insulin_doses[i] if i < len(insulin_doses) else 0.0
            sol = odeint(self.dynamics, state0, [0.0, self.dt], args=(insulin_dose, meal_rate))
            state0 = sol[-1]
            G_trace[i] = state0[0]
            X_trace[i] = state0[1]
            I_trace[i] = state0[2]
            self.t = t + self.dt

        return G_trace, I_trace


def meal_absorption(t, meal_time, carbs, tau=45):
    """
    Same helper you were using: returns glucose appearance rate in mg/dL per minute.
    t and meal_time are in hours; tau in minutes.
    """
    if t < meal_time:
        return 0.0

    dt_minutes = (t - meal_time) * 60.0  # convert hours -> minutes
    glucose_per_gram = 3.5  # mg/dL per gram (approx)
    total_glucose_rise = carbs * glucose_per_gram

    # Exponential absorption kernel: (total / tau) * exp(-t/tau) gives mg/dL per minute
    rate = (total_glucose_rise / tau) * np.exp(-dt_minutes / tau)
    return rate


# Example realistic meal schedule (keeps the same format your simulation uses)
meals = {
    7.0: 50,   # breakfast
    12.0: 60,  # lunch
    18.0: 70   # dinner
}
