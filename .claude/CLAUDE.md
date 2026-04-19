# Public Transport Network Simulation & Optimization

## Project Overview

This project simulates the behavior of public transport networks (primarily trains and metros) to enable optimization of schedules, testing of routing logic, generation of performance metrics, and future integration with reinforcement learning (RL) algorithms.

## Core Objectives

1. **Realistic Simulation**: Model the complex dynamics of public transport operations including passenger flows, train movements, and network constraints
2. **Optimization Platform**: Provide a testbed for evaluating different scheduling strategies, frequency adjustments, and routing algorithms
3. **Metrics Generation**: Produce actionable insights on network performance (wait times, crowding, reliability, etc.)
4. **RL Integration (Future)**: Create environment interfaces compatible with RL frameworks for autonomous optimization

## Key Design Decisions (Locked In)

### 1. **Discrete Time Simulation**
- Time advances in fixed steps (e.g., 1 second, 10 seconds)
- Simpler to implement and reason about than event-driven
- All state updates happen at discrete time ticks
- Trade-off: Less efficient than event-driven, but easier to debug and extend

### 2. **Individual Passenger Tracking**
- Each passenger is a distinct entity with their own state
- Enables detailed metrics (individual journey times, wait times)
- Can aggregate statistics from individual data
- Future: Could optimize to aggregate flows if performance becomes an issue

### 3. **Stochastic Model**
- Include randomness in passenger arrivals
- Can add randomness to other aspects (dwell times, etc.) later
- Use seed control for reproducibility in experiments
- More realistic than pure deterministic models

### 4. **Simple Train Physics (Initially)**
- **Constant speed**: Trains travel at fixed speed between stations
- No acceleration/deceleration modeling initially
- No complex dispatch logic initially
- Can add complexity incrementally (variable speeds, delays, etc.)

### 5. **Python Implementation**
- Rapid development and prototyping
- Excellent ecosystem for optimization, RL, and visualization
- Easy to iterate and refine
- Performance optimizations (NumPy, Cython) available if needed later

## System Architecture

### 1. Infrastructure Layer

**Stations**
- Unique identifier and name
- Spatial coordinates (x, y) for visualization
- Capacity constraints (platform capacity)
- Properties: transfer hub flag, facilities
- Maintains queues of waiting passengers (by destination/line)

**Lines**
- Named route (e.g., "Red Line", "Line 1")
- Ordered sequence of stations (list of station IDs)
- Can be circular (loop line) or linear
- Properties: direction(s) of operation
- Multiple lines can share stations (transfer points)

**Network**
- Graph representation: stations as nodes, line segments as edges
- Edge properties: travel time between adjacent stations (distance/speed)
- Supports pathfinding algorithms (shortest path, multi-modal routing)
- Configuration loaded from files (JSON/YAML)

### 2. Operations Layer

**Trains**
- Operates on a specific line
- Properties:
  - Current position (at station, between stations, or progress along segment)
  - Direction (forward/backward along line)
  - Passenger capacity (total seats/standing room)
  - Current passenger load (list of passengers on board)
  - Speed (constant for now)
- State: at_station, traveling, boarding_alighting

**Schedules**
- **Simple approach initially**: Fixed headway (time between trains)
- Trains spawn at line start at regular intervals
- Future: Complex timetables, time-of-day variations

**Train Operations (Simple Initial Model)**
- Travel at constant speed between stations
- Arrive at station
- Dwell time = fixed base time + time proportional to passengers boarding/alighting
- Depart when dwell complete
- No collision detection initially (assume perfect spacing)

### 3. Passenger Demand Layer

**Passengers**
- Unique identifier
- Origin station and destination station (OD pair)
- Spawn time (when they arrive at origin station)
- State: waiting, on_train, transferring, arrived, abandoned
- Journey tracking: spawn time, board time(s), alight time(s), arrival time
- Current location (station or train)

**Demand Generation**
- **OD Matrix**: Probability distribution of origin-destination pairs
- **Arrival Process**: Stochastic arrivals at each station
  - Time-varying arrival rates (peak vs off-peak)
  - Poisson process or other distributions
  - Configurable per station and time of day

**Passenger Routing**
- **Path Planning**: At spawn, determine route from origin to destination
  - Initially: Shortest path by travel time
  - Can include transfers
  - Future: Consider crowding, reliability, preferences
