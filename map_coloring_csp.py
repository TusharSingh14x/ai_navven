#!/usr/bin/env python3
"""
AI Lab Evaluation: Task 3 - Map Coloring using CSP
Assigned Roll Numbers: 3n + 2 (2, 5, 8, 11, ...)

Algorithms Implemented:
- Recursive Backtracking Search
- Minimum Remaining Values (MRV) Heuristic
- Degree Heuristic (as MRV Tie-Breaker)
- Least Constraining Value (LCV) Heuristic
- Forward Checking (FC) with domain pruning, wipeout detection, and domain restoration
"""

import sys
import json
import copy
from collections import defaultdict

import json
import sys
from collections import defaultdict

# ---------------------------------------------------------------------------
# Core CSP Implementation with Complete Step & Backtrack Tracing
# ---------------------------------------------------------------------------
class MapColoringCSP:
    def __init__(self, variables, domains, neighbors):
        self.variables = list(variables)
        self.initial_domains = {v: list(domains[v]) for v in self.variables}
        self.neighbors = {v: set(neighbors.get(v, [])) for v in self.variables}

        for u in self.variables:
            for v in list(self.neighbors[u]):
                if v in self.neighbors:
                    self.neighbors[v].add(u)

        self.backtracks = 0
        self.assignments_count = 0
        self.timeline = []
        self.call_stack = []
        self.selection_order = []

    def select_unassigned_variable(self, assignment, domains):
        unassigned = [v for v in self.variables if v not in assignment]
        min_len = min(len(domains[v]) for v in unassigned)
        candidates = [v for v in unassigned if len(domains[v]) == min_len]

        def remaining_degree(v):
            return sum(1 for n in self.neighbors[v] if n not in assignment)

        if len(candidates) == 1:
            return candidates[0], f"MRV (domain size = {min_len})"
        else:
            chosen = max(candidates, key=remaining_degree)
            deg = remaining_degree(chosen)
            return chosen, f"MRV tie ({min_len} values) broken by Degree Heuristic (unassigned degree = {deg})"

    def order_domain_values(self, var, assignment, domains):
        unassigned_nbrs = [n for n in self.neighbors[var] if n not in assignment]

        def conflict_count(val):
            return sum(1 for n in unassigned_nbrs if val in domains[n])

        sorted_values = sorted(domains[var], key=conflict_count)
        lcv_details = [(val, conflict_count(val)) for val in sorted_values]
        return sorted_values, lcv_details

    def forward_check(self, var, val, assignment, domains):
        pruned = defaultdict(list)
        wipeout_nbr = None
        for neighbor in self.neighbors[var]:
            if neighbor not in assignment:
                if val in domains[neighbor]:
                    domains[neighbor].remove(val)
                    pruned[neighbor].append(val)
                    if len(domains[neighbor]) == 0:
                        wipeout_nbr = neighbor
                        return False, pruned, wipeout_nbr
        return True, pruned, None

    def restore_domains(self, domains, pruned):
        for neighbor, values in pruned.items():
            domains[neighbor].extend(values)

    def solve(self):
        self.backtracks = 0
        self.assignments_count = 0
        self.timeline = []
        self.call_stack = []
        self.selection_order = []
        current_domains = {v: list(self.initial_domains[v]) for v in self.variables}
        assignment = {}

        # Frame 0: Init
        self.timeline.append({
            "step": 0,
            "action": "init",
            "var": None,
            "val": None,
            "reason": "Initial state: All variables unassigned with full legal domains.",
            "lcv": [],
            "assignment": dict(assignment),
            "domains": {k: list(v) for k, v in current_domains.items()},
            "pruned": {},
            "backtrack_num": 0,
            "wipeout_var": None,
            "call_stack": []
        })

        res = self._backtrack(assignment, current_domains)
        return res

    def _backtrack(self, assignment, domains):
        if len(assignment) == len(self.variables):
            return assignment

        var, var_reason = self.select_unassigned_variable(assignment, domains)
        if var not in self.selection_order:
            self.selection_order.append(var)
        ordered_values, lcv_details = self.order_domain_values(var, assignment, domains)

        for val in ordered_values:
            self.assignments_count += 1
            assignment[var] = val
            self.call_stack.append({"var": var, "val": val})

            success, pruned, wipeout_nbr = self.forward_check(var, val, assignment, domains)

            self.timeline.append({
                "step": len(assignment),
                "action": "assign",
                "var": var,
                "val": val,
                "reason": var_reason,
                "lcv": lcv_details,
                "assignment": dict(assignment),
                "domains": {k: list(v) for k, v in domains.items()},
                "pruned": {k: list(v) for k, v in pruned.items()},
                "success": success,
                "backtrack_num": self.backtracks,
                "wipeout_var": wipeout_nbr,
                "call_stack": list(self.call_stack)
            })

            if success:
                sub_res = self._backtrack(assignment, domains)
                if sub_res is not None:
                    return sub_res

            # Backtrack
            self.backtracks += 1
            del assignment[var]
            if self.call_stack and self.call_stack[-1]["var"] == var:
                self.call_stack.pop()
            self.restore_domains(domains, pruned)

            failure_reason = f"Domain wipeout on neighbor '{wipeout_nbr}' (0 legal colors remaining)" if wipeout_nbr else "Subtree search exhausted without a valid coloring"

            self.timeline.append({
                "step": len(assignment),
                "action": "backtrack",
                "var": var,
                "val": val,
                "reason": f"Backtrack #{self.backtracks}: Undoing {var} = {val}. Reason: {failure_reason}. Restored pruned colors.",
                "lcv": lcv_details,
                "assignment": dict(assignment),
                "domains": {k: list(v) for k, v in domains.items()},
                "pruned": {k: list(v) for k, v in pruned.items()},
                "success": False,
                "backtrack_num": self.backtracks,
                "wipeout_var": wipeout_nbr,
                "call_stack": list(self.call_stack)
            })

        return None

    def verify_solution(self, assignment):
        if assignment is None:
            return False, ["No assignment provided (None)."]
        if len(assignment) != len(self.variables):
            return False, [f"Incomplete assignment ({len(assignment)}/{len(self.variables)} variables)."]

        conflicts = []
        for u in self.variables:
            for v in self.neighbors[u]:
                if u < v:
                    if assignment[u] == assignment[v]:
                        conflicts.append(f"Border Conflict: {u} and {v} both have {assignment[u]}")
        return (len(conflicts) == 0), conflicts


# ---------------------------------------------------------------------------
# Australia Map Definitions & True Geographic Paths
# ---------------------------------------------------------------------------
AUSTRALIA_REGIONS = ["WA", "NT", "SA", "Q", "NSW", "V", "T"]
AUSTRALIA_NAMES = {
    "WA": "Western Australia", "NT": "Northern Territory", "SA": "South Australia",
    "Q": "Queensland", "NSW": "New South Wales", "V": "Victoria", "T": "Tasmania"
}
AUSTRALIA_NEIGHBORS = {
    "WA": ["NT", "SA"],
    "NT": ["WA", "SA", "Q"],
    "SA": ["WA", "NT", "Q", "NSW", "V"],
    "Q": ["NT", "SA", "NSW"],
    "NSW": ["Q", "SA", "V"],
    "V": ["SA", "NSW"],
    "T": []
}

