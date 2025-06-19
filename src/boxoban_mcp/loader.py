import os
import requests
import zipfile
import shutil
import tempfile
import numpy as np

# Attempting relative import, assuming game.py is in the same directory
from .game import BoxobanGame

class GameLoader:
    """
    Handles loading BoxobanGame instances from various sources,
    including automatic download and caching of puzzle files.
    """
    BOXOBAN_RAW_URL = "https://raw.githubusercontent.com/google-deepmind/boxoban-levels/refs/heads/master/"
    CACHE_DIR = os.path.join(tempfile.gettempdir(), "boxoban_cache")

    @classmethod
    def load_game_from_string(cls, board_str):
        """Loads a game directly from a board string representation."""
        return BoxobanGame(board_str)

    @classmethod
    def load_game_from_file(cls, file_path, puzzle_index=0):
        """
        Loads a game from a specified file path and puzzle index.
        The path should be relative to the root of the puzzles directory structure,
        e.g., 'medium/train/000.txt'.
        This method does NOT handle caching or downloading directly; it expects
        the file to be locally accessible at the given path. For automatic
        downloading and caching, use load_game_from_params or ensure
        the file exists in the cache when calling this.
        """
        # This method, as moved, assumes file_path is a direct path to a readable file.
        # The caching logic was primarily in load_game_from_params.
        # If the intention is for this to ALSO check cache, the logic needs to be adapted.
        # For now, sticking to a direct interpretation of "load from file".
        # However, the original load_game_from_params CALLED this method with a CACHED path.
        # Let's refine this: this method should just load, the caller (like load_game_from_params)
        # is responsible for providing the correct path (cached or otherwise).
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
                if is_raw_puzzle:
                    found_puzzle_str = single_part
                elif single_part.startswith(target_prefix_for_current_index):
                    found_puzzle_str = header_check_parts[1].strip() if len(header_check_parts) > 1 else ""
            elif single_part.startswith(target_prefix_for_current_index):
                 found_puzzle_str = header_check_parts[1].strip() if len(header_check_parts) > 1 else ""

        if found_puzzle_str is None:
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

        return BoxobanGame(found_puzzle_str)

    @classmethod
    def load_game_from_params(cls, difficulty, split, puzzle_set_num, puzzle_num):
        """
        Loads a game based on difficulty, split, and puzzle numbers.
        Handles downloading and caching of puzzle files from an online repository.
        """
        try:
            puzzle_set_filename = f"{int(str(puzzle_set_num).strip()):03d}.txt"
        except ValueError:
            raise ValueError(f"puzzle_set_num must be a number or string representing a number. Got: {puzzle_set_num}")

        if not os.path.exists(cls.CACHE_DIR):
            os.makedirs(cls.CACHE_DIR)

        # Path within the cache structure
        cached_file_path = os.path.join(cls.CACHE_DIR, difficulty, split, puzzle_set_filename)

        if os.path.exists(cached_file_path):
            return cls.load_game_from_file(cached_file_path, puzzle_index=puzzle_num)
        else:
            # Construct the direct download URL
            direct_url = f"{cls.BOXOBAN_RAW_URL}{difficulty}/{split}/{puzzle_set_filename}"
            print(f"Cache miss for {cached_file_path}. Downloading from {direct_url}...")

            try:
                response = requests.get(direct_url)
                response.raise_for_status()  # Raise an exception for HTTP errors
            except requests.exceptions.RequestException as e:
                raise IOError(f"Failed to download puzzle file from {direct_url}: {e}")

            # Ensure the cache directory for the file exists
            os.makedirs(os.path.dirname(cached_file_path), exist_ok=True)

            # Save the downloaded content to the cache file
            try:
                with open(cached_file_path, "wb") as f:
                    f.write(response.content)
            except IOError as e:
                raise IOError(f"Failed to save downloaded puzzle to {cached_file_path}: {e}")

            # Verify the file was actually created
            if not os.path.exists(cached_file_path):
                raise FileNotFoundError(
                    f"Puzzle file {cached_file_path} not found after download. "
                    f"Download seemed to succeed but file is missing."
                )

            return cls.load_game_from_file(cached_file_path, puzzle_index=puzzle_num)
