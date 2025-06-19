import sys
import os # os is already imported, but sys.path needs it before other imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import pytest
import os
from src.boxoban_mcp.game import BoxobanGame
from src.boxoban_mcp.loader import GameLoader

# Helper to create a dummy puzzle file
def create_dummy_puzzle_file(filepath, content):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        f.write(content)

# Sample board strings for testing
SIMPLE_BOARD_STR = "####\n#@.#\n####" # Corrected to \n for internal consistency if used directly
BOARD_WITH_BOX_STR = "#####\n#@$.#\n#####"
BOARD_FOR_PARAMS_STR = "#####\n# $.#\n# @ #\n#####" # This is used for get_game_state() comparison
SOLVED_BOARD_STR = "####\n# *#\n####"
SOLVABLE_SETUP_STR = "#####\n#@$ .#\n#####"
COMPLEX_BOARD_STR = "#######\n#.@ # #\n#$$ # #\n# . # #\n#######"

def test_load_game_from_string():
    game = GameLoader.load_game_from_string(SIMPLE_BOARD_STR.replace("\\n", "\n")) # Ensure actual newlines
    assert game.player_pos == (1, 1)
    assert (1, 2) in game._targets
    assert game.board[1, 1] == BoxobanGame.ORD_PLAYER
    assert game.board[1, 2] == BoxobanGame.ORD_TARGET
    assert game.get_game_state() == SIMPLE_BOARD_STR.replace("\\n", "\n")

def test_load_game_from_string_player_on_target():
    board_str = "####\n#+.#\n####"
    game = GameLoader.load_game_from_string(board_str)
    assert game.player_pos == (1, 1)
    assert (1, 1) in game._targets
    assert (1, 2) in game._targets
    assert game.board[1, 1] == BoxobanGame.ORD_PLAYER
    assert game.get_game_state() == board_str

def test_load_game_from_string_box_on_target():
    board_str = "####\n#*.#\n####"
    with pytest.raises(ValueError, match="Player .* not found"):
        GameLoader.load_game_from_string(board_str)

    board_str_with_player = "####\n#*@#\n####"
    game = GameLoader.load_game_from_string(board_str_with_player)
    assert game.player_pos == (1, 2)
    assert (1, 1) in game._targets
    assert game.board[1, 1] == BoxobanGame.ORD_BOX
    assert game.board[1, 2] == BoxobanGame.ORD_PLAYER
    assert game.get_game_state() == board_str_with_player

@pytest.fixture
def temp_puzzle_file_first(tmp_path): # Renamed to avoid collision
    file_content = "0\n####\n#@.#\n####;1\n#####\n#@$.#\n#####" # Use \n
    filepath = tmp_path / "test_puzzles_first.txt"
    create_dummy_puzzle_file(filepath, file_content)
    return filepath

def test_load_game_from_file_first_set(temp_puzzle_file_first): # Renamed
    game0 = GameLoader.load_game_from_file(temp_puzzle_file_first, puzzle_index=0)
    assert game0.player_pos == (1,1)
    assert game0.get_game_state() == "####\n#@.#\n####"
    game1 = GameLoader.load_game_from_file(temp_puzzle_file_first, puzzle_index=1)
    assert game1.player_pos == (1,1)
    assert game1.board[1, 2] == BoxobanGame.ORD_BOX
    assert (1,3) in game1._targets
    assert game1.get_game_state() == "#####\n#@$.#\n#####"

def test_load_game_from_file_single_raw_first(tmp_path): # Renamed
    file_content = "####\n#@.#\n####"
    filepath = tmp_path / "single_raw_first.txt"
    create_dummy_puzzle_file(filepath, file_content)
    game = GameLoader.load_game_from_file(filepath, puzzle_index=0)
    assert game.get_game_state() == file_content

def test_load_game_from_file_single_with_header_first(tmp_path): # Renamed
    file_content = "0\n####\n#@.#\n####"
    filepath = tmp_path / "single_with_header_first.txt"
    create_dummy_puzzle_file(filepath, file_content)
    game = GameLoader.load_game_from_file(filepath, puzzle_index=0)
    assert game.get_game_state() == "####\n#@.#\n####"
    with pytest.raises(ValueError):
        GameLoader.load_game_from_file(filepath, puzzle_index=1)