- **Line Selection**: If multiple lines serve route, choose based on criteria
  - Initially: First available train
  - Future: Prefer less crowded, minimize transfers
- **Transfer Behavior**:
  - Alight at transfer station
  - Walk to correct platform (transfer time penalty)
  - Wait for next line

**Boarding Behavior (Simple Initial Model)**
- Passengers board first arriving train on their planned route
- Board if train has capacity
- If train full, wait for next train
- Future: Balking (abandon trip after too much waiting)

### 4. Simulation Engine

**Time Management**
- Discrete time steps (e.g., Δt = 1 second or 10 seconds)
- Global simulation clock
- Simulation runs from t=0 to t=T_max

**Simulation Loop (Each Time Step)**
1. Generate new passenger arrivals (stochastic)
2. Update train positions
   - If traveling: advance position toward next station
   - If at station: handle boarding/alighting, update dwell timer
3. Handle passenger boarding (passengers attempt to board available trains)
4. Handle passenger alighting (passengers exit at their target station)
5. Update passenger states (waiting → on_train → arrived)
6. Collect metrics
7. Advance time: t = t + Δt

**State Tracking**
- List of all trains with positions and passenger loads
- List of all passengers with states and locations
- Station queues (passengers waiting at each station)
- Historical data for metrics

**Configuration Loading**
- Network topology from file (stations, lines, connections)
- Schedule parameters (headway, train capacity, speed)
- Demand scenario (OD matrix, arrival rates)
- Simulation parameters (duration, time step, random seed)

### 5. Routing & Pathfinding

**Graph Representation**
- Use NetworkX or similar for graph operations
- Nodes = stations, Edges = direct line connections
- Edge weights = travel time between stations

**Pathfinding Algorithms**
- **Dijkstra's shortest path** (by travel time)
- Find sequence of lines and stations from origin to destination
- Identify transfer stations
- Initially: Static paths computed at passenger spawn
- Future: Dynamic routing based on real-time conditions

### 6. Optimization Layer (Future Focus)

**What to Optimize**
- Train headway (frequency) per line
- Starting times (schedule synchronization)
- Fleet size (number of trains per line)
- Routing advice to passengers

**Optimization Approaches**
- Exhaustive search for small parameter spaces
- Heuristics and metaheuristics
- Simulation-based optimization (run many scenarios, compare metrics)
- Gradient-free optimization (e.g., CMA-ES, Bayesian optimization)
- RL-based optimization (future)

**Evaluation**
- Run simulation with candidate solution
- Compute objective function from metrics
- Compare against baseline

### 7. Metrics & Analytics

**Passenger Experience Metrics**
- **Wait time**: Time from arrival at station to boarding
- **Journey time**: Total time from origin arrival to destination arrival
- **Transfer count**: Number of transfers per passenger
- **Completion rate**: % of passengers who reach destination (vs abandon)
- **Crowding**: Average load factor experienced

**Operational Metrics**
- **Train load factor**: (Passengers on train) / (Capacity)
- **Service frequency**: Actual headway achieved
- **Fleet utilization**: Average passengers per train

**Network Metrics**
- **Throughput**: Passengers delivered per hour
- **Station congestion**: Queue lengths at stations

**Statistical Summaries**
- Mean, median, 95th percentile for wait time and journey time
- Distribution plots

**Outputs**
- Time series data (metrics over time)
- Summary statistics per simulation run
- Visualization: animations, plots, heatmaps

### 8. Reinforcement Learning Integration (Future)

**Environment Interface (Gymnasium Compatible)**
- **State**: Current network state (train positions, passenger queues, time)
- **Actions**: Scheduling decisions (adjust headway, dispatch timing)
- **Rewards**: Negative of average passenger wait time, or composite metric
- **Episodes**: One simulation run

**RL Use Cases**
- Adaptive headway control
- Real-time dispatching
- Long-term schedule optimization

## Project Structure

