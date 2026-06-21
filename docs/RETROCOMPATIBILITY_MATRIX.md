# Retrocompatibility Matrix - Activity 6
**Date**: 2026-06-20  
**Purpose**: Define how unified runtime.py maintains backward compatibility with all 5 game types

---

## Game Type Definitions

| Game Type | Source | Status | Features |
|-----------|--------|--------|----------|
| **TETRIS** | Original (Base 2026-1s) | Original | Line clearing, Tetris shapes |
| **SNAKE** | Original (Base 2026-1s) | Original | Food, direction, collision with walls |
| **TETRIS_REMAKE** | Tetris Remake A3 | Enhanced | Tetris + weighted power-ups (column-clear) |
| **SNAKE_EVOLVED** | Snake Evolved A4 | Enhanced | Snake + multi-levels (BABY/ENTHUSIAST/NYAN_CAT) + poison + clouds |
| **TANKS** | Brick Tanks | New | Tank warfare, HP system, boss fight, bullets |

---

## Retrocompatibility Requirements

### Requirement 1: All Original Games Must Run Unchanged
**Scope**: TETRIS, SNAKE (original from Base 2026-1s)

| Feature | Required | Implementation |
|---------|----------|-----------------|
| Shape spawning | ✅ Random from shape list | Use weighted selection (weight=100 if no chance specified) |
| Grid collision | ✅ Block overlaps fail move | Unified collision detection |
| Line clearing | ✅ Full rows clear, score +10 per line | Tetris-specific logic in game module |
| Snake growth | ✅ Food spawns random, snake grows 1 block | Snake-specific spawn logic |
| Food collision | ✅ Snake head + food = score +1 | Event: ON_COLLISION_FOOD → score increment |
| Direction change | ✅ Arrow keys change direction | Unified input handler |
| Game over | ✅ Head hits wall/body | Event: ON_COLLISION_WALL → game over |

**Validation**: Original Base 2026-1s games run identically with unified runtime.py

---

### Requirement 2: Enhanced Games Must Run With All New Features
**Scope**: TETRIS_REMAKE, SNAKE_EVOLVED

#### TETRIS_REMAKE Features
| Feature | Specification | Retrocompat Handling |
|---------|---|---|
| **Power-ups** | Column-clear via ON_POWERUP_ACTIVATE event | Game-type specific: only triggers in TETRIS game type |
| **Weighted Spawn** | Shapes with `chance` attribute (0-100) | Use `bisect` weighted selection if available |
| **Shape Normalization** | Old format (list) → new format (dict) | Normalizer applies before runtime starts |

**Validation**: TETRIS_REMAKE power-ups work; Tetris shapes spawn at correct weights

#### SNAKE_EVOLVED Features
| Feature | Specification | Retrocompat Handling |
|---------|---|---|
| **Multi-Levels** | BABY/ENTHUSIAST/NYAN_CAT (keys 1/2/3) | Level selector available only for SNAKE_EVOLVED game type |
| **Poison Fruit** | Enabled via level config `poison_enabled` | Spawns alternative sprite if level flag true |
| **Clouds** | Obstacles enabled via `clouds_enabled` | Spawns as wall-type obstacles if flag true |
| **Nyan Cat** | Head→circle, body→rainbow triangles | Applied only when level == NYAN_CAT |

**Validation**: All 3 levels playable; Nyan Cat renders correctly; poison/clouds toggle on/off

---

### Requirement 3: New Game Type Must Execute
**Scope**: TANKS

| Feature | Specification | Retrocompat Handling |
|---------|---|---|
| **Player Tank** | Controlled via arrows (move) + spacebar (shoot) | New input mapping in unified handler |
| **HP System** | Player: 100 HP; Enemies: variable; Boss: 500 HP | Damage/healing via ON_COLLISION_* events |
| **Enemy Waves** | Spawn periodically, increase with score | Tanks-specific spawn manager |
| **Boss Fight** | Triggers at score ≥ 1000 | Tanks-specific boss logic |
| **Bullets** | Player + Enemy projectiles with collision | Bullet physics engine (Tanks-only) |
| **Walls** | Obstacles with durability (hit-points) | Wall collision reduces durability |

**Validation**: TANKS game runs with all features intact

---

## Feature Compatibility Matrix

