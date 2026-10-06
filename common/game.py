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
