The solution must be provided as a JSON object with exactly two keys:

```json
{
  "path": "string containing pipe-delimited path notation",
  "analysis": "string containing full explanation and reasoning"
}
```

**Key Specifications:**
- **`path`**: A string value containing ONLY the pipe-delimited notation. No extra text, explanations, or MP counts.
- **`analysis`**: A string value containing the complete explanation of the solution, including:
  - Reasoning for the chosen route
  - Why this path is optimal
  - Total MP count and breakdown
  - Alternative paths considered
  - Any strategic decisions made


### Pipe-Delimited Path Notation

The solution path should be encoded as a pipe-delimited string with the following format:

**Basic Format:**
```
TILE|TILE|TILE|...|TILE
```

**Special Actions:**
- **Collecting items**: `TILE:item_name` (e.g., `E24:ladder`, `C4:key`, `D1:dynamite`)
- **Using dynamite**: `clear:TILE` (e.g., `clear:C2`)
- **Regular movement**: Just the tile name (e.g., `C1`, `B4`)

**Rules:**
1. Each element is separated by a pipe character `|`
2. Path starts from the starting position and ends at A1
3. Include every tile visited in sequence
4. Item collection is marked with colon after the tile (e.g., `E24:ladder`)
5. Dynamite usage is marked as `clear:TILE` where TILE is the blocked tile being cleared
6. No spaces around pipes
