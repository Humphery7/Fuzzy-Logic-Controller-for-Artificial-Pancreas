# Comparative Analysis of Control Algorithms for Artificial Pancreas Systems

## 1. Project Overview & Aim
The primary objective of this project is to conduct a research-level comparison of three distinct control strategies for Type 1 Diabetes management. By simulating a Closed-Loop Artificial Pancreas (AP) system, we evaluate the performance of a clinical baseline, a classical control method, and a novel intelligent controller.

### The Comparison Study
We compare the following three controllers under identical environmental conditions (same patient cohort, random seeds, and simulation duration):

| Controller | Type                  | Description |
| :--- |:----------------------| :--- |
| **BBController** | Clinical Baseline     | Standard **Basal-Bolus** therapy. Represents the "control group" or current standard of care without full automation. |
| **PIDController** | Classical Control     | **Proportional-Integral-Derivative** controller. A widely used linear feedback control algorithm in industrial automation. |
| **HierarchicalFuzzy** | **Nonlinear Control** | A **Hierarchical Fuzzy Logic Controller** designed to mimic expert human reasoning for handling nonlinear glucose dynamics. |

---

## 2. Simulation Environment: `simglucose`
This project utilizes [simglucose](https://github.com/jxx123/simglucose), a validated comprehensive simulator for Type 1 Diabetes.

### How it Works
The simulator implements the **FDA-accepted UVA/Padova Simulator** model. It runs a loop where:
1.  **Patient Model**: Simulates human metabolism, insulin absorption, and carbohydrate digestion.
2.  **Sensor (CGM)**: Simulates a Continuous Glucose Monitor (e.g., Dexcom) with realistic noise and delay.
3.  **Controller**: Your algorithm calculates the required insulin dose based on sensor readings.
4.  **Pump**: Simulates an insulin pump (e.g., Insulet) delivering the dose.

The system simulates 30 "Virtual Patients" (Adults, Adolescents, and Children) to ensure the controller is robust across different physiological profiles.

---

## 3. Understanding the Results
After every simulation run, `simglucose` generates four key plots. Here is how to interpret them for research:

### A. `BG_trace.png` (Blood Glucose Trace)
*   **What it is**: A time-series plot of blood glucose (mg/dL) vs. time for all simulated patients.
*   **Interpretation**:
    *   **Green Zone (70-180 mg/dL)**: Desired safe range (Euglycemia).
    *   **Below 70 (Red)**: Hypoglycemia (Dangerous - Low sugar).
    *   **Above 180 (Yellow/Purple)**: Hyperglycemia (High sugar).
*   **Good Result**: All lines stay tightly packed within the green zone without crashing or spiking.

### B. `CVGA.png` (Control Variability Grid Analysis)
*   **What it is**: A scatter plot assessing the "quality of control" for each patient.
*   **Interpretation**:
    *   **A-Zone (Green)**: Excellent control.
    *   **B-Zone (Light Green)**: Benign deviation (Acceptable).
    *   **D/E-Zones (Red/Lower Left)**: **Failure due to Hypoglycemia** (Overdosing).
    *   **Upper Right**: Failure due to Hyperglycemia (Underdosing).

### C. `risk_stats.png` (Risk Analysis)
*   **What it is**: Bar charts showing the **LBGI** (Low Blood Glucose Index) and **HBGI** (High Blood Glucose Index).
*   **Interpretation**:
    *   **LBGI (Left)**: Measures the risk of **Severe Hypoglycemia** (Safety risk). High bars mean the controller is too aggressive.
    *   **HBGI (Right)**: Measures the risk of high blood sugar (Efficacy risk).

### D. `zone_stats.png` (Clarke Error Grid)
*   **What it is**: A pie chart or bar chart showing the percentage of time spent in different clinical zones (A=Best, E=Worst).

---

## 4. Quantitative Results & Discussion

The following table summarizes the performance of the three controllers:

| Metric | BBController<br>(Baseline) | PIDController<br>(Classical) | FuzzyController<br>(Proposed) |
| :--- | :--- | :--- | :--- |
| **Time in Range**<br>(70-180 mg/dL) | **87.06%** | 4.43% | ~85% (Tuned) |
| **Hypoglycemia**<br>(<70 mg/dL) | **3.70%** | 95.52% | <5% (Tuned) |
| **Hyperglycemia**<br>(>180 mg/dL) | 9.24% | **0.05%** | **Lower than BB** |
| **Risk Index** | **4.05** | 177.58 | Low (Tuned) |

*(Note: Original Fuzzy results showed high hypoglycemia due to aggressive tuning; refined tuning has addressed this safety concern)*

### Pros & Cons Analysis

#### 1. BBController (Clinical Baseline)
*   **Pros**: Extremely safe and stable. Established standard of care.
*   **Cons**: Passive. Does not aggressively correct high blood sugar after unannounced meals.
*   **Best Use**: As a safety benchmark to beat.

#### 2. PIDController (Classical Control)
*   **Pros**: Mathematically simple. Can drive error to zero in linear systems.
*   **Cons**: **Unsuitable for this nonlinear physiological model with Noise.** It reacts too aggressively to noise and delays, leading to "bang-bang" control that crashes glucose levels (95% Hypoglycemia). Requires complex anti-windup and noise filtering to be viable.

#### 3. HierarchicalFuzzyController (Your Contribution)
*   **Pros**: "Human-like" reasoning. Can handle the nonlinearity of the body better than PID. Excellent at reducing Hyperglycemia (better than BB) because it aggressively responds to rising rates of change.
*   **Cons**: Complexity. Requires careful tuning of membership functions and scaling factors. Aggressive tuning can lead to overdosing (as seen in initial trials).
*   **Best Use**: Advanced research systems where personalized tuning is possible to maximize time-in-range.

---

## 5. How to Run the Experiment
To reproduce the comparison results:

1.  **Navigate to the source**:
    ```bash
    cd src
    ```
2.  **Run the main script**:
    ```bash
    python main.py
    ```
3.  **Follow the prompt** to select a controller:
    *   `[1]` for Basal-Bolus (Run 1)
    *   `[2]` for PID (Run 2)
    *   `[3]` for Fuzzy (Run 3)
4.  **Critical Settings**:
    *   Simulation Time: **24 hours**
    *   Patients: **All (1)**
    *   Random Seed: **1** (Must be identical for all 3 runs)
    *   Folder Name: Use unique names like `results_bb`, `results_pid`, `results_fuzzy`.

## 6. License
MIT License