```
public_transport_optimization/
├── src/
│   ├── core/
│   │   ├── station.py          # Station class
│   │   ├── line.py             # Line class
│   │   ├── network.py          # Network graph and pathfinding
│   │   ├── train.py            # Train class and movement logic
│   │   └── passenger.py        # Passenger class and behavior
│   ├── simulation/
│   │   ├── simulator.py        # Main simulation loop
│   │   ├── time_manager.py     # Time stepping logic
│   │   └── state.py            # Global state management
│   ├── demand/
│   │   ├── od_matrix.py        # Origin-destination demand
│   │   ├── arrival_process.py  # Stochastic arrival generation
│   │   └── routing.py          # Passenger pathfinding
│   ├── optimization/
│   │   ├── objective.py        # Objective function definitions
│   │   ├── algorithms/         # Optimization algorithms
│   │   └── evaluator.py        # Scenario evaluation
│   ├── metrics/
│   │   ├── collector.py        # Metrics collection during simulation
│   │   ├── analyzer.py         # Post-simulation analysis
│   │   └── visualizer.py       # Plotting and visualization
│   └── utils/
│       ├── config_loader.py    # Load YAML/JSON configs
│       └── random_state.py     # Seeded random number generation
├── configs/
│   ├── networks/
│   │   ├── simple_line.yaml    # Single line, few stations
│   │   ├── two_lines.yaml      # Two lines with transfer
│   │   └── metro_network.yaml  # Complex multi-line network
│   ├── schedules/
│   │   └── base_schedule.yaml  # Headway and train parameters
│   └── demand/
│       ├── uniform_demand.yaml # Uniform OD distribution
│       └── peak_demand.yaml    # Rush hour patterns
├── tests/
│   ├── test_station.py
│   ├── test_train.py
│   ├── test_passenger.py
│   ├── test_network.py
│   └── test_simulation.py
├── experiments/
│   ├── baseline.py             # Run baseline scenarios
│   ├── optimize_headway.py     # Headway optimization experiment
│   └── results/                # Experiment outputs
├── notebooks/
│   ├── exploratory.ipynb       # Data exploration
│   └── visualization.ipynb     # Results visualization
├── requirements.txt
├── README.md
└── .claude/
    └── claude_instructions.md  # This file
```

## Development Phases

### Phase 1: Minimal Viable Simulation ⭐ START HERE
**Goal**: Simulate one train on one line with passengers

Components:
- Station class (basic)
- Line class (ordered list of stations)
- Train class (position, capacity, passenger list)
- Passenger class (origin, destination, state)
- Simple network (single line)
- Discrete time simulator
- Constant speed train movement
- Random passenger arrivals (simple Poisson process)
- Basic metrics (wait time, journey time)

**Validation**: Run toy scenario (5 stations, 1 train, 50 passengers) and compute metrics

### Phase 2: Multi-line Network with Transfers
- Network graph (multiple lines, shared stations)
- Pathfinding (Dijkstra shortest path)
- Transfer logic (alight, switch line, board)
- Multiple trains per line
- Enhanced metrics (transfers, crowding)

**Validation**: Two-line network with transfer station

### Phase 3: Realistic Demand Patterns
- OD matrix (configurable demand patterns)
- Time-varying arrival rates (peak/off-peak)
- Multiple demand scenarios
- Capacity constraints and queuing

**Validation**: Compare different demand patterns, observe realistic behaviors

### Phase 4: Optimization Framework
- Parameterize schedules (headway as variable)
- Objective function (minimize average wait time)
- Grid search or simple optimization
- Scenario comparison tools

**Validation**: Show improved metrics with optimized schedule vs. baseline

### Phase 5: Advanced Features (Future)
- Disruptions (delays, closures)
- Advanced passenger behavior (balking, crowding avoidance)
- Real-time adaptive policies
- RL environment interface

## Key Implementation Details

### Train Movement (Constant Speed Model)
```
At each time step:
- If train is traveling between stations:
  - progress += speed * dt
  - if progress >= distance_to_next:
    - arrive at next station
    - set state = at_station
    - set dwell_timer = base_dwell_time
- If train is at station:
  - handle boarding/alighting
  - dwell_timer -= dt
  - if dwell_timer <= 0:
    - depart to next station
    - set state = traveling
```

### Passenger Arrivals (Poisson Process)
```
At each time step:
- For each station:
  - lambda = arrival_rate[station][current_time]
  - num_arrivals = Poisson(lambda * dt)
  - For each arrival:
    - sample destination from OD matrix
    - create passenger (origin=station, destination=sampled)
    - compute route (pathfinding)
    - add to station waiting queue
```

