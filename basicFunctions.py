import chess
import cairosvg
import cv2
import svg_custom.svg_custom as svg_custom
import numpy as np

def svg_to_png(img, directory='svg_custom', puzzle='board'):
    """ Converts given svg image to png. Written by SARFA authors.

    :param img: image in .svg format
    :param directory: destination folder
    :param puzzle: name of puzzle
    :return: svg_custom/board.png or given directory/puzzle
    """

    with open('svg_custom/board.svg', 'w+') as f:
        f.write(img)
    path = "{}/{}.png".format(directory, puzzle)
    cairosvg.svg2png(url='svg_custom/board.svg', write_to=path)


def generate_heatmap(board, evaluation, bestmove, directory, puzzle, file=None):
    """ Generates heatmap for saliency evaluation of best move. Written by SARFA authors.

    :param board: chess.Board()
    :param evaluation: dictionary with saliency information per square
    :param bestmove: original best move (chess.Move())
    :param directory: destination folder
    :param puzzle: name of puzzle
    :param file: output file
    """

    if file is None:
        file = open("svg_custom/output.txt", "a")  # append mode
        file.truncate(0)

    # Laying the saliency map over the board
    heatmap = np.zeros((8, 8))
    for position in evaluation:
        x, y = evaluation[position]['int'] // 8, evaluation[position]['int'] % 8
        heatmap[x, y] = evaluation[position]['saliency']
    heatmap = np.flipud(heatmap)

    # Saliency map overlaid on board
    svg = svg_custom.board(board, arrows=[svg_custom.Arrow(tail=bestmove.from_square, head=bestmove.to_square, color='#e6e600')])

    with open('svg_custom/board.svg', 'w+') as f:
        f.write(svg)
    path = "{}/{}.png".format(directory, puzzle)
    cairosvg.svg2png(url='svg_custom/board.svg', write_to=path)

    # original board as a numpy array
    board_array = cv2.imread(path, cv2.IMREAD_UNCHANGED)

    threshold = (100 / 256) * np.max(heatmap)  # percentage threshold. Saliency values above this threshold won't be mapped onto board
    file.write("threshold: {}\n".format(threshold))

    # Create bounding boxes with saliency colours for every square on chess board
    for i in range(0, 8, 1):
        for j in range(0, 8, 1):
            ii = 45 * i + 20
            jj = 45 * j + 20
            value_of_square = heatmap[i, j]
            if value_of_square < threshold:
                continue
            for box_i in range(ii, ii + 44, 1):
                for box_j in range(jj, jj + 44, 1):
                    if box_i > ii + 4 and box_i < ii + 40 and box_j > jj + 4 and box_j < jj + 40:
                        continue
                    board_array[box_i, box_j, 0] = 256 - 0.8 * 256 * heatmap[i, j] / (np.max(heatmap) + 1e-10)
                    board_array[box_i, box_j, 1] = 256 - 0.84 * 256 * heatmap[i, j] / (np.max(heatmap) + 1e-10)
                    board_array[box_i, box_j, 2] = 256 - 0.19 * 256 * heatmap[i, j] / (np.max(heatmap) + 1e-10)
    cv2.imwrite(path, board_array)


def sortbySaliency(answer, number, file=None):
    """ Sorts a dictionary after their saliency values.

    :param answer: dictionary with saliency information per square
    :param number: specifies how many elements should be sorted
    :param file: output file
    """

    sortedKeys = sorted(answer, key=lambda x: answer[x]['saliency'], reverse=True)
    count = 0
    above = {}
    below = {}
    th = (100 / 256)
    if file is not None:
        file.write("Printing positive saliencies in order: \n")
    for key in sortedKeys:
        if count == number or answer[key]['saliency'] <= 0:
            break
        elif answer[key]['saliency'] >= th:
            above[key] = answer[key]['saliency']
        else:
            below[key] = answer[key]['saliency']
        if file is not None:
            file.write("{}: {}\n".format(key, answer[key]['saliency']))
        count += 1
    return above, below