### Input Mapping (Unified)
| Key | TETRIS | SNAKE | TETRIS_REMAKE | SNAKE_EVOLVED | TANKS |
|-----|--------|-------|---------------|---------------|-------|
| **Arrow Up** | Rotate | Up | Rotate | Up | Up (move) |
| **Arrow Down** | ▼ | Down | ▼ | Down | Down (move) |
| **Arrow Left** | ◄ | Left | ◄ | Left | Left (move) |
| **Arrow Right** | ► | Right | ► | Right | Right (move) |
| **Spacebar** | - | - | - | - | Shoot (TANKS only) |
| **Key 1** | - | - | - | Level BABY | - |
| **Key 2** | - | - | - | Level ENTHUSIAST | - |
| **Key 3** | - | - | - | Level NYAN_CAT | - |

---

### Event Compatibility Matrix

**Event Dispatch Order** (guaranteed for all games):
1. ON_START (game initialization)
2. ON_TICK (each frame)
3. ON_KEY_* (key pressed)
4. ON_COLLISION_* (collision detected)
5. ON_LINE_CLEAR (Tetris only, if applicable)

| Event Type | TETRIS | SNAKE | TETRIS_REMAKE | SNAKE_EVOLVED | TANKS | Spec |
|-----------|--------|-------|---------------|---------------|-------|------|
| ON_START | ✅ | ✅ | ✅ | ✅ | ✅ | Initialize game state |
| ON_TICK | ✅ | ✅ | ✅ | ✅ | ✅ | Frame logic; score increment |
| ON_KEY_UP | ✅ | ✅ | ✅ | ✅ | ✅ | Rotate (Tetris) / Move (Snake/Tanks) |
| ON_KEY_DOWN | ✅ | ✅ | ✅ | ✅ | ✅ | Move down / Shoot |
| ON_KEY_LEFT | ✅ | ✅ | ✅ | ✅ | ✅ | Move left |
| ON_KEY_RIGHT | ✅ | ✅ | ✅ | ✅ | ✅ | Move right |
| ON_COLLISION_WALL | ✅ | ✅ | ✅ | ✅ | ✅ | Game over / Bounce |
| ON_COLLISION_BODY | ✅ | ✅ | ✅ | ✅ | ✅ | Game over / HP -1 (Tanks) |
| ON_COLLISION_FOOD | ❌ | ✅ | ❌ | ✅ | ❌ | Score +1, spawn new |
| ON_COLLISION_ENEMY | ❌ | ❌ | ❌ | ❌ | ✅ | HP -= enemy.damage |
| ON_COLLISION_POWERUP | ❌ | ❌ | ✅ | ✅ | ❌ | Activate power-up |
| ON_COLLISION_BOSS | ❌ | ❌ | ❌ | ❌ | ✅ | HP -= player.damage |
| ON_LINE_CLEAR | ✅ | ❌ | ✅ | ❌ | ❌ | Score +10 |
| ON_POWERUP_ACTIVATE | ❌ | ❌ | ✅ | ✅ | ❌ | Apply effect (column-clear / invincibility) |
| ON_TARGET_SCORE | ❌ | ❌ | ❌ | ❌ | ✅ | Boss spawn at 1000+ |

---

### Shape Format Compatibility

**Old Format** (Base 2026-1s, some A3 files):
```json
"shapes": {
  "PLAYER": [
    [[1, 1], [1, 1]]
  ]
}
```

**New Format** (A3/A4/Tanks):
```json
"shapes": {
  "PLAYER": {
    "color": "#00FFFF",
    "tipo": "PLAYER",
    "hp": 100,
    "damage": 1,
    "chance": 10,
    "speed": 1,
    "estados": [
      [[1, 1], [1, 1]]
    ]
  }
}
```