### Boarding Logic
```
When train arrives at station:
- Get passengers waiting for this train's line (on their route)
- Sort by arrival time (FIFO)
- For each passenger:
  - if train has capacity:
    - board passenger (remove from queue, add to train)
  - else:
    - passenger stays in queue
```

### Alighting Logic
```
When train arrives at station:
- Check passengers on train
- For each passenger:
  - if current_station == next_station_on_route:
    - alight passenger
    - if current_station == final_destination:
      - mark passenger as arrived
    - else:
      - mark passenger as transferring
      - add to waiting queue for next line
```

## Dependencies & Libraries

**Core**
- Python 3.10+
- NumPy (numerical operations, random number generation)
- Pandas (data handling, metrics tables)
- NetworkX (graph representation, pathfinding)

**Configuration**
- PyYAML or pydantic (config loading and validation)

**Visualization**
- Matplotlib (basic plots)
- Seaborn (statistical visualizations)
- Plotly (interactive plots, animations)

**Optimization (Future)**
- SciPy (optimization algorithms)
- scikit-optimize (Bayesian optimization)

**RL (Future)**
- Gymnasium (environment interface)
- Stable-Baselines3 (RL algorithms)

**Testing**
- pytest
- hypothesis (property-based testing)

## Testing Strategy

1. **Unit Tests**: Each class in isolation
   - Station: add/remove passengers
   - Train: movement, boarding, alighting
   - Passenger: state transitions
   - Network: pathfinding correctness

2. **Integration Tests**: Simulation scenarios
   - Single train, single passenger (end-to-end)
   - Verify passenger reaches destination
   - Check metric calculations

3. **Validation Tests**: Known solutions
   - Simple scenarios with hand-calculated expected results
   - Conservation laws (passengers in = passengers out)

4. **Regression Tests**: Ensure changes don't break existing functionality

## Configuration File Examples

### Network Config (YAML)
```yaml
stations:
  - id: S1
    name: "Central Station"
    x: 0
    y: 0
  - id: S2
    name: "North Station"
    x: 0
    y: 10

lines:
  - id: L1
    name: "Red Line"
    stations: [S1, S2, S3]
    speed: 10  # units per second
```

### Schedule Config
```yaml
lines:
  L1:
    headway: 300  # seconds between trains
    capacity: 100  # passengers per train
```

### Demand Config
```yaml
arrival_rates:
  S1: 0.5  # passengers per second
  S2: 0.3

od_matrix:
  S1:
    S2: 0.4
    S3: 0.6
  S2:
    S1: 0.5
    S3: 0.5
```

## Metrics to Track

### Individual Passenger
- Spawn time
- First board time → wait_time = first_board_time - spawn_time
- Arrival time → journey_time = arrival_time - spawn_time
- Number of transfers
- Crowding experienced (average load factor on trains used)

### Aggregate (Across All Passengers)
- Mean/median/95th percentile wait time
- Mean/median/95th percentile journey time
- Average transfers
- Completion rate

### System
- Train load factors over time
- Station queue lengths over time
- Throughput (passengers arriving per hour)

## Success Criteria for Phase 1

- Simulate a single line with 3-5 stations
- 1-3 trains on the line
- 50-100 passengers with random arrivals and destinations
- Passengers board trains, travel, and alight correctly
- Compute basic metrics: average wait time, average journey time
- Visualization: train positions over time, passenger states
- Reproducible with random seed control

## Notes for Claude

- **Start minimal**: Get Phase 1 working before adding complexity
- **Test frequently**: Write tests alongside implementation
- **Keep it simple**: Resist urge to over-engineer early
- **Validate logic**: Manually trace through simple scenarios to ensure correctness
- **Use type hints**: Python type annotations for clarity
- **Document assumptions**: Comment any simplifications or assumptions in code
- **Configuration-driven**: Avoid hardcoding parameters; use config files
- **Think about RL future**: Design state representation with RL in mind, but don't implement yet

## Evolution Path

This project should start simple and grow incrementally:
1. **Now**: Single line, constant speed, simple arrivals, basic metrics
2. **Next**: Multiple lines, transfers, better demand models
3. **Then**: Optimization algorithms, advanced metrics
4. **Future**: RL integration, disruptions, advanced realism

The goal is to have a working system quickly that can be refined and extended based on what's learned from initial experiments.