@pytest.fixture
def temp_puzzle_cache_first(tmp_path): # Renamed fixture
    difficulty = "medium"
    split = "train"
    puzzle_set_num_str = "001"
    # GameLoader expects files directly under CACHE_DIR/difficulty/split/
    full_dir = tmp_path / difficulty / split
    os.makedirs(full_dir, exist_ok=True)
    # Use \n for board content as get_game_state returns that
    board_content_for_file = BOARD_FOR_PARAMS_STR
    file_content = f"12\n{board_content_for_file}"
    filepath = full_dir / f"{puzzle_set_num_str}.txt"
    with open(filepath, 'w') as f:
        f.write(file_content)
    return tmp_path

def test_load_game_from_params_first(temp_puzzle_cache_first, monkeypatch): # Renamed
    monkeypatch.setattr(GameLoader, 'CACHE_DIR', temp_puzzle_cache_first)
    expected_board_content = BOARD_FOR_PARAMS_STR
    game = GameLoader.load_game_from_params("medium", "train", 1, 12)
    assert game.get_game_state() == expected_board_content
    assert game.player_pos == (2,2)
    game_str_num = GameLoader.load_game_from_params("medium", "train", "001", 12)
    assert game_str_num.get_game_state() == expected_board_content

# Consolidating and correcting tests based on the first block's structure, removing \\n, using ORD_, tuples for pos
def test_get_valid_moves_simple_first(): # Renamed
    game = GameLoader.load_game_from_string("####\n#@ #\n####")
    assert sorted(game.get_valid_moves()) == sorted(['right'])
    game_open = GameLoader.load_game_from_string("# #\n @ \n# #")
    assert sorted(game_open.get_valid_moves()) == sorted(['up', 'down', 'left', 'right'])

def test_get_valid_moves_wall_first(): # Renamed
    game = GameLoader.load_game_from_string("###\n#@#\n###")
    assert game.get_valid_moves() == []

def test_get_valid_moves_push_box_empty_behind_first(): # Renamed
    game = GameLoader.load_game_from_string("#@$ #")
    assert game.get_valid_moves() == ['right']
    game_left = GameLoader.load_game_from_string("# $@#")
    assert game_left.get_valid_moves() == ['left']

def test_get_valid_moves_push_box_wall_behind_first(): # Renamed
    game = GameLoader.load_game_from_string("#@$#")
    assert game.get_valid_moves() == []
    game_blocked_both_sides = GameLoader.load_game_from_string("##$@$##")
    assert game_blocked_both_sides.get_valid_moves() == [] # Corrected to assert on game_blocked_both_sides

def test_take_action_move_empty_first(): # Renamed
    game = GameLoader.load_game_from_string("####\n#@ #\n####")
    assert game.take_action('right') is True
    assert game.player_pos == (1, 2)
    assert game.board[1, 1] == BoxobanGame.ORD_EMPTY
    assert game.board[1, 2] == BoxobanGame.ORD_PLAYER
    assert game.get_game_state() == "####\n# @#\n####"

def test_take_action_move_to_target_first(): # Renamed
    game = GameLoader.load_game_from_string("####\n#@.#\n####")
    assert game.take_action('right') is True
    assert game.player_pos == (1, 2)
    assert game.board[1, 1] == BoxobanGame.ORD_EMPTY
    assert game.board[1, 2] == BoxobanGame.ORD_PLAYER
    assert (1,2) in game._targets
    assert game.get_game_state() == "####\n# +#\n####"

def test_take_action_move_from_target_first(): # Renamed
    game = GameLoader.load_game_from_string("####\n#+ #\n####")
    assert game.take_action('right') is True
    assert game.player_pos == (1, 2)
    assert game.board[1, 1] == BoxobanGame.ORD_TARGET
    assert game.board[1, 2] == BoxobanGame.ORD_PLAYER
    assert game.get_game_state() == "####\n#.@#\n####"

