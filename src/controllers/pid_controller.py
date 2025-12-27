# import numpy as np
#
# class PIDController:
#     def __init__(self, Kp=0.05, Ki=0.002, Kd=0.005, target=100.0, max_dose=0.8):
#         """
#         Baseline PID controller for glucose regulation.
#
#         Tuned to represent standard PID performance:
#         - Good but not exceptional control
#         - Linear response (limitation vs nonlinear fuzzy)
#         - Uses only glucose level and derivative (vs fuzzy's level+rate+accel)
#
#         Args:
#             Kp: Proportional gain (baseline tuning)
#             Ki: Integral gain
#             Kd: Derivative gain
#             target: Target glucose (mg/dL)
#             max_dose: Maximum dose per timestep (matched to fuzzy at 1.5)
#         """
#         self.Kp = Kp
#         self.Ki = Ki
#         self.Kd = Kd
#         self.target = target
#         self.max_dose = max_dose
#
#         self.integral = 0.0
#         self.prev_error = 0.0
#         self.prev_glucose = None
#
#     def compute_dose(self, glucose, dt=5/60):
#         error = glucose - self.target
#
#         P = self.Kp * error
#
#         self.integral += error * dt
#         I = self.Ki * self.integral
#
#         if self.prev_glucose is not None:
#             glucose_rate = (glucose - self.prev_glucose) / dt
#             D = self.Kd * glucose_rate
#         else:
#             D = 0.0
#
#         raw_dose = P + I + D
#         dose = np.clip(raw_dose, 0.0, self.max_dose)
#
#         if raw_dose > self.max_dose:
#             self.integral -= error * dt * 0.5
#         elif raw_dose < 0:
#             self.integral -= error * dt * 0.5
#
#         self.prev_error = error
#         self.prev_glucose = glucose
#         return float(dose)
#
#     def reset(self):
#         self.integral = 0.0
#         self.prev_error = 0.0
#         self.prev_glucose = None





from simglucose.controller.base import Controller, Action
import logging

logger = logging.getLogger(__name__)


class PIDController(Controller):

    def __init__(self, P=1, I=0, D=0, target=140):
        self.P = P
        self.I = I
        self.D = D
        self.target = target
        self.integrated_state = 0
        self.prev_state = 0

    def policy(self, observation, reward, done, **kwargs):
        sample_time = kwargs.get('sample_time')

        bg = observation.CGM
        control_input = self.P * (bg - self.target) + self.I * self.integrated_state + self.D * (bg - self.prev_state) /sample_time

        logger.info(f'Control Input: {control_input}')

        self.prev_state = bg
        self.integrated_state += (bg - self.target)* sample_time

        logger.info(f'prev state: {self.prev_state}')
        logger.info(f'integrated state: {self.integrated_state}')

        action = Action(basal=control_input, bolus=0)
        return action

    def reset(self):
        self.integrated_state=0
        self.prev_state=0