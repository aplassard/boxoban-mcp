import unittest
import io
import contextlib
import json # Though direct json output isn't being tested for structure yet, good to have if needed.

# Corrected imports to use GameLoader for loading games
from src.boxoban_mcp.loader import GameLoader
from src.boxoban_mcp.game import BoxobanGame # Still needed for direct instantiation and type
from src.boxoban_mcp.game_interface import GameInterface

# Board string literals are now removed and loaded from tests/data/

class TestGameInterface(unittest.TestCase):

    def setUp(self):
        """Set up for each test method."""
        # For most tests, a simple game instance is sufficient.
        self.simple_game = GameLoader.load_game_from_file("tests/data/simple_board.txt")
        self.simple_interface = GameInterface(self.simple_game)

        # For tests involving box pushing or more complex scenarios.
        self.action_game = GameLoader.load_game_from_file("tests/data/solvable_setup.txt")
        self.action_interface = GameInterface(self.action_game)

    def test_initialization(self):
        """Test that the GameInterface initializes correctly."""
        self.assertIsNotNone(self.simple_interface.game)
        self.assertEqual(self.simple_interface.actions_taken_list, [])
        self.assertEqual(self.simple_interface.game.get_game_state(), "####\n#@.#\n####")

    def test_take_action_successful(self):
        """Test a single successful action."""
        expected_state_after_move = "####\n# +#\n####"
        result_dict = self.simple_interface.take_action('right')
        self.assertTrue(result_dict["success"])
        self.assertEqual(result_dict["game_state"], expected_state_after_move)
        self.assertEqual(len(self.simple_interface.actions_taken_list), 1)
        self.assertEqual(self.simple_interface.actions_taken_list, ['right'])
        self.assertEqual(self.simple_interface.return_game_state()['current_game_state'], expected_state_after_move)

    def test_take_action_unsuccessful(self):
        """Test a single unsuccessful action (e.g., moving into a wall)."""
        initial_state_str = "####\n#@.#\n####"
        result_dict = self.simple_interface.take_action('up')
        self.assertFalse(result_dict["success"])
        self.assertEqual(result_dict["game_state"], initial_state_str)
        self.assertEqual(len(self.simple_interface.actions_taken_list), 0)
        self.assertEqual(self.simple_interface.actions_taken_list, [])
        self.assertEqual(self.simple_interface.return_game_state()['current_game_state'], initial_state_str)

    def test_take_action_list_all_successful(self):
        """Test take_action_list where all actions are successful."""
        actions = ['right', 'right']
        expected_final_state = "##### \n#  @*#\n##### "
        result = self.action_interface.take_action_list(actions)
        self.assertEqual(result['actions_sent'], 2)
        self.assertEqual(result['actions_taken'], 2)
        self.assertEqual(result['current_game_state'], expected_final_state)
        self.assertEqual(len(self.action_interface.actions_taken_list), 2)
        self.assertEqual(self.action_interface.actions_taken_list, ['right', 'right'])

    def test_take_action_list_stops_on_fail(self):
        """Test take_action_list where an action in the middle fails."""
        actions = ['right', 'up', 'left']
        expected_state_after_partial = "####\n# +#\n####"
        result = self.simple_interface.take_action_list(actions)
        self.assertEqual(result['actions_sent'], 3)
        self.assertEqual(result['actions_taken'], 1)
        self.assertEqual(result['current_game_state'], expected_state_after_partial)
        self.assertEqual(len(self.simple_interface.actions_taken_list), 1)
        self.assertEqual(self.simple_interface.actions_taken_list, ['right'])

    def test_take_action_list_empty(self):
        """Test take_action_list with an empty list of actions."""
        actions = []
        initial_state = self.simple_interface.game.get_game_state()
        result = self.simple_interface.take_action_list(actions)
        self.assertEqual(result['actions_sent'], 0)
        self.assertEqual(result['actions_taken'], 0)
        self.assertEqual(result['current_game_state'], initial_state)
        self.assertEqual(len(self.simple_interface.actions_taken_list), 0)
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
        self.simple_interface.take_action('right')
        self.simple_interface.take_action('left')
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
        expected_dict_before = {"current_game_state": initial_state_str}
        self.assertEqual(self.simple_interface.return_game_state(), expected_dict_before)
        self.simple_interface.take_action('right')
        expected_state_after_move = "####\n# +#\n####"
        expected_dict_after = {"current_game_state": expected_state_after_move}
        self.assertEqual(self.simple_interface.return_game_state(), expected_dict_after)

    def test_get_heuristic_score_standard_case(self):
        game = GameLoader.load_game_from_file("tests/data/iface_heuristic_standard.txt")
        interface = GameInterface(game)
        self.assertEqual(interface.get_heuristic_score(), 5.0)

    def test_get_heuristic_score_box_on_goal(self):
        game = GameLoader.load_game_from_file("tests/data/iface_heuristic_box_on_goal.txt")
        interface = GameInterface(game)
        self.assertEqual(interface.get_heuristic_score(), 0.0)

    def test_get_heuristic_score_mismatched_boxes_goals_no_goals(self):
        game = GameLoader.load_game_from_file("tests/data/iface_heuristic_no_goals.txt")
        interface = GameInterface(game)
        self.assertEqual(interface.get_heuristic_score(), float('inf'))

    def test_get_heuristic_score_mismatched_boxes_goals_fewer_goals(self):
        game = GameLoader.load_game_from_file("tests/data/iface_heuristic_fewer_goals.txt")
        interface = GameInterface(game)
        self.assertEqual(interface.get_heuristic_score(), float('inf'))

    def test_get_heuristic_score_no_boxes(self):
        game = GameLoader.load_game_from_file("tests/data/iface_heuristic_no_boxes.txt")
        interface = GameInterface(game)
        self.assertEqual(interface.get_heuristic_score(), 0.0)

    def test_pretty_print_game_state(self):
        board_string = "##\n@.#\n##"
        # BoxobanGame constructor is still valid for direct string instantiation
        game = BoxobanGame(board_string)
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

