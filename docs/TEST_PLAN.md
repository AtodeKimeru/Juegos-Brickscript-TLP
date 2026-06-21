# Test Plan - Activity 6 Unified Runtime
**Date**: 2026-06-20  
**Objective**: Comprehensive testing of unified runtime.py supporting 5 game types

---

## Test Scope

| Game Type | Category | Status |
|-----------|----------|--------|
| **TETRIS** | Original | Must test |
| **SNAKE** | Original | Must test |
| **TETRIS_REMAKE** | Enhanced | Must test |
| **SNAKE_EVOLVED** | Enhanced | Must test |
| **TANKS** | New | Must test |

---

## Phase 1: Unit Tests (Pre-Execution)

### Test Set 1.1: Shape Management
**Objective**: Verify shape parsing, normalization, and selection

#### Test 1.1.1: Shape Normalization (Old Format)
```python
# Input: Old format (list only)
old_shape = [[1, 1], [1, 1]]  

# Expected: Converted to new format with defaults
expected = {
    "color": "#FFFFFF",
    "tipo": "RECTANGLE",
    "hp": 0,
    "damage": 0,
    "chance": 10,
    "speed": 0.1,
    "estados": [[[1, 1], [1, 1]]]
}

# Verify all fields present ✅
```

#### Test 1.1.2: Shape Normalization (New Format)
```python
# Input: New format (partial)
new_shape = {
    "color": "#00FF00",
    "tipo": "CIRCLE",
    "chance": 50,
    "estados": [[[1]]]
}

# Expected: All defaults filled
expected = {
    "color": "#00FF00",
    "tipo": "CIRCLE",
    "hp": 0,      # DEFAULT (missing)
    "damage": 0,  # DEFAULT (missing)
    "chance": 50, # KEPT
    "speed": 0.1, # DEFAULT (missing)
    "estados": [[[1]]]
}

# Verify all missing fields added ✅
```

#### Test 1.1.3: Weighted Selection
```python
# Input: 4 shapes with varying weights
shapes = {
    "A": {"chance": 100, ...},  # Must always be selected (weight=1.0)
    "B": {"chance": 50, ...},   # Selected 50% of time (weight=0.5)
    "C": {"chance": 25, ...},   # Selected 25% of time (weight=0.25)
    "D": {"chance": 25, ...},   # Selected 25% of time (weight=0.25)
}

# Expected: 100 selections → A appears ~100 times, B ~50 times, C ~25 times, D ~25 times
# Tolerance: ±10% variance acceptable
```

#### Test 1.1.4: Shape Access Edge Cases
```python
# Test missing shape → fallback to random rect ✅
# Test invalid shape format → skip, log warning ✅
# Test duplicate shape names → last one wins ✅
```

---

### Test Set 1.2: Level Management
**Objective**: Verify level parsing, defaults, and switching

#### Test 1.2.1: Level Defaults (Missing niveles)
```python
# Input: "niveles": {} (empty)
# Expected: DEFAULT level created
expected = {
    "DEFAULT": {
        "speed": 0.15,
        "poison_enabled": false,
        "clouds_enabled": false,
        "powerup_duration": 0
    }
}

# Verify DEFAULT exists ✅
```

#### Test 1.2.2: Multi-Level Support (Snake_Evolved)
```python
# Input: 3 levels (BABY, ENTHUSIAST, NYAN_CAT)
expected = {
    "BABY": {"speed": 0.05, "poison_enabled": true, ...},
    "ENTHUSIAST": {"speed": 0.15, "poison_enabled": true, "clouds_enabled": true, ...},
    "NYAN_CAT": {"speed": 0.30, "poison_enabled": false, ...}
}

# Verify all 3 levels accessible ✅
# Verify attributes apply when level switched ✅
```

#### Test 1.2.3: Level Switching (Keys 1/2/3)
```python
# Input: User presses key 1
# Expected: Current level → BABY
# - Speed changes to 0.05 ✅
# - Poison enabled ✅
# - Visual update (snake head shape/color if configured) ✅
```

---

### Test Set 1.3: Event System
**Objective**: Verify event dispatch, error handling, edge cases

#### Test 1.3.1: Event Dispatch Order
```python
# Expected order (guaranteed):
1. ON_START → initialize
2. ON_TICK → frame loop
3. ON_KEY_* → input handling
4. ON_COLLISION_* → collision detection
5. ON_LINE_CLEAR → if Tetris + full row
6. ON_POWERUP_ACTIVATE → if power-up triggered

# Verify no out-of-order execution ✅
```