aus_geo_paths = {
    "WA": "M 250,115 C 215,85 175,95 145,140 C 95,190 65,240 45,290 C 45,340 60,405 75,470 C 85,510 120,525 175,505 C 210,485 235,465 250,450 L 250,115 Z",
    "NT": "M 250,115 C 270,75 305,65 340,75 C 370,105 385,140 375,190 C 370,225 380,240 380,250 L 380,300 L 250,300 L 250,115 Z",
    "SA": "M 250,300 L 380,300 L 430,300 L 430,345 L 430,430 L 430,510 C 400,490 380,470 370,455 C 355,420 345,440 330,470 C 290,465 265,455 250,450 L 250,300 Z",
    "Q": "M 380,250 C 400,255 425,225 440,160 C 455,100 465,55 465,55 C 480,115 510,180 540,245 C 570,310 595,365 605,410 C 608,425 610,430 610,430 L 430,345 L 430,300 L 380,300 L 380,250 Z",
    "NSW": "M 430,345 L 610,430 C 615,465 608,505 595,535 C 580,555 565,575 550,595 L 430,430 L 430,345 Z",
    "V": "M 430,430 L 550,595 C 530,610 510,615 490,600 C 465,575 445,550 430,510 L 430,430 Z",
    "T": "M 480,635 C 495,620 535,620 545,635 C 555,655 545,680 515,695 C 485,680 475,655 480,635 Z"
}

aus_centroids = {
    "WA": [150, 310], "NT": [315, 185], "SA": [340, 375],
    "Q": [485, 235], "NSW": [520, 475], "V": [480, 560], "T": [512, 660]
}


# ---------------------------------------------------------------------------
# India Map Definitions & Contiguous Geographic Paths (28 States + 8 UTs)
# ---------------------------------------------------------------------------
INDIA_STATES_28 = [
    "AP", "AR", "AS", "BR", "CG", "GA", "GJ", "HR", "HP", "JH",
    "KA", "KL", "MP", "MH", "MN", "ML", "MZ", "NL", "OD", "PB",
    "RJ", "SK", "TN", "TS", "TR", "UP", "UK", "WB"
]

INDIA_STATE_NAMES = {
    "AP": "Andhra Pradesh", "AR": "Arunachal Pradesh", "AS": "Assam", "BR": "Bihar",
    "CG": "Chhattisgarh", "GA": "Goa", "GJ": "Gujarat", "HR": "Haryana",
    "HP": "Himachal Pradesh", "JH": "Jharkhand", "KA": "Karnataka", "KL": "Kerala",
    "MP": "Madhya Pradesh", "MH": "Maharashtra", "MN": "Manipur", "ML": "Meghalaya",
    "MZ": "Mizoram", "NL": "Nagaland", "OD": "Odisha", "PB": "Punjab",
    "RJ": "Rajasthan", "SK": "Sikkim", "TN": "Tamil Nadu", "TS": "Telangana",
    "TR": "Tripura", "UP": "Uttar Pradesh", "UK": "Uttarakhand", "WB": "West Bengal",
    "DL": "Delhi (UT)", "JK": "Jammu and Kashmir (UT)", "LA": "Ladakh (UT)",
    "CH": "Chandigarh (UT)", "PY": "Puducherry (UT)",
    "DNHDD": "Dadra & Nagar Haveli and Daman & Diu (UT)",
    "AN": "Andaman and Nicobar Islands (UT)", "LD": "Lakshadweep (UT)"
}

INDIA_STATE_NEIGHBORS = {
    "AP": ["TN", "KA", "TS", "OD", "CG"],
    "AR": ["AS", "NL"],
    "AS": ["WB", "AR", "NL", "MN", "MZ", "TR", "ML"],
    "BR": ["UP", "JH", "WB"],
    "CG": ["MP", "UP", "JH", "OD", "AP", "TS", "MH"],
    "GA": ["MH", "KA"],
    "GJ": ["RJ", "MP", "MH"],
    "HR": ["PB", "HP", "RJ", "UP"],
    "HP": ["PB", "HR", "UK", "UP"],
    "JH": ["BR", "UP", "CG", "OD", "WB"],
    "KA": ["GA", "MH", "TS", "AP", "TN", "KL"],
    "KL": ["KA", "TN"],
    "MP": ["RJ", "UP", "CG", "MH", "GJ"],
    "MH": ["GJ", "MP", "CG", "TS", "KA", "GA"],
    "MN": ["NL", "AS", "MZ"],
    "ML": ["AS"],
    "MZ": ["AS", "MN", "TR"],
    "NL": ["AR", "AS", "MN"],
    "OD": ["WB", "JH", "CG", "AP"],
    "PB": ["HP", "HR", "RJ"],
    "RJ": ["PB", "HR", "UP", "MP", "GJ"],
    "SK": ["WB"],
    "TN": ["KL", "KA", "AP"],
    "TS": ["MH", "CG", "AP", "KA"],
    "TR": ["AS", "MZ"],
    "UP": ["UK", "HP", "HR", "RJ", "MP", "CG", "JH", "BR"],
    "UK": ["HP", "UP"],
    "WB": ["OD", "JH", "BR", "SK", "AS"]
}

INDIA_UTS = ["DL", "JK", "LA", "CH", "PY", "DNHDD", "AN", "LD"]
INDIA_UT_NEIGHBORS = {
    "DL": ["HR", "UP"],
    "JK": ["LA", "HP", "PB"],
    "LA": ["JK", "HP"],
    "CH": ["PB", "HR"],
    "PY": ["TN", "AP", "KL"],
    "DNHDD": ["GJ", "MH"],
    "AN": [],
    "LD": []
}

def build_india_graph(include_uts=True):
    variables = list(INDIA_STATES_28)
    neighbors = {k: list(v) for k, v in INDIA_STATE_NEIGHBORS.items()}
    if include_uts:
        variables.extend(INDIA_UTS)
        for ut in INDIA_UTS:
            neighbors[ut] = list(INDIA_UT_NEIGHBORS.get(ut, []))
        for ut, ut_nbrs in INDIA_UT_NEIGHBORS.items():
            for nbr in ut_nbrs:
                if nbr in neighbors and ut not in neighbors[nbr]:
                    neighbors[nbr].append(ut)
    return variables, neighbors

