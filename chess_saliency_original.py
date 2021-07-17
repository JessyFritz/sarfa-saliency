"""
contains original code of SARFA authors without functionality changes
    https://github.com/nikaashpuri/sarfa-saliency
added directory and file handling in order to save puzzles outputs into a dataset
    used to evaluate original saliency map implementation with various chess engines
"""

import chess.engine
from collections import defaultdict
import sarfa_saliency
from basicFunctions import *

engine = None
threshold = (100 / 256)


async def return_bestmove(board, eval_time=5, directory='svg_custom', puzzle='board'):
    """ Returns best move for a given chess position.

    :param board: chess.Board
    :param eval_time: evaluation time
    :param directory: destination folder
    :param puzzle: name of puzzle
    :return: bestmove: chess.Move
    """

    if engine.options["MultiPV"].max < 100:
        evaluation = await engine.analyse(board, chess.engine.Limit(time=eval_time), multipv=engine.options["MultiPV"].max)
    else:
        evaluation = await engine.analyse(board, chess.engine.Limit(time=eval_time), multipv=100)
    bestmove = evaluation[0]["pv"][0]
    svg_w_arrow = svg_custom.board(board, arrows=[svg_custom.Arrow(tail=bestmove.from_square, head=bestmove.to_square, color='#e6e600')])
    svg_to_png(svg_w_arrow, directory, puzzle)
    return evaluation, bestmove