def raiseSaliency(answer, saliencySquares, num, file=None):
    """ Increases saliency values in first dictionary according to given square keys.

    :param answer: dictionary with saliency information per square
    :param saliencySquares: squares whose salencies should be raised
    :param num: specifies how many salencies should be raised
    :param file: output file
    """

    sortedKeys = sorted(saliencySquares, key=lambda x: saliencySquares[x]['sal'], reverse=True)
    if len(sortedKeys) > num:
        sortedKeys = sortedKeys[0:num]
    th = (100 / 256)

    for key in saliencySquares:
        if sortedKeys.__contains__(key):
            answer[key]['saliency'] = saliencySquares[key]['sal']
        else:
            answer[key]['saliency'] = 0

    minSal = 1
    for key in sortedKeys:
        if float(saliencySquares[key]['sal']) < minSal:
            minSal = float(saliencySquares[key]['sal'])
    if minSal < th:  # increase saliency
        for key in sortedKeys:
            answer[key]['saliency'] = float(answer[key]['saliency']) + (th - minSal)
            if answer[key]['saliency'] > 0.8:
                answer[key]['saliency'] = 0.8
    if file is not None:
        file.write("{}\n".format(sortedKeys))


def printSaliency(answer, saliencySquares, file):
    """ Prints saliency values in first dictionary according to given square keys.

    :param answer: dictionary with saliency information per square
    :param saliencySquares: squares whose salencies should be printed
    :param file: output file
    """

    sortedKeys = sorted(saliencySquares, key=lambda x: saliencySquares[x]['sal'], reverse=True)
    if float(answer[sortedKeys[0]]['saliency']) > 0:
        for squarestring in sortedKeys:
            if float(answer[squarestring]['saliency']) <= 0:
                break
            file.write("{}: max: {}, colour player: {}, colour opponent: {}\n".format(squarestring, answer[squarestring]['saliency'], saliencySquares[squarestring]['sal1'], saliencySquares[squarestring]['sal2']))
    else:
        file.write("None\n")


def get_moves_squares(board, moveFrom, moveTo):
    """ Defines all squares included in a given best move.

    :param board: chess.Board()
    :param moveFrom: move starting position
    :param moveTo: move ending position
    """

    original_move_Squares = {chess.SQUARE_NAMES[moveTo]}
    if chess.square_distance(moveFrom, moveTo) > 1 and board.piece_type_at(chess.SQUARES[moveFrom]) != chess.KNIGHT:
        if chess.square_file(moveFrom) < chess.square_file(moveTo):
            if chess.square_rank(moveFrom) < chess.square_rank(moveTo):
                i = moveFrom + 9
                while i != moveTo:
                    original_move_Squares.add(chess.SQUARE_NAMES[i])
                    i += 9
            elif chess.square_rank(moveFrom) > chess.square_rank(moveTo):
                i = moveFrom - 7
                while i != moveTo:
                    original_move_Squares.add(chess.SQUARE_NAMES[i])
                    i -= 7
            else:
                i = moveFrom + 1
                while i != moveTo:
                    original_move_Squares.add(chess.SQUARE_NAMES[i])
                    i += 1
        elif chess.square_file(moveFrom) > chess.square_file(moveTo):
            if chess.square_rank(moveFrom) > chess.square_rank(moveTo):
                i = moveFrom - 9
                while i != moveTo:
                    original_move_Squares.add(chess.SQUARE_NAMES[i])
                    i -= 9
            elif chess.square_rank(moveFrom) < chess.square_rank(moveTo):
                i = moveFrom + 7
                while i != moveTo:
                    original_move_Squares.add(chess.SQUARE_NAMES[i])
                    i += 7
            else:
                i = moveFrom - 1
                while i != moveTo:
                    original_move_Squares.add(chess.SQUARE_NAMES[i])
                    i -= 1
        else:
            if chess.square_rank(moveFrom) < chess.square_rank(moveTo):
                i = moveFrom + 8
                while i != moveTo:
                    original_move_Squares.add(chess.SQUARE_NAMES[i])
                    i += 8
            else:
                i = moveFrom - 8
                while i != moveTo:
                    original_move_Squares.add(chess.SQUARE_NAMES[i])
                    i -= 8
    return original_move_Squares
