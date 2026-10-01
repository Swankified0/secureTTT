def print_board(board_state):
    horizontal_bar = '--------------------------------'
    vertical_bars = '          |          |          '
    ascii_board = [list(vertical_bars) for _ in range(5)] \
        + [horizontal_bar] \
        + [list(vertical_bars) for _ in range(5)] \
        + [horizontal_bar] \
        + [list(vertical_bars) for _ in range(5)]

    def draw_x(r, c):
        r = r*5 + r
        c = c*10 + c
        ascii_board[r][c:c+10] =   ' X      X '
        ascii_board[r+1][c:c+10] = '  XX  XX  '
        ascii_board[r+2][c:c+10] = '    XX    '
        ascii_board[r+3][c:c+10] = '  XX  XX  '
        ascii_board[r+4][c:c+10] = ' X      X '

    def draw_o(r, c):
        r = r*5 + r
        c = c*10 + c
        ascii_board[r][c:c+10] =   '  OOOOOO  '
        ascii_board[r+1][c:c+10] = ' O      O '
        ascii_board[r+2][c:c+10] = ' O      O '
        ascii_board[r+3][c:c+10] = ' O      O '
        ascii_board[r+4][c:c+10] = '  OOOOOO  '        
    
    for r, row in enumerate(board_state):
        for c, cell in enumerate(row):
            if cell == 'X':
                draw_x(r, c)
            elif cell == 'O':
                draw_o(r, c)


    print('\n'.join(''.join(row) for row in ascii_board))
    print()