#### Test 1.3.2: Missing Event Action
```python
# Input: Event with undefined action
{"action": "UNKNOWN_ACTION", ...}

# Expected: Logged to stderr, game continues ✅
# No crash ✅
```

#### Test 1.3.3: Invalid Event Format
```python
# Input: Event missing required field "action"
# Expected: Graceful skip, warning logged ✅
```

#### Test 1.3.4: Event with Parameter (TARGET_SCORE)
```python
# Input: ON TARGET_SCORE 500:
# Expected: Events.get('TARGET_SCORE_500') triggered at score >= 500 ✅
# Parameter extracted correctly ✅
```

---

### Test Set 1.4: Power-up System
**Objective**: Verify power-up triggering, effects, and game-type filtering

#### Test 1.4.1: Power-up Game-Type Filtering
```python
# Input: Tetris game type + power-up marked for SNAKE_EVOLVED
# Expected: Power-up silently ignored ✅
# No crash, no error ✅
```

#### Test 1.4.2: Column-Clear Power-up (Tetris)
```python
# Input: TETRIS game type + COLUMN_CLEAR power-up triggered
# Expected: One column cleared, score += 10 ✅
# Blocks above fall down ✅
```

#### Test 1.4.3: Invincibility Power-up (Snake)
```python
# Input: SNAKE_EVOLVED game type + INVINCIBILITY power-up triggered
# Expected: Duration counter started (300 ticks) ✅
# Snake immune to collisions for duration ✅
# Visual indicator shown (flashing or color change) ✅
```

#### Test 1.4.4: Power-up Duration Expiry
```python
# Input: INVINCIBILITY active, ticks counting down
# Expected: At tick 0, invincibility disabled ✅
# Snake can collide normally ✅
```

---

### Test Set 1.5: Collision Detection
**Objective**: Verify collision logic, edge cases, physics

#### Test 1.5.1: Block Collision (Tetris)
```python
# Input: Tetris block hits settled block
# Expected: Block locks, new shape spawns ✅
```

#### Test 1.5.2: Wall Collision (All games)
```python
# Input: Shape hits grid boundary
# Expected: 
#   - TETRIS: Block locks
#   - SNAKE: Game over ✅
#   - TANKS: Bounce or stop ✅
```

#### Test 1.5.3: Snake Self-Collision
```python
# Input: Snake head hits body
# Expected: Game over ✅
# Score preserved ✅
```

#### Test 1.5.4: Poison Fruit Collision (Snake_Evolved)
```python
# Input: Snake head hits poison fruit
# Expected: Game over ✅
# Score not increased ✅
```

#### Test 1.5.5: Cloud Obstacle Collision (Snake_Evolved)
```python
# Input: Snake head hits cloud
# Expected: Game over ✅
# Cloud remains (not consumed) ✅
```

#### Test 1.5.6: Tank Bullet Collision
```python
# Input: Player bullet hits enemy tank
# Expected: Enemy hp -= player.damage ✅
# If enemy.hp <= 0 → enemy removed ✅
# Score += 10 ✅
```

#### Test 1.5.7: Boss Collision
```python
# Input: Player bullet hits boss
# Expected: Boss hp -= player.damage ✅
# If boss.hp <= 0 → boss defeated, score += 100 ✅
```

---

## Phase 2: Integration Tests (Execution on Unified Runtime)

### Test Set 2.1: Game Startup
**Objective**: Verify each game type initializes correctly

#### Test 2.1.1: TETRIS Startup
```bash
python final_project/compiler.py tetris_remake/tetris_remake/tetris_remake.brick
python final_project/runtime.py tetris_remake/tetris_remake/tetris_remake.json

Expected:
✅ Window opens
✅ Grid 10x20 visible
✅ First Tetris shape appears
✅ Score: 0, Level: 0
```

#### Test 2.1.2: SNAKE Startup
```bash
python final_project/compiler.py snake_evolved/snake_evolved/games/snake_evolved.brick --level BABY
python final_project/runtime.py snake_evolved/snake_evolved/games/snake_evolved.json

Expected:
✅ Window opens
✅ Grid with snake (4 blocks) visible
✅ Food appears at random location
✅ Score: 0
```

