"""
contains original code of SARFA authors with some functionality changes
    https://github.com/nikaashpuri/sarfa-saliency
added directory and file handling and more chess specific aspects like the empty square perturbation and requirements from evaluation_sarfaDataset (calculateImprovements)
"""

import chess.engine
from collections import defaultdict
import sarfa_saliency
from basicFunctions import *

engine = None
threshold = (100 / 256)
enableEmptySquares = False


async def return_bestmove(board, eval_time=5, directory='svg_custom', puzzle='board'):
    """
    Returns best move for a given chess position
    Input :
        board : chess.Board
        eval_time : evaluation time
        directory : destination folder
        puzzle : name of puzzle
    Output :
        bestmove : chess.Move
    """

    if engine.options["MultiPV"].max < 100:
        evaluation = await engine.analyse(board, chess.engine.Limit(time=eval_time), multipv=engine.options["MultiPV"].max)
    else:
        evaluation = await engine.analyse(board, chess.engine.Limit(time=eval_time), multipv=100)
    # print(evaluation)
    i = 0
    while i < len(evaluation):
        if evaluation[i].__contains__("pv"):
            bestmove = evaluation[i]["pv"][0]
            break
        i += 1
        if i == len(evaluation):
            bestmove = evaluation[0]
    svg_w_arrow = svg_custom.board(board, arrows=[
        svg_custom.Arrow(tail=bestmove.from_square, head=bestmove.to_square, color='#e6e600')])
    svg_to_png(svg_w_arrow, directory, puzzle)
    return evaluation, bestmove