def test_take_action_push_box_first(): # Renamed
    game = GameLoader.load_game_from_string("#@$ #")
    assert game.take_action('right') is True
    assert game.player_pos == (0, 2)
    assert game.board[0, 1] == BoxobanGame.ORD_EMPTY
    assert game.board[0, 2] == BoxobanGame.ORD_PLAYER
    assert game.board[0, 3] == BoxobanGame.ORD_BOX
    assert game.get_game_state() == "# @$#"

def test_take_action_push_box_to_target_first(): # Renamed
    game = GameLoader.load_game_from_string("#@$.#")
    assert game.take_action('right') is True
    assert game.player_pos == (0, 2)
    assert game.board[0, 1] == BoxobanGame.ORD_EMPTY
    assert game.board[0, 2] == BoxobanGame.ORD_PLAYER
    assert game.board[0, 3] == BoxobanGame.ORD_BOX
    assert (0,3) in game._targets
    assert game.get_game_state() == "# @*#"

def test_take_action_push_box_from_target_first(): # Renamed
    game = GameLoader.load_game_from_string("#@* #")
    assert game.player_pos == (0,1)
    assert game.board[0, 2] == BoxobanGame.ORD_BOX
    assert (0,2) in game._targets
    assert game.take_action('right') is True
    assert game.player_pos == (0, 2)
    assert game.board[0, 1] == BoxobanGame.ORD_EMPTY
    assert game.board[0, 2] == BoxobanGame.ORD_PLAYER
    assert game.board[0, 3] == BoxobanGame.ORD_BOX
    assert (0,2) in game._targets
    assert game.get_game_state() == "# +$#"

def test_take_action_invalid_move_wall_first(): # Renamed
    game = GameLoader.load_game_from_string("####\n#@##\n####")
    assert game.take_action('right') is False
    assert game.player_pos == (1, 1)
    assert game.get_game_state() == "####\n#@##\n####"

def test_take_action_invalid_push_wall_first(): # Renamed
    game = GameLoader.load_game_from_string("#@$#")
    assert game.take_action('right') is False
    assert game.player_pos == (0, 1)
    assert game.board[0, 2] == BoxobanGame.ORD_BOX
    assert game.get_game_state() == "#@$#"

def test_is_solved_first(): # Renamed
    game1 = GameLoader.load_game_from_string("####\n#@*#\n####")
    assert game1.is_solved() is True
    game2 = GameLoader.load_game_from_string("####\n#+*#\n####")
    assert game2.is_solved() is False
    game3_str = "#*#\n#*#"
    with pytest.raises(ValueError):
        GameLoader.load_game_from_string(game3_str)
    game3_ok_str = "#*@\n#*#"
    game3 = GameLoader.load_game_from_string(game3_ok_str)
    assert game3.is_solved() is True

def test_is_not_solved_first(): # Renamed
    game = GameLoader.load_game_from_string("####\n#@$.#\n####")
    assert game.is_solved() is False
    game2 = GameLoader.load_game_from_string("####\n#@ .#\n####")
    assert game2.is_solved() is False
    game3_with_box = GameLoader.load_game_from_string("#+$ .#")
    assert game3_with_box.is_solved() is False
    game4 = GameLoader.load_game_from_string("#@$ .#")
    assert game4.is_solved() is False

def test_full_game_sequence_solve_first(): # Renamed
    game = GameLoader.load_game_from_string("#####\n#@$.#\n#####")
    assert game.is_solved() is False
    assert game.take_action('right') is True
    assert game.player_pos == (1,2)
    assert game.board[1,3] == BoxobanGame.ORD_BOX
    assert (1,3) in game._targets
    assert game.get_game_state() == "#####\n# @*#\n#####"
    assert game.is_solved() is True

# --- Start of the (mostly) duplicated test section ---
# I will apply the same fixes here.
# Removed 'import unittest' as it's not standard for pytest files and was oddly placed.
# pytest, os, numpy, BoxobanGame, GameLoader are already imported at the top.

