# Runtime Gap Report - Activity 6
**Date**: 2026-06-20  
**Status**: Gap Analysis Complete  
**Target**: Unified runtime.py for TETRIS, SNAKE, TETRIS_REMAKE, SNAKE_EVOLVED, TANKS

---

## Executive Summary

| Aspect | Gap | Severity | Impact |
|--------|-----|----------|--------|
| **Code Duplication** | 2800+ LOC across 4 runtimes | CRITICAL | Maintenance nightmare, bugs multiply |
| **Game Support** | No single runtime supports all 5 games | CRITICAL | Games must use separate runtimes |
| **Power-up System** | Different per game (Column-clear vs Invincibility) | HIGH | Cannot port power-ups between games |
| **Event Handling** | Inconsistent error handling, no centralization | HIGH | Crashes differ per game |
| **Level System** | Only Snake_Evolved implements (BABY/ENTHUSIAST/NYAN_CAT) | MEDIUM | Cannot add levels to other games |
| **Shape Management** | A3 has normalizar_shapes(); A4/Tanks don't | MEDIUM | Compatibility failures |
| **Naming Inconsistency** | serpiente vs h vs w vs nx | MEDIUM | Code unclear, hard to unify |

---

## Current Runtime Implementations

### RetroBrik Base 2026-1s (Reference)
- **LOC**: ~300
- **Games**: TETRIS, SNAKE (2 types)
- **Features**: Basic Tkinter GUI, random shape selection
- **Event System**: `ON_START`, `ON_TICK`, `ON_KEY_*`, `ON_LINE_CLEAR`, `ON_COLLISION_*`
- **Gap**: No power-ups, no levels, no boss, basic collision

### Tetris Remake A3
- **LOC**: ~650
- **Games**: TETRIS, SNAKE (2 types)
- **NEW Features**:
  - ✅ Power-up system (column-clear, visual indicator)
  - ✅ Weighted random selection via `bisect`
  - ✅ Shape normalization (`_normalizar_shapes()`)
- **Gap**: Power-ups hardcoded for Tetris; no multi-level system; event error handling missing

### Snake Evolved A4
- **LOC**: ~600
- **Games**: SNAKE (1 type) with variants via LEVELS
- **NEW Features**:
  - ✅ Multi-level system (BABY, ENTHUSIAST, NYAN_CAT)
  - ✅ Poison fruit + cloud obstacles (level-dependent)
  - ✅ Nyan Cat rendering
  - ✅ Weighted selection (implicit)
- **Gap**: Tetris support incomplete; Nyan Cat rendering hardcoded; no power-up error handling

### Brick Tanks (New)
- **LOC**: ~700
- **Games**: TETRIS, SNAKE, **TANKS** (3 types)
- **NEW Features**:
  - ✅ HP system (Player tank, enemies, boss)
  - ✅ Boss fight at score 1000+
  - ✅ Bullet physics (player + enemy)
  - ✅ Error handling + safe dict access
- **Gap**: Weighted selection fragile; event error handling incomplete; no power-up integration

---

## Critical Unification Gaps

### 1. **Event System Fragmentation**
**Problem**: Each runtime implements events differently
- Base/A3: Direct dict access without validation → crashes if key missing
- A4: Better isolation but still fragile
- Tanks: Safe dict access with `.get()` but inconsistent

**Impact**: A crashed event freezes game without feedback

**Solution Needed**: Centralized event dispatcher with try-catch wrapper

---

### 2. **Power-up System Incompatibility**
**Problem**: Two different power-up implementations cannot coexist
- A3: Column-clear (Tetris-specific) + visual delay
- A4: Invincibility (Snake-specific) + duration counter

**Impact**: Tetris power-ups fail in Tanks; Snake power-ups fail in Tetris

**Solution Needed**: Generic power-up framework with callbacks

---

### 3. **Shape Management Inconsistency**
**Problem**: Shapes stored/accessed differently
- Base: List of raw coords
- A3: Has `_normalizar_shapes()` to convert old format → dict format
- A4/Tanks: Assume dict format, no fallback

**Impact**: Backward compatibility breaks for old .brick files using old format

**Solution Needed**: Always apply shape normalization before runtime starts

---

### 4. **Level System Isolation**
**Problem**: Multi-level system only in Snake_Evolved
- LEVELS section parsed but not used elsewhere
- Key 1/2/3 switching hard-coded to Snake

**Impact**: Cannot add difficulty levels to Tetris or Tanks

