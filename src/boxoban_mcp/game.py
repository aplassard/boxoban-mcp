import os
import numpy as np

class BoxobanGame:
    EMPTY = ' '
    WALL = '#'
    PLAYER = '@'
    BOX = '$'
    TARGET = '.'
    BOX_ON_TARGET = '*'  # For get_game_state: Box ($) on a destination (.)
    PLAYER_ON_TARGET = '+' # For get_game_state: Player character (@) on a destination

    ORD_EMPTY = ord(EMPTY)
    ORD_WALL = ord(WALL)
    ORD_PLAYER = ord(PLAYER)
    ORD_BOX = ord(BOX)
    ORD_TARGET = ord(TARGET)
    ORD_PLAYER_ON_TARGET = ord(PLAYER_ON_TARGET)
    ORD_BOX_ON_TARGET = ord(BOX_ON_TARGET)

    ACTION_MAP = {
        'up': (-1, 0),
        'down': (1, 0),
        'left': (0, -1),
        'right': (0, 1)
    }
    ACTION_NAMES = list(ACTION_MAP.keys())

    def __init__(self, board_string):
        self.board_string_raw = board_string # Keep original for debugging if needed
        self._targets: set[tuple[int, int]] = set()
        self.board: np.ndarray | None = None # Will be initialized by _parse_board_string
        self._parse_board_string(board_string)
        self.player_pos: tuple[int, int] | None = self._find_player_position() # player_pos is (r, c)
        if self.player_pos is None:
            # This case should ideally be caught by _parse_board_string if player char is missing
            raise ValueError("Player ('@' or '+') not found on the board.")

    def _parse_board_string(self, board_str_raw):
        board_chars = []
        # Normalize: remove surrounding whitespace from the whole string, then split
        # Use actual newline '\n' as separator, as loaded strings should have it.
        lines = board_str_raw.strip().split('\n')
        max_len = 0
        for r, row_str in enumerate(lines):
            row_chars = []
            max_len = max(max_len, len(row_str))
            for c, char in enumerate(row_str):
                actual_char_to_store = self.EMPTY
                if char == self.TARGET:
                    self._targets.add((r, c))
                    actual_char_to_store = self.TARGET
                elif char == self.PLAYER_ON_TARGET:
                    self._targets.add((r, c))
                    actual_char_to_store = self.PLAYER # Store as PLAYER, target status is in _targets
                elif char == self.BOX_ON_TARGET:
                    self._targets.add((r, c))
                    actual_char_to_store = self.BOX    # Store as BOX, target status is in _targets
                elif char == self.PLAYER:
                    actual_char_to_store = self.PLAYER
                elif char == self.BOX:
                    actual_char_to_store = self.BOX
                elif char == self.WALL:
                    actual_char_to_store = self.WALL
                elif char == self.EMPTY:
                    actual_char_to_store = self.EMPTY
                # else: unknown chars are treated as EMPTY (already default)
                row_chars.append(ord(actual_char_to_store))
            board_chars.append(row_chars)

        # Pad rows to ensure rectangular board for NumPy array
        # Using ORD_EMPTY for padding
        num_rows = len(board_chars)
        self.board = np.full((num_rows, max_len), self.ORD_EMPTY, dtype=np.uint8)
        for r, row_data in enumerate(board_chars):
            self.board[r, :len(row_data)] = row_data

        # _find_player_position will use self.board, so it's called after self.board is set.

    def _find_player_position(self):
        # Player position is stored based on ORD_PLAYER in the numpy array
        if self.board is None: # Should not happen if _parse_board_string was called
            return None
        player_coords = np.where(self.board == self.ORD_PLAYER)
        if player_coords[0].size > 0:
            # Return as a tuple (r, c)
            return (player_coords[0][0], player_coords[1][0])
        return None

    def get_game_state(self):
        output_rows = []
        for r in range(self.board.shape[0]):
            row_str_parts = []
            for c in range(self.board.shape[1]):
                char_ord = self.board[r, c]
                is_target = (r, c) in self._targets

                if char_ord == self.ORD_PLAYER and is_target:
                    row_str_parts.append(self.PLAYER_ON_TARGET)
                elif char_ord == self.ORD_BOX and is_target:
                    row_str_parts.append(self.BOX_ON_TARGET)
                elif char_ord == self.ORD_TARGET: # Should display TARGET if it's an empty target
                    row_str_parts.append(self.TARGET)
                elif char_ord == self.ORD_EMPTY and is_target: # Empty space that is a target
                    row_str_parts.append(self.TARGET)
                else:
                    row_str_parts.append(chr(char_ord)) # Convert ord back to char
            output_rows.append("".join(row_str_parts))
        return "\n".join(output_rows) # Use actual newline for string representation

    def _simulate_move_on_temp_board(self, temp_board: np.ndarray, temp_player_pos: tuple[int, int], action: str):
        r_player, c_player = temp_player_pos
        dr, dc = self.ACTION_MAP[action]
        nr, nc = r_player + dr, c_player + dc

        # Determine character for player's old spot
        player_old_pos_char_ord = self.ORD_TARGET if (r_player, c_player) in self._targets else self.ORD_EMPTY

        if temp_board[nr, nc] == self.ORD_BOX: # Check using ORD_BOX
            bnr, bnc = nr + dr, nc + dc
            # Determine character for box's old spot (player's new spot before player moves)
            box_old_pos_char_ord = self.ORD_TARGET if (nr, nc) in self._targets else self.ORD_EMPTY
            temp_board[bnr, bnc] = self.ORD_BOX       # Move box to its new position
            temp_board[nr, nc] = box_old_pos_char_ord # Set box's old spot character (player will occupy this)

        temp_board[r_player, c_player] = player_old_pos_char_ord # Set player's old spot character
        temp_board[nr, nc] = self.ORD_PLAYER                     # Move player to new spot

        return temp_board, (nr, nc) # Return new player position as tuple

    def get_valid_moves(self):
        candidate_moves = []
        r_player, c_player = self.player_pos # player_pos is now a tuple (r,c)

        for move_name, (dr, dc) in self.ACTION_MAP.items():
            nr, nc = r_player + dr, c_player + dc

            # Check boundaries for player's new position
            if not (0 <= nr < self.board.shape[0] and 0 <= nc < self.board.shape[1]):
                continue

            char_at_new_pos_ord = self.board[nr, nc]

            if char_at_new_pos_ord == self.ORD_WALL:
                continue
            elif char_at_new_pos_ord == self.ORD_BOX:
                # Check boundaries and content for box's new position (one step further)
                bnr, bnc = nr + dr, nc + dc
                if not (0 <= bnr < self.board.shape[0] and 0 <= bnc < self.board.shape[1]):
                    continue

                char_behind_box_ord = self.board[bnr, bnc]
                if char_behind_box_ord == self.ORD_WALL or char_behind_box_ord == self.ORD_BOX:
                    continue

            candidate_moves.append(move_name)

        # final_valid_moves now consists of all moves that passed initial checks
        # (boundary, wall/box collision), without deadlock consideration.
        final_valid_moves = candidate_moves

        return final_valid_moves

    def take_action(self, action):
        if action not in self.ACTION_MAP:
             return False

        r_player, c_player = self.player_pos # player_pos is a tuple (r,c)
        dr, dc = self.ACTION_MAP[action]

        nr, nc = r_player + dr, c_player + dc

        # Check if the move is actually valid according to game rules
        # This re-confirms the logic from get_valid_moves essentially
        if not (0 <= nr < self.board.shape[0] and 0 <= nc < self.board.shape[1]):
            return False

        destination_char_ord = self.board[nr, nc]

        if destination_char_ord == self.ORD_WALL:
            return False

        if destination_char_ord == self.ORD_BOX:
            bnr, bnc = nr + dr, nc + dc
            if not (0 <= bnr < self.board.shape[0] and 0 <= bnc < self.board.shape[1]):
                return False

            char_behind_box_ord = self.board[bnr, bnc]
            if char_behind_box_ord == self.ORD_WALL or char_behind_box_ord == self.ORD_BOX:
                return False

            self.board[bnr, bnc] = self.ORD_BOX # Move the box

        # Update player's old position
        self.board[r_player, c_player] = self.ORD_TARGET if (r_player, c_player) in self._targets else self.ORD_EMPTY

        # Update player's new position
        self.board[nr, nc] = self.ORD_PLAYER
        self.player_pos = (nr, nc) # Update player_pos to the new tuple

        return True

    def is_solved(self):
        # Condition 1: All targets must be covered by boxes.
        for tr, tc in self._targets:
            if self.board[tr, tc] != self.ORD_BOX: # Compare with ORD_BOX
                return False

        # Condition 2: No boxes should be on non-target squares.
        for r_idx in range(self.board.shape[0]):
            for c_idx in range(self.board.shape[1]):
                if self.board[r_idx, c_idx] == self.ORD_BOX and (r_idx, c_idx) not in self._targets:
                    return False # A box is on a non-target square
        return True
