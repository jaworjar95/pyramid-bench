# PYRAMID PUZZLE - GAME RULES

---

## **PYRAMID PUZZLE - GAME RULES**

### **Objective**

Reach the peak of the pyramid (tile A1) after collecting the Key, using the minimum number of Movement Points (MP).

---

### **PYRAMID STRUCTURE & LAYOUT**

The pyramid is a five-level, four-sided structure. For gameplay, it's best to visualize it from a **top-down perspective**, like a series of concentric squares.

| Level | Symbol | Total Tiles | Tiles per Side | Tile Range |
| --- | --- | --- | --- | --- |
| Peak | A | 1 (Center) | - | A1 |
| 4th | B | 4 | 1 | B1 to B4 |
| 3rd | C | 8 | 2 | C1 to C8 |
| 2nd | D | 16 | 4 | D1 to D16 |
| Base | E | 32 | 8 | E1 to E32 |

**Tile Numbering**:

Tiles are numbered **counter-clockwise** around each square level.

- **E1** is the bottom-left corner of the entire pyramid base.
- The numbering continues up the left side, across the top, down the right side, and across the bottom back to the start.
- **Corner Tiles on Level E**: E1, E9, E17, E25.

---

### **MOVEMENT SYSTEM**

From most tiles, you can move in up to 5 directions. Think of movement as either moving *around* a level, moving *inward* to a higher level, or *outward* to a lower level.

### **Notation**

XY - represents the single tile on the pyramid:
- X: represents the level on the pyramid, for example B
- Y: represents number of the the tile on the level X, for example 8
- Xmax: max value of Y for the level X:
    A - 1
    B - 4
    C - 8
    D - 16
    E - 32

### **1. AROUND**

This is like walking along the edge of one of the pyramid's square layers.

**COUNTER-CLOCKWISE**

- **From**: XY
- **To**: X(Y-1), or X(Xmax) if Y=1 (this is just turning a corner).
- *Example*: C3 → C2. From corner C1, the next tile counter-clockwise is C8.

**CLOCKWISE**

- **From**: XY
- **To**: X(Y+1), or X1 if Y=Xmax (this is just turning a corner).
- *Example*: C7 → C8. From corner C8, the next tile clockwise is C1.

### **2. INWARD (Up a Level)**

You move from your current tile to the single tile on the level above that rests over it. Each upper tile connects to two adjacent lower tiles.

- **From**: XY
- **To**: (X+1)⌈Y/2⌉
- *Example*: Both **E5** and **E6** are "underneath" **D3**. Moving Inward from either E5 or E6 takes you to D3.

### **3. OUTWARD (Down a Level)**

You move from your current tile to one of the two tiles directly beneath it on the level below.

**OUTWARD-LEFT**

- **From**: XY
- **To**: (X-1)(2Y-1)
- *Example*: From C3, you can move Outward-Left to **D5**.

**OUTWARD-RIGHT**

- **From**: XY
- **To**: (X-1)(2Y)
- *Example*: From C3, you can move Outward-Right to **D6**.

### **Special Cases**

- **Starting Position**: Players can start from any E-level tile (E1 through E32).
- **From the Peak (A1)**: Can only move OUTWARD to any B tile (B1, B2, B3, or B4).
- **To the Peak (A1)**: All B tiles can move INWARD to A1.
- **From the Base (E-Tiles)**: Cannot move OUTWARD.

---

### **MOVEMENT COSTS**

| Movement Direction | Base Cost | With Ladder |
| --- | --- | --- |
| Clockwise / Counter-Clockwise | 1 MP | 1 MP |
| Outward-Left / Outward-Right | 1 MP | 1 MP |
| **Inward (Up a Level)** | **2 MP** | **1 MP** |

---

### **SPECIAL TILES**

| Tile Type | Effect | Cost to Use |
| --- | --- | --- |
| **Blocked** | Cannot enter this tile. | - |
| **Key** | Required to enter A1 and win the game. | 0 MP to collect |
| **Dynamite** | Clears any blocked tile permanently on the pyramid (single use). Basically means you can enter ONE blocked tile after colecting the dynamite | 0 MP to use |
| **Ladder** | Permanent: All INWARD moves now cost only 1 MP. | 0 MP to collect |
| **Goal (A1)** | Victory tile (requires Key). | - |
