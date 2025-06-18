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
        game = BoxobanGame(board_string_input=board_string) # Use board_string_input
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

if __name__ == '__main__':
    unittest.main()