async def computeSaliency(enginePath='engines/stockfish-11-win/stockfish-11-win/Windows/stockfish_20011801_32bit.exe', FEN="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", directory ='svg_custom', puzzle='board', givenMove=None, file=None):
    """
    Function returns saliency map for given board position
    Input :
        enginePath : path containing engine's executable file
        FEN : Board position encoded in a FEN
        directory : destination folder
        puzzle : name of puzzle
        givenMove : guarantees that bestmove is equal to givenMove
        file : output file
    Output:
        answer : Saliency for each location on the board
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

    evaluation, original_move = await return_bestmove(board, evaltime, directory, puzzle)
    if givenMove is not None and givenMove != str(original_move)[0:4]:
        file.write("assigned new best move to engine\n")
        original_move = chess.Move(answer[givenMove[0:2]]['int'], answer[givenMove[2:4]]['int'])
        if len(givenMove) > 4:
            original_move = chess.Move(answer[givenMove[0:2]]['int'], answer[givenMove[2:4]]['int'],chess.Piece.from_symbol(givenMove[4]).piece_type)
    file.write("Best move is {}\n".format(original_move))
    colorPlayer = board.piece_at(answer[chess.SQUARE_NAMES[original_move.from_square]]['int']).color
    if colorPlayer == chess.WHITE:
        colorOpponent = chess.BLACK
    else:
        colorOpponent = chess.WHITE
    dict_q_values_before_perturbation = await get_dict_q_vals(board, legal_moves, evaltime, original_move, file, evaluation)
    file.write('------------------------------------------\n')

    original_move_Squares = get_moves_squares(board, original_move.from_square, original_move.to_square)
    file.write('squares of best move:\n')
    file.write("{}\n".format(original_move_Squares))
    file.write('------------------------------------------\n')

    # Iteratively perturb each feature on the board
    saliencyEmptySquares = {}
    for square_string in sorted(answer.keys()):
        entry = answer[square_string]
        entry_keys = ['saliency', 'dP', 'K', 'QMaxAnswer', 'actionGapBeforePerturbation', 'actionGapAfterPerturbation']
        file.write("perturbing square = {}\n".format(square_string))
        piece_removed = board.remove_piece_at(entry['int']) # remove piece on current square

        if piece_removed is None:
            if enableEmptySquares:
                if original_move_Squares.__contains__(square_string):
                    file.write('square is part of original move and must remain empty\n')
                    for key in entry_keys:
                        entry[key] = -1
                    entry['saliency'] = threshold # squares included in best move should be equally salient

                    if chess.square_rank(entry['int']) == 7 and board.piece_type_at(answer[chess.SQUARE_NAMES[original_move.from_square]]['int']) == chess.PAWN:
                        file.write("pawn promotion on this square\n")
                        entry['saliency'] = 1

                    if square_string == chess.SQUARE_NAMES[original_move.to_square]: # check for check after original move
                        board.set_piece_at(entry['int'], chess.Piece(board.piece_type_at(answer[chess.SQUARE_NAMES[original_move.from_square]]['int']), colorPlayer))
                        if board.was_into_check():
                            file.write('opponent is in check after best move\n')
                            for key in entry_keys:
                                entry[key] = -1
                            entry['saliency'] = 1
                            answer[chess.SQUARE_NAMES[chess.SQUARES.__getitem__(board.king(colorOpponent))]]['saliency'] = 1 # update king's saliency
                        board.remove_piece_at(entry['int'])

                elif chess.square_rank(entry['int']) != 0 and chess.square_rank(entry['int']) != 7:  # double pawn perturbation on rank 2-7 (1,8 excluded)
                    check = board.is_check()
                    file.write('square is empty, so put a pawn from player\'s color here\n')
                    board.set_piece_at(entry['int'], chess.Piece(chess.PAWN, colorPlayer))
                    if check is False and board.is_check() or board.was_into_check():
                        file.write('placed pawn results in check\n')
                        saliency = 0
                    else:
                        dict_q_values_after_perturbation = await get_dict_q_vals(board, legal_moves, evaltime, colorPlayer, file)
                        saliency, dP, k, qmax, gapBefore, gapAfter = sarfa_saliency.computeSaliencyUsingSarfa(
                            str(original_move), dict_q_values_before_perturbation, dict_q_values_after_perturbation,file)
                        file.write(
                            "saliency for this square with player\'s pawn: \'saliency\': {}, \'dP\': {}, \'K\': {} \n".format(saliency, dP, k))
                    board.remove_piece_at(entry['int'])

                    file.write('square is empty, so put a pawn from opponent\'s color here\n')
                    board.set_piece_at(entry['int'], chess.Piece(chess.PAWN, colorOpponent))
                    if check is False and board.is_check() or board.was_into_check():
                        file.write("placed pawn results in check\n")
                        saliency2 = 0
                    else:
                        dict_q_values_after_perturbation2 = await get_dict_q_vals(board, legal_moves, evaltime, colorPlayer, file)
                        if board.piece_type_at(chess.SQUARES[original_move.from_square]) == chess.KING:
                            if str(original_move) in dict_q_values_after_perturbation and str(original_move) in dict_q_values_after_perturbation2:  # be careful as opponents pawn can make original move illegal
                                saliency2, dP2, k2, qmax2, gapBefore2, gapAfter2 = sarfa_saliency.computeSaliencyUsingSarfa(
                                    str(original_move), dict_q_values_before_perturbation,
                                    dict_q_values_after_perturbation2, file)
                                file.write("saliency for this square with opponent\'s pawn: \'saliency\': {}, \'dP\': {}, \'K\': {} \n".format(saliency2, dP2, k2))
                            else:
                                file.write('inserted pawn makes king\'s move illegal\n')
                                saliency2 = 0
                        elif str(original_move) in dict_q_values_after_perturbation and str(original_move) in dict_q_values_after_perturbation2:
                            saliency2, dP2, k2, qmax2, gapBefore2, gapAfter2 = sarfa_saliency.computeSaliencyUsingSarfa(str(original_move), dict_q_values_before_perturbation,dict_q_values_after_perturbation2, file)
                            file.write("saliency for this square with opponent\'s pawn: \'saliency\': {}, \'dP\': {}, \'K\': {} \n".format(saliency2, dP2, k2))
                    board.remove_piece_at(entry['int'])

                    for key in entry_keys:
                        entry[key] = -1
                    entry['saliency'] = max([saliency, saliency2])
                    if entry['saliency'] > 0:
                        saliencyEmptySquares[square_string] = {'sal': entry['saliency'], 'sal1': saliency, 'sal2': saliency2}
                    file.write("saliency calculated as max from pawn perturbation for this empty square: {}\n".format(entry['saliency']))

                else: # rank 1 & 8
                    file.write('can not put a pawn on this square - so skipped\n')
            else:
                file.write('square was empty, so skipped\n')
            file.write('------------------------------------------\n')
            continue

        elif piece_removed == chess.Piece(6, colorOpponent) or piece_removed == chess.Piece(6, colorPlayer) or board.was_into_check(): # king can't be removed
            file.write('illegal piece was removed\n')
            if board.is_check(): # my king is currently in check
                answer[chess.SQUARE_NAMES[chess.SQUARES.__getitem__(board.king(colorPlayer))]]['saliency'] = 1  # update king's saliency
                file.write("king is salient because of check\n")
            if entry['saliency'] < 0:
                for key in entry_keys:
                    entry[key] = -1
                entry['saliency'] = 0
            if entry['int'] == answer[chess.SQUARE_NAMES[original_move.from_square]]['int']:
                entry['saliency'] = 1

        else:
            # Check if the original move is still valid
            if board.is_legal(original_move):

                dict_q_values_after_perturbation = await get_dict_q_vals(board, legal_moves, evaltime, original_move, file)
                entry['saliency'], entry['dP'], entry['K'], entry['QMaxAnswer'], entry['actionGapBeforePerturbation'], entry['actionGapAfterPerturbation'] \
                    = sarfa_saliency.computeSaliencyUsingSarfa(str(original_move), dict_q_values_before_perturbation, dict_q_values_after_perturbation, file)
                file.write("\'saliency\': {}, \'dP\': {}, \'K\': {}, \'QMaxAnswer\': {}, \'actionGapBeforePerturbation\': {}, \'actionGapAfterPerturbation\': {}\n".format(
                        entry['saliency'], entry['dP'], entry['K'], entry['QMaxAnswer'], entry['actionGapBeforePerturbation'], entry['actionGapAfterPerturbation']))

                if entry['saliency'] >= threshold:
                    if entry['dP'] >= 0.35 and entry['K'] >= 0: # precision(dp 0.35 - 1.0, K 0.0 - 1.0)
                        file.write("saliency is in best positive range\n")
                    else:
                        file.write("saliency is not in best positive range\n")
                        entry['saliency'] = 0
                        file.write("new saliency: {}\n".format(entry['saliency']))

                else:
                    file.write("saliency below threshold\n")
                    if entry['dP'] >= 0.15 and entry['K'] >= 0.05 and entry['K'] <= 0.9:  #dP between 0.15 and 1.0, K between 0.05 and 0.9
                        entry['saliency'] += threshold
                        file.write("new saliency: {}\n".format(entry['saliency']))
                        file.write("added calculated improvement\n")

                    else:
                        file.write("else clause: \'saliency\': {}, \'dP\': {}, \'K\': {}\n".format(entry['saliency'], entry['dP'],entry['K']))
                        file.write("dP and K do not meet requirements = {}\n".format(entry))
                file.write("saliency for this square = {}\n".format(entry))

            else:  # legal move must be pseudo legal, not variant end & not into check
                if board.is_variant_end():
                    file.write("variant end\n")
                if board.is_pseudo_legal(original_move) is False:
                    file.write('not pseudo legal\n')
                if board.is_into_check(original_move):
                    file.write("board is into check\n")

                # illegal original move in perturbed state, therefore piece removed is probably important
                file.write("original move illegal in perturbed state {}\n".format(square_string))
                for key in entry_keys:
                    entry[key] = -1
                entry['saliency'] = 1

        # undo perturbation
        file.write('------------------------------------------\n')
        board.set_piece_at(entry['int'], piece_removed)

    if len(saliencyEmptySquares) > 0:
        file.write('considered salient:\n')
        printSaliency(answer, saliencyEmptySquares, file)

        file.write('displaying top empty squares:\n')
        raiseSaliency(answer, saliencyEmptySquares, 3, file)

    aboveThreshold, belowThreshold = sortbySaliency(answer, 64, file)
    file.write('------------------------------------------\n')

    generate_heatmap(board, answer, original_move, directory, puzzle, file)

    board.push(original_move)
    result = board.is_game_over()
    if result:
        file.write("game ended with {}\n".format(board.result()))
    board.pop()
    await engine.quit()

    return answer, aboveThreshold, belowThreshold, original_move, colorPlayer, colorOpponent


async def get_dict_q_vals(board, legal_moves, eval_time, color, file, info=None):
    """
    This function returns a dictionary of Q-values for every move.
    Input :
        board : chess.Board()
        legal_moves : List of legal moves of original state
        eval_time : evaluation time
        file : output file
        info : None or given engine evaluation
    Output:
        q_vals_dict : Dictionary of move with respective Q-value
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
            info = await engine.analyse(board, chess.engine.Limit(time=eval_time),multipv=engine.options["MultiPV"].max)
        else:
            info = await engine.analyse(board, chess.engine.Limit(time=eval_time), multipv=100)
    dict_moves_to_score = defaultdict(int)

    # iterate over all possible moves
    move_id = 0
    while move_id < len(info):
        if "multipv" in info[move_id] and len(info[move_id]['pv']) > 0:
            move_string = str(info[move_id]['pv'][0])  # move representation (e.g. 'c5b6')

            if info[move_id]["score"].pov(color).score() is None:  # move has no centipawn evaluation value
                mate_in_moves = float(
                    ''.join(filter(lambda i: i.isdigit(), str(info[move_id]["score"].pov(color)))))
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
