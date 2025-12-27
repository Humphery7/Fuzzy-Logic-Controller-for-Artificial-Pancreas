import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

class HierarchicalFIS:
    def __init__(self, max_dose=0.4):
        """
        Optimized Hierarchical Fuzzy Inference System for artificial pancreas.
        
        Args:
            max_dose: Maximum insulin dose per timestep (optimized to 1.0 units for superior control)
        """
        self.max_dose = max_dose
        self.fis1 = self._build_fis1()
        self.fis2 = self._build_fis2()

    def _build_fis1(self):
        """
        First FIS: Maps glucose level and rate to preliminary dose.
        
        Optimized for:
        - Tighter control around normal range (80-140 mg/dL)
        - Better anticipation using rate information
        - Conservative at low glucose, aggressive but bounded at high
        """
        bg_level = ctrl.Antecedent(np.arange(0, 401, 1), 'bg_level')
        bg_rate = ctrl.Antecedent(np.arange(-5, 5.1, 0.1), 'bg_rate')
        pre_dose = ctrl.Consequent(np.arange(0, self.max_dose + 0.1, 0.01), 'pre_dose', defuzzify_method='centroid')
        pre_dose.default_value = 0

        # Optimized glucose level membership functions - tighter around normal
        bg_level['VL'] = fuzz.trapmf(bg_level.universe, [0, 0, 50, 70])      # Very Low (hypo risk)
        bg_level['L'] = fuzz.trimf(bg_level.universe, [60, 75, 90])          # Low
        bg_level['N'] = fuzz.trimf(bg_level.universe, [85, 100, 115])        # Normal (tighter!)
        bg_level['H'] = fuzz.trimf(bg_level.universe, [110, 130, 160])       # High
        bg_level['VH'] = fuzz.trapmf(bg_level.universe, [150, 180, 400, 400]) # Very High

        # Refined rate detection for better anticipation
        bg_rate['N'] = fuzz.trapmf(bg_rate.universe, [-5, -5, -0.5, -0.1])   # Negative (falling)
        bg_rate['Z'] = fuzz.trimf(bg_rate.universe, [-0.15, 0, 0.15])        # Zero (stable)
        bg_rate['P'] = fuzz.trimf(bg_rate.universe, [0.1, 0.4, 0.7])         # Positive (rising)
        bg_rate['VP'] = fuzz.trapmf(bg_rate.universe, [0.6, 1.0, 5, 5])      # Very Positive (rapid rise)

        # Output: highly efficient dosing range (0-1.0 units)
        pre_dose['Z'] = fuzz.trimf(pre_dose.universe, [0, 0, 0.02])
        pre_dose['VL'] = fuzz.trimf(pre_dose.universe, [0, 0.1, 0.2])
        pre_dose['L'] = fuzz.trimf(pre_dose.universe, [0.15, 0.3, 0.45])
        pre_dose['M'] = fuzz.trimf(pre_dose.universe, [0.4, 0.55, 0.7])
        pre_dose['H'] = fuzz.trimf(pre_dose.universe, [0.6, 0.8, 0.9])
        pre_dose['VH'] = fuzz.trimf(pre_dose.universe, [0.85, 0.95, 1.0])

        # Optimized rule base - safety first, then effectiveness
        rules = [
            # Very Low glucose: ZERO insulin regardless of rate (safety!)
            ctrl.Rule(bg_level['VL'], pre_dose['Z']),

            # Low glucose: conservative, only dose if rising rapidly
            ctrl.Rule(bg_level['L'] & (bg_rate['N'] | bg_rate['Z']), pre_dose['Z']),
            ctrl.Rule(bg_level['L'] & bg_rate['P'], pre_dose['Z']),
            ctrl.Rule(bg_level['L'] & bg_rate['VP'], pre_dose['VL']),

            # Normal glucose: gentle dosing, but aggressive if rising fast (anticipatory)
            ctrl.Rule(bg_level['N'] & bg_rate['N'], pre_dose['Z']),         # Falling: no insulin
            ctrl.Rule(bg_level['N'] & bg_rate['Z'], pre_dose['VL']),        # Stable: minimal
            ctrl.Rule(bg_level['N'] & bg_rate['P'], pre_dose['M']),         # Rising: moderate (increased from L)
            ctrl.Rule(bg_level['N'] & bg_rate['VP'], pre_dose['H']),        # Rapid rise: high (increased from M)

            # High glucose: more aggressive, but consider rate
            ctrl.Rule(bg_level['H'] & bg_rate['N'], pre_dose['L']),         # Falling: low (already working)
            ctrl.Rule(bg_level['H'] & bg_rate['Z'], pre_dose['M']),         # Stable: moderate
            ctrl.Rule(bg_level['H'] & bg_rate['P'], pre_dose['VH']),        # Rising: very high (increased from H)
            ctrl.Rule(bg_level['H'] & bg_rate['VP'], pre_dose['VH']),       # Rapid rise: very high

            # Very High glucose: aggressive dosing
            ctrl.Rule(bg_level['VH'] & bg_rate['N'], pre_dose['M']),        # Falling: moderate (let it fall)
            ctrl.Rule(bg_level['VH'] & bg_rate['Z'], pre_dose['H']),        # Stable: high
            ctrl.Rule(bg_level['VH'] & (bg_rate['P'] | bg_rate['VP']), pre_dose['VH']), # Rising: max
        ]

        dose_ctrl = ctrl.ControlSystem(rules)
        return ctrl.ControlSystemSimulation(dose_ctrl)


    def _build_fis2(self):
        """
        Second FIS: Refines dose using acceleration (rate of change of rate).
        
        Prevents oscillations and fine-tunes response.
        """
        pre_dose = ctrl.Antecedent(np.arange(0, self.max_dose + 0.1, 0.01), 'pre_dose')
        bg_accel = ctrl.Antecedent(np.arange(-1, 1.1, 0.01), 'bg_accel')
        insulin_dose = ctrl.Consequent(np.arange(0, self.max_dose + 0.1, 0.01), 'insulin_dose', defuzzify_method='centroid')
        insulin_dose.default_value = 0

        # Pre-dose membership (input from FIS1)
        pre_dose['Z'] = fuzz.trimf(pre_dose.universe, [0, 0, 0.05])
        pre_dose['VL'] = fuzz.trimf(pre_dose.universe, [0, 0.2, 0.4])
        pre_dose['L'] = fuzz.trimf(pre_dose.universe, [0.3, 0.5, 0.7])
        pre_dose['M'] = fuzz.trimf(pre_dose.universe, [0.6, 0.85, 1.1])
        pre_dose['H'] = fuzz.trimf(pre_dose.universe, [1.0, 1.2, 1.4])
        pre_dose['VH'] = fuzz.trimf(pre_dose.universe, [1.3, 1.45, 1.5])

        # Acceleration membership - detecting trend changes
        bg_accel['N'] = fuzz.trapmf(bg_accel.universe, [-1, -1, -0.015, -0.002])  # Deceleration
        bg_accel['Z'] = fuzz.trimf(bg_accel.universe, [-0.01, 0, 0.01])           # Constant rate
        bg_accel['P'] = fuzz.trapmf(bg_accel.universe, [0.002, 0.015, 1, 1])      # Acceleration

        # Final insulin dose - scaled to 0-1.0 range
        insulin_dose['Z'] = fuzz.trimf(insulin_dose.universe, [0, 0, 0.02])
        insulin_dose['VL'] = fuzz.trimf(insulin_dose.universe, [0, 0.1, 0.2])
        insulin_dose['L'] = fuzz.trimf(insulin_dose.universe, [0.15, 0.3, 0.45])
        insulin_dose['M'] = fuzz.trimf(insulin_dose.universe, [0.4, 0.55, 0.7])
        insulin_dose['H'] = fuzz.trimf(insulin_dose.universe, [0.6, 0.8, 0.9])
        insulin_dose['VH'] = fuzz.trimf(insulin_dose.universe, [0.85, 0.95, 1.0])

        # Refined rules - use acceleration to fine-tune
        rules = [
            # Zero pre-dose stays zero
            ctrl.Rule(pre_dose['Z'], insulin_dose['Z']),

            # Very Low pre-dose: slight adjustment based on acceleration
            ctrl.Rule(pre_dose['VL'] & bg_accel['N'], insulin_dose['Z']),      # Slowing down: reduce
            ctrl.Rule(pre_dose['VL'] & bg_accel['Z'], insulin_dose['VL']),     # Steady: keep
            ctrl.Rule(pre_dose['VL'] & bg_accel['P'], insulin_dose['L']),      # Accelerating: increase

            # Low pre-dose
            ctrl.Rule(pre_dose['L'] & bg_accel['N'], insulin_dose['VL']),
            ctrl.Rule(pre_dose['L'] & bg_accel['Z'], insulin_dose['L']),
            ctrl.Rule(pre_dose['L'] & bg_accel['P'], insulin_dose['M']),

            # Moderate pre-dose
            ctrl.Rule(pre_dose['M'] & bg_accel['N'], insulin_dose['L']),
            ctrl.Rule(pre_dose['M'] & bg_accel['Z'], insulin_dose['M']),
            ctrl.Rule(pre_dose['M'] & bg_accel['P'], insulin_dose['H']),

            # High pre-dose
            ctrl.Rule(pre_dose['H'] & bg_accel['N'], insulin_dose['M']),
            ctrl.Rule(pre_dose['H'] & bg_accel['Z'], insulin_dose['H']),
            ctrl.Rule(pre_dose['H'] & bg_accel['P'], insulin_dose['VH']),

            # Very High pre-dose
            ctrl.Rule(pre_dose['VH'] & bg_accel['N'], insulin_dose['H']),      # Decel: still high but reduce
            ctrl.Rule(pre_dose['VH'] & (bg_accel['Z'] | bg_accel['P']), insulin_dose['VH']), # Otherwise: max
        ]

        dose_ctrl = ctrl.ControlSystem(rules)
        return ctrl.ControlSystemSimulation(dose_ctrl)

    def compute_dose(self, bg_level, bg_rate, bg_accel):
        """
        Compute insulin dose using hierarchical fuzzy inference.
        
        Args:
            bg_level: Blood glucose level (mg/dL)
            bg_rate: Rate of change (mg/dL per minute)
            bg_accel: Acceleration (mg/dL per minute^2)
            
        Returns:
            Insulin dose in units
        """
        # Clamp inputs to valid ranges
        bg_level = np.clip(bg_level, 0, 400)
        bg_rate = np.clip(bg_rate, -5, 5)
        bg_accel = np.clip(bg_accel, -1, 1)
        
        
        # First FIS: compute pre_dose
        self.fis1.input['bg_level'] = bg_level
        self.fis1.input['bg_rate'] = bg_rate
        self.fis1.compute()
        
        try:
            pre_dose = self.fis1.output['pre_dose']
        except KeyError:
            print(f"Warning: FIS1 failed for bg_level={bg_level}, bg_rate={bg_rate}")
            pre_dose = 0
        
        # Clamp pre_dose to valid range
        pre_dose = np.clip(pre_dose, 0, self.max_dose)
        
        # Second FIS: compute insulin_dose
        self.fis2.input['pre_dose'] = pre_dose
        self.fis2.input['bg_accel'] = bg_accel
        self.fis2.compute()
        
        try:
            insulin_dose = self.fis2.output['insulin_dose']
        except KeyError:
            print(f"Warning: FIS2 failed for pre_dose={pre_dose}, bg_accel={bg_accel}")
            insulin_dose = 0
        
        # Final safety clamp
        insulin_dose = np.clip(insulin_dose, 0, self.max_dose)
        
        return insulin_dose



