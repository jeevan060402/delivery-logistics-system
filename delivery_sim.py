"""
FastBox Delivery Simulator

ASSUMPTIONS:
1. Input Data: Handles both 'List' and 'Dict' styles for Warehouses/Agents to support all provided test cases.
2. Assignment: 'Nearest Neighbor' based on Agent's INITIAL location relative to the Warehouse.
3. Movement: Agent travels Current -> Warehouse -> Destination. Location updates to Destination after delivery.
4. Metric: 'Efficiency' = Total Distance / Packages Delivered. LOWER is better.
5. Dynamic Mode: Splits packages 50/50. Holds back the lexicographically last agent for the first batch.
"""
import json
import math
import sys
from dataclasses import dataclass
from typing import List, Dict, Protocol, Optional, Any

# --- Domain Models ---

@dataclass(frozen=True)
class Point:
    x: float
    y: float

    @staticmethod
    def from_list(coord: List[float]) -> 'Point':
        return Point(x=coord[0], y=coord[1])

    def distance_to(self, other: 'Point') -> float:
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)

@dataclass
class Warehouse:
    id: str
    location: Point

@dataclass
class Package:
    id: str
    warehouse_id: str
    destination: Point

class Agent:
    def __init__(self, agent_id: str, start_location: Point, warehouses: Dict[str, Warehouse]):
        self.id = agent_id
        self.location = start_location
        self.warehouses = warehouses
        self.assigned_packages: List[Package] = []
        self.total_distance: float = 0.0
        self.packages_delivered_count: int = 0

    def assign_package(self, package: Package):
        self.assigned_packages.append(package)

    def perform_deliveries(self):
        """
        Executes the delivery process for all assigned packages sequentially.
        Updates internal state (location, total_distance, count).
        """
        for pkg in self.assigned_packages:
            warehouse = self.warehouses.get(pkg.warehouse_id)
            if not warehouse:
                print(f"Warning: Warehouse {pkg.warehouse_id} not found for package {pkg.id}")
                continue

            # Trip 1: To Warehouse
            dist_to_warehouse = self.location.distance_to(warehouse.location)
            self.total_distance += dist_to_warehouse
            
            # Trip 2: To Destination
            dist_to_dest = warehouse.location.distance_to(pkg.destination)
            self.total_distance += dist_to_dest
            
            # Update State
            self.location = pkg.destination
            self.packages_delivered_count += 1

    @property
    def efficiency(self) -> float:
        if self.packages_delivered_count == 0:
            return 0.0
        return round(self.total_distance / self.packages_delivered_count, 2)

    def get_stats(self) -> Dict[str, Any]:
        return {
            "packages_delivered": self.packages_delivered_count,
            "total_distance": round(self.total_distance, 2),
            "efficiency": self.efficiency
        }

# --- Strategies ---

class AssignmentStrategy(Protocol):
    def assign(self, agents: Dict[str, Agent], packages: List[Package], warehouses: Dict[str, Warehouse]):
        """Distributes packages to agents."""
        ...

class NearestNeighborStrategy:
    """Assigns each package to the agent closest to the pickup warehouse."""
    
    def assign(self, agents: Dict[str, Agent], packages: List[Package], warehouses: Dict[str, Warehouse]):
        for pkg in packages:
            warehouse = warehouses.get(pkg.warehouse_id)
            if not warehouse:
                continue

            best_agent: Optional[Agent] = None
            min_dist = float('inf')

            for agent in agents.values():
                # We assume current agent location is the start location for assignment
                # If we wanted dynamic reassignment based on real-time location, that would be different.
                # The prompt implies pre-assignment based on initial state.
                dist = agent.location.distance_to(warehouse.location)
                if dist < min_dist:
                    min_dist = dist
                    best_agent = agent
            
            if best_agent:
                best_agent.assign_package(pkg)

# --- Data Loading ---