ind_geo_paths = {
    "LA": "M 280,30 C 315,25 365,30 405,50 C 420,75 410,115 385,130 L 315,130 C 300,95 285,60 280,30 Z",
    "JK": "M 225,55 C 255,40 280,30 280,30 C 285,60 300,95 315,130 L 265,145 C 235,145 220,115 210,85 Z",
    "HP": "M 265,145 L 315,130 L 385,130 L 370,175 L 305,185 L 265,180 Z",
    "PB": "M 210,135 L 265,145 L 265,180 L 255,215 L 205,205 C 195,175 200,150 210,135 Z",
    "CH": "M 255,170 L 270,170 L 270,185 L 255,185 Z",
    "UK": "M 370,175 L 435,160 C 445,190 425,225 390,225 L 335,225 L 305,185 Z",
    "HR": "M 255,215 L 265,180 L 305,185 L 335,225 L 305,275 L 245,265 Z",
    "DL": "M 295,235 L 315,235 L 315,255 L 295,255 Z",
    "RJ": "M 140,215 C 175,200 205,205 245,265 L 305,275 L 285,340 C 240,360 210,380 185,340 C 145,330 120,275 140,215 Z",
    "GJ": "M 140,335 C 175,345 185,340 185,340 C 210,380 200,410 175,415 C 140,430 95,410 85,365 C 80,340 105,330 140,335 Z",
    "DNHDD": "M 165,415 L 180,415 L 180,430 L 165,430 Z",
    "UP": "M 335,225 L 390,225 C 445,235 485,255 495,295 L 435,340 C 375,345 335,325 305,275 Z",
    "MP": "M 285,340 L 435,340 C 455,385 435,420 385,420 C 335,430 295,410 255,415 C 235,385 255,360 285,340 Z",
    "CG": "M 435,340 L 475,340 L 465,475 C 435,485 415,465 415,440 L 385,420 C 435,420 455,385 435,340 Z",
    "BR": "M 495,295 C 545,285 570,300 565,340 L 485,350 L 435,340 Z",
    "JH": "M 485,350 L 565,340 C 565,380 545,415 505,415 L 465,415 L 475,340 Z",
    "OD": "M 465,415 L 505,415 C 545,425 550,470 515,510 C 475,525 450,490 465,475 Z",
    "WB": "M 565,300 C 585,275 600,285 595,330 C 595,380 575,430 550,445 L 545,415 C 565,380 565,340 565,300 Z",
    "SK": "M 575,255 L 600,255 L 595,285 L 575,285 Z",
    "AR": "M 635,210 C 695,195 765,225 760,270 L 705,270 C 685,245 655,235 635,210 Z",
    "AS": "M 605,275 L 705,270 L 695,335 C 655,345 635,335 605,315 Z",
    "ML": "M 615,315 L 675,315 L 670,345 L 615,345 Z",
    "NL": "M 705,270 L 745,270 L 740,315 L 705,310 Z",
    "MN": "M 705,310 L 740,315 L 735,360 L 700,355 Z",
    "MZ": "M 685,360 L 725,360 L 715,425 L 685,420 Z",
    "TR": "M 645,350 L 685,350 L 680,395 L 645,390 Z",
    "MH": "M 175,415 C 200,410 235,385 255,415 L 385,420 L 375,490 C 315,505 255,515 205,520 C 185,480 175,445 175,415 Z",
    "GA": "M 205,520 L 225,520 L 225,545 L 205,545 Z",
    "TS": "M 315,485 L 385,480 L 405,545 C 365,565 325,550 315,485 Z",
    "AP": "M 385,480 L 465,475 C 475,525 435,595 365,635 L 345,595 C 385,570 405,545 385,480 Z",
    "KA": "M 205,520 C 255,515 315,505 315,485 C 325,550 345,595 325,640 L 255,640 C 225,595 215,555 205,520 Z",
    "TN": "M 325,640 C 365,635 375,640 375,670 C 365,720 325,765 295,785 C 275,750 285,690 325,640 Z",
    "KL": "M 255,640 L 325,640 C 285,690 275,750 295,785 C 265,770 245,710 255,640 Z",
    "PY": "M 365,670 L 380,670 L 380,685 L 365,685 Z",
    "AN": "M 670,580 L 700,580 L 695,740 L 665,740 Z",
    "LD": "M 140,640 L 170,640 L 165,740 L 135,740 Z"
}

ind_centroids = {
    "LA": [340, 75], "JK": [255, 95], "HP": [315, 155], "PB": [235, 175],
    "CH": [262, 177], "UK": [375, 195], "HR": [280, 230], "DL": [305, 245],
    "RJ": [210, 280], "GJ": [135, 375], "DNHDD": [172, 422], "UP": [395, 280],
    "MP": [345, 380], "CG": [440, 410], "BR": [505, 320], "JH": [505, 380],
    "OD": [495, 465], "WB": [575, 370], "SK": [587, 270], "AR": [700, 235],
    "AS": [650, 305], "ML": [645, 330], "NL": [725, 290], "MN": [720, 335],
    "MZ": [705, 390], "TR": [665, 372], "MH": [265, 460], "GA": [215, 532],
    "TS": [355, 520], "AP": [415, 560], "KA": [270, 565], "TN": [330, 710],
    "KL": [275, 710], "PY": [372, 677], "AN": [682, 660], "LD": [152, 690]
}


# ---------------------------------------------------------------------------
# Solver Run & Bundle Builder
# ---------------------------------------------------------------------------
csp_aus = MapColoringCSP(AUSTRALIA_REGIONS, {v: ["Red", "Green", "Blue"] for v in AUSTRALIA_REGIONS}, AUSTRALIA_NEIGHBORS)
sol_aus = csp_aus.solve()

vars_ind, nbrs_ind = build_india_graph(include_uts=True)
csp_ind_4 = MapColoringCSP(vars_ind, {v: ["Red", "Green", "Blue", "Yellow"] for v in vars_ind}, nbrs_ind)
sol_ind_4 = csp_ind_4.solve()

csp_ind_3 = MapColoringCSP(vars_ind, {v: ["Red", "Green", "Blue"] for v in vars_ind}, nbrs_ind)
sol_ind_3 = csp_ind_3.solve()

data_bundle = {
    "australia": {
        "title": "Part A: Australia Map (3 Colors)",
        "colors": ["Red", "Green", "Blue"],
        "names": AUSTRALIA_NAMES,
        "coords": aus_centroids,
        "paths": aus_geo_paths,
        "neighbors": AUSTRALIA_NEIGHBORS,
        "timeline": csp_aus.timeline,
        "backtracks": csp_aus.backtracks,
        "solved": sol_aus is not None,
        "viewBox": "0 0 700 740"
    },
    "india_4": {
        "title": "Part B: India Map (4 Colors, 28 States + 8 UTs)",
        "colors": ["Red", "Green", "Blue", "Yellow"],
        "names": INDIA_STATE_NAMES,
        "coords": ind_centroids,
        "paths": ind_geo_paths,
        "neighbors": nbrs_ind,
        "timeline": csp_ind_4.timeline,
        "backtracks": csp_ind_4.backtracks,
        "solved": sol_ind_4 is not None,
        "viewBox": "0 0 820 840"
    },
    "india_3": {
        "title": "Part B: India Map (3 Colors, Failure & Backtrack Demonstration)",
        "colors": ["Red", "Green", "Blue"],
        "names": INDIA_STATE_NAMES,
        "coords": ind_centroids,
        "paths": ind_geo_paths,
        "neighbors": nbrs_ind,
        "timeline": csp_ind_3.timeline,
        "backtracks": csp_ind_3.backtracks,
        "solved": sol_ind_3 is not None,
        "viewBox": "0 0 820 840"
    }
}

json_data = json.dumps(data_bundle)

