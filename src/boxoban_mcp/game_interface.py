import json
import numpy as np
from scipy.optimize import linear_sum_assignment
from .game import BoxobanGame

class GameInterface:
    def __init__(self, game: BoxobanGame):
        """
        Initializes the GameInterface with a BoxobanGame instance.

        Args:
            game: An instance of the BoxobanGame class.
        """
        self.game = game
        self.actions_taken_list = []
        # self.total_actions_taken_count = 0  <- This line is removed

    def take_action(self, action: str) -> dict: # Changed return type hint
        """
        Attempts to take a single action in the game.

        Args:
            action: The action string (e.g., 'up', 'down', 'left', 'right').

        Returns:
            A dictionary containing:
                - "game_state": The current game state (string) after the action.
                - "success": A boolean indicating if the action was successful.
        """
        success = self.game.take_action(action)
        if success:
            self.actions_taken_list.append(action)
            # The line incrementing total_actions_taken_count is removed
        return {"game_state": self.game.get_game_state(), "success": success}

    def take_action_list(self, actions: list[str]) -> dict:
        """
        Attempts to take a list of actions sequentially. Stops if an illegal action is encountered.

        Args:
            actions: A list of action strings.

        Returns:
            A dictionary containing:
                - "current_game_state": The game state after the last attempted action.
                - "actions_sent": The total number of actions in the input list.
                - "actions_taken": The number of actions successfully taken.
        """
        actions_attempted = len(actions)
        actions_successful = 0
        current_game_state = self.game.get_game_state()

        for action_item in actions: # Renamed 'action' to 'action_item' to avoid conflict with method name
            result_dict = self.take_action(action_item) # Now returns a dict
            current_game_state = result_dict["game_state"]
            if result_dict["success"]:
                actions_successful += 1
            else:
                break

        return {
            "current_game_state": current_game_state,
            "actions_sent": actions_attempted,
            "actions_taken": actions_successful
        }

    def return_full_game_state(self) -> dict:
        """
        Returns the current game state, total number of actions successfully taken,
        and the list of actions that have been successfully taken.

        Returns:
            A dictionary containing:
                - "current_game_state": The current string representation of the game board.
                - "total_actions_successfully_taken": The total count of successful actions.
                - "list_of_actions_successfully_taken": The list of successful action strings.
        """
        return {
            "current_game_state": self.game.get_game_state(),
            "total_actions_successfully_taken": len(self.actions_taken_list), # Updated to use len()
            "list_of_actions_successfully_taken": self.actions_taken_list
        }

    def return_game_state(self) -> dict:
        """
        Returns the current game state as a JSON object.

        Returns:
            A dictionary containing:
                - "current_game_state": The current string representation of the game board.
        """
        return {
            "current_game_state": self.game.get_game_state()
        }

    def get_valid_moves(self) -> dict[str, list[str]]: # Update return type hint
        """
        Returns a dictionary containing a list of valid action strings for the current game state.

        Returns:
            A dictionary with a single key "valid_moves",
            whose value is a list of strings, where each string is a valid action
            (e.g., {'valid_moves': ['up', 'down']}).
        """
        moves = self.game.get_valid_moves()
        return {"valid_moves": moves}

    def calculate_greedy_score(self) -> float:
        """
        Calculates a heuristic score based on the Manhattan distance between boxes and goals.
        Uses the internal game board representation for efficiency.

        Returns:
            The calculated heuristic score.
        """
        # Access internal game state directly
        # self.game.board is a NumPy array of ord(char)
        # self.game._targets is a set of (r, c) tuples

        box_locs = []
        goal_locs = [] # All target locations

        # Find all target locations first
        for r_idx, c_idx in self.game._targets:
            goal_locs.append((r_idx, c_idx))

        # Find all box locations
        # Iterate through the board to find boxes
        for r_idx in range(self.game.board.shape[0]):
            for c_idx in range(self.game.board.shape[1]):
                if self.game.board[r_idx, c_idx] == self.game.ORD_BOX:
                    box_locs.append((r_idx, c_idx))
                    # If a box is on a location that is also a target,
                    # it's already implicitly handled by goal_locs containing all targets.
                    # The cost matrix will correctly assign a distance of 0 if a box is on a goal.

        # If there are no boxes, the score is 0 (puzzle solved or trivial).
        if not box_locs:
            return 0.0

        # If there are boxes but no goals, it's an impossible state for MCP.
        if not goal_locs:
            return float('inf')

        # If there are more boxes than goals, it's an impossible state for MCP.
        if len(box_locs) > len(goal_locs):
            return float('inf')

        # Create a cost matrix: rows are boxes, columns are goals
        # Cost is Manhattan distance
        cost_matrix = np.zeros((len(box_locs), len(goal_locs)))

        for i, (br, bc) in enumerate(box_locs):
            for j, (gr, gc) in enumerate(goal_locs):
                cost_matrix[i, j] = abs(br - gr) + abs(bc - gc)

        # Use Hungarian algorithm to find the optimal assignment
        row_ind, col_ind = linear_sum_assignment(cost_matrix)

        # Sum the distances of the optimal assignments
        score = cost_matrix[row_ind, col_ind].sum()

        return float(score)

    def get_heuristic_score(self) -> float:
        """
        Returns the heuristic score for the current game state.
        This method is a wrapper around calculate_greedy_score.

        Returns:
            The heuristic score as a float.
        """
        return self.calculate_greedy_score()

    def pretty_print_game_state(self):
        game_state_str = self.game.get_game_state()
        if not game_state_str:
            print("Empty game state.")
            return

        rows = game_state_str.strip().split('\n')
        if not rows or not rows[0]:
            print("Game state has no rows or the first row is empty.")
            return

        num_cols = len(rows[0])
        if num_cols == 0:
            print("Game state has rows but no columns.")
            return

        # Create the horizontal border
        horizontal_border = "+" + "---+" * num_cols

        # Print the top border
        print(horizontal_border)

        for row_str in rows:
            # Ensure all rows are processed consistently, even if shorter than num_cols
            # This might happen if the game state string is not perfectly rectangular,
            # though get_game_state() from BoxobanGame should produce rectangular output.
            # We will format based on num_cols derived from the first row.

            formatted_row_parts = []
            for i in range(num_cols):
                char = row_str[i] if i < len(row_str) else ' ' # Use space if row is shorter
                formatted_row_parts.append(f" {char} ")

            print("|" + "|".join(formatted_row_parts) + "|")
            print(horizontal_border)
