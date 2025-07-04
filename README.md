# Boxoban Game Engine

This repository provides a Python-based game engine for Boxoban, a box-pushing puzzle game inspired by Sokoban. The engine allows for loading game levels, representing the game state, identifying valid moves, and taking actions.

## Installation

To use the `BoxobanGame` class in your own projects, you first need to install it. Navigate to the root directory of this repository in your terminal.

It's recommended to use a virtual environment:
```bash
uv venv
source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
```

Then, install the package. For a regular install:
```bash
uv pip install .
```
For an editable install (allows you to make changes to the source code and have them immediately reflected):
```bash
uv pip install -e .
```

After installation, you can import the game class as shown in the examples below.

## Game Representation

The game is played on a grid. The following symbols are used to represent the game elements:

*   `#`: Wall - Impassable.
*   `@`: Player - The character controlled by the user.
*   `$`: Box - An object that can be pushed by the player.
*   `.`: Target - A destination square for a box.
*   ` `: Empty - An empty square.
*   `+`: Player on Target - The player is currently on a target square.
*   `*`: Box on Target - A box is currently on a target square.

The objective of the game is to push all boxes (`$`) onto all target squares (`.`). When a box is on a target, it is represented as `*`.

## `BoxobanGame` Class

The core of the engine is the `BoxobanGame` class, located in `boxoban_mcp.game` once installed.

### Initialization and Loading Games

You can load a game in several ways:

1.  **From a string:**
    ```python
    from boxoban_mcp import GameLoader # For loading
    # from boxoban_mcp import BoxobanGame # If you need to type hint or refer to the game class directly

    board_string = "####\\n#@$.#\\n####"
    # Represents:
    # ####
    # #@$.#  (Player, Box, Target)
    # ####
    game = GameLoader.load_game_from_string(board_string) # Returns a BoxobanGame instance
    ```

2.  **From a file:**
    Puzzle files can contain multiple puzzles, separated by a semicolon and a puzzle number (e.g., `0\nPuzzleData0;1\nPuzzleData1`).
    The game engine will automatically download and cache puzzle files if they are not found locally.
    ```python
    from boxoban_mcp import GameLoader

    # The engine will attempt to load this from a local cache or download it.
    # Example: puzzles/medium/train/000.txt
    # And puzzle 0 in that file is "####\\n#@.#\\n####"
    game = GameLoader.load_game_from_file("medium/train/000.txt", puzzle_index=0)
    ```
    If a file contains only a single puzzle string without a preceding index number, use `puzzle_index=0`.
    When using `load_game_from_file`, the path provided should be relative to the root of the cached puzzle structure (e.g., `difficulty/split/filename.txt`).

3.  **From parameters:**
    This is the recommended method for loading standard puzzles. It automatically handles downloading and caching.
    The game will construct the necessary paths and fetch files from an online repository if not found in the local cache (typically located in your system's temporary directory).
    ```python
    from boxoban_mcp import GameLoader

    # Loads puzzle 12 from the 'medium' difficulty, 'train' split, set '001'.
    # Files will be downloaded and cached if not present locally.
    game = GameLoader.load_game_from_params( # Corrected: GameLoader
        difficulty="medium",
        split="train",
        puzzle_set_num="001", # or e.g. 1
        puzzle_num=12
    )
    ```

### Interacting with the Game

Once a game is loaded:

*   **Get Game State:**
    Returns the current board as a string, using the symbols described above (including `+` and `*`).
    ```python
    state_string = game.get_game_state()
    print(state_string)
    # Example output:
    # #####
    # # @*#  (Player is next to a Box on a Target)
    # #####
    ```

*   **Get Valid Moves:**
    Returns a list of valid actions the player can currently take. Actions are strings: `'up'`, `'down'`, `'left'`, `'right'`.
    ```python
    valid_moves = game.get_valid_moves()
    # e.g., ['up', 'right']
    ```

*   **Take Action:**
    Applies an action to the game state. Returns `True` if the action was legal and performed, `False` otherwise.
    ```python
    if 'right' in game.get_valid_moves():
        was_legal = game.take_action('right')
        if was_legal:
            print("Moved right!")
            print(game.get_game_state())
    ```
    The `take_action` method will update the player's position and any pushed box. If the player pushes a box into a wall or another box, the action is illegal.

*   **Check if Solved:**
    Returns `True` if all boxes are on target squares, `False` otherwise.
    ```python
    if game.is_solved():
        print("Puzzle solved!")
    ```

## Development and Testing

This project uses `uv` for package management and `pytest` for testing.

1.  **Setup (using uv):**
    If you plan to contribute or run tests, set up a virtual environment and install development dependencies:
    ```bash
    uv venv
    source .venv/bin/activate
    uv pip install -e .[dev] # Installs the package in editable mode along with dev dependencies like pytest
    ```

2.  **Running Tests:**
    Navigate to the root of the repository and run:
    ```bash
    pytest
    ```

## Original Dataset Information (Citation)

If you use the underlying Boxoban level dataset in your work (the game automatically downloads levels based on this dataset's structure), please cite the original authors:

**Note on the local `puzzles/` directory:**
The `puzzles/` directory included in this repository is for reference and historical purposes. The game engine now automatically downloads and caches the required puzzle files from an online source into a temporary directory on your system when `load_game_from_params` (or `load_game_from_file` if the file isn't in the cache) is called. Therefore, the local `puzzles/` directory is no longer actively used by the game logic for loading levels and can be manually removed from your local clone of the repository if desired.

```bibtex
@misc{boxobanlevels,
author = {Arthur Guez and Mehdi Mirza and Karol Gregor and Rishabh Kabra and Sebastien Racaniere and Theophane Weber and David Raposo and Adam Santoro and Laurent Orseau and Tom Eccles and Greg Wayne and David Silver and Timothy Lillicrap and Victor Valdes},
title = {An investigation of Model-free planning: boxoban levels},
howpublished= {https://github.com/deepmind/boxoban-levels/},
year = "2018"
}
```
Questions regarding the dataset can be directed to Theophane Weber (theophane@google.com).

This is not an official Google product.

## Boxoban MCP Server

A Model Context Protocol (MCP) server for interacting with the Boxoban game is available in `src/boxoban_mcp/server.py`.

This server allows loading Boxoban puzzles and interacting with them using standard MCP tools.

### Running the Server

To run the MCP server locally:

```bash
python src/boxoban_mcp/server.py
```

This will start the server, typically on `127.0.0.1:65432`. You can then connect to it using an MCP client or development tools like `mcp dev`.

### Available Tools (partial list)

- `load_game(difficulty: str, split: str, puzzle_set_num: int, puzzle_num: int)`: Loads a specific game.
- `get_game_state()`: Returns the current board state.
- `get_valid_moves()`: Lists valid moves.
- `take_action(action: str)`: Performs an action.
- `take_action_list(actions: list[str])`: Performs a sequence of actions.
- `return_full_game_state()`: Provides a comprehensive game state.

(Note: Tool names in the server implementation might slightly differ, e.g., `get_full_game_state` for `return_full_game_state`. Refer to the server code for exact names.)
