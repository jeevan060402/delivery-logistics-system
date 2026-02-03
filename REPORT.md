# Project Report

## 1. Significant Technical Challenge
**Challenge:** The most significant challenge was the inconsistency in the input data formats. The `base_case.json` provided data as **Lists of Dictionaries** (e.g., `[{"id": "W1", ...}]`), whereas the PDF description and the 10 provided test cases used **Dictionaries of Dictionaries** (e.g., `{"W1": {...}}`). Additionally, keys varied slightly (`warehouse_id` vs `warehouse`).

**Resolution:** I implemented a robust `DataLoader` class that abstracts this complexity away from the core logic. It inspects the data structure type (List vs Dict) at runtime and "normalizes" everything into a consistent internal dictionary format (`{id: Object}`). This ensures the simulation logic works seamlessly regardless of which input file is used.

## 2. Summary of Approach
I adopted an **Object-Oriented Design** adhering to **SOLID principles** to ensure maintainability and clarity:
*   **Domain Modeling**: Created distinct classes (`Agent`, `Warehouse`, `Package`) to encapsulate state and behavior.
*   **Strategy Pattern**: Implemented an `AssignmentStrategy` interface. The current `NearestNeighborStrategy` can be easily swapped for more complex algorithms (e.g., genetic algorithms) without changing the simulation code.
*   **Separation of Concerns**: Divided the application into Data Loading, Strategy, Simulation Control, and Reporting layers.

## 3. Logic Assumptions
*   **Assignment**: Packages are assigned to the agent who is closest to the *Warehouse* (pickup point), based on the agent's *initial* position.
*   **Routing**: Agents deliver packages sequentially in the order they were assigned (which matches the input order in the JSON). They travel `Current -> Warehouse -> Dest`.
*   **Location Updates**: Agents do not return to a "home base". Their new start location for the next delivery is the destination of the previous one.
*   **Metric**: "Efficiency" is defined as `Total Distance / Packages Delivered`. A lower score implies higher efficiency (less travel per package).
*   **Tie-Breaking**: If two agents are equidistant, the one encountered first in the iteration order (usually determined by ID sorting or input order) is chosen.
