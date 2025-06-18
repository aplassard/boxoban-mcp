import unittest
import io
import contextlib
import json # Though direct json output isn't being tested for structure yet, good to have if needed.
from src.boxoban_mcp.game import BoxobanGame
from src.boxoban_mcp.game_interface import GameInterface

# Board string literals are now removed and loaded from tests/data/

class TestGameInterface(unittest.TestCase):

    def setUp(self):
        """Set up for each test method."""
        # For most tests, a simple game instance is sufficient.
        self.simple_game = BoxobanGame.load_game_from_file("tests/data/simple_board.txt")
        self.simple_interface = GameInterface(self.simple_game)

        # For tests involving box pushing or more complex scenarios.
        self.action_game = BoxobanGame.load_game_from_file("tests/data/solvable_setup.txt")
        self.action_interface = GameInterface(self.action_game)

    def test_initialization(self):
        """Test that the GameInterface initializes correctly."""
        self.assertIsNotNone(self.simple_interface.game)
        self.assertEqual(self.simple_interface.actions_taken_list, [])
        # self.assertEqual(self.simple_interface.total_actions_taken_count, 0) # Removed
        self.assertEqual(self.simple_interface.game.get_game_state(), "####\n#@.#\n####")

    def test_take_action_successful(self):
        """Test a single successful action."""
        # Initial state from simple_board.txt: "####\n#@.#\n####"
        # Action: 'right' -> P moves to T(1,2).
        # Old P(1,1) becomes EMPTY (' '). New P(1,2) (was TARGET '.') becomes PLAYER_ON_TARGET ('+').
        # Expected state: "####\n# +#\n####"
        expected_state_after_move = "####\n# +#\n####"

        result_dict = self.simple_interface.take_action('right') # Now returns a dict

        self.assertTrue(result_dict["success"])
        self.assertEqual(result_dict["game_state"], expected_state_after_move)
        self.assertEqual(len(self.simple_interface.actions_taken_list), 1) # Check via len
        self.assertEqual(self.simple_interface.actions_taken_list, ['right'])
        # Verify game state via interface method too
        self.assertEqual(self.simple_interface.return_game_state()['current_game_state'], expected_state_after_move)

    def test_take_action_unsuccessful(self):
        """Test a single unsuccessful action (e.g., moving into a wall)."""
        # Initial state from simple_board.txt: "####\n#@.#\n####"
        # Action: 'up' (into a wall)
        # Expected state: "####\n#@.#\n####" (no change)
        initial_state_str = "####\n#@.#\n####"

        result_dict = self.simple_interface.take_action('up') # Now returns a dict

        self.assertFalse(result_dict["success"])
        self.assertEqual(result_dict["game_state"], initial_state_str)
        self.assertEqual(len(self.simple_interface.actions_taken_list), 0) # Check via len
        self.assertEqual(self.simple_interface.actions_taken_list, [])
        self.assertEqual(self.simple_interface.return_game_state()['current_game_state'], initial_state_str)

    def test_take_action_list_all_successful(self):
        """Test take_action_list where all actions are successful."""
        # Uses action_interface with board from solvable_setup.txt: "#####\n#@$ .#\n#####"
        # P(1,1), B(1,2), E(1,3), T(1,4)
        # Actions: ['right', 'right']
        # 1. 'right': Player pushes Box from (1,2) to (1,3). Player moves to (1,2). Box to (1,3).
        #    State: #####\n# @$.#\n#####
        # 2. 'right': Player pushes Box from (1,3) to (1,4) (Target). Player moves to (1,3). Box to (1,4).
        #    State: #####\n#  @*#\n##### (Player, Box on Target)

        actions = ['right', 'right']
        # solvable_setup.txt lines: "#####" (len 5), "#@$ .#" (len 6). So, max_len = 6.
        # get_game_state pads all lines to max_len.
        # The middle line after actions, "#  @*#", is also length 6.
        # Padded "#####" becomes "##### ".
        expected_final_state = "##### \n#  @*#\n##### " # P(1,3), B(1,4) on T(1,4)

        result = self.action_interface.take_action_list(actions)

        self.assertEqual(result['actions_sent'], 2)
        self.assertEqual(result['actions_taken'], 2)
        self.assertEqual(result['current_game_state'], expected_final_state)
        self.assertEqual(len(self.action_interface.actions_taken_list), 2) # Check via len
        self.assertEqual(self.action_interface.actions_taken_list, ['right', 'right'])

    def test_take_action_list_stops_on_fail(self):
        """Test take_action_list where an action in the middle fails."""
        # Uses simple_interface with board: "####\\n#@.#\\n####"
        # P(1,1), T(1,2)
        # Actions: ['right', 'up', 'left']
        # 1. 'right': Success. P moves to (1,2) (on Target). State: "####\n# +#\n####"
        # 2. 'up': Fails (wall). Loop should stop.
        # 3. 'left': Should not be attempted.

        actions = ['right', 'up', 'left']
        expected_state_after_partial = "####\n# +#\n####" # After the first 'right'

        result = self.simple_interface.take_action_list(actions)

        self.assertEqual(result['actions_sent'], 3)
        self.assertEqual(result['actions_taken'], 1) # Only 'right' succeeded
        self.assertEqual(result['current_game_state'], expected_state_after_partial)
        self.assertEqual(len(self.simple_interface.actions_taken_list), 1) # Check via len
        self.assertEqual(self.simple_interface.actions_taken_list, ['right'])

    def test_take_action_list_empty(self):
        """Test take_action_list with an empty list of actions."""
        actions = []
        initial_state = self.simple_interface.game.get_game_state()

        result = self.simple_interface.take_action_list(actions)

        self.assertEqual(result['actions_sent'], 0)
        self.assertEqual(result['actions_taken'], 0)
        self.assertEqual(result['current_game_state'], initial_state) # State should be unchanged
        self.assertEqual(len(self.simple_interface.actions_taken_list), 0) # Check via len
        self.assertEqual(self.simple_interface.actions_taken_list, [])

    def test_return_full_game_state_no_actions(self):
        """Test return_full_game_state before any actions are taken."""
        initial_state_str = "####\n#@.#\n####"
        expected_dict = {
            "current_game_state": initial_state_str,
            "total_actions_successfully_taken": 0,
            "list_of_actions_successfully_taken": []
        }
        self.assertEqual(self.simple_interface.return_full_game_state(), expected_dict)

    def test_return_full_game_state_after_actions(self):
        """Test return_full_game_state after some actions have been taken."""
        self.simple_interface.take_action('right') # P(1,1) -> P(1,2) on T
        self.simple_interface.take_action('left')  # P(1,2) -> P(1,1) off T
        # Expected state after these actions is the initial state of simple_board.txt
        expected_state_final = "####\n#@.#\n####"

        expected_dict = {
            "current_game_state": expected_state_final,
            "total_actions_successfully_taken": 2,
            "list_of_actions_successfully_taken": ['right', 'left']
        }
        self.assertEqual(self.simple_interface.return_full_game_state(), expected_dict)

    def test_return_game_state(self):
        """Test return_game_state output."""
        initial_state_str = "####\n#@.#\n####"
        # Test before any action
        expected_dict_before = {"current_game_state": initial_state_str}
        self.assertEqual(self.simple_interface.return_game_state(), expected_dict_before)

        # Test after an action
        self.simple_interface.take_action('right')
        # Expected state: "####\n# +#\n####" (Player moved from (1,1) to (1,2) which is target)
        expected_state_after_move = "####\n# +#\n####"
        expected_dict_after = {"current_game_state": expected_state_after_move}
        self.assertEqual(self.simple_interface.return_game_state(), expected_dict_after)

    # --- Tests for get_heuristic_score ---

    def test_get_heuristic_score_standard_case(self):
        """Test heuristic score for a standard board configuration."""
        # Original board_str_issue = "#######\n#.    #\n# $ # $ #\n#   . @#\n#######"
        # Corresponds to tests/data/iface_heuristic_standard.txt
        game = BoxobanGame.load_game_from_file("tests/data/iface_heuristic_standard.txt")
        interface = GameInterface(game)
        self.assertEqual(interface.get_heuristic_score(), 5.0)

    def test_get_heuristic_score_box_on_goal(self):
        """Test heuristic score when a box is already on a goal."""
        # Original board_str = "#####\n#* .#\n# @ #\n#####"
        # Corresponds to tests/data/iface_heuristic_box_on_goal.txt
        game = BoxobanGame.load_game_from_file("tests/data/iface_heuristic_box_on_goal.txt")
        interface = GameInterface(game)
        self.assertEqual(interface.get_heuristic_score(), 0.0)

    def test_get_heuristic_score_mismatched_boxes_goals_no_goals(self):
        """Test heuristic score with boxes but no goals."""
        # Original board_str = "#####\n#$  #\n# @ #\n#####"
        # Corresponds to tests/data/iface_heuristic_no_goals.txt
        game = BoxobanGame.load_game_from_file("tests/data/iface_heuristic_no_goals.txt")
        interface = GameInterface(game)
        self.assertEqual(interface.get_heuristic_score(), float('inf'))

    def test_get_heuristic_score_mismatched_boxes_goals_fewer_goals(self):
        """Test heuristic score with more boxes than goals."""
        # Original board_str = "#####\n#$ $#\n# . #\n# @ #\n#####"
        # Corresponds to tests/data/iface_heuristic_fewer_goals.txt
        game = BoxobanGame.load_game_from_file("tests/data/iface_heuristic_fewer_goals.txt")
        interface = GameInterface(game)
        self.assertEqual(interface.get_heuristic_score(), float('inf'))


    def test_get_heuristic_score_no_boxes(self):
        """Test heuristic score when there are no boxes."""
        # Original board_str = "#####\n#.  #\n# @ #\n#####"
        # Corresponds to tests/data/iface_heuristic_no_boxes.txt
        game = BoxobanGame.load_game_from_file("tests/data/iface_heuristic_no_boxes.txt")
        interface = GameInterface(game)
        self.assertEqual(interface.get_heuristic_score(), 0.0)

    def test_pretty_print_game_state(self):
        """Test the pretty_print_game_state method for correct formatting."""
        # Board string: "##\n@.#\n##"
        # BoxobanGame._parse_board_string pads rows. max_len will be 3.
        # Game state becomes: "## \n@.#\n## "
        # pretty_print_game_state uses len(rows[0]) for num_cols, so 3.
        board_string = "##\n@.#\n##"
        game = BoxobanGame(board_string) # Use board_string
        interface = GameInterface(game)

        expected_output_lines = [
            "+---+---+---+",
            "| # | # |   |",
            "+---+---+---+",
            "| @ | . | # |",
            "+---+---+---+",
            "| # | # |   |",
            "+---+---+---+"
        ]
        expected_output = "\n".join(expected_output_lines) + "\n"

        stdout_capture = io.StringIO()
        with contextlib.redirect_stdout(stdout_capture):
            interface.pretty_print_game_state()

        captured_output = stdout_capture.getvalue()
        self.assertEqual(captured_output, expected_output)

