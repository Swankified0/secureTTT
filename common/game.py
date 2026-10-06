board = [["", "", ""],
         ["", "", ""],
         ["", "", ""]]


def reset_board():
    """Reset the board to an empty 3x3 grid."""
    global board
    board = [["", "", ""],
             ["", "", ""],
             ["", "", ""]]


def move(player, row, col):
    """
    Place a player's mark on the board.

    Returns True if the move was valid, otherwise False.
    """
    if player not in ("X", "O"):
        return False

    if not (0 <= row < 3 and 0 <= col < 3):
        return False

    if board[row][col] != "":
        return False

    board[row][col] = player
    return True


def check_if_winner():
    """Return True if either player has three in a row."""

    # Rows
    for row in board:
        if row[0] == row[1] == row[2] != "":
            return True

    # Columns
    for col in range(3):
        if board[0][col] == board[1][col] == board[2][col] != "":
            return True

    # Diagonals
    if board[0][0] == board[1][1] == board[2][2] != "":
        return True

    if board[0][2] == board[1][1] == board[2][0] != "":
        return True

    return False


def check_if_tie():
    """Return True if the board is full and nobody has won."""
    return all(cell != "" for row in board for cell in row)


def check_game_status():
    """
    Return:
        "winner" if somebody won
        "tie" if the board is full
        None if the game is still active
    """
    if check_if_winner():
        return "winner"

    if check_if_tie():
        return "tie"

    return None

def print_board():
    """Print the current state of the board."""
    print("\n  0   1   2")
    for idx, row in enumerate(board):
        display_row = [cell if cell != "" else " " for cell in row]
        print(f"{idx} " + " | ".join(display_row))
        if idx < 2:
            print(" ---+---+---")
    print()

def run_game():
    """Run a simple command-line version of the game."""
    reset_board()
    current_player = "X"

    while True:
        print_board()
        print(f"Player {current_player}'s turn.")
        row = int(input("Enter row (0-2): "))
        col = int(input("Enter column (0-2): "))

        if move(current_player, row, col):
            status = check_game_status()
            if status == "winner":
                print_board()
                print(f"Player {current_player} wins!")
                break
            elif status == "tie":
                print_board()
                print("It's a tie!")
                break
            current_player = "O" if current_player == "X" else "X"
        else:
            print("Invalid move. Try again.")

if __name__ == "__main__":
    run_game()