async def computeSaliency(enginePath='engines/stockfish-11-win/stockfish-11-win/Windows/stockfish_20011801_32bit.exe', FEN="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", directory ='svg_custom', puzzle='board', givenMove=None, file=None):
    """ Computes saliency map for given board position. Written by SARFA authors.

    :param enginePath: path containing engine's executable file
    :param FEN: Board position encoded in a FEN
    :param directory: destination folder
    :param puzzle: name of puzzle
    :param givenMove: guarantees that bestmove is equal to givenMove
    :param file: output file
    :return: Saliency map
    """

    global engine
    transport, engine = await chess.engine.popen_uci(enginePath)

    if file is None:
        file = open("{}/output.txt".format(directory), "a")  # append mode
        file.truncate(0)

    file.write("***********************{}**********************\n".format(FEN))
    board = chess.Board(FEN)
    if board.is_valid() is False:
        print("Given Fen is not valid! {}".format(FEN))
        print(board.status())
        return
    evaltime = 5
    legal_moves = list(board.legal_moves)

    answer = {
        'a1': {'int': chess.A1, 'saliency': -2},
        'a2': {'int': chess.A2, 'saliency': -2},
        'a3': {'int': chess.A3, 'saliency': -2},
        'a4': {'int': chess.A4, 'saliency': -2},
        'a5': {'int': chess.A5, 'saliency': -2},
        'a6': {'int': chess.A6, 'saliency': -2},
        'a7': {'int': chess.A7, 'saliency': -2},
        'a8': {'int': chess.A8, 'saliency': -2},
        'b1': {'int': chess.B1, 'saliency': -2},
        'b2': {'int': chess.B2, 'saliency': -2},
        'b3': {'int': chess.B3, 'saliency': -2},
        'b4': {'int': chess.B4, 'saliency': -2},
        'b5': {'int': chess.B5, 'saliency': -2},
        'b6': {'int': chess.B6, 'saliency': -2},
        'b7': {'int': chess.B7, 'saliency': -2},
        'b8': {'int': chess.B8, 'saliency': -2},
        'c1': {'int': chess.C1, 'saliency': -2},
        'c2': {'int': chess.C2, 'saliency': -2},
        'c3': {'int': chess.C3, 'saliency': -2},
        'c4': {'int': chess.C4, 'saliency': -2},
        'c5': {'int': chess.C5, 'saliency': -2},
        'c6': {'int': chess.C6, 'saliency': -2},
        'c7': {'int': chess.C7, 'saliency': -2},
        'c8': {'int': chess.C8, 'saliency': -2},
        'd1': {'int': chess.D1, 'saliency': -2},
        'd2': {'int': chess.D2, 'saliency': -2},
        'd3': {'int': chess.D3, 'saliency': -2},
        'd4': {'int': chess.D4, 'saliency': -2},
        'd5': {'int': chess.D5, 'saliency': -2},
        'd6': {'int': chess.D6, 'saliency': -2},
        'd7': {'int': chess.D7, 'saliency': -2},
        'd8': {'int': chess.D8, 'saliency': -2},
        'e1': {'int': chess.E1, 'saliency': -2},
        'e2': {'int': chess.E2, 'saliency': -2},
        'e3': {'int': chess.E3, 'saliency': -2},
        'e4': {'int': chess.E4, 'saliency': -2},
        'e5': {'int': chess.E5, 'saliency': -2},
        'e6': {'int': chess.E6, 'saliency': -2},
        'e7': {'int': chess.E7, 'saliency': -2},
        'e8': {'int': chess.E8, 'saliency': -2},
        'f1': {'int': chess.F1, 'saliency': -2},
        'f2': {'int': chess.F2, 'saliency': -2},
        'f3': {'int': chess.F3, 'saliency': -2},
        'f4': {'int': chess.F4, 'saliency': -2},
        'f5': {'int': chess.F5, 'saliency': -2},
        'f6': {'int': chess.F6, 'saliency': -2},
        'f7': {'int': chess.F7, 'saliency': -2},
        'f8': {'int': chess.F8, 'saliency': -2},
        'g1': {'int': chess.G1, 'saliency': -2},
        'g2': {'int': chess.G2, 'saliency': -2},
        'g3': {'int': chess.G3, 'saliency': -2},
        'g4': {'int': chess.G4, 'saliency': -2},
        'g5': {'int': chess.G5, 'saliency': -2},
        'g6': {'int': chess.G6, 'saliency': -2},
        'g7': {'int': chess.G7, 'saliency': -2},
        'g8': {'int': chess.G8, 'saliency': -2},
        'h1': {'int': chess.H1, 'saliency': -2},
        'h2': {'int': chess.H2, 'saliency': -2},
        'h3': {'int': chess.H3, 'saliency': -2},
        'h4': {'int': chess.H4, 'saliency': -2},
        'h5': {'int': chess.H5, 'saliency': -2},
        'h6': {'int': chess.H6, 'saliency': -2},
        'h7': {'int': chess.H7, 'saliency': -2},
        'h8': {'int': chess.H8, 'saliency': -2},
    }

    # Q-values for original state
    evaluation, original_move = await return_bestmove(board, evaltime, directory, puzzle)
    if givenMove is not None and givenMove != str(original_move)[0:4]:
        file.write("assigned new best move to engine\n")
        original_move = chess.Move(answer[givenMove[0:2]]['int'],answer[givenMove[2:4]]['int'])
        if len(givenMove) > 4:
            original_move = chess.Move(answer[givenMove[0:2]]['int'], answer[givenMove[2:4]]['int'], chess.Piece.from_symbol(givenMove[4]).piece_type)
    file.write("Best move is {}\n".format(original_move))
    colorPlayer = board.piece_at(answer[chess.SQUARE_NAMES[original_move.from_square]]['int']).color
    if colorPlayer == chess.WHITE:
        colorOpponent = chess.BLACK
    else:
        colorOpponent = chess.WHITE
    dict_q_values_before_perturbation = await get_dict_q_vals(board, legal_moves, evaltime, colorPlayer, file, evaluation)
    file.write('------------------------------------------\n')

    for square_string in sorted(answer.keys()):
        entry = answer[square_string]
        entry_keys = ['saliency', 'dP', 'K', 'QMaxAnswer', 'actionGapBeforePerturbation', 'actionGapAfterPerturbation']
        file.write("perturbing square = {}\n".format(square_string))
        piece_removed = board.remove_piece_at(entry['int'])

        if piece_removed is None:
            # square was empty, so proceed without changing anything
            file.write('square was empty, so skipped\n')
            file.write('------------------------------------------\n')
            continue

        elif (piece_removed == chess.Piece(6, True) or piece_removed == chess.Piece(6,False)) or board.was_into_check():
            # illegal piece was removed
            file.write('illegal piece was removed\n')
            for key in entry_keys:
                entry[key] = 0

        else:
            # Check if the original move is still valid
            if board.is_legal(original_move):
                # Find the q values
                dict_q_values_after_perturbation = await get_dict_q_vals(board, legal_moves, evaltime, colorPlayer, file)
                entry['saliency'], entry['dP'], entry['K'], entry['QMaxAnswer'], \
                entry['actionGapBeforePerturbation'], entry['actionGapAfterPerturbation'] \
                    = sarfa_saliency.computeSaliencyUsingSarfa(str(original_move), dict_q_values_before_perturbation,
                                                               dict_q_values_after_perturbation, file)
                file.write("saliency for this square = {}\n".format(entry))

            else:
                # illegal original move in perturbed state, therefore piece removed is probably important
                file.write('original move illegal in perturbed state\n')
                for key in entry_keys:
                    entry[key] = -1
                entry['saliency'] = 1

                # undo perturbation
        file.write('------------------------------------------\n')

        board.set_piece_at(entry['int'], piece_removed)
    aboveThreshold, belowThreshold = sortbySaliency(answer, 64, file)
    file.write('------------------------------------------\n')

    if len(aboveThreshold) == 0 and len(belowThreshold) > 0:
        sortedKeys = sorted(belowThreshold, key=lambda x: belowThreshold[x], reverse=True)
        th = belowThreshold[sortedKeys[0]] * (100 / 256)
        i = 0
        while i < len(belowThreshold):
            sq = sortedKeys[i]
            i += 1
            if belowThreshold[sq] > th:
                aboveThreshold[sq] = belowThreshold[sq]
                belowThreshold.__delitem__(sq)

    generate_heatmap(board, answer, original_move, directory, puzzle, file)

    board.push(original_move)
    result = board.is_game_over()
    if result:
        file.write("game ended with {}\n".format(board.result()))
    board.pop()
    await engine.quit()

    return answer, aboveThreshold, belowThreshold, original_move, colorPlayer, colorOpponent


