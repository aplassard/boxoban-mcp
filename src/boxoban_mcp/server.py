import json
from mcp.server.fastmcp import FastMCP
from boxoban_mcp.loader import GameLoader
from boxoban_mcp.game_interface import GameInterface

# Global variable to hold the game interface instance
game_interface_instance: GameInterface | None = None

# Create an instance of FastMCP
mcp = FastMCP("Boxoban", host="0.0.0.0", port=8080)

@mcp.tool()
def get_game_rules() -> dict:
    """
    Returns the rules of the Boxoban game.
    This tool does not require a game to be loaded.
    """
    rules_string = """1.  **Objective:** The goal is to move every box (`$`) onto a target square (`.`). When a box is on a target, it's represented as `*`.
2.  **Player:** You control the player (`@`). If the player is on a target, it's represented as `+`.
3.  **Movement:**
    *   The player can move up, down, left, or right into an empty square (` `) or onto a target square (`.`).
    *   The player cannot move into a wall (`#`).
4.  **Pushing Boxes:**
    *   The player can push a single box (`$`) if the square immediately beyond the box (in the direction of the push) is either empty or a target.
    *   The player cannot push a box if the square beyond it is another box or a wall.
    *   Boxes cannot be pulled.
5.  **Winning:** The puzzle is solved when all target squares are occupied by boxes. There should be no boxes on non-target squares."""
    return {"status": "success", "game_rules": rules_string}

@mcp.tool()
def load_game(difficulty: str, split: str, puzzle_set_num: int, puzzle_num: int) -> dict:
    """
    Loads a Boxoban game instance based on the provided parameters.
    The loaded game is stored in a global variable for subsequent commands.
    """
    global game_interface_instance
    try:
        game_instance = GameLoader.load_game_from_params(
            difficulty=difficulty,
            split=split,
            puzzle_set_num=puzzle_set_num,
            puzzle_num=puzzle_num
        )
        game_interface_instance = GameInterface(game_instance)
        return {"status": "success", "message": f"Game loaded: {difficulty}/{split}/{puzzle_set_num:03d} puzzle {puzzle_num}"}
    except FileNotFoundError as e:
        game_interface_instance = None # Ensure instance is None if loading fails
        return {"status": "error", "message": str(e)}
    except Exception as e:
        game_interface_instance = None # Ensure instance is None if loading fails
        return {"status": "error", "message": f"An unexpected error occurred during game loading: {e}"}

@mcp.tool()
def get_game_state() -> dict:
    """
    Returns the current game state if a game is loaded.
    """
    global game_interface_instance
    if game_interface_instance is None:
        return {"status": "error", "message": "No game loaded. Call load_game first."}
    return {"status": "success", **game_interface_instance.return_game_state()}

@mcp.tool()
def get_valid_moves() -> dict:
    """
    Returns the valid moves for the current game state if a game is loaded.
    """
    global game_interface_instance
    if game_interface_instance is None:
        return {"status": "error", "message": "No game loaded. Call load_game first."}
    return {"status": "success", **game_interface_instance.get_valid_moves()}

@mcp.tool()
def take_action(action: str) -> dict:
    """
    Takes the given action in the current game if a game is loaded.
    """
    global game_interface_instance
    if game_interface_instance is None:
        return {"status": "error", "message": "No game loaded. Call load_game first."}
    result = game_interface_instance.take_action(action)
    return {"status": "success", **result}

@mcp.tool()
def take_action_list(actions: list[str]) -> dict:
    """
    Attempts to take a list of actions sequentially in the current game.
    Stops if an illegal action is encountered.
    """
    global game_interface_instance
    if game_interface_instance is None:
        return {"status": "error", "message": "No game loaded. Call load_game first."}

    result_dict = game_interface_instance.take_action_list(actions)
    return {"status": "success", **result_dict}

@mcp.tool()
def get_full_game_state() -> dict:
    """
    Returns the full game state, including actions taken and total actions.
    """
    global game_interface_instance
    if game_interface_instance is None:
        return {"status": "error", "message": "No game loaded. Call load_game first."}
    return {"status": "success", **game_interface_instance.return_full_game_state()}

@mcp.tool()
def is_solved() -> dict:
    """
    Checks if the current game is solved.
    """
    global game_interface_instance
    if game_interface_instance is None:
        return {"status": "error", "message": "No game loaded. Call load_game first."}
    solved_status = game_interface_instance.game.is_solved()
    return {"status": "success", "is_solved": solved_status}

def main():
    print("Starting Boxoban MCP server...")
    mcp.run()

if __name__ == "__main__":
    main()
    