# Renaming tests in this section to avoid pytest collection errors if names are identical.
# And applying GameLoader and consistency fixes.

def test_load_game_from_string_second(): # Note: Original was load_game_from_file but named ..._string
    board_str_content = "####\n#@.#\n####" # Using consistent \n
    game = GameLoader.load_game_from_string(board_str_content) # Changed to load_game_from_string
    assert game.player_pos == (1, 1)
    assert (1, 2) in game._targets
    assert game.board[1, 1] == BoxobanGame.ORD_PLAYER
    assert game.board[1, 2] == BoxobanGame.ORD_TARGET
    assert game.get_game_state() == board_str_content

def test_load_game_from_string_player_on_target_second():
    board_str_content = "####\n#+.#\n####"
    game = GameLoader.load_game_from_string(board_str_content) # Changed to load_game_from_string
    assert game.player_pos == (1, 1)
    assert (1, 1) in game._targets
    assert (1, 2) in game._targets
    assert game.board[1, 1] == BoxobanGame.ORD_PLAYER
    assert game.get_game_state() == board_str_content

def test_load_game_from_string_box_on_target_second():
    board_str_no_player = "####\n#*.#\n####"
    with pytest.raises(ValueError, match="Player .* not found"):
        GameLoader.load_game_from_string(board_str_no_player) # Changed to load_game_from_string

    board_str_with_player = "####\n#*@#\n####"
    game = GameLoader.load_game_from_string(board_str_with_player) # Changed to load_game_from_string
    assert game.player_pos == (1, 2)
    assert (1, 1) in game._targets
    assert game.board[1, 1] == BoxobanGame.ORD_BOX
    assert game.board[1, 2] == BoxobanGame.ORD_PLAYER
    assert game.get_game_state() == board_str_with_player


@pytest.fixture
def temp_puzzle_file_second(tmp_path): # Renamed fixture
    # Using the actual file content from tests/data for consistency
    with open("tests/data/multi_puzzle_test.txt", "r") as f:
        file_content = f.read()
    filepath = tmp_path / "test_puzzles_second.txt"
    create_dummy_puzzle_file(filepath, file_content)
    return filepath

def test_load_game_from_file_second_set(temp_puzzle_file_second): # Renamed
    game0 = GameLoader.load_game_from_file(temp_puzzle_file_second, puzzle_index=0)
    assert game0.player_pos == (1, 1)
    assert game0.get_game_state() == "####\n#@.#\n####"

    game1 = GameLoader.load_game_from_file(temp_puzzle_file_second, puzzle_index=1)
    assert game1.player_pos == (1, 1)
    assert game1.board[1, 2] == BoxobanGame.ORD_BOX
    assert (1,3) in game1._targets
    assert game1.get_game_state() == "#####\n#@$.#\n#####"

def test_load_game_from_file_single_raw_second(tmp_path): # Renamed
    game = GameLoader.load_game_from_file("tests/data/simple_board.txt", puzzle_index=0)
    assert game.get_game_state() == "####\n#@.#\n####"

def test_load_game_from_file_single_with_header_second(tmp_path): # Renamed
    filepath = "tests/data/single_with_header.txt"
    game = GameLoader.load_game_from_file(filepath, puzzle_index=0)
    assert game.get_game_state() == "####\n#@.#\n####"
    with pytest.raises(ValueError):
        GameLoader.load_game_from_file(filepath, puzzle_index=1)

@pytest.fixture
def temp_puzzle_cache_second(tmp_path): # Renamed
    difficulty = "medium"
    split = "train"
    puzzle_set_num_str = "001"
    full_dir = tmp_path / difficulty / split
    os.makedirs(full_dir, exist_ok=True)
    # board_content = BOARD_FOR_PARAMS_STR # Defined at the top, ensure it's \n
    file_content = f"12\n{BOARD_FOR_PARAMS_STR}" # Use \n
    filepath = full_dir / f"{puzzle_set_num_str}.txt"
    with open(filepath, 'w') as f:
        f.write(file_content)
    return tmp_path

