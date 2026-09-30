board = [["", "", ""],
        ["", "", ""],
        ["", "", ""]]

def move(player, row, col):
    if board[row][col] == "":
        board[row][col] = player
        return True
    else:
        return False

def check_if_winner():
    # Check rows
    for row in board:
        if row[0] == row[1] == row[2] != "":
            return True

    # Check columns
    for col in range(3):
        if board[0][col] == board[1][col] == board[2][col] != "":
            return True

    # Check diagonals
    if board[0][0] == board[1][1] == board[2][2] != "":
        return True
    if board[0][2] == board[1][1] == board[2][0] != "":
        return True

    return False

def check_if_tie():
    for row in board:
        for cell in row:
            if cell == "":
                return False
    return True

def check_game_status():
    if check_if_winner():
        print("We have a winner!")
        return True
    elif check_if_tie():
        print("It's a tie!")
        return True
    else:
        return False

if __name__ == "__main__":
    print("Welcome to Tic Tac Toe!")
    print(board)

    complete = False

    # X is 0, O is 1
    turn = 0

    while not complete:
        if turn == 0:
            player = "X"
        else:
            player = "O"

        row = int(input(f"Player {player}, enter the row (1, 2, or 3): "))
        col = int(input(f"Player {player}, enter the column (1, 2, or 3): "))

        if move(player, row - 1, col - 1):
            print(board)
        else:
            print("Invalid move. Try again.")

        # Check for a winner or a tie
        if check_game_status():
            complete = True
            print("Game Over!")
            print(board)
            complete = True

        turn = 1 - turn  # Switch turns between 0 and 1
    
