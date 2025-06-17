# Boxoban Game Engine

This repository provides a Python-based game engine for Boxoban, a box-pushing puzzle game inspired by Sokoban. The engine allows for loading game levels, representing the game state, identifying valid moves, and taking actions.

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

The core of the engine is the `BoxobanGame` class, located in `src.boxoban_mcp.game`.

### Initialization and Loading Games

You can load a game in several ways:

1.  **From a string:**
    ```python
    from src.boxoban_mcp.game import BoxobanGame

    board_string = "####\n#@$.#\n####"
    # Represents:
    # ####
    # #@$.#  (Player, Box, Target)
    # ####
    game = BoxobanGame.load_game_from_string(board_string)
    ```

2.  **From a file:**
    Puzzle files can contain multiple puzzles, separated by a semicolon and a puzzle number (e.g., `0\nPuzzleData0;1\nPuzzleData1`).
    ```python
    # Assuming 'puzzles/medium/train/000.txt' exists
    # And puzzle 0 in that file is "####\n#@.#\n####"
    game = BoxobanGame.load_game_from_file("puzzles/medium/train/000.txt", puzzle_index=0)
    ```
    If a file contains only a single puzzle string without a preceding index number, use `puzzle_index=0`.

3.  **From parameters:**
    This method constructs the path to standard puzzle files within the `puzzles/` directory.
    ```python
    # Loads puzzle 12 from puzzles/medium/train/001.txt
    game = BoxobanGame.load_game_from_params(
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
    It's recommended to set up a virtual environment.
    ```bash
    uv venv
    source .venv/bin/activate
    uv pip install pytest
    ```

2.  **Running Tests:**
    Navigate to the root of the repository and run:
    ```bash
    pytest
    ```

## Original Dataset Information (Citation)

If you use the underlying Boxoban level dataset in your work (found in the `puzzles/` directory), please cite the original authors:

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