html_markup = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Map Coloring CSP Geographic Visualizer</title>
<style>
  :root {
    --bg-page: #080d1a;
    --bg-surface: #111a2e;
    --bg-elevated: #1a2742;
    --border: #263859;
    --text-primary: #f8fafc;
    --text-secondary: #94a3b8;
    --accent: #38bdf8;
    --accent-hover: #0284c7;
    --c-red: #e11d48;
    --c-green: #059669;
    --c-blue: #2563eb;
    --c-yellow: #d97706;
    --c-unassigned: #334155;
    --c-backtrack: #ec4899;
    --c-wipeout: #f43f5e;
  }

  [data-theme="light"] {
    --bg-page: #f1f5f9;
    --bg-surface: #ffffff;
    --bg-elevated: #e2e8f0;
    --border: #cbd5e1;
    --text-primary: #0f172a;
    --text-secondary: #475569;
    --accent: #0284c7;
    --accent-hover: #0369a1;
    --c-red: #dc2626;
    --c-green: #047857;
    --c-blue: #1d4ed8;
    --c-yellow: #b45309;
    --c-unassigned: #94a3b8;
    --c-backtrack: #be185d;
    --c-wipeout: #e11d48;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: var(--bg-page);
    color: var(--text-primary);
    padding: 18px 24px;
    line-height: 1.5;
    transition: background 0.2s ease, color 0.2s ease;
  }

  header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    max-width: 1480px;
    margin: 0 auto 14px auto;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--border);
  }

  .header-left h1 { font-size: 1.5rem; font-weight: 700; }
  .header-left p { color: var(--text-secondary); font-size: 0.88rem; }

  .theme-btn {
    background: var(--bg-surface);
    border: 1px solid var(--border);
    color: var(--text-primary);
    padding: 8px 14px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.85rem;
    font-weight: 600;
  }

  .scenario-bar {
    display: flex;
    gap: 10px;
    max-width: 1480px;
    margin: 0 auto 12px auto;
    flex-wrap: wrap;
  }

  .tab-btn {
    padding: 9px 18px;
    background: var(--bg-surface);
    border: 1px solid var(--border);
    color: var(--text-primary);
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.88rem;
    font-weight: 600;
    transition: all 0.15s ease;
  }

  .tab-btn.active {
    background: var(--accent);
    color: #ffffff;
    border-color: var(--accent);
  }

  /* Recursion Call Stack Breadcrumb */
  .call-stack-bar {
    max-width: 1480px;
    margin: 0 auto 12px auto;
    background: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 8px 14px;
    display: flex;
    align-items: center;
    gap: 8px;
    overflow-x: auto;
    white-space: nowrap;
    font-size: 0.82rem;
  }

  .stack-label {
    font-weight: 700;
    color: var(--accent);
    margin-right: 4px;
  }

  .stack-pill {
    padding: 3px 8px;
    border-radius: 4px;
    font-weight: 600;
    color: #ffffff;
    display: inline-flex;
    align-items: center;
    gap: 4px;
  }

  .stack-arrow { color: var(--text-secondary); }

  .main-grid {
    display: grid;
    grid-template-columns: 1.6fr 1fr;
    gap: 18px;
    max-width: 1480px;
    margin: 0 auto;
  }

  @media (max-width: 1100px) {
    .main-grid { grid-template-columns: 1fr; }
  }

  .card {
    background: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px;
  }

  .map-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
    flex-wrap: wrap;
    gap: 8px;
  }

  .view-toggle-grp {
    display: flex;
    background: var(--bg-elevated);
    border-radius: 6px;
    padding: 2px;
    border: 1px solid var(--border);
  }

  .view-toggle-btn {
    padding: 5px 12px;
    border: none;
    background: transparent;
    color: var(--text-secondary);
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.8rem;
    font-weight: 600;
  }

  .view-toggle-btn.active {
    background: var(--accent);
    color: #ffffff;
  }

  .bottleneck-btn {
    padding: 6px 12px;
    background: #f59e0b;
    border: none;
    color: #000;
    border-radius: 4px;
    font-weight: 700;
    font-size: 0.8rem;
    cursor: pointer;
  }

  .playback-bar {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
    flex-wrap: wrap;
    background: var(--bg-elevated);
    padding: 8px 12px;
    border-radius: 6px;
    border: 1px solid var(--border);
  }

  .ctrl-btn {
    padding: 6px 12px;
    background: var(--bg-surface);
    border: 1px solid var(--border);
    color: var(--text-primary);
    border-radius: 4px;
    cursor: pointer;
    font-weight: 600;
    font-size: 0.82rem;
  }
  .ctrl-btn:hover { background: var(--accent); color: #fff; }

  .scrubber-wrap {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-grow: 1;
    min-width: 140px;
  }

  .scrubber-wrap input[type="range"] {
    flex-grow: 1;
    cursor: pointer;
  }

  .speed-select {
    padding: 5px 8px;
    background: var(--bg-surface);
    border: 1px solid var(--border);
    color: var(--text-primary);
    border-radius: 4px;
    font-size: 0.8rem;
  }

  .step-badge {
    font-weight: 700;
    color: var(--accent);
    font-size: 0.85rem;
    min-width: 75px;
    text-align: right;
  }

  .svg-box {
    width: 100%;
    height: 600px;
    background: var(--bg-elevated);
    border: 1px solid var(--border);
    border-radius: 6px;
    position: relative;
    overflow: hidden;
  }

  svg { width: 100%; height: 100%; }

  .legend-bar {
    display: flex;
    gap: 14px;
    margin-top: 12px;
    flex-wrap: wrap;
    font-size: 0.82rem;
  }

  .legend-item { display: flex; align-items: center; gap: 6px; }
  .color-dot { width: 13px; height: 13px; border-radius: 50%; }

  .stats-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin-bottom: 12px;
  }

  .stat-card {
    background: var(--bg-elevated);
    padding: 8px 12px;
    border-radius: 6px;
    border: 1px solid var(--border);
  }
  .stat-label { font-size: 0.72rem; color: var(--text-secondary); text-transform: uppercase; font-weight: 600; }
  .stat-val { font-size: 0.98rem; font-weight: 700; color: var(--text-primary); }

  .alert-box {
    padding: 10px 14px;
    border-radius: 6px;
    margin-bottom: 12px;
    font-size: 0.85rem;
    border: 1px solid var(--border);
  }
  .alert-box.assign {
    background: rgba(16, 185, 129, 0.12);
    border-color: var(--c-green);
  }
  .alert-box.backtrack {
    background: rgba(236, 72, 153, 0.15);
    border-color: var(--c-backtrack);
    animation: flashBacktrack 0.35s ease;
  }
  .alert-box.wipeout {
    background: rgba(244, 63, 94, 0.2);
    border-color: var(--c-wipeout);
    color: #ff8597;
    font-weight: 600;
  }
  .alert-box.init { background: var(--bg-elevated); }

  @keyframes flashBacktrack {
    0% { transform: scale(0.99); background: rgba(236, 72, 153, 0.35); }
    100% { transform: scale(1); background: rgba(236, 72, 153, 0.15); }
  }

  .section-title {
    font-size: 0.88rem;
    font-weight: 700;
    margin-bottom: 6px;
    color: var(--accent);
  }

  .trace-box {
    background: var(--bg-elevated);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 10px 12px;
    font-size: 0.82rem;
    margin-bottom: 12px;
    max-height: 140px;
    overflow-y: auto;
  }

  .tabs-right {
    display: flex;
    gap: 8px;
    margin-bottom: 8px;
  }

  .sub-tab-btn {
    padding: 4px 10px;
    background: var(--bg-elevated);
    border: 1px solid var(--border);
    color: var(--text-secondary);
    border-radius: 4px;
    font-size: 0.78rem;
    font-weight: 600;
    cursor: pointer;
  }
  .sub-tab-btn.active {
    background: var(--accent);
    color: #ffffff;
  }

  .domain-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(115px, 1fr));
    gap: 6px;
    max-height: 220px;
    overflow-y: auto;
    background: var(--bg-elevated);
    padding: 8px;
    border-radius: 6px;
    border: 1px solid var(--border);
  }

  .domain-card {
    background: var(--bg-surface);
    border: 1px solid var(--border);
    padding: 5px 7px;
    border-radius: 4px;
    font-size: 0.74rem;
  }
  .domain-card.assigned {
    border-color: var(--accent);
    background: rgba(56, 189, 248, 0.08);
  }
  .domain-card.active-now {
    border-color: #f59e0b;
    box-shadow: 0 0 0 2px rgba(245, 158, 11, 0.4);
  }
  .domain-card.wipeout-now {
    border-color: var(--c-wipeout);
    background: rgba(244, 63, 94, 0.15);
    box-shadow: 0 0 0 2px rgba(244, 63, 94, 0.5);
  }

  .pills-row {
    display: flex;
    gap: 3px;
    margin-top: 3px;
    flex-wrap: wrap;
  }
  .pill {
    padding: 1px 4px;
    border-radius: 3px;
    font-size: 0.65rem;
    font-weight: 700;
    color: #ffffff;
  }

  .backtrack-log-list {
    max-height: 220px;
    overflow-y: auto;
    background: var(--bg-elevated);
    padding: 6px;
    border-radius: 6px;
    border: 1px solid var(--border);
    font-size: 0.78rem;
    display: none;
  }

  .log-item {
    padding: 6px 8px;
    margin-bottom: 4px;
    border-radius: 4px;
    background: var(--bg-surface);
    border: 1px solid var(--border);
    cursor: pointer;
    transition: background 0.1s ease;
  }
  .log-item:hover {
    background: rgba(236, 72, 153, 0.15);
    border-color: var(--c-backtrack);
  }

  .tooltip {
    position: absolute;
    pointer-events: none;
    background: rgba(15, 23, 42, 0.96);
    color: #ffffff;
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 0.78rem;
    border: 1px solid var(--accent);
    display: none;
    z-index: 100;
    box-shadow: 0 4px 12px rgba(0,0,0,0.5);
  }

  .bottleneck-modal {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: var(--bg-surface);
    border: 2px solid #f59e0b;
    border-radius: 8px;
    padding: 20px;
    max-width: 520px;
    z-index: 200;
    box-shadow: 0 10px 25px rgba(0,0,0,0.7);
    display: none;
  }
  .modal-backdrop {
    position: fixed;
    top:0; left:0; width:100%; height:100%;
    background: rgba(0,0,0,0.6);
    z-index: 199;
    display: none;
  }