#### Test 2.1.3: TETRIS_REMAKE Startup
```bash
Expected:
✅ Same as TETRIS
✅ Power-up icon visible (if configured)
```

#### Test 2.1.4: SNAKE_EVOLVED Startup
```bash
Expected:
✅ Same as SNAKE
✅ Level indicator (BABY) visible
✅ Poison fruit visible (if enabled)
✅ Cloud obstacles visible (if enabled)
```

#### Test 2.1.5: TANKS Startup
```bash
python final_project/runtime.py brick_tanks/brick_tanks/games/tanks.json

Expected:
✅ Window opens
✅ Grid with player tank (cyan, bottom-center)
✅ Enemy tanks visible
✅ Boss NOT visible yet (only at score 1000+)
✅ HP: 100 visible (top-left)
```

---

### Test Set 2.2: Gameplay Mechanics
**Objective**: Verify game mechanics work correctly in unified runtime

#### Test 2.2.1: TETRIS Block Rotation
```
Input: Press UP arrow
Expected: Current Tetris block rotates 90° CW ✅
```

#### Test 2.2.2: TETRIS Line Clearing
```
Input: Fill complete row
Expected:
✅ Row flashes (visual feedback)
✅ Row disappears
✅ Blocks above fall
✅ Score += 10
```

#### Test 2.2.3: SNAKE Movement
```
Input: Press arrow keys repeatedly
Expected:
✅ Snake moves in correct direction
✅ Snake cannot reverse into itself
✅ Smooth movement (no jitter)
```

#### Test 2.2.4: SNAKE Food Consumption
```
Input: Move snake head to food
Expected:
✅ Food disappears
✅ Snake grows 1 block (tail extends)
✅ New food spawns at random location
✅ Score += 1
```

#### Test 2.2.5: SNAKE_EVOLVED Poison Damage
```
Input: (requires poison_enabled) Move snake head to poison fruit
Expected:
✅ Game ends immediately
✅ Score NOT increased
✅ Game over screen shown
```

#### Test 2.2.6: SNAKE_EVOLVED Cloud Avoidance
```
Input: (requires clouds_enabled) Move snake near cloud
Expected:
✅ Cloud blocks movement (acts like wall)
✅ Snake bounces back
✅ Cloud not consumed (stays)
```

#### Test 2.2.7: SNAKE_EVOLVED Level Switch
```
Input: Start SNAKE_EVOLVED at BABY level, press key 2
Expected:
✅ Level changes to ENTHUSIAST
✅ Speed increases
✅ Poison/clouds configuration changes
✅ Game continues (no pause)
```

#### Test 2.2.8: TANKS Player Movement
```
Input: Press arrow keys
Expected:
✅ Player tank moves in grid (not smooth, block-by-block)
✅ Tank stays within grid bounds
✅ Tank rotation follows direction
```

#### Test 2.2.9: TANKS Shooting
```
Input: Press spacebar
Expected:
✅ Bullet spawns at player position
✅ Bullet travels upward (toward enemies)
✅ Bullet collision with enemy detected
✅ Enemy takes damage
```

#### Test 2.2.10: TANKS Enemy Spawning
```
Input: Game running, observe score increasing
Expected:
✅ Enemies spawn at edges periodically
✅ Enemy count increases with score
✅ Enemies move toward player
```

#### Test 2.2.11: TANKS Boss Spawn
```
Input: Accumulate score ≥ 1000
Expected:
✅ Boss spawns at center-top
✅ Boss larger/different appearance than enemies
✅ Boss has 500 HP (takes multiple hits)
✅ Defeating boss triggers score bonus
```

#### Test 2.2.12: TANKS HP System
```
Input: Enemy bullet hits player
Expected:
✅ Player HP -= enemy.damage
✅ HP display updates
✅ When HP <= 0 → game over ✅
```

---

### Test Set 2.3: Score System
**Objective**: Verify scoring logic correct for all game types

| Game Type | Action | Score Change |
|-----------|--------|--------------|
| TETRIS | Line clear | +10 per line |
| TETRIS_REMAKE | Power-up column clear | +10 |
| SNAKE | Consume food | +1 |
| SNAKE_EVOLVED | Consume food | +1 |
| SNAKE_EVOLVED | Consume poison | Game ends (no +) |
| TANKS | Hit enemy | +10 |
| TANKS | Hit boss | +100 |
| TANKS | Defeat boss | +1000 |