**Solution Needed**: Generic level manager that works for any game

---

### 5. **Weighted Selection Fragmentation**
**Problem**: Shape selection implemented 3+ ways
- Base: `random.choice()` (uniform)
- A3: `seleccion_ponderada()` with bisect (correct)
- A4: Implicit weighting through spawn logic (unclear)
- Tanks: Similar to A4 (fragile)

**Impact**: Shape spawn distribution unreliable in non-A3 runtimes

**Solution Needed**: Centralize weighted selection as utility function

---

### 6. **Naming Inconsistency**
**Problem**: Same variables named differently across runtimes
| Variable | Base | A3 | A4 | Tanks |
|----------|------|-----|-----|-------|
| Width | ancho | ancho | w | w |
| Height | alto | alto | h | h |
| Snake | serpiente | - | serpiente | - |
| Player | - | - | - | player |
| Next X | - | - | nx | nx |

**Impact**: Unifying code requires constant translation

**Solution Needed**: Standardize all variable names in unified runtime

---

### 7. **Game Type Support Matrix**
**Problem**: No single runtime supports all game types

| Runtime | TETRIS | SNAKE | TETRIS_REMAKE | SNAKE_EVOLVED | TANKS |
|---------|--------|-------|---------------|---------------|-------|
| Base 2026 | ✅ | ✅ | ❌ | ❌ | ❌ |
| A3 | ✅ | ✅ | ✅ | ❌ | ❌ |
| A4 | ❌ | ✅ | ❌ | ✅ | ❌ |
| Tanks | ✅ | ✅ | ❌ | ❌ | ✅ |

**Impact**: Cannot use single runtime.py for all games

**Solution Needed**: Unified runtime that supports all 5 game types

---

## Unification Strategy

### Priority 1: Core Engine (Mandatory for all games)
- [ ] Abstract `GameEngine` base class
- [ ] Centralized event dispatcher with error handling
- [ ] Tkinter rendering pipeline
- [ ] Input handling (arrows + spacebar)
- [ ] Standardized variable naming

### Priority 2: Game-Specific Features (Addon modules)
- [ ] Tetris module (line-clearing logic)
- [ ] Snake module (food, poison, obstacles)
- [ ] Tanks module (HP, boss, bullets)
- [ ] Power-up framework (generic callbacks)
- [ ] Level system (generic difficulty scaling)

### Priority 3: Backward Compatibility
- [ ] Shape normalization for old .brick files
- [ ] Event format validation
- [ ] Graceful degradation for missing features
- [ ] Error messages that guide users

### Priority 4: Testing
- [ ] Unit tests for collision detection
- [ ] Integration tests for event flow
- [ ] Regression tests for each game type
- [ ] Stress tests (rapid key presses, high spawn rates)

---

## Implementation Constraints

### Python 2.7 Compatibility
- ✅ No f-strings
- ✅ No type hints
- ✅ `print` statements (no parentheses) or print()
- ✅ `.items()` returns list (not iterator)
- ✅ No unicode literals by default

### No External Dependencies
- Only stdlib: sys, json, time, random, Tkinter, tkMessageBox, bisect
- No numpy, pygame, or custom libraries

### File Structure
- All changes in `final_project/` only
- Reference directories (RetroBrik, tetris_remake, snake_evolved, brick_tanks) are READ-ONLY
- No distribution to other directories

---

## Success Criteria

A unified runtime.py is successful when:

1. ✅ Compiles all 5 game types (TETRIS, SNAKE, TETRIS_REMAKE, SNAKE_EVOLVED, TANKS)
2. ✅ Executes all 5 games without crashes
3. ✅ Backward compatible with old .brick file formats
4. ✅ All events (ON_START, ON_TICK, ON_KEY_*, ON_LINE_CLEAR, ON_COLLISION_*) work consistently
5. ✅ Power-ups trigger and apply correctly for each game
6. ✅ Levels work (BABY/ENTHUSIAST/NYAN_CAT for Snake; default for others)
7. ✅ Scoring, collision detection, game-over logic work correctly
8. ✅ No crashes on invalid input or edge cases

---

## Next Steps

1. ✅ Complete RUNTIME_GAP_REPORT.md (this file)
2. ⏳ Complete RETROCOMPATIBILITY_MATRIX.md
3. ⏳ Complete TEST_PLAN.md
4. ⏳ Create unified runtime.py in final_project/
5. ⏳ Create unified jugar.bat in final_project/
6. ⏳ Test all 5 games