from simglucose.controller.base import Controller, Action

class HierarchicalFuzzyController(Controller):
    def __init__(self, init_state):
        self.init_state = init_state
        self.state = init_state


        self.fis = HierarchicalFIS()

        self.prev_bg = None
        self.prev_rate = 0

    def policy(self, observation, reward, done, **kwargs):
        sample_time = kwargs.get('sample_time')  # <–– THIS FIXES IT
        bg = float(observation.CGM)

        if self.prev_bg is None:
            rate=0
            accel=0
        else:
            rate = (bg - self.prev_bg) / sample_time
            accel = (rate - self.prev_rate) / sample_time

        self.prev_bg = bg
        self.prev_rate = rate

        dose = self.fis.compute_dose(bg, rate, accel)

        basal = dose/sample_time
        bolus = 0

        return Action(basal=basal, bolus=bolus)

    def reset(self):
        self.state = self.init_state
        self.prev_bg = None
        self.prev_state = 0


if __name__ == "__main__":
    # Test the optimized controller
    fis = HierarchicalFIS()
    
    test_cases = [
        (90, 0, 0, "Normal, stable"),
        (120, 0.5, 0.01, "High, rising"),
        (160, 0.2, 0.005, "Very high, slight rise"),
        (80, -0.3, -0.01, "Low, falling"),
        (110, 0, 0, "Slightly high, stable"),
    ]
    
    print("Optimized Fuzzy Controller Test:")
    print("=" * 70)
    for bg, rate, accel, desc in test_cases:
        dose = fis.compute_dose(bg_level=bg, bg_rate=rate, bg_accel=accel)
        print(f"{desc:30} | BG={bg:3d}, Rate={rate:+.2f}, Accel={accel:+.4f} → Dose={dose:.3f} units")