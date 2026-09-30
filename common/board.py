horizontal_bar = '--------------------------------'
space = '          |          |          '

board = [list(space) for _ in range(5)] \
      + [horizontal_bar] \
      + [list(space) for _ in range(5)] \
      + [horizontal_bar] \
      + [list(space) for _ in range(5)]

def print_board():
    print()
    print('\n'.join(''.join(row) for row in board))
    print()


print_board()