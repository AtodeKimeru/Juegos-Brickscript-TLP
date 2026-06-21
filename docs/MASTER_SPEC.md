# ACTIVITY6_MASTER_SPEC

## Context

We are working on BrickScript Final Project - Activity 6 (Total Integration and Unified Project).

Important:

* Initial compiler analysis has already been completed.
* A unified compiler.py already exists inside final_project.
* Do NOT repeat compiler inventory work.
* Focus only on integration, validation, architecture consistency and retrocompatibility.

---

# Objective

Produce a fully integrated BrickScript ecosystem capable of executing:

1. Original Tetris
2. Original Snake
3. Extended Tetris
4. Evolved Snake
5. Tanks

using the SAME:

* compiler.py
* runtime.py
* jugar.bat

without modifying Python code between executions.

---

# Development Methodology

Follow strict Spec-Driven Development.

Process:

SPEC
→ GAP ANALYSIS
→ IMPLEMENTATION PLAN
→ PATCHES
→ VALIDATION
→ DOCUMENTATION

Never jump directly into coding.

---

# Scope

## Included

### Compiler

Validate unified compiler.

Verify:

* game detection
* parser flexibility
* default values
* backward compatibility

### Runtime

Analyze and refactor if necessary.

Must support:

* Tetris
* Snake
* Tanks

through a polymorphic architecture.

### Grammar

Validate support for:

* Original grammars
* Extended grammars
* Tanks grammar

### Documentation

Generate:

* README.txt
* MANUAL.txt

### Testing

Generate complete compatibility matrix.

---

# Retrocompatibility Requirements

The following scenarios MUST work.

## Scenario A

Original Tetris.

Must compile and execute without requiring:

* COLOR
* CHANCE
* POWERUP

## Scenario B

Original Snake.

Must compile and execute without requiring:

* LEVELS
* OBSTACLES
* POWERUPS

Default level:

BABY

## Scenario C

Extended Tetris.

Must support:

* COLOR
* CHANCE
* POWERUP
* Additional pieces
* Complete rotations

## Scenario D

Evolved Snake.

Must support:

* LEVELS
* BABY
* ENTHUSIAST
* NYAN_CAT
* Poison fruits
* Clouds
* Invulnerability

## Scenario E

Tanks.

Must support:

* PLAYER
* ENEMY
* BOSS
* HP
* BULLET
* TARGET_SCORE

---

# Required Deliverables

Generate the following artifacts.

## 1

MASTER_GAP_REPORT.md

Include:

* Missing runtime features
* Missing compatibility features
* Missing grammar support
* Risks

Rank:

CRITICAL
HIGH
MEDIUM
LOW

---

## 2

RUNTIME_INTEGRATION_PLAN.md

Include:

* Current architecture
* Desired architecture
* Refactor steps
* Migration strategy

Do not generate code.

---

## 3

RETROCOMPATIBILITY_MATRIX.md

Format:

| Feature | Tetris Original | Snake Original | Tetris Extended | Snake Evolved | Tanks |
| ------- | --------------- | -------------- | --------------- | ------------- | ----- |

---

## 4

TEST_PLAN.md

Include:

Compilation tests

Execution tests

Gameplay tests

Boss tests

Powerup tests

Level tests

---

# Runtime Requirements

Prefer architecture similar to:

RuntimeDispatcher

TetrisEngine

SnakeEngine

TanksEngine

Avoid spreading:

if game_type == ...

through the entire runtime.

Centralize dispatching.

---

# Default Values Strategy

Missing optional fields must never break execution.

Examples:

COLOR → default color

CHANCE → 1

LEVEL → BABY

HP → 1

POWERUPS → empty list

BOSS → null

Use safe access patterns.

Avoid direct dictionary indexing when field may not exist.

---

# Agent Tasks

Execute in order.

Task 1

Produce MASTER_GAP_REPORT.md

STOP.

Wait.

Task 2

Produce RUNTIME_INTEGRATION_PLAN.md

STOP.

Wait.

Task 3

Produce RETROCOMPATIBILITY_MATRIX.md

STOP.

Wait.

Task 4

Produce TEST_PLAN.md

STOP.

Wait.

Only after approval:

Task 5

Generate runtime patches.

Task 6

Generate documentation.

---

# Output Rules

Be concise.

Do not explain BrickScript theory.

Do not repeat project description.

Do not rewrite requirements already known.

Focus only on actionable engineering work.

Prefer checklists, tables and patch plans.

Minimize token usage.
