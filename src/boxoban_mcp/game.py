import os

class BoxobanGame:
    EMPTY = ' '
    WALL = '#'
    PLAYER = '@'
    BOX = '$'
    TARGET = '.'
    BOX_ON_TARGET = '*'  # For get_game_state: Box ($) on a destination (.)
    PLAYER_ON_TARGET = '+' # For get_game_state: Player character (@) on a destination

    ACTION_MAP = {
        'up': (-1, 0),
        'down': (1, 0),
        'left': (0, -1),
        'right': (0, 1)
    }
    ACTION_NAMES = list(ACTION_MAP.keys())

    def __init__(self, board_string):
        self.board_string_raw = board_string # Keep original for debugging if needed
        self._targets = set()
        self.board = self._parse_board_string(board_string)
        self.player_pos = self._find_player_position()
        if self.player_pos is None:
            # This case should ideally be caught by _parse_board_string if player char is missing
            raise ValueError("Player ('@' or '+') not found on the board.")

    def _parse_board_string(self, board_str_raw):
        board = []
        # Normalize: remove surrounding whitespace from the whole string, then split
        # Literal '\\n' is the separator in the string format for methods like split()
        lines = board_str_raw.strip().split('\\n')
        for r, row_str in enumerate(lines):
            row = []
            for c, char in enumerate(row_str):
                if char == self.TARGET:
                    self._targets.add((r, c))
                    row.append(self.TARGET)
                elif char == self.PLAYER_ON_TARGET:
                    self._targets.add((r, c))
                    row.append(self.PLAYER) # Store as PLAYER, target status is in _targets
                elif char == self.BOX_ON_TARGET:
                    self._targets.add((r, c))
                    row.append(self.BOX)    # Store as BOX, target status is in _targets
                elif char == self.PLAYER:
                    row.append(self.PLAYER)
                elif char == self.BOX:
                    row.append(self.BOX)
                elif char == self.WALL:
                    row.append(self.WALL)
                elif char == self.EMPTY:
                    row.append(self.EMPTY)
                else:
                    # If character is unknown, treat as empty or raise error
                    # For now, let's treat as empty, could be safer to raise error
                    row.append(self.EMPTY)
            board.append(row)

        if board and any(len(r) != len(board[0]) for r in board):
            pass # Not strictly enforcing rectangularity

        return board

    def _find_player_position(self):
        for r, row in enumerate(self.board):
            for c, char in enumerate(row):
                if char == self.PLAYER:
                    return [r, c]
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
        target_prefix_for_current_index = str(puzzle_index) + "\\n"

        if len(parts) == 1:
            single_part = parts[0].strip()
            first_line_of_part = single_part.split('\\n', 1)[0]
            is_raw_puzzle = not first_line_of_part.isdigit() # True if first line is not purely digits

            if puzzle_index == 0:
                if is_raw_puzzle: # e.g. "####\n#@.#\n####"
                    found_puzzle_str = single_part
                elif single_part.startswith(target_prefix_for_current_index): # e.g. "0\n####\n#@.#\n####"
                    found_puzzle_str = single_part[len(target_prefix_for_current_index):].strip()
            # If index > 0, it must have the "N\n" header
            elif single_part.startswith(target_prefix_for_current_index):
                 found_puzzle_str = single_part[len(target_prefix_for_current_index):].strip()

        if found_puzzle_str is None: # Search through multiple parts or if not found in single part logic
            for part in parts:
                current_part = part.strip()
                if current_part.startswith(target_prefix_for_current_index):
                    found_puzzle_str = current_part[len(target_prefix_for_current_index):].strip()
                    break

        if found_puzzle_str is None:
            available_puzzle_headers = [p.strip().split('\\n',1)[0] for p in parts if p.strip()]
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
        for r, row_list in enumerate(self.board):
            row_str_parts = []
            for c, char_code in enumerate(row_list):
                is_target = (r, c) in self._targets
                if char_code == self.PLAYER and is_target:
                    row_str_parts.append(self.PLAYER_ON_TARGET)
                elif char_code == self.BOX and is_target:
                    row_str_parts.append(self.BOX_ON_TARGET)
                elif char_code == self.TARGET:
                    row_str_parts.append(self.TARGET)
                elif char_code == self.EMPTY and is_target: # Empty space that is a target
                    row_str_parts.append(self.TARGET)
                else:
                    row_str_parts.append(char_code)
            output_rows.append("".join(row_str_parts))
        return "\\n".join(output_rows) # Use '\n' for string representation

    def _simulate_move_on_temp_board(self, temp_board, temp_player_pos, action):
        r_player, c_player = temp_player_pos
        dr, dc = self.ACTION_MAP[action]
        nr, nc = r_player + dr, c_player + dc

        # Determine character for player's old spot
        player_old_pos_char = self.TARGET if (r_player, c_player) in self._targets else self.EMPTY

        if temp_board[nr][nc] == self.BOX:
            bnr, bnc = nr + dr, nc + dc
            # Determine character for box's old spot (player's new spot before player moves)
            box_old_pos_char = self.TARGET if (nr, nc) in self._targets else self.EMPTY
            temp_board[bnr][bnc] = self.BOX       # Move box to its new position
            temp_board[nr][nc] = box_old_pos_char # Set box's old spot character (player will occupy this)

        temp_board[r_player][c_player] = player_old_pos_char # Set player's old spot character
        temp_board[nr][nc] = self.PLAYER                     # Move player to new spot

        return temp_board, [nr, nc]

    def get_valid_moves(self):
        # original_player_pos = list(self.player_pos) # Not strictly needed as self.player_pos isn't modified by simulation
        # original_board = [row[:] for row in self.board] # Not strictly needed as self.board isn't modified by simulation

        candidate_moves = []
        r_player, c_player = self.player_pos

        for move_name, (dr, dc) in self.ACTION_MAP.items():
            nr, nc = r_player + dr, c_player + dc

            # Check boundaries for player's new position
            if not (0 <= nr < len(self.board) and 0 <= nc < len(self.board[0])):
                continue

            char_at_new_pos = self.board[nr][nc]

            if char_at_new_pos == self.WALL:
                continue
            elif char_at_new_pos == self.BOX:
                # Check boundaries and content for box's new position (one step further)
                bnr, bnc = nr + dr, nc + dc
                if not (0 <= bnr < len(self.board) and 0 <= bnc < len(self.board[0])):
                    continue

                char_behind_box = self.board[bnr][bnc]
                if char_behind_box == self.WALL or char_behind_box == self.BOX:
                    continue

            candidate_moves.append(move_name)

        final_valid_moves = []
        for move_name in candidate_moves:
            temp_player_pos = list(self.player_pos) # Use a copy for simulation
            temp_board = [row[:] for row in self.board] # Use a deep copy for simulation

            simulated_board, _ = self._simulate_move_on_temp_board(temp_board, temp_player_pos, move_name)

            is_resulting_deadlock = self._is_deadlock(simulated_board)
            if not is_resulting_deadlock:
                final_valid_moves.append(move_name)

        return final_valid_moves

    def take_action(self, action):
        if action not in self.ACTION_MAP:
             return False

        r_player, c_player = self.player_pos
        dr, dc = self.ACTION_MAP[action]

        nr, nc = r_player + dr, c_player + dc

        # Check if the move is actually valid according to game rules
        # This re-confirms the logic from get_valid_moves essentially
        if not (0 <= nr < len(self.board) and 0 <= nc < len(self.board[0])):
            return False

        destination_char = self.board[nr][nc]

        if destination_char == self.WALL:
            return False

        if destination_char == self.BOX:
            bnr, bnc = nr + dr, nc + dc
            if not (0 <= bnr < len(self.board) and 0 <= bnc < len(self.board[0])):
                return False

            char_behind_box = self.board[bnr][bnc]
            if char_behind_box == self.WALL or char_behind_box == self.BOX:
                return False

            self.board[bnr][bnc] = self.BOX # Move the box

        # Update player's old position
        self.board[r_player][c_player] = self.TARGET if (r_player, c_player) in self._targets else self.EMPTY

        # Update player's new position
        self.board[nr][nc] = self.PLAYER
        self.player_pos = [nr, nc]

        return True

    def is_solved(self):
        # Condition 1: All targets must be covered by boxes.
        for tr, tc in self._targets:
            if self.board[tr][tc] != self.BOX:
                return False

        # Condition 2: No boxes should be on non-target squares.
        # (This is often redundant if num_boxes == num_targets and all targets are covered,
        # but good for robustness).
        for r_idx, row in enumerate(self.board):
            for c_idx, char_code in enumerate(row):
                if char_code == self.BOX and (r_idx, c_idx) not in self._targets:
                    return False # A box is on a non-target square
        return True

    def _is_deadlock(self, board):
        # Helper function to check if a position is a wall
        def is_wall(r, c):
            return not (0 <= r < len(board) and 0 <= c < len(board[0])) or \
                   board[r][c] == self.WALL

        for r, row in enumerate(board):
            for c, char_code in enumerate(row):
                if char_code == self.BOX:
                    # If the box is on a target, it's not a deadlock from this box's perspective
                    if (r, c) in self._targets:
                        continue

                    # Simple Corner Deadlock: Box in a corner formed by two walls
                    # Check corners: (Up, Left), (Up, Right), (Down, Left), (Down, Right)
                    if (is_wall(r - 1, c) and is_wall(r, c - 1)) or \
                       (is_wall(r - 1, c) and is_wall(r, c + 1)) or \
                       (is_wall(r + 1, c) and is_wall(r, c - 1)) or \
                       (is_wall(r + 1, c) and is_wall(r, c + 1)):
                        # This is a simple corner, and the box is not on a target.
                        return True

                    # Frozen Against a Wall Deadlock (Exact match to issue snippet logic)
                    height = len(board)
                    width = len(board[0])

                    # Rule 1: Vertical Wall Freeze (North or South wall)
                    if is_wall(r - 1, c) or is_wall(r + 1, c): # Box is against a North or South wall
                        can_move_out_vertical = False
                        # Scan Left
                        temp_c = c
                        while temp_c - 1 >= 0 and board[r][temp_c - 1] != self.WALL:
                            if (r, temp_c - 1) in self._targets:
                                can_move_out_vertical = True; break
                            if board[r][temp_c - 1] == self.BOX: # Blocked by another box
                                break
                            temp_c -= 1

                        if not can_move_out_vertical:
                            # Scan Right
                            temp_c = c
                            while temp_c + 1 < width and board[r][temp_c + 1] != self.WALL:
                                if (r, temp_c + 1) in self._targets:
                                    can_move_out_vertical = True; break
                                if board[r][temp_c + 1] == self.BOX: # Blocked by another box
                                    break
                                temp_c += 1

                        if not can_move_out_vertical:
                            return True # Deadlock: Frozen against N/S wall

                    # Rule 2: Horizontal Wall Freeze (West or East wall)
                    if is_wall(r, c - 1) or is_wall(r, c + 1): # Box is against a West or East wall
                        can_move_out_horizontal = False
                        # Scan Up
                        temp_r = r
                        while temp_r - 1 >= 0 and board[temp_r - 1][c] != self.WALL:
                            if (temp_r - 1, c) in self._targets:
                                can_move_out_horizontal = True; break
                            if board[temp_r - 1][c] == self.BOX: # Blocked by another box
                                break
                            temp_r -= 1

                        if not can_move_out_horizontal:
                            # Scan Down
                            temp_r = r
                            while temp_r + 1 < height and board[temp_r + 1][c] != self.WALL:
                                if (temp_r + 1, c) in self._targets:
                                    can_move_out_horizontal = True; break
                                if board[temp_r + 1][c] == self.BOX: # Blocked by another box
                                    break
                                temp_r += 1

                        if not can_move_out_horizontal:
                            return True # Deadlock: Frozen against E/W wall

                    # 2x2 Box Deadlock
                    # Check for a 2x2 square of boxes. If such a square exists and none are on a goal, it's a deadlock.
                    # More strongly: if a 2x2 of boxes exists, it's a deadlock if not ALL of them are on goals.
                    # Even more strongly: any 2x2 of boxes is an immediate deadlock as none can be moved.
                    # Let's check if (r,c), (r+1,c), (r,c+1), (r+1,c+1) are all boxes.
                    # The loop is iterating (r,c) for a box. So we check its neighbors.
                    if board[r][c] == self.BOX: # Current is a box
                        # Check (r, c+1), (r+1, c), (r+1, c+1)
                        if (r + 1 < len(board) and c + 1 < len(board[0]) and
                            board[r][c+1] == self.BOX and
                            board[r+1][c] == self.BOX and
                            board[r+1][c+1] == self.BOX):
                            # Found a 2x2 group of boxes.
                            # According to the issue: "if all four squares are boxes, and none of them are on a goal square"
                            # However, a 2x2 of boxes is always a deadlock unless the game is already solved by this 2x2.
                            # If any of these 4 boxes is NOT on a target, it's a deadlock.
                            if not ((r,c) in self._targets and \
                                    (r,c+1) in self._targets and \
                                    (r+1,c) in self._targets and \
                                    (r+1,c+1) in self._targets):
                                return True
        return False
