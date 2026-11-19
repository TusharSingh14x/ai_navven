# AI Lab Evaluation: Task 3 - Map Coloring using CSP
**Assigned Roll Numbers:** $3n + 2$ ($2, 5, 8, 11, 14, 17, 20, \dots$)  
**Subject:** Artificial Intelligence Laboratory  

---

## 1. Problem Overview & Formulation

Map coloring is modeled as a **Constraint Satisfaction Problem (CSP)** defined by the triplet $\langle X, D, C \rangle$:

1. **Variables ($X$):**
   - **Part A (Australia):** 7 regions: $\text{WA, NT, SA, Q, NSW, V, T}$.
   - **Part B (India):** 28 States and 8 Union Territories (36 total administrative entities), or 28 mainland states.

2. **Domains ($D$):**
   - **Part A:** 3 colors: $\{\text{Red, Green, Blue}\}$.
   - **Part B:** 
     - Experiment 1: 3 colors: $\{\text{Red, Green, Blue}\}$.
     - Experiment 2: 4 colors: $\{\text{Red, Green, Blue, Yellow}\}$.

3. **Constraints ($C$):**
   - Binary inequality constraints: For any two adjacent regions $u$ and $v$ sharing a land border, $\text{Color}(u) \neq \text{Color}(v)$.

---

## 2. Heuristics & Propagation Mechanics

### 2.1 Minimum Remaining Values (MRV)
- Also called the **Most Constrained Variable** heuristic or "fail-first" heuristic.
- Selects the unassigned variable with the fewest legal values remaining in its domain:
  $$\text{MRV} = \arg\min_{v \in \text{Unassigned}} |\text{Domain}(v)|$$
- **Purpose:** Prunes branches early where choices are already severely restricted, reducing the effective branching factor near the top of the search tree.

### 2.2 Degree Heuristic (DH)
- Used as a **tie-breaker** when multiple variables have the same minimum domain size under MRV.
- Selects the variable that imposes constraints on the largest number of *unassigned* neighbors:
  $$\text{DH} = \arg\max_{v \in \text{Tied}} \sum_{u \in \text{Neighbors}(v)} [u \notin \text{Assignment}]$$
- **Purpose:** Quickly reduces the search space for the remaining unassigned variables.

### 2.3 Least Constraining Value (LCV)
- Once a variable is chosen, LCV orders its candidate domain values in order of preference.
- Evaluates candidate value $c$ by counting how many choices it eliminates from the domains of unassigned neighbors:
  $$\text{Cost}(c) = \sum_{u \in \text{Neighbors}(v), u \notin \text{Assignment}} [c \in \text{Domain}(u)]$$
- The value with the lowest conflict count is tried first.
- **Purpose:** Aims to maximize flexibility for remaining variables so the algorithm finds a solution without backtracking.

### 2.4 Forward Checking (FC)
- Whenever variable $X$ is assigned color $c$, forward checking immediately iterates through every unassigned neighbor $Y$ of $X$ and removes $c$ from $\text{Domain}(Y)$.
- If any neighbor's domain becomes empty ($\text{Domain}(Y) = \emptyset$), a **domain wipeout** is detected immediately.
- The algorithm aborts the branch and backtracks without wasting time exploring an already doomed subtree.

---

## 3. Part A: Australia Map Coloring (3 Colors)

### Adjacency Graph
- **WA:** NT, SA
- **NT:** WA, SA, Q
- **SA:** WA, NT, Q, NSW, V (degree 5)
- **Q:** NT, SA, NSW
- **NSW:** Q, SA, V
- **V:** SA, NSW
- **T:** (Island, degree 0)

### Step-by-Step Execution Trace

| Step | Selected Variable | Domain Size & Heuristic Reason | LCV Value Ordering | Forward Checking Pruning |
| :---: | :---: | :--- | :--- | :--- |
| **1** | **SA** | MRV tie (3 values), Degree Heuristic = 5 | Red, Green, Blue (all cost 5) $\rightarrow$ Pick **Red** | NT, Q, NSW, V, WA all prune **{Red}**. Domains reduced from 3 to 2 values. |
| **2** | **NT** | MRV tie (2 values), Degree Heuristic = 2 (WA, Q unassigned) | Green, Blue (both cost 2) $\rightarrow$ Pick **Green** | WA, Q prune **{Green}**. WA domain becomes {Blue}, Q domain becomes {Blue}. |
| **3** | **Q** | MRV tie (1 value: {Blue}), Degree Heuristic = 1 (NSW unassigned) | Blue (cost 1) $\rightarrow$ Pick **Blue** | NSW prunes **{Blue}**. NSW domain becomes {Green}. |
| **4** | **NSW** | MRV tie (1 value: {Green}), Degree Heuristic = 1 (V unassigned) | Green (cost 1) $\rightarrow$ Pick **Green** | V prunes **{Green}**. V domain becomes {Blue}. |
| **5** | **WA** | MRV tie (1 value: {Blue}), Degree Heuristic = 0 | Blue (cost 0) $\rightarrow$ Pick **Blue** | No unassigned neighbors affected. |
| **6** | **V** | MRV (1 value: {Blue}) | Blue (cost 0) $\rightarrow$ Pick **Blue** | No unassigned neighbors affected. |
| **7** | **T** | MRV (3 values: {Red, Green, Blue}), Island (degree 0) | Red, Green, Blue (all cost 0) $\rightarrow$ Pick **Red** | Final variable assigned. Search completes. |

