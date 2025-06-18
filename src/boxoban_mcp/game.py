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
        player_coords = np.where(self.board == self.ORD_PLAYER)
        if player_coords[0].size > 0:
            # Return as a tuple (r, c)
            return (player_coords[0][0], player_coords[1][0])
        return None

    @classmethod
    def load_game_from_string(cls, board_str):
        return cls(board_str)

    @classmethod
    def load_game_from_file(cls, file_path, puzzle_index=0):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        with open(file_path, 'r') as f:
            content = f.read()

        parts = content.strip().split(';')
        if not parts or (len(parts) == 1 and not parts[0].strip()):
            raise ValueError(f"No puzzle data found in file: {file_path}")

        found_puzzle_str = None
        # Use actual newline for prefix matching
        target_prefix_for_current_index = str(puzzle_index) + "\n"

        if len(parts) == 1:
            single_part = parts[0].strip()
            # Split by actual newline to check header
            header_check_parts = single_part.split('\n', 1)
            first_line_of_part = header_check_parts[0]
            is_raw_puzzle = not first_line_of_part.isdigit()

            if puzzle_index == 0:
                if is_raw_puzzle: # e.g. "####\n#@.#\n####"
                    found_puzzle_str = single_part
                elif single_part.startswith(target_prefix_for_current_index): # e.g. "0\n####\n#@.#\n####"
                    found_puzzle_str = header_check_parts[1].strip() if len(header_check_parts) > 1 else ""
            # If index > 0, it must have the "N\n" header
            elif single_part.startswith(target_prefix_for_current_index):
                 found_puzzle_str = header_check_parts[1].strip() if len(header_check_parts) > 1 else ""

        if found_puzzle_str is None: # Search through multiple parts or if not found in single part logic
            for part in parts:
                current_part = part.strip()
                if current_part.startswith(target_prefix_for_current_index):
                    # Split by actual newline to extract puzzle string after header
                    puzzle_content_parts = current_part.split('\n', 1)
                    found_puzzle_str = puzzle_content_parts[1].strip() if len(puzzle_content_parts) > 1 else ""
                    break

        if found_puzzle_str is None:
            # Split by actual newline for displaying available headers
            available_puzzle_headers = [p.strip().split('\n',1)[0] for p in parts if p.strip()]
            raise ValueError(
                f"Puzzle with index {puzzle_index} (expected prefix '{target_prefix_for_current_index.strip()}') "
                f"not found in {file_path}. File contains {len(parts)} part(s). "
                f"Available headers/starts: {available_puzzle_headers}"
            )

        return cls(found_puzzle_str)

    @classmethod
    def load_game_from_params(cls, difficulty, split, puzzle_set_num, puzzle_num):
        try:
            # Format puzzle_set_num to three digits with leading zeros, e.g., "1" -> "001"
            puzzle_set_filename = f"{int(str(puzzle_set_num).strip()):03d}.txt"
        except ValueError:
            raise ValueError(f"puzzle_set_num must be a number or string representing a number. Got: {puzzle_set_num}")

        file_path = os.path.join("puzzles", difficulty, split, puzzle_set_filename)
        return cls.load_game_from_file(file_path, puzzle_index=puzzle_num)

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

        final_valid_moves = []
        for move_name in candidate_moves:
            # Current player position and action details
            r_player, c_player = self.player_pos
            dr, dc = self.ACTION_MAP[move_name]

            # Player's target position on the current board (self.board)
            player_next_r, player_next_c = r_player + dr, c_player + dc

            box_pushed_to_pos = None
            # Check self.board (current board state) to see if the player is about to push a box.
            # char_at_new_pos_ord from candidate generation was self.board[player_next_r, player_next_c]
            if self.board[player_next_r, player_next_c] == self.ORD_BOX:
                # If the player's next move is onto a box, then that box will be pushed.
                # Calculate where that box will land.
                box_pushed_to_pos = (player_next_r + dr, player_next_c + dc)

            # Simulate the move
            temp_board_for_sim = self.board.copy() # Simulate on a copy of the current board
            simulated_board, _ = self._simulate_move_on_temp_board(temp_board_for_sim, self.player_pos, move_name)

            move_causes_action_deadlock = False
            if box_pushed_to_pos:
                # A box was pushed. Check if THAT specific box is now deadlocked on the simulated_board.
                # The box is now at box_pushed_to_pos on the simulated_board.
                if self._is_deadlock(simulated_board, only_check_box_at_pos=box_pushed_to_pos):
                    move_causes_action_deadlock = True
            # Else (no box pushed):
            # If the player just moves to an empty/target square, we do not check for deadlocks
            # for the purpose of this specific issue resolution. The goal is to prevent
            # unrelated, pre-existing deadlocks from blocking such simple moves.

            if not move_causes_action_deadlock:
                final_valid_moves.append(move_name)

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

    def _check_box_deadlock(self, board: np.ndarray, r: int, c: int, height: int, width: int, is_wall_func):
        """Checks if the box at (r,c) on the board is in a deadlock state."""
        if (r, c) in self._targets:
            return False # Box is on a target, not a deadlock for this box

        # Simple Corner Deadlock: Box in a corner formed by two walls
        if (is_wall_func(r - 1, c) and is_wall_func(r, c - 1)) or \
           (is_wall_func(r - 1, c) and is_wall_func(r, c + 1)) or \
           (is_wall_func(r + 1, c) and is_wall_func(r, c - 1)) or \
           (is_wall_func(r + 1, c) and is_wall_func(r, c + 1)):
            return True

        # Frozen Against a Wall Deadlock
        # Rule 1: Vertical Wall Freeze (North or South wall)
        if is_wall_func(r - 1, c) or is_wall_func(r + 1, c):
            can_move_out_vertical = False
            # Scan Left
            temp_c = c
            while temp_c - 1 >= 0 and board[r, temp_c - 1] != self.ORD_WALL:
                if (r, temp_c - 1) in self._targets: can_move_out_vertical = True; break
                if board[r, temp_c - 1] == self.ORD_BOX: break
                temp_c -= 1
            if not can_move_out_vertical:
                # Scan Right
                temp_c = c
                while temp_c + 1 < width and board[r, temp_c + 1] != self.ORD_WALL:
                    if (r, temp_c + 1) in self._targets: can_move_out_vertical = True; break
                    if board[r, temp_c + 1] == self.ORD_BOX: break
                    temp_c += 1
            if not can_move_out_vertical: return True

        # Rule 2: Horizontal Wall Freeze (West or East wall)
        if is_wall_func(r, c - 1) or is_wall_func(r, c + 1):
            can_move_out_horizontal = False
            # Scan Up
            temp_r = r
            while temp_r - 1 >= 0 and board[temp_r - 1, c] != self.ORD_WALL:
                if (temp_r - 1, c) in self._targets: can_move_out_horizontal = True; break
                if board[temp_r - 1, c] == self.ORD_BOX: break
                temp_r -= 1
            if not can_move_out_horizontal:
                # Scan Down
                temp_r = r
                while temp_r + 1 < height and board[temp_r + 1, c] != self.ORD_WALL:
                    if (temp_r + 1, c) in self._targets: can_move_out_horizontal = True; break
                    if board[temp_r + 1, c] == self.ORD_BOX: break
                    temp_r += 1
            if not can_move_out_horizontal: return True

        # 2x2 Box Deadlock - check if this box (r,c) forms part of such a deadlock
        # It must be top-left of a 2x2 square of boxes not all on targets.
        # This check is simplified: if (r,c) is part of any 2x2 box formation, and not all are on targets.
        # Check if (r,c) is top-left of a 2x2 box formation
        if (r + 1 < height and c + 1 < width and
            board[r, c+1] == self.ORD_BOX and board[r+1, c] == self.ORD_BOX and board[r+1, c+1] == self.ORD_BOX):
            # Deadlock if ALL 4 boxes in the 2x2 formation are NOT on targets
            if not((r,c) in self._targets) and not((r,c+1) in self._targets) and \
               not((r+1,c) in self._targets) and not((r+1,c+1) in self._targets):
                return True
        # Check if (r,c) is top-right of a 2x2 block
        if (r + 1 < height and c - 1 >= 0 and
            board[r, c-1] == self.ORD_BOX and board[r+1, c-1] == self.ORD_BOX and board[r+1, c] == self.ORD_BOX):
             # (r,c), (r,c-1), (r+1,c-1), (r+1,c)
            if not((r,c) in self._targets) and not((r,c-1) in self._targets) and \
               not((r+1,c-1) in self._targets) and not((r+1,c) in self._targets):
                return True
        # Check if (r,c) is bottom-left of a 2x2 block
        if (r - 1 >= 0 and c + 1 < width and
            board[r-1, c] == self.ORD_BOX and board[r-1, c+1] == self.ORD_BOX and board[r, c+1] == self.ORD_BOX):
            # (r,c), (r-1,c), (r-1,c+1), (r,c+1)
            if not((r,c) in self._targets) and not((r-1,c) in self._targets) and \
               not((r-1,c+1) in self._targets) and not((r,c+1) in self._targets):
                return True
        # Check if (r,c) is bottom-right of a 2x2 block
        if (r - 1 >= 0 and c - 1 >= 0 and
            board[r-1, c-1] == self.ORD_BOX and board[r-1, c] == self.ORD_BOX and board[r, c-1] == self.ORD_BOX):
            # (r,c), (r-1,c-1), (r-1,c), (r,c-1)
            if not((r,c) in self._targets) and not((r-1,c-1) in self._targets) and \
               not((r-1,c) in self._targets) and not((r,c-1) in self._targets):
                return True

        return False # No deadlock found for this specific box

    def _is_deadlock(self, board: np.ndarray, only_check_box_at_pos: tuple[int, int] | None = None):
        height = board.shape[0]
        width = board.shape[1]

        def is_wall(r_check, c_check):
            if not (0 <= r_check < height and 0 <= c_check < width):
                return True # Out of bounds is like a wall
            return board[r_check, c_check] == self.ORD_WALL

        if only_check_box_at_pos:
            r_box, c_box = only_check_box_at_pos
            if board[r_box, c_box] == self.ORD_BOX:
                return self._check_box_deadlock(board, r_box, c_box, height, width, is_wall)
            return False # Not a box at the specified position, so no deadlock for it
        else:
            # Original global deadlock check
            for r_loop in range(height):
                for c_loop in range(width):
                    if board[r_loop, c_loop] == self.ORD_BOX:
                        if self._check_box_deadlock(board, r_loop, c_loop, height, width, is_wall):
                            return True # Found a deadlocked box
            return False # No deadlocked boxes found globally
