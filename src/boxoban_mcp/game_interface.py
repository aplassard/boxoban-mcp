import json
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
        self.total_actions_taken_count = 0

    def take_action(self, action: str) -> tuple[str, bool]:
        """
        Attempts to take a single action in the game.

        Args:
            action: The action string (e.g., 'up', 'down', 'left', 'right').

        Returns:
            A tuple containing:
                - The current game state (string) after the action.
                - A boolean indicating if the action was successful.
        """
        success = self.game.take_action(action)
        if success:
            self.actions_taken_list.append(action)
            self.total_actions_taken_count += 1
        return self.game.get_game_state(), success

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
        current_game_state = self.game.get_game_state() # Initial state before any action in this list

        for action in actions:
            game_state_after_action, success = self.take_action(action)
            current_game_state = game_state_after_action # Update state regardless of success for the return value
            if success:
                actions_successful += 1
            else:
                break  # Stop on the first illegal action

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
            "total_actions_successfully_taken": self.total_actions_taken_count,
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