</style>
</head>
<body data-theme="dark">

<header>
  <div class="header-left">
    <h1>Constraint Satisfaction Problem (CSP) Map Coloring</h1>
    <p>AI Lab Evaluation | Forward Checking + MRV + Degree Heuristic + LCV</p>
  </div>
  <button class="theme-btn" onclick="toggleTheme()" id="themeBtn">Switch to Light Mode</button>
</header>

<div class="scenario-bar">
  <button class="tab-btn active" id="btnAus" onclick="setScenario('australia')">Part A: Australia (3 Colors)</button>
  <button class="tab-btn" id="btnInd4" onclick="setScenario('india_4')">Part B: India (4 Colors - Solved)</button>
  <button class="tab-btn" id="btnInd3" onclick="setScenario('india_3')">Part B: India (3 Colors - Backtrack Proof)</button>
</div>

<!-- Recursion Call Stack Breadcrumb -->
<div class="call-stack-bar" id="callStackContainer">
  <span class="stack-label">Search Branch:</span>
  <span id="callStackContent" style="color:var(--text-secondary);">[Root]</span>
</div>

<div class="main-grid">
  <!-- Left Column: Map & Controls -->
  <div class="card">
    <div class="map-header">
      <div class="view-toggle-grp">
        <button class="view-toggle-btn active" id="btnViewTerritory" onclick="setViewMode('territory')">🗺️ Territory Map View</button>
        <button class="view-toggle-btn" id="btnViewNetwork" onclick="setViewMode('network')">🕸️ Topological Graph View</button>
      </div>

      <button class="bottleneck-btn" id="btn5Wheel" style="display:none;" onclick="openBottleneckModal()">⚡ Show Why 3 Colors Fail (5-Wheel Bottleneck)</button>
    </div>

    <div class="playback-bar">
      <button class="ctrl-btn" onclick="goToStart()" title="First Step">|◀</button>
      <button class="ctrl-btn" onclick="prevStep()" title="Previous Step">◀</button>
      <button class="ctrl-btn" onclick="togglePlay()" id="playBtn">Play ▶</button>
      <button class="ctrl-btn" onclick="nextStep()" title="Next Step">▶</button>
      <button class="ctrl-btn" onclick="goToEnd()" title="Last Step">▶|</button>
      <button class="ctrl-btn" onclick="resetSteps()" title="Reset">↺</button>
      <div class="scrubber-wrap">
        <input type="range" id="stepSlider" min="0" max="10" value="0" oninput="onSliderChange(this.value)">
      </div>
      <select class="speed-select" id="speedSelect" onchange="onSpeedChange(this.value)">
        <option value="1200">0.5x Speed</option>
        <option value="650" selected>1.0x Speed</option>
        <option value="250">2.0x Speed</option>
      </select>
      <div class="step-badge" id="stepCounter">0 / 0</div>
    </div>

    <div class="svg-box" id="svgBox">
      <svg id="mapSvg" viewBox="0 0 740 740"></svg>
      <div class="tooltip" id="mapTooltip"></div>
    </div>

    <div class="legend-bar" id="legendBox"></div>
  </div>

  <!-- Right Column: Inspector Panels -->
  <div class="card">
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">Current Variable</div>
        <div class="stat-val" id="statVar">None</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Action / Value</div>
        <div class="stat-val" id="statVal">None</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Total Backtracks</div>
        <div class="stat-val" id="statBacktracks">0</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Verification Status</div>
        <div class="stat-val" style="color:var(--c-green);" id="statVerification">Ready</div>
      </div>
    </div>

    <!-- Live Event Alert Banner -->
    <div class="alert-box init" id="alertBox">
      <b>Step 0:</b> Initial state. All variables unassigned.
    </div>

    <div class="section-title">Heuristic Decision & Forward Checking</div>
    <div class="trace-box" id="traceDetails">
      Awaiting execution. Use controls to start backtracking search.
    </div>

    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
      <div class="section-title" id="subPanelTitle">Live Region Domains</div>
      <div class="tabs-right">
        <button class="sub-tab-btn active" id="tabBtnDomains" onclick="showSubTab('domains')">Domain Matrix</button>
        <button class="sub-tab-btn" id="tabBtnLog" onclick="showSubTab('log')">Backtrack Log</button>
      </div>
    </div>

    <div class="domain-grid" id="domainGrid"></div>
    <div class="backtrack-log-list" id="backtrackLogList"></div>
  </div>
</div>

<!-- Bottleneck Modal -->
<div class="modal-backdrop" id="modalBackdrop" onclick="closeBottleneckModal()"></div>
<div class="bottleneck-modal" id="bottleneckModal">
  <h3 style="color:#f59e0b; margin-bottom:8px;">The 5-Wheel Graph Bottleneck ($W_5$)</h3>
  <p style="font-size:0.85rem; color:var(--text-secondary); margin-bottom:12px;">
    Why India can never be colored with 3 colors:
  </p>
  <div style="background:var(--bg-elevated); padding:10px; border-radius:6px; font-size:0.82rem; margin-bottom:12px; border:1px solid var(--border);">
    <ul style="padding-left:18px; line-height:1.6;">
      <li><b>Central Hub:</b> Madhya Pradesh (MP) borders 5 states in a contiguous ring.</li>
      <li><b>Outer 5-Cycle ($C_5$):</b> Gujarat (GJ) &rarr; Rajasthan (RJ) &rarr; Uttar Pradesh (UP) &rarr; Chhattisgarh (CG) &rarr; Maharashtra (MH) &rarr; GJ.</li>
      <li><b>Mathematical Constraint:</b> Any odd cycle requires at least <b>3 colors</b> to avoid adjacent conflict.</li>
      <li><b>Hub Impossibility:</b> MP touches every single vertex in this 5-cycle, so MP must have a color different from all of them, forcing a <b>4th color</b> ($3 + 1 = 4$).</li>
    </ul>
  </div>
  <button class="ctrl-btn" style="width:100%;" onclick="closeBottleneckModal()">Close Explanation</button>
</div>

<script>
const DATA = """ + json_data + """;