### Part A Results Summary
- **Selection Order:** $\text{SA} \rightarrow \text{NT} \rightarrow \text{Q} \rightarrow \text{NSW} \rightarrow \text{WA} \rightarrow \text{V} \rightarrow \text{T}$
- **Total Assignments Tested:** 7
- **Total Backtracks:** 0
- **Final Coloring:**
  - $\text{SA} = \text{Red}$
  - $\text{NT} = \text{Green}$
  - $\text{Q} = \text{Blue}$
  - $\text{NSW} = \text{Green}$
  - $\text{WA} = \text{Blue}$
  - $\text{V} = \text{Blue}$
  - $\text{T} = \text{Red}$
- **Verification:** All 9 borders verified. No neighboring regions share the same color.

---

## 4. Part B: India Map Coloring (Generalization)

### Scope
- **Entities Included:** 28 States and 8 Union Territories (36 entities total).
- The program also supports evaluating on 28 States only.

### 4.1 Test 1: India Map with 3 Colors
- **Result:** **FAILED (Insufficient Colors)**
- **Number of Backtracks:** 33
- **Mathematical Justification:**
  - India cannot be colored with 3 colors because its adjacency graph contains an **odd wheel subgraph ($W_5$)**.
  - Consider **Madhya Pradesh (MP)** as the central hub.
  - MP shares land borders with:
    1. Gujarat (GJ)
    2. Rajasthan (RJ)
    3. Uttar Pradesh (UP)
    4. Chhattisgarh (CG)
    5. Maharashtra (MH)
  - These 5 neighboring states form an odd cycle of length 5 ($C_5$):
    $$\text{GJ} - \text{RJ} - \text{UP} - \text{CG} - \text{MH} - \text{GJ}$$
  - A cycle of odd length ($C_5$) requires at least 3 distinct colors.
  - Because MP is directly connected to all 5 states in this cycle, MP must have a color different from all of them.
  - Therefore, coloring $W_5$ requires at least $3 + 1 = 4$ colors.
  - Hence, a 3-coloring of the Indian map is mathematically impossible. The algorithm correctly explores all possibilities, encounters domain wipeouts, backtracks 33 times, and returns failure.

### 4.2 Test 2: India Map with 4 Colors
- **Result:** **SUCCESSFULLY SOLVED**
- **Colors Used:** Red, Green, Blue, Yellow
- **Number of Backtracks:** 0 (with MRV + DH + LCV + FC)
- **Total Assignments Tested:** 36 (equal to the number of variables)
- **Four Color Theorem Consistency:** By the Four Color Theorem (Appel & Haken, 1976), any planar map can be colored with at most 4 colors such that no two adjacent regions share the same color.

---

## 5. Visualizer & Presentation Features (Atlas Design System)

The visualizer ([map_coloring_visualizer.html](file:///Users/testaccount/Desktop/ai_h/map_coloring_visualizer.html)) implements an authentic cartographic aesthetic adhering to the antislop UI guidelines:

1. **Atlas-Grade Geographical Vector Paths:**
   - Real SVG boundary paths with organic coastlines for Australia (e.g. Shark Bay, Great Australian Bight, Spencer Gulf, Cape York).
   - Contiguous geographic boundary paths for all 36 Indian states and Union Territories (e.g. the Kashmir crown, Saurashtra peninsula in Gujarat, southern peninsula down to Kanyakumari, and the northeastern frontier).
2. **Dual-Mode Map Rendering:**
   - **Geographic Territory Map View:** Regions fill with warm cartographic ink fills as assignments are made.
   - **Topological Network View:** Nodes sized by degree with border constraint edges.
3. **Live Recursion Call Stack Breadcrumb:**
   - Shows the active search path above the map (`Root ➔ [SA: Red] ➔ [NT: Green] ➔ ...`).
   - When backtracked, the failed assignment flashes red with `[❌ Reverted]` and unwinds up the call stack.
4. **Domain Wipeout Alerts:**
   - When Forward Checking leaves a neighbor with 0 legal colors, the affected territory glows in pulsing crimson with an animated warning icon.
   - The conflicting boundary edge pulses with a thick dashed red warning beam.
5. **Interactive Backtrack History Log:**
   - Full scrollable list of all backtracks and their exact triggers.
   - Clicking any backtrack in the list scrubs the visualizer directly to that moment in time.
6. **The 5-Wheel Bottleneck Callout:**
   - Interactive button on India (3 Colors) isolating the Madhya Pradesh hub and surrounding 5-state cycle.
7. **Complete Offline Operation:**
   - Zero external CDNs or network requests; 100% self-contained in 230 KB.

---

## 6. How to Run the Program

```bash
# 1. Interactive CLI Menu
python3 map_coloring_csp.py

# 2. Automated Evaluation Suite (Executes Part A, Part B, and updates visualizer)
python3 map_coloring_csp.py --all

# 3. Open the Interactive Visualizer in your Browser
open map_coloring_visualizer.html
```
