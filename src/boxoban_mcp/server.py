import json
from mcp.server.fastmcp import FastMCP
from .loader import GameLoader
from .game_interface import GameInterface

# Global variable to hold the game interface instance
game_interface_instance: GameInterface | None = None

# Create an instance of FastMCP
mcp_server = FastMCP()

@mcp_server.command
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

@mcp_server.tool()
def get_game_state() -> dict:
    """
    Returns the current game state if a game is loaded.
    """
    global game_interface_instance
    if game_interface_instance is None:
        return {"status": "error", "message": "No game loaded. Call load_game first."}
    return {"status": "success", **game_interface_instance.return_game_state()}

@mcp_server.tool()
def get_valid_moves() -> dict:
    """
    Returns the valid moves for the current game state if a game is loaded.
    """
    global game_interface_instance
    if game_interface_instance is None:
        return {"status": "error", "message": "No game loaded. Call load_game first."}
    return {"status": "success", **game_interface_instance.get_valid_moves()}

@mcp_server.tool()
def take_action(action: str) -> dict:
    """
    Takes the given action in the current game if a game is loaded.
    """
    global game_interface_instance
    if game_interface_instance is None:
        return {"status": "error", "message": "No game loaded. Call load_game first."}
    result = game_interface_instance.take_action(action)
    return {"status": "success", **result}

@mcp_server.tool()
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

@mcp_server.tool()
def get_heuristic_score() -> dict:
    """
    Calculates and returns the heuristic score for the current game state.
    """
    global game_interface_instance
    if game_interface_instance is None:
        return {"status": "error", "message": "No game loaded. Call load_game first."}
    score = game_interface_instance.get_heuristic_score()
    return {"status": "success", "heuristic_score": score}

@mcp_server.tool()
def get_full_game_state() -> dict:
    """
    Returns the full game state, including actions taken and total actions.
    """
    global game_interface_instance
    if game_interface_instance is None:
        return {"status": "error", "message": "No game loaded. Call load_game first."}
    return {"status": "success", **game_interface_instance.return_full_game_state()}

@mcp_server.tool()
def is_solved() -> dict:
    """
    Checks if the current game is solved.
    """
    global game_interface_instance
    if game_interface_instance is None:
        return {"status": "error", "message": "No game loaded. Call load_game first."}
    solved_status = game_interface_instance.game.is_solved()
    return {"status": "success", "is_solved": solved_status}

@mcp_server.command
def pretty_print_game_state_on_server() -> dict:
    """
    Pretty prints the current game state on the server console.
    Useful for debugging.
    """
    global game_interface_instance
    if game_interface_instance is None:
        return {"status": "error", "message": "No game loaded. Call load_game first."}
    try:
        print("--- Game State (Pretty Print) ---")
        game_interface_instance.pretty_print_game_state()
        print("---------------------------------")
        return {"status": "success", "message": "Game state printed on server console."}
    except Exception as e:
        return {"status": "error", "message": f"Error pretty printing: {e}"}


if __name__ == "__main__":
    # The mcp.server.runner.run_server is one way to run it,
    # but FastMCP objects also have a built-in run() method.
    print("Starting Boxoban MCP server...")
    mcp_server.run(host="127.0.0.1", port=65432)