const COLOR_MAP = {
  'Red': '#e11d48',
  'Green': '#059669',
  'Blue': '#2563eb',
  'Yellow': '#d97706',
  'Unassigned': '#334155'
};

let currentKey = 'australia';
let frameIndex = 0;
let playTimer = null;
let playSpeed = 650;
let viewMode = 'territory'; // 'territory' or 'network'

function setScenario(key) {
  if (playTimer) togglePlay();
  currentKey = key;
  frameIndex = 0;

  document.getElementById('btnAus').classList.toggle('active', key === 'australia');
  document.getElementById('btnInd4').classList.toggle('active', key === 'india_4');
  document.getElementById('btnInd3').classList.toggle('active', key === 'india_3');

  document.getElementById('btn5Wheel').style.display = (key === 'india_3') ? 'inline-block' : 'none';

  const sc = DATA[currentKey];
  const slider = document.getElementById('stepSlider');
  slider.max = sc.timeline.length - 1;
  slider.value = 0;

  buildLegend();
  buildBacktrackLog();
  renderFrame();
}

function setViewMode(mode) {
  viewMode = mode;
  document.getElementById('btnViewTerritory').classList.toggle('active', mode === 'territory');
  document.getElementById('btnViewNetwork').classList.toggle('active', mode === 'network');
  renderFrame();
}

function buildLegend() {
  const sc = DATA[currentKey];
  const leg = document.getElementById('legendBox');
  leg.innerHTML = '';
  sc.colors.forEach(c => {
    leg.innerHTML += `<div class="legend-item"><div class="color-dot" style="background:${COLOR_MAP[c]}"></div><span>${c}</span></div>`;
  });
  leg.innerHTML += `<div class="legend-item"><div class="color-dot" style="background:${COLOR_MAP['Unassigned']}"></div><span>Unassigned</span></div>`;
  leg.innerHTML += `<div class="legend-item"><div class="color-dot" style="background:var(--c-wipeout)"></div><span>Wipeout Alert</span></div>`;
}

function buildBacktrackLog() {
  const sc = DATA[currentKey];
  const logList = document.getElementById('backtrackLogList');
  logList.innerHTML = '';

  const backtracks = sc.timeline.filter(f => f.action === 'backtrack');
  document.getElementById('tabBtnLog').textContent = `Backtrack Log (${backtracks.length})`;

  if (backtracks.length === 0) {
    logList.innerHTML = '<div style="padding:10px; color:var(--text-secondary); text-align:center;">No backtracks occurred! Solved deterministically.</div>';
    return;
  }

  sc.timeline.forEach((f, idx) => {
    if (f.action === 'backtrack') {
      const item = document.createElement('div');
      item.className = 'log-item';
      item.innerHTML = `
        <div style="display:flex; justify-content:space-between; font-weight:700;">
          <span style="color:var(--c-backtrack);">Backtrack #${f.backtrack_num}</span>
          <span style="color:var(--text-secondary);">Step ${f.step}</span>
        </div>
        <div style="color:var(--text-primary); margin-top:2px;">Reverted <b>${f.var} = ${f.val}</b></div>
        <div style="color:var(--text-secondary); font-size:0.72rem; margin-top:1px;">${f.reason}</div>
      `;
      item.onclick = () => {
        frameIndex = idx;
        renderFrame();
      };
      logList.appendChild(item);
    }
  });
}

function showSubTab(tab) {
  document.getElementById('tabBtnDomains').classList.toggle('active', tab === 'domains');
  document.getElementById('tabBtnLog').classList.toggle('active', tab === 'log');
  document.getElementById('domainGrid').style.display = (tab === 'domains') ? 'grid' : 'none';
  document.getElementById('backtrackLogList').style.display = (tab === 'log') ? 'block' : 'none';
}