**Tests**:
- [ ] TETRIS: Clear 3 lines → score = 30
- [ ] SNAKE: Consume 5 foods → score = 5
- [ ] TANKS: Hit 3 enemies → score = 30
- [ ] TANKS: Defeat boss → score increases 1000+

---

### Test Set 2.4: Error Resilience
**Objective**: Verify game handles edge cases without crashing

#### Test 2.4.1: Rapid Key Presses
```
Input: Press arrow keys rapidly (50 per second)
Expected:
✅ Game handles without lag (or gracefully degrades)
✅ No crash
✅ Input queue processed correctly
```

#### Test 2.4.2: Invalid JSON (Missing Field)
```
Input: .json file missing "shapes" field
Expected:
✅ Warning logged to stderr
✅ Game uses empty shapes dict
✅ Continues with fallback behavior ✅
```

#### Test 2.4.3: Invalid Level Name
```
Input: Level name not in niveles dict
Expected:
✅ Current level unchanged
✅ User informed (stderr message)
✅ Game continues ✅
```

#### Test 2.4.4: Zero-Speed Level
```
Input: Level config with speed: 0
Expected:
✅ Game paused (nothing moves)
✅ No freeze/lag
✅ Resumable with key press ✅
```

#### Test 2.4.5: Negative HP
```
Input: Enemy takes 500 damage (only 100 HP)
Expected:
✅ HP clamped to 0 (not negative display)
✅ Enemy removed correctly
✅ Score applied ✅
```

---

### Test Set 2.5: Backward Compatibility
**Objective**: Verify old .brick files still work

#### Test 2.5.1: Old TETRIS Format
```
Source: Base 2026-1s tetris.brick
Run: python final_project/runtime.py old_tetris.json
Expected:
✅ Game runs identically to original
✅ Shapes normalize correctly
✅ Scoring unchanged
```

#### Test 2.5.2: Old SNAKE Format
```
Source: Base 2026-1s snake.brick
Expected:
✅ Game runs identically to original
✅ Food spawning unchanged
✅ Scoring unchanged
```

#### Test 2.5.3: Old Shape Format (List Only)
```json
"shapes": {
  "BLOCK": [[[1, 1], [1, 1]]]
}
```
Expected:
✅ Converted to new format automatically
✅ Game runs with correct shape visualization ✅

---

## Phase 3: Acceptance Tests (User Perspective)

### Test 3.1: User Workflow
**Scenario 1: Tetris Player**
```
1. Extract unified final_project/ folder
2. Run: python jugar.bat tetris_remake
3. Expected:
   ✅ Compilation succeeds
   ✅ Tetris game launches
   ✅ Game is playable
   ✅ No errors or warnings
```

**Scenario 2: Snake Player (Multi-Level)**
```
1. Extract unified final_project/ folder
2. Run: python jugar.bat snake_evolved
3. Expected:
   ✅ Compilation succeeds
   ✅ Snake game launches (BABY level)
   ✅ Press key 2 → switches to ENTHUSIAST
   ✅ All 3 levels accessible
   ✅ No errors
```

**Scenario 3: Tanks Player**
```
1. Extract unified final_project/ folder
2. Run: python jugar.bat tanks
3. Expected:
   ✅ Compilation succeeds
   ✅ Tanks game launches
   ✅ Player can move/shoot
   ✅ Boss appears at score 1000+
   ✅ No errors or crashes
```

---

## Test Execution Schedule

| Phase | Tests | Timeline | Criteria |
|-------|-------|----------|----------|
| **1: Unit** | 5 test sets | Before runtime.py implemented | All ✅ |
| **2: Integration** | 5 test sets | After runtime.py complete | All ✅ |
| **3: Acceptance** | 3 scenarios | Final validation | All ✅ |

---

## Success Criteria

✅ **All Phase 1 unit tests pass**  
✅ **All Phase 2 integration tests pass for all 5 game types**  
✅ **All Phase 3 acceptance scenarios complete without errors**  
✅ **No backward compatibility breaks**  
✅ **Performance acceptable (no lag, smooth gameplay)**  
✅ **Error messages helpful (users know what went wrong)**  

---

## Known Issues / Limitations

None identified at this planning stage.

---

## Test Report Location

Results saved to: `final_project/docs/TEST_RESULTS.md` (created after testing phase)