async def get_dict_q_vals(board, legal_moves, eval_time, color, file, info=None):
    """ Returns a dictionary of Q-values for every move.

    :param board: chess.Board()
    :param legal_moves: List of legal moves of original state
    :param eval_time: evaluation time
    :param color: currently played color
    :param file: output file
    :param info: None or given engine evaluation
    :return: q_vals_dict : Dictionary of move with respective Q-value
        evaluation.bestmove : chess.Move() - Best move in perturbed state
    """

    i = 0
    q_vals_dict = {}

    set_current_legal_moves = set(board.legal_moves)
    set_original_legal_moves = set(legal_moves)
    intersection_set = set_current_legal_moves.intersection(set_original_legal_moves)

    if info is None:
        file.write('querying engine with perturbed position\n')
        if engine.options["MultiPV"].max < 100:
            info = await engine.analyse(board, chess.engine.Limit(time=eval_time), multipv=engine.options["MultiPV"].max)
        else:
            info = await engine.analyse(board, chess.engine.Limit(time=eval_time), multipv=100)
    dict_moves_to_score = defaultdict(int)
    file.write("{}\n".format(info))

    # iterate over all possible moves
    move_id = 0
    while move_id < len(info):
        if "multipv" in info[move_id] and len(info[move_id]['pv']) > 0:
            move_string = str(info[move_id]['pv'][0])  # move representation (e.g. 'c5b6')

            if info[move_id]["score"].pov(color).score() is None:  # move has no centipawn evaluation value
                mate_in_moves = float(''.join(filter(lambda i: i.isdigit(), str(info[move_id]["score"].pov(color)))))
                if mate_in_moves > 0:
                    # white will win in some number of moves
                    move_score = 40
                else:
                    # black will win
                    move_score = -40
            else:
                move_score = round(info[move_id]["score"].pov(color).score() / 100.0, 2)
            dict_moves_to_score[move_string] = move_score
        move_id += 1

    file.write("Total Legal Moves : {}\n".format(len(intersection_set)))

    for el in legal_moves:
        if el in intersection_set:
            i += 1
            score = dict_moves_to_score[str(el)]
            q_vals_dict[el.uci()] = score
    file.write("Q Values: {}\n".format(q_vals_dict))

    return q_vals_dict