class DataLoader:
    """Handles the messy reality of inconsistent JSON formats."""
    
    @staticmethod
    def load(filepath: str) -> tuple[Dict[str, Warehouse], Dict[str, Agent], List[Package]]:
        with open(filepath, 'r') as f:
            data = json.load(f)

        warehouses = DataLoader._parse_warehouses(data.get("warehouses"))
        agents = DataLoader._parse_agents(data.get("agents"), warehouses) # Pass warehouses to Agent constructor? No, simpler.
        
        # Correction: Agents need access to Warehouse locations during simulation.
        # So we pass the warehouse dict to the Agent constructor later.
        # Let's just return the raw configs for Agents and construct them in the Controller.
        
        packages = DataLoader._parse_packages(data.get("packages"))
        
        # Instantiate Agents here to return clean Domain Objects?
        # Yes, but Agents need the Warehouse DICT.
        agent_objects = {}
        # Re-parsing agents to inject dependencies
        raw_agents = DataLoader._parse_raw_agents(data.get("agents"))
        for aid, loc in raw_agents.items():
            agent_objects[aid] = Agent(aid, loc, warehouses)

        return warehouses, agent_objects, packages

    @staticmethod
    def _parse_warehouses(data: Any) -> Dict[str, Warehouse]:
        warehouses = {}
        if isinstance(data, list):
            for item in data:
                w = Warehouse(item["id"], Point.from_list(item["location"]))
                warehouses[w.id] = w
        elif isinstance(data, dict):
            for wid, loc in data.items():
                warehouses[wid] = Warehouse(wid, Point.from_list(loc))
        return warehouses

    @staticmethod
    def _parse_raw_agents(data: Any) -> Dict[str, Point]:
        agents = {}
        if isinstance(data, list):
            for item in data:
                agents[item["id"]] = Point.from_list(item["location"])
        elif isinstance(data, dict):
            for aid, loc in data.items():
                agents[aid] = Point.from_list(loc)
        return agents

    @staticmethod
    def _parse_packages(data: Any) -> List[Package]:
        packages = []
        if isinstance(data, list):
            for item in data:
                # Handle key mismatch: "warehouse_id" vs "warehouse"
                wid = item.get("warehouse_id") or item.get("warehouse")
                packages.append(Package(
                    id=item["id"],
                    warehouse_id=wid,
                    destination=Point.from_list(item["destination"])
                ))
        return packages
    
    @staticmethod
    def _parse_agents(data: Any, warehouses: Dict[str, Warehouse]) -> Dict[str, Agent]:
        # Helper not strictly needed if we do it in load(), but cleaner.
        # We did it inline in load() for simplicity.
        pass

# --- Simulation Controller ---

class SimulationController:
    def __init__(self, data_loader: DataLoader, strategy: AssignmentStrategy):
        self.loader = data_loader
        self.strategy = strategy

    def run(self, filepath: str) -> Dict[str, Any]:
        try:
            warehouses, agents, packages = self.loader.load(filepath)
        except Exception as e:
            print(f"Failed to load data: {e}")
            sys.exit(1)

        # 1. Assign
        self.strategy.assign(agents, packages, warehouses)

        # 2. Simulate
        results = {}
        for agent in agents.values():
            agent.perform_deliveries()
            results[agent.id] = agent.get_stats()

        # 3. Report
        return self._generate_report(results)

    def run_dynamic_scenario(self, filepath: str) -> Dict[str, Any]:
        """
        Bonus: Simulates a new agent joining 'mid-day'.
        1. Start with N-1 agents.
        2. Assign first 50% of packages ('morning shift').
        3. Add the Nth agent.
        4. Assign remaining 50% of packages ('afternoon shift').
        """
        try:
            warehouses, agents, packages = self.loader.load(filepath)
        except Exception:
            sys.exit(1)
            
        if len(agents) < 2:
            print("Not enough agents for dynamic scenario.")
            return self.run(filepath)

        # Identify the "New" Agent (e.g., the last one sorted by ID)
        sorted_ids = sorted(agents.keys())
        new_agent_id = sorted_ids[-1]
        new_agent = agents.pop(new_agent_id)
        
        print(f"\n--- Dynamic Scenario Started ---")
        print(f"Morning Shift: Agents {list(agents.keys())} active.")
        print(f"Agent {new_agent_id} will join later.\n")

        # Split packages
        mid_point = len(packages) // 2
        morning_packages = packages[:mid_point]
        afternoon_packages = packages[mid_point:]

        # Assign Morning
        self.strategy.assign(agents, morning_packages, warehouses)
        
        # New Agent JOINS
        agents[new_agent_id] = new_agent
        print(f"*** MID-DAY UPDATE: Agent {new_agent_id} has joined the fleet! ***\n")

        # Assign Afternoon (considering ALL agents now)
        self.strategy.assign(agents, afternoon_packages, warehouses)

        # Simulate
        results = {}
        for agent in agents.values():
            agent.perform_deliveries()
            results[agent.id] = agent.get_stats()

        return self._generate_report(results)

    def _generate_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        report = results.copy()
        
        best_agent = None
        best_efficiency = float('inf')
        
        # Logic: Lowest "efficiency" number (Dist/Pkg) is best
        for agent_id, stats in results.items():
            if stats["packages_delivered"] > 0:
                if stats["efficiency"] < best_efficiency:
                    best_efficiency = stats["efficiency"]
                    best_agent = agent_id
        
        report["best_agent"] = best_agent
        return report