# This is the failing test
def test_load_game_from_params_second(temp_puzzle_cache_second, monkeypatch): # Renamed
    monkeypatch.setattr(GameLoader, 'CACHE_DIR', temp_puzzle_cache_second)
    expected_board_content = BOARD_FOR_PARAMS_STR # This should be "#####\n# $.#\n# @ #\n#####"

    game = GameLoader.load_game_from_params("medium", "train", 1, 12)
    assert game.get_game_state() == expected_board_content
    assert game.player_pos == (2,2)

    game_str_num = GameLoader.load_game_from_params("medium", "train", "001", 12)
    assert game_str_num.get_game_state() == expected_board_content


def test_get_valid_moves_simple_second(): # Renamed
    game = GameLoader.load_game_from_file("tests/data/valid_moves_simple_1.txt")
    assert sorted(game.get_valid_moves()) == sorted(['right'])
    game_open = GameLoader.load_game_from_file("tests/data/valid_moves_simple_game_open.txt")
    assert sorted(game_open.get_valid_moves()) == sorted(['up', 'down', 'left', 'right'])

def test_get_valid_moves_wall_second(): # Renamed
    game = GameLoader.load_game_from_file("tests/data/valid_moves_wall.txt")
    assert game.get_valid_moves() == []

def test_get_valid_moves_push_box_empty_behind_second(): # Renamed
    game = GameLoader.load_game_from_file("tests/data/valid_moves_push_empty_1.txt")
    assert game.get_valid_moves() == ['right']
    game_left = GameLoader.load_game_from_file("tests/data/valid_moves_push_empty_left.txt")
    assert game_left.get_valid_moves() == ['left']

def test_get_valid_moves_push_box_wall_behind_second(): # Renamed
    game = GameLoader.load_game_from_file("tests/data/valid_moves_push_wall_1.txt")
    assert game.get_valid_moves() == []
    game_blocked_both_sides = GameLoader.load_game_from_file("tests/data/valid_moves_push_wall_blocked_sides.txt")
    assert game_blocked_both_sides.get_valid_moves() == []

def test_take_action_move_empty_second(): # Renamed
    game = GameLoader.load_game_from_file("tests/data/valid_moves_simple_1.txt")
    assert game.take_action('right') is True
    assert game.player_pos == (1, 2)
    assert game.board[1, 1] == BoxobanGame.ORD_EMPTY
    assert game.board[1, 2] == BoxobanGame.ORD_PLAYER
    assert game.get_game_state() == "####\n# @#\n####"

def test_take_action_move_to_target_second(): # Renamed
    game = GameLoader.load_game_from_file("tests/data/simple_board.txt")
    assert game.take_action('right') is True
    assert game.player_pos == (1, 2)
    assert game.board[1, 1] == BoxobanGame.ORD_EMPTY
    assert game.board[1, 2] == BoxobanGame.ORD_PLAYER
    assert (1,2) in game._targets
    assert game.get_game_state() == "####\n# +#\n####"

def test_take_action_move_from_target_second(): # Renamed
    game = GameLoader.load_game_from_file("tests/data/action_move_from_target.txt")
    assert game.take_action('right') is True
    assert game.player_pos == (1, 2)
    assert game.board[1, 1] == BoxobanGame.ORD_TARGET
    assert game.board[1, 2] == BoxobanGame.ORD_PLAYER
    assert game.get_game_state() == "####\n#.@#\n####"

def test_take_action_push_box_second(): # Renamed
    game = GameLoader.load_game_from_file("tests/data/valid_moves_push_empty_1.txt")
    assert game.take_action('right') is True
    assert game.player_pos == (0, 2)
    assert game.board[0, 1] == BoxobanGame.ORD_EMPTY
    assert game.board[0, 2] == BoxobanGame.ORD_PLAYER
    assert game.board[0, 3] == BoxobanGame.ORD_BOX
    assert game.get_game_state() == "# @$.#"

