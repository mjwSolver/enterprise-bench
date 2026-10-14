# Architecture Specification: Adaptive Complexity Gears & Enterprise Density

> **Target Role:** Core Platform Engineer / Presentation Engine Maintainer (`enterprise-bench-dev`, `presentation-maker`)  
> **Status:** Approved Architectural Standard  
> **Target Subsystems:** [`src/ppt_engine/consulting_archetypes.py`](../../src/ppt_engine/consulting_archetypes.py), [`src/ppt_engine/diagram_engine.py`](../../src/ppt_engine/diagram_engine.py), [`skills/presentation-maker/SKILL.md`](../../skills/presentation-maker/SKILL.md), [`AGENTS.md`](../../AGENTS.md)  
> **Related Documents:** [`docs/specs/drawio_edge_routing_and_collision_prevention.md`](drawio_edge_routing_and_collision_prevention.md), [`docs/specs/openxml_purging_and_cleansing.md`](openxml_purging_and_cleansing.md)

---

## 1. Executive Summary & Problem Framing

Modern minimalist diagram philosophies (e.g. `diagram-design`) enforce rigid aesthetic caps: *target density 4/10, maximum 9 nodes, exactly 1 accent color, prohibition of warning badges and inline bullet lists*.

While suitable for consumer blogs, applying these dogmas to enterprise IT consulting (e.g., Bank Sinarmas / Cloudera-to-Databricks migration decks) creates severe operational defects:
1. **Rule Pegging / Scope Truncation:** Agents proactively delete contractual tasks, drop security guardrails, and omit named counterpart matrices to artificially satisfy a low density score.
2. **Context Fragmentation:** Contractual runbooks are splintered across dozens of sparse slides rather than co-locating cross-cutting dependencies on a single negotiation viewport.
3. **Signal Erasure:** Forcing a single accent color strips critical diagnostic status registers (e.g., red bottleneck borders vs. amber boundary fences).

**The Architectural Invariant:** In enterprise consulting, **high information density ($7.0/10$ to $9.5/10$) is a functional requirement, not a design defect.** Legibility is maintained through **hierarchical containerization, strict typographic scaling, and boundary swimlanes**, never by deleting necessary technical scope.

---

## 2. The 3-Tier Adaptive Complexity Gear System

Engineers and automated agents must select from three distinct complexity gears based on audience and engagement lifecycle:

```
[ GEAR 1: EXECUTIVE / PITCH ] ──► Target Density: 4.0/10 to 5.0/10
  • Target Audience: Board of Directors, Steering Committee kickoff, executive sponsor.
  • Visual Archetype: 3-Horizon Modernization, Core Strategic Pillars, Macro Takeaways.
  • Layout Pattern: Generous whitespace, 1 primary focal anchor, max 3 takeaway cards.
  • Reference: BSIM Pre-KOM Slide 1 (Cover) & Slide 4 (Objectives).

[ GEAR 2: PRE-KOM / ALIGNMENT ] ──► Target Density: 6.5/10 to 7.5/10 (DEFAULT BASELINE)
  • Target Audience: Technical Directors, Enterprise Architects, Engagement PMOs.
  • Visual Archetype: Target Architecture Topology, Scope Breakdown, Migration Waves.
  • Layout Pattern: 3-column boundary swimlanes (On-Premises ➔ Cloud ➔ Consumers),
                    labeled path connectors (WS1, WS2, WS4), out-of-scope boundaries.
  • Reference: BSIM Pre-KOM Slide 6 (Target Architecture) & Slide 10 (Approach).

[ GEAR 3: TECHNICAL WORKSTREAM ] ──► Target Density: 8.5/10 to 9.5/10 (MAXIMUM POTENTIAL)
  • Target Audience: Lead Engineers, Security Officers, SysAdmins, DBAs.
  • Visual Archetype: Landing Zone Runbooks, Action Matrices, Multi-Tier Network Hubs.
  • Layout Pattern: 4-Quadrant Container Discipline (Objective, MII Actions, Client Actions,
                    Cross-Stream Dependencies, Named PIC Table).
  • Typographic Scale: Tight hierarchy (Header 18-20pt, Section Tag 10pt bold, Body 8.5-9.5pt,
                       Metadata/PICs 7.5-8.5pt). Zero-margin text frames.
  • Reference: BSIM Workstream Slide 4 (Landing Zone), Slide 5 (Architecture), Slide 8 (WS1-3).
```

---

## 3. The Enterprise Diagnostic Status Triad

Rather than enforcing a 1-accent aesthetic limit, diagrams and cards incorporate deterministic semantic signaling:

| Semantic Role | Border / Accent Hex | Fill Tint Hex | Operational Meaning in Consulting |
| :--- | :--- | :--- | :--- |
| **Critical Defect / Bottleneck** | `#DC2626` (Red-600) | `#FEE2E2` (Red-100) | P1 bottleneck, single-point-of-failure, legacy debt. |
| **Warning / Boundary / Sync** | `#D97706` (Amber-600) | `#FEF3C7` (Amber-100) | Synchronous wait, temporary VPN, freeze window. |
| **Client Ingress / Active Flow** | `#0284C7` (Sky-600) | `#EFF6FF` (Blue-50) | Primary data ingress, client requests, runtime triggers. |
| **Target State / Reconciled** | `#16A34A` (Green-600) | `#DCFCE7` (Green-100) | Target cloud platform, reconciled data, approved state. |
| **Neutral Container / Body** | `#CBD5E1` (Slate-300) | `#F8FAFC` / `#F1F5F9` | Standard storage, structural containers, boundaries. |

---

## 4. Casual Ingress & Zero-Friction Routing Contract

To ensure future agents select the appropriate gear in one-shot scenarios without forcing users into tedious specification prompts:

1. **Default to Gear 2:** Any vague, casual, or underspecified prompt (*"make a slide on data migration"*) defaults to **Gear 2 (Pre-KOM Alignment)**.
2. **Domain-Noun Auto-Elevation:** If prompt input contains high-density enterprise entities (e.g., specific workload counts, VPC/CIDR, PrivateLink, CAB, PIC, BAST milestones, or named vendor tools), the agent automatically elevates to **Gear 3 (Technical Workstream)**.
3. **1-Word Steering Levers:**
   - `"pack it"` / `"full BSIM"` &rarr; Elevate to Gear 3.
   - `"simplify"` / `"board view"` &rarr; Drop to Gear 1.
   - `"swimlane it"` &rarr; Convert topology to 3-column boundary architecture.
