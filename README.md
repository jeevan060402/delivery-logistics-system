# FastBox Delivery Simulator

## Overview
This script simulates a delivery logistics system, assigning packages to agents based on proximity and calculating performance metrics.

## Key Assumptions

1.  **Input Formats**: The system automatically detects and handles two conflicting JSON structures found in the assignment data:
    *   **List-Based**: `{"warehouses": [{"id": "W1", ...}]}` (used in `base_case.json`)
    *   **Dict-Based**: `{"warehouses": {"W1": ...}}` (used in `test_case_*.json`)

2.  **Assignment Logic**:
    *   Packages are assigned to the **Nearest Agent** (Euclidean distance) to the package's **Point of Origin** (Warehouse).
    *   Assignment is based on the agent's **Initial Location**.

3.  **Movement & Distance**:
    *   Agents travel: `Current Location` -> `Warehouse` -> `Destination`.
    *   After a delivery, the agent's new "Current Location" is the **Destination**.
    *   Agents do *not* return to a central depot between deliveries.

4.  **Efficiency Metric**:
    *   Calculated as `Total Distance / Packages Delivered`.
    *   **Lower is Better** (less distance traveled per package).

5.  **Dynamic Scenario (Bonus)**:
    *   Assumes a "Morning" and "Afternoon" shift split (50/50 package distribution).
    *   Assumes the "New Agent" is the one with the lexicographically last ID (e.g., "A3" if "A1, A2, A3" exist).

## Usage

**Standard Run**:
```bash
python3 delivery_sim.py base_case.json
```

**Dynamic Mode (Bonus)**:
```bash
python3 delivery_sim.py base_case.json --dynamic
```