# --- Bonus Features ---

class CSVReporter:
    @staticmethod
    def export_best_agent(report: Dict[str, Any], filename: str = "top_performer.csv"):
        best_agent_id = report.get("best_agent")
        if not best_agent_id:
            return

        stats = report.get(best_agent_id)
        if not stats:
            return

        try:
            with open(filename, "w") as f:
                # Header
                f.write("AgentID,PackagesDelivered,TotalDistance,Efficiency\n")
                # Data
                f.write(f"{best_agent_id},{stats['packages_delivered']},{stats['total_distance']},{stats['efficiency']}\n")
            print(f"Top performer exported to {filename}")
        except IOError as e:
            print(f"Error writing CSV: {e}")

class AsciiVisualizer:
    def __init__(self, width: int = 50, height: int = 25):
        self.width = width
        self.height = height

    def render(self, agents: Dict[str, Agent], warehouses: Dict[str, Warehouse], packages: List[Package]):
        """
        Renders a snapshot of the initial state.
        Scale coordinates to fit the grid.
        Assuming max world coords roughly 0-100 based on input data.
        """
        grid = [[' ' for _ in range(self.width)] for _ in range(self.height)]
        
        # Determine bounds
        max_x = 100
        max_y = 100
        
        # Helper to scale
        def scale(pt: Point) -> tuple[int, int]:
            x = int((pt.x / max_x) * (self.width - 1))
            y = int((pt.y / max_y) * (self.height - 1))
            # Clamp
            x = max(0, min(x, self.width - 1))
            y = max(0, min(y, self.height - 1))
            return x, y

        # Plot Warehouses
        for w in warehouses.values():
            x, y = scale(w.location)
            grid[y][x] = 'W'

        # Plot Packages Dest
        for p in packages:
            x, y = scale(p.destination)
            if grid[y][x] == ' ':
                grid[y][x] = '.'

        # Plot Agents
        for a in agents.values():
            x, y = scale(a.location)
            grid[y][x] = 'A'

        print("\n--- Initial State Visualization ---")
        print("W: Warehouse, A: Agent, .: Package Dest")
        print("-" * (self.width + 2))
        for row in grid:
            print("|" + "".join(row) + "|")
        print("-" * (self.width + 2))


# --- Entry Point ---

def main():
    if len(sys.argv) < 2:
        print("Usage: python delivery_sim.py <input_file> [--dynamic]")
        sys.exit(1)

    filepath = sys.argv[1]
    is_dynamic = "--dynamic" in sys.argv
    
    # Initialize
    loader = DataLoader()
    strategy = NearestNeighborStrategy()
    controller = SimulationController(loader, strategy)
    
    # Load data specifically for visualization before simulation alters state
    try:
        warehouses, agents, packages = loader.load(filepath)
        # Visualization
        visualizer = AsciiVisualizer()
        visualizer.render(agents, warehouses, packages)
    except Exception:
        pass # Fail silently if viz fails, core logic is priority

    # Run Simulation
    if is_dynamic:
        report = controller.run_dynamic_scenario(filepath)
    else:
        report = controller.run(filepath)
    
    print(json.dumps(report, indent=4))
    
    # Save Report
    with open("report.json", "w") as f:
        json.dump(report, f, indent=4)
        
    # CSV Export
    CSVReporter.export_best_agent(report)

if __name__ == "__main__":
    main()