function renderFrame() {
  const sc = DATA[currentKey];
  const frame = sc.timeline[frameIndex];
  const svg = document.getElementById('mapSvg');
  svg.setAttribute('viewBox', sc.viewBox || '0 0 740 740');
  svg.innerHTML = '';

  document.getElementById('stepSlider').value = frameIndex;
  document.getElementById('stepCounter').textContent = `${frameIndex} / ${sc.timeline.length - 1}`;

  // Update Call Stack Breadcrumb
  const stackContent = document.getElementById('callStackContent');
  if (!frame.call_stack || frame.call_stack.length === 0) {
    stackContent.innerHTML = '<span style="color:var(--text-secondary);">[Root: Empty Stack]</span>';
  } else {
    let stackHtml = '<span style="color:var(--text-secondary);">Root</span>';
    frame.call_stack.forEach((item, idx) => {
      const isLast = (idx === frame.call_stack.length - 1);
      const bg = COLOR_MAP[item.val] || COLOR_MAP['Unassigned'];
      stackHtml += ` <span class="stack-arrow">&rarr;</span> <span class="stack-pill" style="background:${bg}; ${isLast ? 'box-shadow:0 0 0 2px #fff;' : ''}">${item.var}: ${item.val}</span>`;
    });
    if (frame.action === 'backtrack') {
      stackHtml += ` <span class="stack-arrow">&rarr;</span> <span class="stack-pill" style="background:var(--c-backtrack); text-decoration:line-through;">${frame.var}: ${frame.val}</span> <span style="color:var(--c-backtrack); font-weight:bold;">[❌ Reverted]</span>`;
    }
    stackContent.innerHTML = stackHtml;
  }

  // Draw Geographic Territory Paths (Territory Mode)
  if (viewMode === 'territory' && sc.paths && Object.keys(sc.paths).length > 0) {
    for (const [r, pathD] of Object.entries(sc.paths)) {
      const assigned = frame.assignment[r];
      const isCurrent = (frame.var === r);
      const isWipeout = (frame.wipeout_var === r);

      const pathElem = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      pathElem.setAttribute('d', pathD);
      pathElem.setAttribute('fill', assigned ? COLOR_MAP[assigned] : 'rgba(51, 65, 85, 0.45)');
      pathElem.setAttribute('stroke', isWipeout ? 'var(--c-wipeout)' : (isCurrent ? '#f59e0b' : 'var(--border)'));
      pathElem.setAttribute('stroke-width', (isCurrent || isWipeout) ? '3.5' : '1.4');
      pathElem.style.cursor = 'pointer';
      pathElem.style.transition = 'fill 0.25s ease, stroke 0.25s ease';
      pathElem.onmouseenter = (e) => showTooltip(e, r, assigned, frame.domains[r], sc.neighbors[r]);
      pathElem.onmouseleave = hideTooltip;

      svg.appendChild(pathElem);
    }
  }

  // Draw Edges (Network Mode or dashed boundary links)
  const drawnEdges = new Set();
  for (const [u, nbrs] of Object.entries(sc.neighbors)) {
    for (const v of nbrs) {
      const edgeKey = [u, v].sort().join('--');
      if (!drawnEdges.has(edgeKey) && sc.coords[u] && sc.coords[v]) {
        drawnEdges.add(edgeKey);
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', sc.coords[u][0]);
        line.setAttribute('y1', sc.coords[u][1]);
        line.setAttribute('x2', sc.coords[v][0]);
        line.setAttribute('y2', sc.coords[v][1]);

        const isWipeoutEdge = (frame.var === u && frame.wipeout_var === v) || (frame.var === v && frame.wipeout_var === u);

        if (isWipeoutEdge) {
          line.setAttribute('stroke', 'var(--c-wipeout)');
          line.setAttribute('stroke-width', '4');
          line.setAttribute('stroke-dasharray', '5,5');
        } else {
          line.setAttribute('stroke', viewMode === 'network' ? 'var(--border)' : 'rgba(71, 85, 105, 0.35)');
          line.setAttribute('stroke-width', viewMode === 'network' ? '2' : '1');
          if (viewMode === 'territory') line.setAttribute('stroke-dasharray', '3,3');
        }
        svg.appendChild(line);
      }
    }
  }

  // Draw Nodes / Centroid Badges
  for (const [node, pos] of Object.entries(sc.coords)) {
    const isCurrent = (frame.var === node);
    const isWipeout = (frame.wipeout_var === node);
    const assigned = frame.assignment[node];
    const fillHex = assigned ? COLOR_MAP[assigned] : COLOR_MAP['Unassigned'];

    const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    g.style.cursor = 'pointer';
    g.onmouseenter = (e) => showTooltip(e, node, assigned, frame.domains[node], sc.neighbors[node]);
    g.onmouseleave = hideTooltip;

    const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    circle.setAttribute('cx', pos[0]);
    circle.setAttribute('cy', pos[1]);
    const r = (currentKey === 'australia') ? (viewMode === 'network' ? 24 : 17) : (viewMode === 'network' ? 18 : 13);
    circle.setAttribute('r', r);
    circle.setAttribute('fill', fillHex);
    circle.setAttribute('stroke', isWipeout ? 'var(--c-wipeout)' : (isCurrent ? '#f59e0b' : '#ffffff'));
    circle.setAttribute('stroke-width', (isCurrent || isWipeout) ? '3.5' : '1.5');

    const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    label.setAttribute('x', pos[0]);
    label.setAttribute('y', pos[1] + 4);
    label.setAttribute('text-anchor', 'middle');
    label.setAttribute('fill', '#ffffff');
    label.setAttribute('font-size', (currentKey === 'australia') ? '11px' : '8.5px');
    label.setAttribute('font-weight', 'bold');
    label.textContent = node;

    g.appendChild(circle);
    g.appendChild(label);
    svg.appendChild(g);
  }

  // Update Stats Cards
  document.getElementById('statVar').textContent = frame.var ? `${frame.var} (${sc.names[frame.var] || ''})` : 'None';
  document.getElementById('statVal').textContent = frame.val || 'None';
  document.getElementById('statBacktracks').textContent = frame.backtrack_num;

  // Update Alert Banner
  const alertBox = document.getElementById('alertBox');
  if (frame.action === 'init') {
    alertBox.className = 'alert-box init';
    alertBox.innerHTML = `<b>Initialization:</b> ${frame.reason}`;
    document.getElementById('statVerification').textContent = 'Ready to Start';
    document.getElementById('statVerification').style.color = 'var(--text-secondary)';
  } else if (frame.action === 'assign') {
    if (frame.wipeout_var) {
      alertBox.className = 'alert-box wipeout';
      alertBox.innerHTML = `⚠️ <b>DOMAIN WIPEOUT DETECTED:</b> Assigning <b>${frame.var} = ${frame.val}</b> left neighbor <b>${frame.wipeout_var}</b> with 0 legal colors!`;
      document.getElementById('statVerification').textContent = 'Wipeout Detected';
      document.getElementById('statVerification').style.color = 'var(--c-wipeout)';
    } else {
      alertBox.className = 'alert-box assign';
      alertBox.innerHTML = `<b>[Step ${frame.step}] Assigned:</b> <b>${frame.var} = ${frame.val}</b> (Forward Checking pruned neighbors).`;
      if (frameIndex === sc.timeline.length - 1 && sc.solved) {
        document.getElementById('statVerification').textContent = 'PASSED (0 Conflicts)';
        document.getElementById('statVerification').style.color = 'var(--c-green)';
      } else {
        document.getElementById('statVerification').textContent = 'Solving in progress...';
        document.getElementById('statVerification').style.color = 'var(--accent)';
      }
    }
  } else if (frame.action === 'backtrack') {
    alertBox.className = 'alert-box backtrack';
    alertBox.innerHTML = `⏪ <b>[Backtrack #${frame.backtrack_num}]:</b> ${frame.reason}`;
    document.getElementById('statVerification').textContent = `Backtrack #${frame.backtrack_num}`;
    document.getElementById('statVerification').style.color = 'var(--c-backtrack)';
  }

  // Update Trace Box
  const traceBox = document.getElementById('traceDetails');
  if (frame.action === 'init') {
    traceBox.innerHTML = 'All variables begin with full domains. MRV & Degree Heuristic will select the first region.';
  } else {
    let prunedStr = 'None';
    if (frame.pruned && Object.keys(frame.pruned).length > 0) {
      prunedStr = Object.entries(frame.pruned).map(([k, v]) => `<b>${k}</b> (-{${v.join(', ')}})`).join(', ');
    }
    let lcvStr = 'N/A';
    if (frame.lcv && frame.lcv.length > 0) {
      lcvStr = frame.lcv.map(([c, cost]) => `${c} (cost=${cost})`).join(', ');
    }

    traceBox.innerHTML = `
      <div><b>Variable Selection:</b> ${frame.reason}</div>
      <div style="margin-top:5px;"><b>LCV Value Ordering:</b> ${lcvStr}</div>
      <div style="margin-top:5px;"><b>Forward Checking Pruned:</b> ${prunedStr}</div>
    `;
  }

  // Update Domain Matrix
  const grid = document.getElementById('domainGrid');
  grid.innerHTML = '';
  for (const [v, dList] of Object.entries(frame.domains)) {
    const isAssigned = (frame.assignment[v] !== undefined);
    const isNow = (frame.var === v);
    const isWiped = (frame.wipeout_var === v);

    const dCard = document.createElement('div');
    dCard.className = `domain-card ${isAssigned ? 'assigned' : ''} ${isNow ? 'active-now' : ''} ${isWiped ? 'wipeout-now' : ''}`;

    let pillsHtml = '';
    sc.colors.forEach(c => {
      const hasColor = dList.includes(c);
      if (hasColor) {
        pillsHtml += `<span class="pill" style="background:${COLOR_MAP[c]}">${c[0]}</span>`;
      } else {
        pillsHtml += `<span class="pill" style="background:transparent; border:1px solid var(--border); color:var(--text-secondary); text-decoration:line-through;">${c[0]}</span>`;
      }
    });

    dCard.innerHTML = `
      <div style="display:flex; justify-content:space-between; font-weight:700;">
        <span>${v}</span>
        <span style="color:var(--text-secondary); font-size:0.68rem;">${isAssigned ? '✓ ' + frame.assignment[v] : (isWiped ? '⚠️ 0 left' : dList.length + ' left')}</span>
      </div>
      <div class="pills-row">${pillsHtml}</div>
    `;
    grid.appendChild(dCard);
  }
}

function showTooltip(e, node, assigned, domains, nbrs) {
  const tt = document.getElementById('mapTooltip');
  const sc = DATA[currentKey];
  const name = sc.names[node] || node;
  tt.style.display = 'block';
  tt.style.left = (e.pageX + 14) + 'px';
  tt.style.top = (e.pageY + 14) + 'px';
  tt.innerHTML = `
    <div style="font-weight:700; font-size:0.9rem; color:var(--accent);">${node} - ${name}</div>
    <div><b>Assigned Color:</b> ${assigned ? assigned : 'None (Unassigned)'}</div>
    <div><b>Remaining Domain:</b> [${domains ? domains.join(', ') : 'None'}]</div>
    <div><b>Borders (${nbrs.length}):</b> ${nbrs.join(', ')}</div>
  `;
}

function hideTooltip() {
  document.getElementById('mapTooltip').style.display = 'none';
}