class TestGetValidMoves(unittest.TestCase): # This class uses direct BoxobanGame instantiation, which is fine.
    def test_get_valid_moves_open_area(self):
        simple_board_open = """#####
#   #
# @ #
#   #
#####"""
        game = BoxobanGame(simple_board_open)
        interface = GameInterface(game)
        result_dict = interface.get_valid_moves()
        self.assertIn("valid_moves", result_dict)
        self.assertIsInstance(result_dict["valid_moves"], list)
        expected_moves = {'up', 'down', 'left', 'right'}
        self.assertEqual(set(result_dict["valid_moves"]), expected_moves, f"Expected {expected_moves}, got {set(result_dict['valid_moves'])}")

    def test_get_valid_moves_cornered_by_wall(self):
        board_player_cornered = """###
#@#
###"""
        game = BoxobanGame(board_player_cornered)
        interface = GameInterface(game)
        result_dict = interface.get_valid_moves()
        self.assertIn("valid_moves", result_dict)
        self.assertIsInstance(result_dict["valid_moves"], list)
        expected_moves = set()
        self.assertEqual(set(result_dict["valid_moves"]), expected_moves, f"Expected {expected_moves}, got {set(result_dict['valid_moves'])}")

    def test_get_valid_moves_partially_blocked_by_wall(self):
        board_player_partially_blocked = """###
#@ #
## #"""
        game = BoxobanGame(board_player_partially_blocked)
        interface = GameInterface(game)
        result_dict = interface.get_valid_moves()
        self.assertIn("valid_moves", result_dict)
        self.assertIsInstance(result_dict["valid_moves"], list)
        expected_moves = {'right'}
        self.assertEqual(set(result_dict["valid_moves"]), expected_moves, f"Expected {expected_moves}, got {set(result_dict['valid_moves'])}")

    def test_get_valid_moves_push_box_open(self):
        board_player_next_to_box_can_push_revised = """#####
# @$ #
#    #
#####"""
        game = BoxobanGame(board_player_next_to_box_can_push_revised)
        interface = GameInterface(game)
        result_dict = interface.get_valid_moves()
        self.assertIn("valid_moves", result_dict)
        self.assertIsInstance(result_dict["valid_moves"], list)
        expected_moves = {'down', 'left', 'right'}
        self.assertEqual(set(result_dict["valid_moves"]), expected_moves, f"Expected {expected_moves}, got {set(result_dict['valid_moves'])}")

    def test_get_valid_moves_push_box_blocked_by_wall(self):
        board_player_next_to_box_wall_block = """#####
#@$##
#   #
#####"""
        game = BoxobanGame(board_player_next_to_box_wall_block)
        interface = GameInterface(game)
        result_dict = interface.get_valid_moves()
        self.assertIn("valid_moves", result_dict)
        self.assertIsInstance(result_dict["valid_moves"], list)
        expected_moves = {'down'}
        self.assertEqual(set(result_dict["valid_moves"]), expected_moves, f"Expected {expected_moves}, got {set(result_dict['valid_moves'])}")

    def test_get_valid_moves_push_box_blocked_by_another_box(self):
        board_player_next_to_box_box_block = """######
#@$$ #
#    #
######"""
        game = BoxobanGame(board_player_next_to_box_box_block)
        interface = GameInterface(game)
        result_dict = interface.get_valid_moves()
        self.assertIn("valid_moves", result_dict)
        self.assertIsInstance(result_dict["valid_moves"], list)
        expected_moves = {'down'}
        self.assertEqual(set(result_dict["valid_moves"]), expected_moves, f"Expected {expected_moves}, got {set(result_dict['valid_moves'])}")

if __name__ == '__main__':
    unittest.main()
