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
        # Use '\n' as the separator for actual newline characters.
        lines = board_str_raw.strip().split('\n')
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
        return "\n".join(output_rows) # Use '\n' for string representation

    def get_valid_moves(self):
        valid = []
        r_player, c_player = self.player_pos

        for move_name, (dr, dc) in self.ACTION_MAP.items():
            nr, nc = r_player + dr, c_player + dc

            if not (0 <= nr < len(self.board) and 0 <= nc < len(self.board[0])):
                continue

            char_at_new_pos = self.board[nr][nc]

            if char_at_new_pos == self.WALL:
                continue
            elif char_at_new_pos == self.BOX:
                bnr, bnc = nr + dr, nc + dc
                if not (0 <= bnr < len(self.board) and 0 <= bnc < len(self.board[0])):
                    continue

                char_behind_box = self.board[bnr][bnc]
                if char_behind_box == self.WALL or char_behind_box == self.BOX:
                    continue

            valid.append(move_name)
        return valid

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