**Retrocompat Handling**: Normalizer converts old → new format before runtime starts
- Missing fields get defaults (color=#FFFFFF, hp=0, damage=0, chance=10, speed=0.1)
- List-only format recognized and wrapped into dict structure

---

### Level Format Compatibility

**Implicit Format** (Base 2026-1s, original):
```json
"niveles": {}  // or missing
```
→ Normalized to DEFAULT level with (speed=0.15, poison_enabled=false, clouds_enabled=false)

**Explicit Format** (A4/Snake_Evolved):
```json
"niveles": {
  "BABY": { "speed": 0.05, "poison_enabled": true },
  "ENTHUSIAST": { "speed": 0.15, "poison_enabled": true, "clouds_enabled": true },
  "NYAN_CAT": { "speed": 0.30, "poison_enabled": false, "clouds_enabled": false }
}
```

**Retrocompat Handling**:
- If niveles missing or empty → use DEFAULT
- If niveles has BABY/ENTHUSIAST/NYAN_CAT → support level switching (SNAKE_EVOLVED only)
- If niveles is dict with custom keys → use first as default

---

### Power-up Compatibility

**Tetris Power-up** (A3):
```json
"powerups": {
  "COLUMN_CLEAR": {
    "condition": "ON_COLLISION_BLOCK",
    "action": "clear_column"
  }
}
```
→ Only active in TETRIS game type

**Snake Power-up** (A4):
```json
"powerups": {
  "INVINCIBILITY": {
    "condition": "ON_COLLISION_FOOD",
    "duration": 300,
    "action": "immunity"
  }
}
```
→ Only active in SNAKE_EVOLVED game type

**Retrocompat Handling**:
- Each power-up has game-type filter
- If game-type doesn't match, power-up is silently ignored (no crash)
- If action/condition unknown, power-up skipped with warning to stderr

---

### Boss/Enemy Compatibility

**TANKS Specification**:
```json
"bosses": {
  "FINAL_FORTRESS": {
    "color": "#FF00FF",
    "hp": 500,
    "type": "BOSS",
    "estados": [ [ [1,1,1], [1,1,1] ] ]
  }
}
```

**Retrocompat Handling**:
- Boss only relevant in TANKS game type
- If otro game type has bosses field → silently ignored
- Collision logic: bullet hits boss → hp -= damage

---

## Backward Compatibility Guarantees

### Guarantee 1: Old .brick Files Run Correctly
- Old files without LEVELS section still work (use DEFAULT level)
- Old files without power-ups still work (no errors)
- Old files with list-format shapes normalize correctly
- Old files without game-type detection still work (inferred from file path or config)

### Guarantee 2: New .brick Files Run Correctly
- New files with LEVELS, POWERUP, DEFINE SHAPE work as designed
- New files with BOSS (TANKS) execute boss logic
- Multi-level system works for SNAKE_EVOLVED
- Weighted spawn works via chance attribute

### Guarantee 3: Mixed Feature Sets Work
- Tetris_Remake: Original Tetris + power-ups (no boss, no levels)
- Snake_Evolved: Original Snake + levels + power-ups (no boss, no HP)
- Tanks: New game + boss + HP (compatible input mapping with other games)
- Original Base: Works exactly as before (no extra features)

### Guarantee 4: Error Resilience
- Invalid event actions logged to stderr, game continues
- Missing shape definitions fallback to random rect
- Crashed collision doesn't freeze game (try-catch wrapper)
- Invalid JSON structure has graceful degradation

---

## Validation Checklist

- [ ] Original TETRIS runs identically to Base 2026-1s
- [ ] Original SNAKE runs identically to Base 2026-1s
- [ ] TETRIS_REMAKE power-ups activate on schedule
- [ ] SNAKE_EVOLVED levels switch (keys 1/2/3) without crash
- [ ] SNAKE_EVOLVED Nyan Cat renders correctly on level 3
- [ ] TANKS boss spawns at score 1000+ and takes damage
- [ ] TANKS player HP displays and updates on collision
- [ ] All games handle invalid input without crashing
- [ ] All games terminate gracefully on game-over
- [ ] Event system handles missing/invalid actions
- [ ] Shape normalization works for old format
- [ ] Power-ups silently ignored if game-type mismatch

---

## Migration Path for Users

### For Base 2026-1s Users
1. Replace runtime.py with unified version
2. Run same .brick files as before
3. No code changes needed ✅

### For Tetris Remake Users
1. Replace runtime.py with unified version
2. Run same .brick files as before
3. Power-ups continue to work ✅

### For Snake Evolved Users
1. Replace runtime.py with unified version
2. Run same .brick files as before
3. All levels accessible (keys 1/2/3) ✅

### For Tanks Users
1. Replace runtime.py with unified version
2. Run same .brick files as before
3. Boss fight, HP system continue to work ✅

**Impact**: Zero migration effort for users ✅
