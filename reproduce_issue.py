import boxoban_mcp

try:
    game = boxoban_mcp.BoxobanGame.load_game_from_params(
        difficulty="medium",
        split="train",
        puzzle_set_num=0,
        puzzle_num=42
    )
    print("Game loaded successfully.")
    print("Initial game state:")
    print(game.get_game_state())
    print(f"Player position: {game.player_pos}")
    print(f"Targets: {game._targets}")

    valid_moves = game.get_valid_moves()
    print(f"Valid moves: {valid_moves}")

    if not valid_moves:
        print("No valid moves returned, as reported in the issue.")
    elif "left" in valid_moves and "right" in valid_moves:
        print("Issue might be resolved or specific to a different state not captured here.")
    else:
        print(f"Returned moves: {valid_moves}, expected 'left' and 'right' (among others potentially).")

except Exception as e:
    print(f"An error occurred: {e}")
    import traceback
    traceback.print_exc()