function nextStep() {
  const sc = DATA[currentKey];
  if (frameIndex < sc.timeline.length - 1) {
    frameIndex++;
    renderFrame();
  } else if (playTimer) {
    togglePlay();
  }
}

function prevStep() {
  if (frameIndex > 0) {
    frameIndex--;
    renderFrame();
  }
}

function goToStart() {
  frameIndex = 0;
  renderFrame();
}

function goToEnd() {
  const sc = DATA[currentKey];
  frameIndex = sc.timeline.length - 1;
  renderFrame();
}

function resetSteps() {
  if (playTimer) togglePlay();
  frameIndex = 0;
  renderFrame();
}

function onSliderChange(val) {
  frameIndex = parseInt(val, 10);
  renderFrame();
}

function onSpeedChange(val) {
  playSpeed = parseInt(val, 10);
  if (playTimer) {
    clearInterval(playTimer);
    playTimer = setInterval(nextStep, playSpeed);
  }
}

function togglePlay() {
  const btn = document.getElementById('playBtn');
  if (playTimer) {
    clearInterval(playTimer);
    playTimer = null;
    btn.textContent = 'Play ▶';
  } else {
    btn.textContent = 'Pause ⏸';
    playTimer = setInterval(nextStep, playSpeed);
  }
}

function toggleTheme() {
  const body = document.body;
  const current = body.getAttribute('data-theme');
  const next = (current === 'dark') ? 'light' : 'dark';
  body.setAttribute('data-theme', next);
  document.getElementById('themeBtn').textContent = (next === 'dark') ? 'Switch to Light Mode' : 'Switch to Dark Mode';
}

function openBottleneckModal() {
  document.getElementById('bottleneckModal').style.display = 'block';
  document.getElementById('modalBackdrop').style.display = 'block';
}

function closeBottleneckModal() {
  document.getElementById('bottleneckModal').style.display = 'none';
  document.getElementById('modalBackdrop').style.display = 'none';
}

// Initial Run
setScenario('australia');
</script>

</body>
</html>
"""

# Write HTML visualizer
with open("map_coloring_visualizer.html", "w", encoding="utf-8") as f:
    f.write(html_markup)

print("Saved updated map_coloring_visualizer.html!")


def run_part_a():
    """Runs Part A: Australia Map Coloring with 3 Colors."""
    print("\n" + "=" * 78)
    print("PART A: AUSTRALIA MAP COLORING (3 COLORS)")
    print("=" * 78)

    csp = MapColoringCSP(AUSTRALIA_REGIONS, {v: ["Red", "Green", "Blue"] for v in AUSTRALIA_REGIONS}, AUSTRALIA_NEIGHBORS)
    solution = csp.solve()

    print("\nSTEP-BY-STEP TRACE:")
    for frame in csp.timeline:
        if frame["action"] == "assign":
            var = frame["var"]
            pruned_str = ", ".join(f"{k} -{{{', '.join(v)}}}" for k, v in frame["pruned"].items())
            print(f"[Step {frame['step']}] Select: {var} ({AUSTRALIA_NAMES.get(var, var)})")
            print(f"  Reason        : {frame['reason']}")
            print(f"  LCV Ordering  : {frame['lcv']}")
            print(f"  -> Assignment : {var} = {frame['val']}")
            print(f"  -> FC Pruned  : {pruned_str if pruned_str else 'None'}\n")

    print("RESULTS SUMMARY:")
    print(f"Selection Order  : {' -> '.join(csp.selection_order)}")
    print(f"Total Assignments: {csp.assignments_count}")
    print(f"Total Backtracks : {csp.backtracks}")
    print("Final Coloring:")
    for r in AUSTRALIA_REGIONS:
        print(f"  {r:5s} ({AUSTRALIA_NAMES[r]:20s}) : {solution[r]}")

    is_valid, conflicts = csp.verify_solution(solution)
    print(f"Verification: {'PASSED (No conflicts)' if is_valid else f'FAILED: {conflicts}'}")


def run_part_b(include_uts=True):
    """Runs Part B: India Map Coloring (3 vs 4 Colors)."""
    scope = "28 States + 8 Union Territories" if include_uts else "28 States Only"
    print("\n" + "=" * 78)
    print(f"PART B: INDIA MAP COLORING ({scope})")
    print("=" * 78)

    variables, neighbors = build_india_graph(include_uts=include_uts)

    # Test with 3 colors
    print("\n[Experiment 1] Testing with 3 Colors (Red, Green, Blue)...")
    csp_3 = MapColoringCSP(variables, {v: ["Red", "Green", "Blue"] for v in variables}, neighbors)
    sol_3 = csp_3.solve()
    print(f"Outcome         : {'SOLVED' if sol_3 else 'FAILED (Insufficient Colors)'}")
    print(f"Backtracks Count: {csp_3.backtracks}")
    print(f"Total Events    : {len(csp_3.timeline)} frames recorded.")
    print("Explanation     : Mathematical impossibility due to the 5-wheel subgraph around Madhya Pradesh.")

    # Test with 4 colors
    print("\n[Experiment 2] Testing with 4 Colors (Red, Green, Blue, Yellow)...")
    csp_4 = MapColoringCSP(variables, {v: ["Red", "Green", "Blue", "Yellow"] for v in variables}, neighbors)
    sol_4 = csp_4.solve()
    print(f"Outcome         : {'SUCCESSFULLY SOLVED' if sol_4 else 'FAILED'}")
    print(f"Backtracks Count: {csp_4.backtracks}")
    print(f"Total Steps     : {csp_4.assignments_count}")

    is_valid, conflicts = csp_4.verify_solution(sol_4)
    print(f"Verification    : {'PASSED (All boundaries valid)' if is_valid else f'FAILED: {conflicts}'}")
    print("\nSample Regional Assignments:")
    sample_keys = ["DL", "JK", "PB", "HR", "UP", "MP", "RJ", "MH", "GJ", "WB"]
    for k in sample_keys:
        if k in sol_4:
            print(f"  {k:5s} ({INDIA_STATE_NAMES[k]:25s}) : {sol_4[k]}")

    return sol_3, sol_4, csp_3.backtracks, csp_4.backtracks


def generate_html_visualizer(filename="map_coloring_visualizer.html"):
    """Saves the complete interactive HTML visualizer with dual-mode map & backtrack inspector."""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_markup)
    print(f"\n[+] Interactive visualizer generated successfully: {filename}")


def interactive_menu():
    """CLI Menu for running parts interactively during evaluation / viva."""
    while True:
        print("\n" + "=" * 52)
        print("    AI LAB EVALUATION: TASK 3 MAP COLORING")
        print("=" * 52)
        print("1. Run Part A: Australia Map (3 Colors)")
        print("2. Run Part B: India Map (3 Colors vs 4 Colors, States + UTs)")
        print("3. Run Part B: India Map (States Only)")
        print("4. Generate Interactive HTML/SVG Visualizer")
        print("5. Run Full Evaluation Suite & Print Viva Summary")
        print("6. Exit")
        choice = input("\nEnter choice [1-6]: ").strip()

        if choice == "1":
            run_part_a()
        elif choice == "2":
            run_part_b(include_uts=True)
        elif choice == "3":
            run_part_b(include_uts=False)
        elif choice == "4":
            generate_html_visualizer()
        elif choice == "5":
            run_part_a()
            run_part_b(include_uts=True)
            generate_html_visualizer()
        elif choice == "6":
            print("\nExiting. Good luck with your AI Lab viva!")
            break
        else:
            print("[!] Invalid option. Please enter a number between 1 and 6.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        run_part_a()
        run_part_b(include_uts=True)
        generate_html_visualizer()
    else:
        interactive_menu()