class TestGetValidMoves(unittest.TestCase):
    def test_get_valid_moves_open_area(self):
        """Test get_valid_moves when player is in an open area."""
        simple_board_open = """#####
#   #
# @ #
#   #
#####"""
        # Player is at (2,2) in a 5x5 grid (0-indexed)
        # Game pads this to:
        # #####
        #   #
        # @ #
        #   #
        # #####
        # Player at (2,2)
        # Up to (1,2) ' ' -> valid
        # Down to (3,2) ' ' -> valid
        # Left to (2,1) ' ' -> valid
        # Right to (2,3) ' ' -> valid
        game = BoxobanGame(simple_board_open)
        interface = GameInterface(game)
        result_dict = interface.get_valid_moves()
        self.assertIn("valid_moves", result_dict)
        self.assertIsInstance(result_dict["valid_moves"], list)
        expected_moves = {'up', 'down', 'left', 'right'}
        self.assertEqual(set(result_dict["valid_moves"]), expected_moves, f"Expected {expected_moves}, got {set(result_dict['valid_moves'])}")

    def test_get_valid_moves_cornered_by_wall(self):
        """Test get_valid_moves when player is cornered by walls."""
        board_player_cornered = """###
#@#
###"""
        # Player at (1,1) in 3x3 grid
        # All adjacent cells are walls.
        game = BoxobanGame(board_player_cornered)
        interface = GameInterface(game)
        result_dict = interface.get_valid_moves()
        self.assertIn("valid_moves", result_dict)
        self.assertIsInstance(result_dict["valid_moves"], list)
        expected_moves = set()
        self.assertEqual(set(result_dict["valid_moves"]), expected_moves, f"Expected {expected_moves}, got {set(result_dict['valid_moves'])}")

    def test_get_valid_moves_partially_blocked_by_wall(self):
        """Test get_valid_moves when player is partially blocked by walls."""
        board_player_partially_blocked = """###
#@ #
## #"""
        # Player at (1,1)
        # Game state after parsing (player at (1,1)):
        # ###
        # @ #
        # ## #
        # Up (0,1) is # -> blocked
        # Down (2,1) is # -> blocked
        # Left (1,0) is # -> blocked
        # Right (1,2) is ' ' -> valid
        game = BoxobanGame(board_player_partially_blocked)
        interface = GameInterface(game)
        result_dict = interface.get_valid_moves()
        self.assertIn("valid_moves", result_dict)
        self.assertIsInstance(result_dict["valid_moves"], list)
        expected_moves = {'right'}
        self.assertEqual(set(result_dict["valid_moves"]), expected_moves, f"Expected {expected_moves}, got {set(result_dict['valid_moves'])}")

    def test_get_valid_moves_push_box_open(self):
        """Test get_valid_moves when player can push a box into an empty space."""
        board_player_next_to_box_can_push = """
        #####
        # @$#
        #   #
        #####
        """
        # Player at (1,2), Box at (1,3), Empty space for box at (1,4) (end of # @$#)
        # Parsed board (player at (1,2)):
        # #####
        #  @$ #  <- Note: original was # @$#, game might parse space before @ based on raw string
        # #   #      BoxobanGame._parse_board_string strips lines then processes.
        # #####      The player is at (1,2) relative to " @$#".
        # Let's re-verify player position based on code:
        # BoxobanGame `_parse_board_string` uses `strip()` on lines.
        # `simple_board_open` has " # @ # ". Player will be at (2,3) of that line.
        # For `board_player_next_to_box_can_push`
        # line 1: "#####"
        # line 2: "# @$#" -> player at (1,2), box at (1,3)
        # line 3: "#   #"
        # line 4: "#####"
        # Player at (1,2).
        # Up to (0,2) is # -> blocked.
        # Down to (2,2) is ' ' -> valid.
        # Left to (1,1) is ' ' -> valid.
        # Right to (1,3) is $, box moves to (1,4) which is # -> push blocked by wall.
        # The prompt description for this test case: "Assert that the returned list includes 'right' (to push the box)"
        # This implies the space after the box should be empty.
        # The board string "# @$#" means the box is at (1,3) and (1,4) is '#'.
        # Let's adjust the board to match the intent:
        board_player_next_to_box_can_push_revised = """#####
# @$ #
#    #
#####"""
        # Player at (1,2), Box at (1,3), Empty at (1,4)
        # Up: (0,2) is # -> blocked
        # Down: (2,2) is ' ' -> valid
        # Left: (1,1) is ' ' -> valid
        # Right: (1,3) is $, box to (1,4) is ' ' -> valid (push)
        game = BoxobanGame(board_player_next_to_box_can_push_revised)
        interface = GameInterface(game)
        result_dict = interface.get_valid_moves()
        self.assertIn("valid_moves", result_dict)
        self.assertIsInstance(result_dict["valid_moves"], list)
        expected_moves = {'down', 'left', 'right'}
        self.assertEqual(set(result_dict["valid_moves"]), expected_moves, f"Expected {expected_moves}, got {set(result_dict['valid_moves'])}")

    def test_get_valid_moves_push_box_blocked_by_wall(self):
        """Test get_valid_moves when a box push is blocked by a wall."""
        board_player_next_to_box_wall_block = """#####
#@$##
#   #
#####"""
        # Player at (1,1), Box at (1,2), Wall at (1,3)
        # Up: (0,1) is # -> blocked
        # Down: (2,1) is ' ' -> valid
        # Left: (1,0) is # -> blocked
        # Right: (1,2) is $, box to (1,3) is # -> push blocked
        game = BoxobanGame(board_player_next_to_box_wall_block)
        interface = GameInterface(game)
        result_dict = interface.get_valid_moves()
        self.assertIn("valid_moves", result_dict)
        self.assertIsInstance(result_dict["valid_moves"], list)
        expected_moves = {'down'}
        self.assertEqual(set(result_dict["valid_moves"]), expected_moves, f"Expected {expected_moves}, got {set(result_dict['valid_moves'])}")

    def test_get_valid_moves_push_box_blocked_by_another_box(self):
        """Test get_valid_moves when a box push is blocked by another box."""
        board_player_next_to_box_box_block = """######
#@$$ #
#    #
######"""
        # Player at (1,1), Box1 at (1,2), Box2 at (1,3)
        # Up: (0,1) is # -> blocked
        # Down: (2,1) is ' ' -> valid
        # Left: (1,0) is # -> blocked
        # Right: (1,2) is $, box1 to (1,3) is $ -> push blocked
        game = BoxobanGame(board_player_next_to_box_box_block)
        interface = GameInterface(game)
        result_dict = interface.get_valid_moves()
        self.assertIn("valid_moves", result_dict)
        self.assertIsInstance(result_dict["valid_moves"], list)
        expected_moves = {'down'}
        self.assertEqual(set(result_dict["valid_moves"]), expected_moves, f"Expected {expected_moves}, got {set(result_dict['valid_moves'])}")

if __name__ == '__main__':
    unittest.main()
