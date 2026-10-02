# Cube Moves and Algorithms

CubeAI's TypeScript cube model and notation parser support the six face turns in Singmaster notation.

## Supported moves

| Face | Meaning |
|---|---|
| `U` | Up face, clockwise |
| `D` | Down face, clockwise |
| `R` | Right face, clockwise |
| `L` | Left face, clockwise |
| `F` | Front face, clockwise |
| `B` | Back face, clockwise |

Add a suffix to change the turn:

- No suffix: quarter-turn clockwise, such as `R`
- Apostrophe (`'`): quarter-turn counter-clockwise, such as `R'`
- `2`: half-turn, such as `R2`

A sequence is written as space-separated moves:

```text
R U R' U'
```

The parser trims whitespace and rejects unsupported tokens. Wide turns (`Rw`), slice turns (`M`, `E`, `S`), and whole-cube rotations (`x`, `y`, `z`) are not supported by this TypeScript notation parser.

## Basic identities

```text
R R'       returns to the starting state
U U U U    returns to the starting state
R2 R2      returns to the starting state
```

For TypeScript use, `Move` is a union of face letters and the `''`, `'`, or `2` modifier. The API uses a different object form: `{ "face": "R", "times": 3 }` means `R'`.

See [Testing](testing.md) for move and notation test commands.