def test_take_action_push_box_to_target_second(): # Renamed
    game = GameLoader.load_game_from_file("tests/data/board_with_box.txt")
    assert game.take_action('right') is True
    assert game.player_pos == (1, 2)
    assert game.board[1, 1] == BoxobanGame.ORD_EMPTY
    assert game.board[1, 2] == BoxobanGame.ORD_PLAYER
    assert game.board[1, 3] == BoxobanGame.ORD_BOX
    assert (1,3) in game._targets
    assert game.get_game_state() == "#####\n# @*#\n#####"

def test_take_action_push_box_from_target_second(): # Renamed
    game = GameLoader.load_game_from_file("tests/data/action_push_box_from_target.txt")
    assert game.player_pos == (0,1)
    assert game.board[0, 2] == BoxobanGame.ORD_BOX
    assert (0,2) in game._targets
    assert game.take_action('right') is True
    assert game.player_pos == (0, 2)
    assert game.board[0, 1] == BoxobanGame.ORD_EMPTY
    assert game.board[0, 2] == BoxobanGame.ORD_PLAYER
    assert game.board[0, 3] == BoxobanGame.ORD_BOX
    assert (0,2) in game._targets
    assert game.get_game_state() == "# +$#"

def test_take_action_invalid_move_wall_second(): # Renamed
    game = GameLoader.load_game_from_file("tests/data/action_invalid_move_wall.txt")
    assert game.take_action('right') is False
    assert game.player_pos == (1, 1)
    assert game.get_game_state() == "####\n#@##\n####"

def test_take_action_invalid_push_wall_second(): # Renamed
    game = GameLoader.load_game_from_file("tests/data/valid_moves_push_wall_1.txt")
    assert game.take_action('right') is False
    assert game.player_pos == (0, 1)
    assert game.board[0, 2] == BoxobanGame.ORD_BOX
    assert game.get_game_state() == "#@$#"

def test_is_solved_second(): # Renamed
    game1 = GameLoader.load_game_from_file("tests/data/is_solved_game1.txt")
    assert game1.is_solved() is True
    game2 = GameLoader.load_game_from_file("tests/data/is_solved_game2.txt")
    assert game2.is_solved() is False
    with pytest.raises(ValueError):
        GameLoader.load_game_from_file("tests/data/is_solved_game3_no_player_error.txt")
    game3 = GameLoader.load_game_from_file("tests/data/is_solved_game3_ok.txt")
    assert game3.is_solved() is True

def test_is_not_solved_second(): # Renamed
    game = GameLoader.load_game_from_file("tests/data/board_with_box.txt")
    assert game.is_solved() is False
    game2 = GameLoader.load_game_from_file("tests/data/simple_board.txt")
    assert game2.is_solved() is False
    game3_with_box = GameLoader.load_game_from_file("tests/data/is_not_solved_game3_with_box.txt")
    assert game3_with_box.is_solved() is False
    game4 = GameLoader.load_game_from_file("tests/data/solvable_setup.txt")
    assert game4.is_solved() is False

def test_full_game_sequence_solve_second(): # Renamed
    game = GameLoader.load_game_from_file("tests/data/board_with_box.txt")
    assert game.is_solved() is False
    assert game.take_action('right') is True
    assert game.player_pos == (1, 2)
    assert game.board[1, 3] == BoxobanGame.ORD_BOX
    assert (1,3) in game._targets
    assert game.get_game_state() == "#####\n# @*#\n#####"
    assert game.is_solved() is True

def test_get_valid_moves_puzzle_medium_train_0_42_second(): # Renamed
    # This test will use the actual cache unless monkeypatched.
    # For it to be robust, it should also use a temporary cache with a known puzzle.
    # However, the original test was for a specific real puzzle.
    # Assuming the cache might contain the real puzzle from previous runs.
    game = GameLoader.load_game_from_params(
        difficulty="medium",
        split="train",
        puzzle_set_num=0, # This will try to load 000.txt
        puzzle_num=42     # from the actual cache (or download it)
    )
    expected_moves = ['left', 'right'] # This assertion depends on the actual puzzle content
    actual_moves = game.get_valid_moves()
    assert sorted(actual_moves) == sorted(expected_moves), \
        f"Expected moves {sorted(expected_moves)}, but got {sorted(actual_moves)}"
