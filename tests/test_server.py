# tests/test_server.py

from src.boxoban_mcp.server import get_game_rules

def test_get_game_rules():
    """
    Tests the get_game_rules MCP tool from the server.
    """
    expected_rules = """1.  **Objective:** The goal is to move every box (`$`) onto a target square (`.`). When a box is on a target, it's represented as `*`.
2.  **Player:** You control the player (`@`). If the player is on a target, it's represented as `+`.
3.  **Movement:**
    *   The player can move up, down, left, or right into an empty square (` `) or onto a target square (`.`).
    *   The player cannot move into a wall (`#`).
4.  **Pushing Boxes:**
    *   The player can push a single box (`$`) if the square immediately beyond the box (in the direction of the push) is either empty or a target.
    *   The player cannot push a box if the square beyond it is another box or a wall.
    *   Boxes cannot be pulled.
5.  **Winning:** The puzzle is solved when all target squares are occupied by boxes. There should be no boxes on non-target squares."""

    result = get_game_rules()

    assert result is not None
    assert "status" in result
    assert result["status"] == "success"
    assert "game_rules" in result
    assert isinstance(result["game_rules"], str)
    assert len(result["game_rules"]) > 0
    assert result["game_rules"] == expected_rules
