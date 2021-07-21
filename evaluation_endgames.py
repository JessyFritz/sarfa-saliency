import json
import os
import re
import chess

import sarfa_saliency
from basicFunctions import get_moves_squares
from chess_saliency_chessSpecific import givenQValues_computeSaliency


def evaluate(directory="evaluation/endgames/original/"):
    """Evaluates endgame puzzles in the given directory based on the ground-truth in the chess_saliency_databases folder.

    :param directory: path where different engines' outputs are stored
    """

    folders = list(filter(lambda x: os.path.isdir(os.path.join(directory, x)), os.listdir(directory)))
    print(folders)
    if len(folders) == 0:
        directory, file = os.path.split(directory)
        directory += '/'
        folders.append(file)

    with open("chess_saliency_databases\endgames\groundTruth.json", "r") as jsonFile: # open endgame solutions
        database = json.load(jsonFile)

    data = dict()
    evaluation = {f: {} for f in folders}
    highestSal = 0
    highestSalEngine = ""

    for engine in folders: # iterate engines
        print(engine)
        evaluation[engine]["salient"] = 0                # number of salient marked squares for puzzles where engine executed solution move
        evaluation[engine]["missing"] = 0                # number of missing salient (false negative) squares for puzzles where engine executed solution move
        evaluation[engine]["precision"] = 0              # precision over puzzles where engine executed solution move
        evaluation[engine]["recall"] = 0                 # recall over puzzles where engine executed solution move
        evaluation[engine]["precision piece"] = []      # precision over non-empty squares where engine executed solution move
        evaluation[engine]["recall piece"] = []         # recall over non-empty squares where engine executed solution move
        evaluation[engine]["precision empty"] = []      # precision over empty squares where engine executed solution move
        evaluation[engine]["recall empty"] = []         # recall over empty squares where engine executed solution move
        evaluation[engine]["wrong move"] = 0             # times that engine executed wrong move
        evaluation[engine]["expected result"] = 0        # times that engine's results were exactly than expected
        evaluation[engine]["better result"] = 0          # times that engine's results were better than expected
        evaluation[engine]["worse result"] = 0           # times that engine's results were worse than expected
        evaluation[engine]["won"] = 0                    # times that engine won endgame
        evaluation[engine]["draw"] = 0                   # times that engine drawed endgame
        evaluation[engine]["lost"] = 0                   # times that engine lost endgame
        evaluation[engine]["game length"] = [0]*20       # engine's length for each endgame in moves
        evaluation[engine]["max game length"] = 0        # engine's longest endgame in moves
        evaluation[engine]["min game length"] = 1000     # engine's shortest endgame in moves
        evaluation[engine]["total game length"] = 0      # sum of all engine's game lengths

        nr = 1
        notGiven = 0

        for puzzle in database: # iterate puzzles
            puzzleNr = "puzzle" + str(nr)
            puzzle = puzzle[puzzleNr]

            miss = 0
            salEmpty = 0
            missEmpty = 0
            gTarrayEmpty = []

            path = "{}/{}/{}/data.json".format(directory, engine, puzzleNr)
            with open(path, "r") as jsonFile:
                data[engine] = json.load(jsonFile)

            board = chess.Board(data[engine]["move1"]["fen"])

            with open("{}/{}/{}/output.txt".format(directory, engine, puzzleNr), "r") as file:
                output = file.readlines()

            evaluation[engine]["game length"][nr-1] = len(data[engine])

            color = "black"
            if "w" in data[engine]["move1"]["fen"]:
                color = "white"

            if len(puzzle["best move"]) > 0:
                print("{} - {}'s turn - solution move is {} - expected result is {}".format(puzzleNr, color, puzzle["best move"], puzzle["expected result"]))
                print("    {}'s move: {}".format(engine,data[engine]["move1"]["move"]))
                j = 0
                while j < len(puzzle["best move"]):
                    if data[engine]["move1"]["move"] in puzzle["best move"][j]:
                        sal = len(data[engine]["move1"]["sorted saliencies"]["above threshold"]) # puzzle's salient squares
                        if sal > highestSal:
                            highestSal = sal
                            highestSalEngine = "{} {}".format(engine, puzzleNr)
                        for sq in data[engine]["move1"]["sorted saliencies"]["above threshold"]:
                            if board.piece_type_at(chess.SQUARES[chess.parse_square(sq)]) is None:
                                salEmpty += 1
                        evaluation[engine]["salient"] += sal
                        gT = puzzle["groundTruth"]
                        if len(puzzle["best move"]) > 1:
                            gT = puzzle["groundTruth"][j]
                        for sq in gT:
                            if board.piece_type_at(chess.SQUARES[chess.parse_square(sq)]) is None:
                                gTarrayEmpty.append(sq)
                            i = 0
                            for key in data[engine]["move1"]["sorted saliencies"]["above threshold"]:
                                if sq == key:
                                    break
                                i += 1
                                if i == len(data[engine]["move1"]["sorted saliencies"]["above threshold"]):
                                    miss += 1  # puzzle's missing ground truth
                                    if board.piece_type_at(chess.SQUARES[chess.parse_square(sq)]) is None:
                                        missEmpty += 1
                        evaluation[engine]["missing"] += miss
                        pr = 0
                        re = 0
                        if sal > 0:
                            print("    {} squares should be salient".format(len(gT)))
                            pr = (len(gT) - miss) / sal * 100       # puzzle's precision
                            re = (len(gT) - miss) / len(gT) * 100   # puzzle's recall
                            print("    {}: salient: {}, missing: {}, precision: {}, recall: {}".format(engine, sal, miss, round(pr, 2), round(re, 2)))
                        evaluation[engine]["precision"] += pr
                        evaluation[engine]["recall"] += re
                        if (sal - salEmpty) > 0:
                            pr = ((len(gT) - len(gTarrayEmpty)) - (miss - missEmpty)) / (sal - salEmpty) * 100
                            re = ((len(gT) - len(gTarrayEmpty)) - (miss - missEmpty)) / (len(gT) - len(gTarrayEmpty)) * 100
                            print("    {} piece squares: salient: {}, missing: {}, precision: {} %, recall: {} %".format(
                                engine, sal - salEmpty, miss - missEmpty, round(pr, 2), round(re, 2)))
                            evaluation[engine]["precision piece"].append(pr)
                            evaluation[engine]["recall piece"].append(re)
                        if len(gTarrayEmpty) > 0:
                            print("    {} empty squares should be salient".format(len(gTarrayEmpty)))  # only empty squares
                            if salEmpty > 0:
                                pr = (len(gTarrayEmpty) - missEmpty) / salEmpty * 100
                                re = (len(gTarrayEmpty) - missEmpty) / len(gTarrayEmpty) * 100
                                print( "      {} empty squares: salient: {}, missing: {}, precision: {} %, recall: {} %".format(
                                        engine, salEmpty, missEmpty, round(pr, 2), round(re, 2)))
                            else:
                                pr = 0
                                re = 0
                                print("    {} empty squares: salient: {}, missing: {}, precision: {} %, recall: {} %".format(
                                        engine, salEmpty, missEmpty, 0, 0))
                            evaluation[engine]["precision empty"].append(pr)
                            evaluation[engine]["recall empty"].append(re)
                        break
                    j += 1
                    if j == len(puzzle["best move"]):
                        evaluation[engine]["wrong move"] += 1

            else:
                print("{} - {}'s turn - no best move provided - expected result is {}".format(puzzleNr, color, puzzle["expected result"]))
                notGiven += 1

            for line in reversed(output):
                if line.startswith("game ended with "): # extract game's result from engine's output file
                    result = line.replace("game ended with ", "")
                    result = result.replace("\n", "")
                    if "1/2-1/2" in result:  # count result occurrences
                        evaluation[engine]["draw"] += 1
                    elif color == "black":
                        if "1-0" in result:
                            evaluation[engine]["lost"] += 1
                        elif "0-1" in result:
                            evaluation[engine]["won"] += 1
                    elif color == "white":
                        if "1-0" in result:
                            evaluation[engine]["won"] += 1
                        elif "0-1" in result:
                            evaluation[engine]["lost"] += 1

                    if result in puzzle["expected result"]:
                        evaluation[engine]["expected result"] += 1
                        print("    result as expected: {}".format(
                            result))  # result equals Larsson's expected possible outcome
                    elif "available result" in puzzle:
                        print("    according to Larsson {} is also possible".format(puzzle["available result"]))
                        if result in puzzle["available result"]:
                            evaluation[engine]["better result"] += 1
                            print("    good result: {}".format(
                                result))  # result equals Larsson's proposed (not expected) possible outcome
                        elif ("1-0" in puzzle["expected result"] and result == "0-1" and color == "black") or (
                                "0-1" in puzzle["expected result"] and result == "1-0" and color == "white"):
                            evaluation[engine]["better result"] += 1
                            print("    better result: {}".format(
                                result))  # result is even better than Larsson's proposed (not expected) possible outcome
                        else:
                            evaluation[engine][
                                "worse result"] += 1  # result is worse than Larsson's expected result and proposed possible outcome
                            if "note" in puzzle:
                                print("    worst result: {} (\"{}\")".format(result, puzzle["note"]))
                            else:
                                print("    worst result: {}".format(result))
                    elif "1/2-1/2" in puzzle["expected result"] and (
                            (result == "0-1" and color == "black") or (result == "1-0" and color == "white")):
                        evaluation[engine]["better result"] += 1
                        print("    unexpected result {} better than Larsson's expected".format(result))
                    elif ("0-1" in puzzle["expected result"] and color == "white") or (
                            "1-0" in puzzle["expected result"] and color == "black"):
                        evaluation[engine]["better result"] += 1
                        print("    unexpected result {} better than Larsson's expected".format(result))
                    elif "1/2-1/2" in puzzle["expected result"] and (
                            (result == "0-1" and color == "white") or (result == "1-0" and color == "black")):
                        evaluation[engine]["worse result"] += 1
                        print("    unexpected result {} worse than Larsson's expected".format(result))
                    elif ("1-0" in puzzle["expected result"] and color == "white") or (
                            "0-1" in puzzle["expected result"] and color == "black"):
                        evaluation[engine]["worse result"] += 1
                        print("    unexpected result {} worse than Larsson's expected".format(result))

            nr += 1

        evaluation[engine]["precision"] = round(evaluation[engine]["precision"] / (nr-1-evaluation[engine]["wrong move"]-notGiven),2)  # calculate mean of all precision values
        evaluation[engine]["recall"] = round(evaluation[engine]["recall"] / (nr-1-evaluation[engine]["wrong move"]-notGiven), 2)       # calculate mean of all recall values
        type1 = ["precision", "recall"]
        for a in type1:
            x = 0
            for m in evaluation[engine]["{} empty".format(a)]:
                x += m
            evaluation[engine]["{} empty".format(a)] = round(x / len(evaluation[engine]["{} empty".format(a)]), 2)
            x = 0
            for m in evaluation[engine]["{} piece".format(a)]:
                x += m
            evaluation[engine]["{} piece".format(a)] = round(x / len(evaluation[engine]["{} piece".format(a)]), 2)
        print('------------------------------------------')

    print('------------------------------------------')
    print("Evaluation:")
    print("highest number of marked squares: {}, {}".format(highestSalEngine, highestSal))
    print("Engines sorted by Result:")
    sortedKeys = sorted(evaluation, key=lambda x: evaluation[x]["expected result"]+evaluation[x]["better result"]-evaluation[x]["worse result"], reverse=True)  # sort engines according to their results
    rank = 1
    for key in sortedKeys:
        print("{}. {}:{} expected result: {}, better result: {}, worse result: {}".format(rank, key, " "*(11-len(key)), evaluation[key]["expected result"],evaluation[key]["better result"],evaluation[key]["worse result"]))
        rank += 1

    i = 0
    while i < 20:
        for engine in folders:
            moves = int(round(evaluation[engine]["game length"][i]/2))
            evaluation[engine]["total game length"] += moves
            if moves > evaluation[engine]["max game length"]:
                evaluation[engine]["max game length"] = moves
            elif moves < evaluation[engine]["min game length"]:
                evaluation[engine]["min game length"] = moves
        i += 1
    print('------------------------------------------')

    print("Engines sorted by Game Lengths:")
    sortedKeys = sorted(evaluation, key=lambda x: evaluation[x]["total game length"] / 20)
    rank = 1
    for key in sortedKeys:
        print("{}. {}:{} total moves: {}, average moves per puzzle: {}, min game length: {}, max game length: {}".format(rank, key, " "*(11-len(key)), evaluation[key]["total game length"], "%.2f" %(evaluation[key]["total game length"]/20) ,evaluation[key]["min game length"], evaluation[key]["max game length"]))
        rank += 1
    print('------------------------------------------')

    print("Engines sorted by Won/Draw/Lost:")
    sortedKeys = sorted(evaluation, key=lambda x: 2 * evaluation[x]["won"] + evaluation[x]["draw"] - 2 * evaluation[x]["lost"], reverse=True)
    rank = 1
    for key in sortedKeys:
        print("{}. {}:{} won: {}, draw: {}, lost: {}".format(rank, key, " "*(11-len(key)), evaluation[key]["won"], evaluation[key]["draw"],evaluation[key]["lost"]))
        rank += 1
    print('------------------------------------------')

    #Analysis For Non-Empty Square
    print("Engines sorted by Non-Empty Squares:")
    sortedKeys = sorted(evaluation, key=lambda x: 2 * (evaluation[x]["precision piece"] * evaluation[x]["recall piece"] / (evaluation[x]["precision piece"] + evaluation[x]["recall piece"])), reverse=True)  # sort engines according to the F1 mean
    rank = 1
    mF = 0
    mP = 0
    mR = 0
    for key in sortedKeys:
        print("{}. {}:{} non-empty Squares F1: {} %, non-empty Squares precision: {} %, non-empty Squares recall: {} %".format(rank, key, " " * (11 - len(key)),
                round(2 * evaluation[key]["precision piece"] * evaluation[key]["recall piece"] / (evaluation[key]["precision piece"] + evaluation[key]["recall piece"]), 2), "%.2f" % (evaluation[key]["precision piece"]), "%.2f" % evaluation[key]["recall piece"]))
        rank += 1
        mF += round(2 * evaluation[key]["precision piece"] * evaluation[key]["recall piece"] / (evaluation[key]["precision piece"] + evaluation[key]["recall piece"]), 2)
        mP += evaluation[key]["precision piece"]
        mR += evaluation[key]["recall piece"]
    print("F1 mean: {} %, precision mean: {} %, recall mean: {} %".format(round(mF / len(folders), 2), round(mP / len(folders), 2),
                                                                          round(mR / len(folders), 2)))
    print('------------------------------------------')

    #Analysis For Empty Square
    print("Engines sorted by Empty Squares:")
    sortedKeys = sorted(evaluation, key=lambda x: 2 * (evaluation[x]["precision empty"] * evaluation[x]["recall empty"] / (evaluation[x]["precision empty"] + evaluation[x]["recall empty"]+1)), reverse=True)  # sort engines according to the F1 mean
    rank = 1
    mF = 0
    mP = 0
    mR = 0
    for key in sortedKeys:
        f = 0
        if evaluation[key]["precision empty"] + evaluation[key]["recall empty"] != 0:
            f = round(2 * evaluation[key]["precision empty"] * evaluation[key]["recall empty"] / (evaluation[key]["precision empty"] + evaluation[key]["recall empty"]), 2)
        print("{}. {}:{} empty Squares F1: {} %, empty Squares precision: {} %, empty Squares recall: {} %".format(rank, key, " " * (11 - len(key)), f, "%.2f" % (evaluation[key]["precision empty"]), "%.2f" % evaluation[key]["recall empty"]))
        rank += 1
        mF += f
        mP += evaluation[key]["precision empty"]
        mR += evaluation[key]["recall empty"]
    print("F1 mean: {} %, precision mean: {} %, recall mean: {} %".format(round(mF / len(folders), 2), round(mP / len(folders), 2), round(mR / len(folders), 2)))
    print('------------------------------------------')

    print("Engines sorted by F1 mean:")
    sortedKeys = sorted(evaluation, key=lambda x: 2 * ((evaluation[x]["precision"] * evaluation[x]["recall"]) / (evaluation[x]["precision"] + evaluation[x]["recall"])), reverse=True)  # sort engines according to the F1 mean
    rank = 1
    mF = 0
    mP = 0
    mR = 0
    for key in sortedKeys:
        print("{}. {}:{} wrong move: {}, F1: {} %, precision: {} %, recall: {} %".format(rank, key, " "*(11-len(key)), evaluation[key]["wrong move"], "%.2f" %(round(2 * ((evaluation[key]["precision"] * evaluation[key]["recall"]) / (evaluation[key]["precision"] + evaluation[key]["recall"])),2)), "%.2f" %(evaluation[key]["precision"]), "%.2f" %(evaluation[key]["recall"])))
        rank += 1
        mF += round(2 * ((evaluation[key]["precision"] * evaluation[key]["recall"]) / (evaluation[key]["precision"] + evaluation[key]["recall"])), 2)
        mP += evaluation[key]["precision"]
        mR += evaluation[key]["recall"]
    print("F1 mean: {} %, precision mean: {} %, recall mean: {} %".format(round(mF / 8, 2), round(mP / 8, 2), round(mR / 8, 2)))


async def evaluateEndgames_allPuzzles(directory="evaluation/endgames/original", mode="All"):
    """Evaluates all endgame puzzles in the given directory based on the ground-truth in the chess_saliency_databases folder.

    :param directory: path where different engines' outputs are stored
    :param mode: options "All"/"Right"/"Wrong" implemented: "All" - evaluate all puzzles (wrong moves with adapted maps and right moves), "Right" - only evaluate puzzles with right moves (should yield highest preciison and recall), "Wrong" - only evaluate puzzles with initial wrong moves, but calculate maps for a solution move
    """

    folders = list(filter(lambda x: os.path.isdir(os.path.join(directory, x)), os.listdir(directory)))
    print(folders)
    if len(folders) == 0:
        directory, file = os.path.split(directory)
        directory += '/'
        folders.append(file)

    if mode != "Right":
        files = directory.split("/")
        pathDir = ""
        i = 0
        while i < len(files) - 1:
            pathDir += files[i] + "/"
            i += 1
        pathDir += "{}_correctedMoves".format(files[i])
        print(pathDir)
        if not os.path.exists(pathDir):
            os.makedirs(pathDir)
            print("created directory")

    with open("chess_saliency_databases\endgames\groundTruth.json", "r") as jsonFile:  # open endgame solutions
        database = json.load(jsonFile)

    evaluation = {f: {} for f in folders}
    highestF1 = 0

    for engine in folders: # iterate engines
        print(engine)
        evaluation[engine]["salient"] = 0  # number of salient marked squares for puzzles where engine executed solution move
        evaluation[engine]["missing"] = 0  # number of missing salient (false negative) squares for puzzles where engine executed solution move
        evaluation[engine]["precision"] = 0  # precision over puzzles where engine executed solution move
        evaluation[engine]["recall"] = 0  # recall over puzzles where engine executed solution move
        evaluation[engine]["precision piece"] = []  # precision over non-empty squares where engine executed solution move
        evaluation[engine]["recall piece"] = []  # recall over non-empty squares where engine executed solution move
        evaluation[engine]["precision empty"] = []  # precision over empty squares where engine executed solution move
        evaluation[engine]["recall empty"] = []  # recall over empty squares where engine executed solution move
        evaluation[engine]["wrong move"] = 0  # times that engine executed wrong move

        if mode != "Right":
            if not os.path.exists(pathDir+"/"+engine):
                os.makedirs(pathDir+"/"+engine)
                print("created directory")

        nr = 1
        notGiven = 0

        for puzzle in database:  # iterate puzzles
            puzzleNr = "puzzle" + str(nr)
            print(puzzleNr)
            puzzle = puzzle[puzzleNr]

            miss = 0
            salEmpty = 0
            missEmpty = 0

            path = "{}/{}/{}/data.json".format(directory, engine, puzzleNr)
            with open(path, "r") as jsonFile:
                data = json.load(jsonFile)

            board = chess.Board(data["move1"]["fen"])

            if len(puzzle["best move"]) == 0:
                notGiven += 1
            else:
                if data["move1"]["move"] in puzzle["best move"]:
                    j = 0
                    while j < len(puzzle["best move"]):
                        if data["move1"]["move"] in puzzle["best move"][j]:
                            break
                        j += 1
                    if mode == "All" or mode == "Right":
                        gTarray = puzzle["groundTruth"]
                        if len(puzzle["best move"]) > 1:
                            gTarray = puzzle["groundTruth"][j]
                        print(gTarray)
                        if gTarray is not None and len(gTarray) > 0:  # calculate precision and recall
                            print("   {} squares should be salient".format(len(gTarray)))

                            gTarrayEmpty = []
                            sal = len(data["move1"]["sorted saliencies"]["above threshold"])
                            for m in data["move1"]["sorted saliencies"]["above threshold"]:  # analyse all empty squares
                                if board.piece_type_at(chess.SQUARES[chess.parse_square(m)]) is None:
                                    salEmpty += 1
                            for m in gTarray:
                                if board.piece_type_at(chess.SQUARES[chess.parse_square(m)]) is None:
                                    gTarrayEmpty.append(m)
                            for sq in data["move1"]["sorted saliencies"]["above threshold"]:
                                if sq in gTarray:
                                    miss += 1
                                if sq in gTarrayEmpty:
                                    missEmpty += 1
                            miss = len(gTarray) - miss
                            missEmpty = len(gTarrayEmpty) - missEmpty

                            if sal > 0:
                                precision = (len(gTarray) - miss) / sal * 100
                                recall = (len(gTarray) - miss) / len(gTarray) * 100
                                print("   {}: salient: {}, missing: {}, precision: {} %, recall: {} %".format(engine, sal,miss,round(precision,2),round(recall,2)))
                            if miss > 0:
                                print("      above threshold: ")
                                for m in data["move1"]["sorted saliencies"]["above threshold"]:
                                    if m in gTarray:
                                        print("      {}: {}".format(m, data["move1"]["sorted saliencies"][
                                            "above threshold"][m]))
                                print("      below threshold: ")
                                for m in data["move1"]["sorted saliencies"]["below threshold"]:
                                    if m in gTarray:
                                        print("      {}: {}".format(m, data["move1"]["sorted saliencies"][
                                            "below threshold"][m]))

                            evaluation[engine]["precision"] += precision
                            evaluation[engine]["recall"] += recall
                            f1 = 2 * precision * recall / (precision + recall)
                            if f1 > highestF1:
                                highestF1 = f1
                                print("highest F1 so far")

                            print("   {} piece squares should be salient".format(
                                len(gTarray) - len(gTarrayEmpty)))  # only non empty squares
                            if (sal - salEmpty) > 0:
                                precision = ((len(gTarray) - len(gTarrayEmpty)) - (miss - missEmpty)) / (sal - salEmpty) * 100
                                recall = ((len(gTarray) - len(gTarrayEmpty)) - (miss - missEmpty)) / (
                                            len(gTarray) - len(gTarrayEmpty)) * 100
                                print("   {} piece squares: salient: {}, missing: {}, precision: {} %, recall: {} %".format(
                                        engine, sal - salEmpty, miss - missEmpty, round(precision, 2), round(recall, 2)))
                                evaluation[engine]["precision piece"].append(precision)
                                evaluation[engine]["recall piece"].append(recall)
                            if len(gTarrayEmpty) > 0:
                                print("   {} empty squares should be salient".format(
                                    len(gTarrayEmpty)))  # only empty squares
                                if salEmpty > 0:
                                    precision = (len(gTarrayEmpty) - missEmpty) / salEmpty * 100
                                    recall = (len(gTarrayEmpty) - missEmpty) / len(gTarrayEmpty) * 100
                                    print("   {} empty squares: salient: {}, missing: {}, precision: {} %, recall: {} %".format(
                                            engine, salEmpty, missEmpty, round(precision, 2), round(recall, 2)))
                                else:
                                    precision = 0
                                    recall = 0
                                    print("   {} empty squares: salient: {}, missing: {}, precision: {} %, recall: {} %".format(engine, salEmpty, missEmpty, 0, 0))
                                evaluation[engine]["precision empty"].append(precision)
                                evaluation[engine]["recall empty"].append(recall)
                else:
                    print("wrong move")
                    evaluation[engine]["wrong move"] += 1

                    if mode == "Wrong" or mode == "All":

                        path = directory + "/" + engine + "/" + puzzleNr + "/" + "output.txt"
                        with open(path, "r") as file:
                            output = file.readlines()

                        qValuesEngine = dict()

                        i = 0
                        while output[i].startswith("move1") is False:
                            i += 1

                        while i < len(output):
                            if output[i].startswith("move1") and len(output[i]) < 15:
                                beforeP = None
                                board = chess.Board(data["move1"]["fen"])
                            elif output[i].startswith("move2") and len(output[i]) < 15:
                                break
                            elif output[i].startswith("Q Values: {") and beforeP is None:
                                beforeP = output[i].replace("Q Values: {", "").split(",")
                                beforePdict = dict()
                                for x in beforeP:
                                    key = ""
                                    value = ""
                                    import re
                                    m = re.search(r"[a-h][1-8][a-h][1-8]", x)
                                    if m is not None:
                                        index = m.span()
                                        key = x[index[0]:index[1]]
                                    m = re.findall(r"[-+]?\d*\.\d+|\d+", x)
                                    if len(m) > 2:
                                        value = m[2]
                                    beforePdict[key] = float(value)
                                print(beforePdict)
                            elif output[i].startswith("perturbing square = "):
                                sq = output[i].replace("perturbing square = ", "")
                                sq = sq.replace("\n", "")
                                qValuesEngine[sq] = dict()
                            elif output[i].startswith("querying engine with perturbed position"):
                                while output[i].startswith("------------------------------------------") is False:
                                    if output[i].startswith("Q Values: {"):
                                        afterP = output[i].replace("Q Values: {", "").split(",")
                                        afterPdict = dict()
                                        for x in afterP:
                                            key = ""
                                            value = ""
                                            import re
                                            m = re.search(r"[a-h][1-8][a-h][1-8]", x)
                                            if m is not None:
                                                index = m.span()
                                                key = x[index[0]:index[1]]
                                            m = re.findall(r"[-+]?\d*\.\d+|\d+", x)
                                            if len(m) > 2:
                                                value = m[2]
                                            afterPdict[key] = float(value)
                                        break
                                    i += 1
                                qValuesEngine[sq]["regular"] = afterPdict
                            elif output[i].startswith("new pawn saliency for this square"):
                                y = i
                                while output[y].startswith("------------------------------------------") is False:
                                    if output[y].startswith("Q Values: {"):
                                        afterP = output[y].replace("Q Values: {", "").split(",")
                                        afterPdict = dict()
                                        for x in afterP:
                                            key = ""
                                            value = ""
                                            m = re.search(r"[a-h][1-8][a-h][1-8]", x)
                                            if m is not None:
                                                index = m.span()
                                                key = x[index[0]:index[1]]
                                            m = re.findall(r"[-+]?\d*\.\d+|\d+", x)
                                            if len(m) > 2:
                                                value = m[2]
                                            afterPdict[key] = float(value)
                                        break
                                    y -= 1
                                    qValuesEngine[sq]["pawn"] = afterPdict
                            elif output[i].startswith("square is empty, so put a pawn from player's color here"):
                                afterP1 = None
                                afterP2 = None
                                while output[i].startswith("------------------------------------------") is False:
                                    if output[i].startswith("Q Values: {") and afterP1 is None:
                                        afterP1 = output[i].replace("Q Values: {", "").split(",")
                                        afterP1dict = dict()
                                        for x in afterP1:
                                            key = ""
                                            value = ""
                                            import re
                                            m = re.search(r"[a-h][1-8][a-h][1-8]", x)
                                            if m is not None:
                                                index = m.span()
                                                key = x[index[0]:index[1]]
                                            m = re.findall(r"[-+]?\d*\.\d+|\d+", x)
                                            if len(m) > 2:
                                                value = m[2]
                                            afterP1dict[key] = float(value)
                                    elif output[i].startswith("Q Values: {") and afterP2 is None:
                                        afterP2 = output[i].replace("Q Values: {", "").split(",")
                                        afterP2dict = dict()
                                        for x in afterP2:
                                            key = ""
                                            value = ""
                                            m = re.search(r"[a-h][1-8][a-h][1-8]", x)
                                            if m is not None:
                                                index = m.span()
                                                key = x[index[0]:index[1]]
                                            m = re.findall(r"[-+]?\d*\.\d+|\d+", x)
                                            if len(m) > 2:
                                                value = m[2]
                                            afterP2dict[key] = float(value)
                                        break
                                    i += 1
                                qValuesEngine[sq] = {
                                    "player" : afterP1dict,
                                    "opponent" : afterP2dict
                                }
                            i += 1
                        print("starting SARFA")
                        ss = puzzle["best move"][0][0:2]
                        ds = puzzle["best move"][0][2:4]
                        move = chess.Move(chess.SQUARES[chess.parse_square(ss)], chess.SQUARES[chess.parse_square(ds)])
                        if mode != "Right":
                            if not os.path.exists(pathDir + "/" + engine + "/" + puzzleNr):
                                os.makedirs(pathDir + "/" + engine + "/" + puzzleNr)
                                print("created directory")
                        aboveThreshold, _ = await givenQValues_computeSaliency(board, move, data["move1"]["fen"], beforePdict, qValuesEngine, pathDir + "/" + engine + "/" + puzzleNr, "move1")

                        gTarray = puzzle["groundTruth"]
                        if len(puzzle["best move"]) > 1:
                            gTarray = puzzle["groundTruth"][0]
                        if gTarray is not None and len(gTarray) > 0:  # calculate precision and recall

                            gTarrayEmpty = []
                            sal = len(aboveThreshold)
                            for m in aboveThreshold:  # analyse all empty squares
                                if board.piece_type_at(chess.SQUARES[chess.parse_square(m)]) is None:
                                    salEmpty += 1
                            for m in gTarray:
                                if board.piece_type_at(chess.SQUARES[chess.parse_square(m)]) is None:
                                    gTarrayEmpty.append(m)
                            for sq in aboveThreshold:
                                if sq in gTarray:
                                    miss += 1
                                if sq in gTarrayEmpty:
                                    missEmpty += 1
                            miss = len(gTarray) - miss
                            missEmpty = len(gTarrayEmpty) - missEmpty

                            if sal > 0:
                                precision = (len(gTarray) - miss) / sal * 100
                                recall = (len(gTarray) - miss) / len(gTarray) * 100
                                print("   {}: salient: {}, missing: {}, precision: {} %, recall: {} %".format(engine, sal, miss, round(precision, 2), round(recall, 2)))
                            if miss > 0:
                                print("      above threshold: ")
                                for m in aboveThreshold:
                                    if m in gTarray:
                                        print("      {}: {}".format(m, aboveThreshold[m]))

                            evaluation[engine]["precision"] += precision
                            evaluation[engine]["recall"] += recall
                            f1 = 2 * precision * recall / (precision + recall)
                            if f1 > highestF1:
                                highestF1 = f1
                                print("highest F1 so far")

                            print("   {} piece squares should be salient".format(
                            len(gTarray) - len(gTarrayEmpty)))  # only non empty squares
                            if (sal - salEmpty) > 0:
                                precision = ((len(gTarray) - len(gTarrayEmpty)) - (miss - missEmpty)) / (sal - salEmpty) * 100
                                recall = ((len(gTarray) - len(gTarrayEmpty)) - (miss - missEmpty)) / (
                                            len(gTarray) - len(gTarrayEmpty)) * 100
                                print("   {} piece squares: salient: {}, missing: {}, precision: {} %, recall: {} %".format(
                                        engine, sal - salEmpty, miss - missEmpty, round(precision, 2), round(recall, 2)))
                                evaluation[engine]["precision piece"].append(precision)
                                evaluation[engine]["recall piece"].append(recall)
                            if len(gTarrayEmpty) > 0:
                                print("   {} empty squares should be salient".format(
                                    len(gTarrayEmpty)))  # only empty squares
                                if salEmpty > 0:
                                    precision = (len(gTarrayEmpty) - missEmpty) / salEmpty * 100
                                    recall = (len(gTarrayEmpty) - missEmpty) / len(gTarrayEmpty) * 100
                                    print("   {} empty squares: salient: {}, missing: {}, precision: {} %, recall: {} %".format(
                                            engine, salEmpty, missEmpty, round(precision, 2), round(recall, 2)))
                                else:
                                    precision = 0
                                    recall = 0
                                    print("   {} empty squares: salient: {}, missing: {}, precision: {} %, recall: {} %".format(engine, salEmpty, missEmpty, 0, 0))
                                evaluation[engine]["precision empty"].append(precision)
                                evaluation[engine]["recall empty"].append(recall)
            nr += 1

        if mode == "All":
            print("{}\'s averages are calculated over all {} puzzles".format(engine, nr - 1 - notGiven))
            evaluation[engine]["precision"] = round(evaluation[engine]["precision"] / (nr - 1 - notGiven), 2)  # calculate mean of all precision values
            evaluation[engine]["recall"] = round(evaluation[engine]["recall"] / (nr - 1 - notGiven), 2)        # calculate mean of all recall values
        elif mode == "Right":
            print("{}\'s averages are calculated over {} puzzles".format(engine, nr - 1 - evaluation[engine]["wrong move"] - notGiven))
            evaluation[engine]["precision"] = round(evaluation[engine]["precision"] / (nr - 1 - evaluation[engine]["wrong move"] - notGiven), 2)  # calculate mean of all precision values
            evaluation[engine]["recall"] = round(evaluation[engine]["recall"] / (nr - 1 - evaluation[engine]["wrong move"] - notGiven), 2)  # calculate mean of all recall values
        elif mode == "Wrong":
            print("{}\'s averages are calculated over {} puzzles".format(engine, evaluation[engine]["wrong move"]))
            if evaluation[engine]["wrong move"] > 0:
                evaluation[engine]["precision"] = round(evaluation[engine]["precision"] / evaluation[engine]["wrong move"], 2)  # calculate mean of all precision values
                evaluation[engine]["recall"] = round(evaluation[engine]["recall"] / evaluation[engine]["wrong move"], 2)  # calculate mean of all recall values

        type1 =["precision", "recall"]
        for a in type1:
            if len(evaluation[engine]["{} empty".format(a)]) > 0:
                x = 0
                for m in evaluation[engine]["{} empty".format(a)]:
                    x += m
                evaluation[engine]["{} empty".format(a)] = round(x / len(evaluation[engine]["{} empty".format(a)]), 2)
            else:
                evaluation[engine]["{} empty".format(a)] = 0
            if len(evaluation[engine]["{} piece".format(a)]) > 0:
                x = 0
                for m in evaluation[engine]["{} piece".format(a)]:
                    x += m
                evaluation[engine]["{} piece".format(a)] = round(x / len(evaluation[engine]["{} piece".format(a)]), 2)
            else:
                evaluation[engine]["{} piece".format(a)] = 0
            print('------------------------------------------')

    if mode == "Right":
        keys = list(evaluation)
        print(keys)
        for engine in keys:
            if evaluation[engine]["wrong move"] == 20-notGiven:
                print("engine {} deleted".format(engine))
                folders.remove(engine)
                del evaluation[engine]
    elif mode == "Wrong":
        keys = list(evaluation)
        for engine in keys:
            if evaluation[engine]["wrong move"] == 0:
                print("engine {} deleted".format(engine))
                folders.remove(engine)
                del evaluation[engine]

    # Analysis For Non-Empty Square
    print("Engines sorted by Non-Empty Squares:")
    keys = list(evaluation)
    copy = evaluation.copy()
    for engine in keys:
        if (evaluation[engine]["precision piece"] + evaluation[engine]["recall piece"]) == 0:
            del copy[engine]
            print("engine {} has {} wrong moves (precision {}, recall {})".format(engine, evaluation[engine][
                "wrong move"], evaluation[engine]["precision piece"], evaluation[engine]["recall piece"]))

    sortedKeys = sorted(copy, key=lambda x: 2 * (
                evaluation[x]["precision piece"] * evaluation[x]["recall piece"] / (
                    evaluation[x]["precision piece"] + evaluation[x]["recall piece"])),
                        reverse=True)  # sort engines according to the F1 mean
    rank = 1
    mF = 0
    mP = 0
    mR = 0
    for key in sortedKeys:
        print("{}. {}:{} non-empty Squares F1: {} %, non-empty Squares precision: {} %, non-empty Squares recall: {} %".format(
                rank, key, " " * (11 - len(key)),
                round(2 * evaluation[key]["precision piece"] * evaluation[key]["recall piece"] / (
                        evaluation[key]["precision piece"] + evaluation[key]["recall piece"]), 2),
                           "%.2f" % (evaluation[key]["precision piece"]), "%.2f" % evaluation[key]["recall piece"]))
        rank += 1
        mF += round(2 * evaluation[key]["precision piece"] * evaluation[key]["recall piece"] / (
                evaluation[key]["precision piece"] + evaluation[key]["recall piece"]), 2)
        mP += evaluation[key]["precision piece"]
        mR += evaluation[key]["recall piece"]
    print("F1 mean: {} %, precision mean: {} %, recall mean: {} %".format(round(mF / len(folders), 2), round(mP / len(folders), 2), round(mR / len(folders), 2)))
    print('------------------------------------------')

    #Analysis For Empty Square
    print("Engines sorted by Empty Squares:")
    keys = list(evaluation)
    copy = evaluation.copy()
    for engine in keys:
        if (evaluation[engine]["precision empty"] + evaluation[engine]["precision empty"]) == 0:
            del copy[engine]
            print("engine {} has {} wrong moves (precision {}, recall {})".format(engine, evaluation[engine]["wrong move"], evaluation[engine]["precision empty"], evaluation[engine]["precision empty"]))

    sortedKeys = sorted(copy, key=lambda x: 2 * (evaluation[x]["precision empty"] * evaluation[x]["recall empty"] / (evaluation[x]["precision empty"] + evaluation[x]["recall empty"]+1)), reverse=True)  # sort engines according to the F1 mean
    rank = 1
    mF = 0
    mP = 0
    mR = 0
    for key in sortedKeys:
        f = 0
        if evaluation[key]["precision empty"] + evaluation[key]["recall empty"] != 0:
            f = round(2 * evaluation[key]["precision empty"] * evaluation[key]["recall empty"] / (evaluation[key]["precision empty"] + evaluation[key]["recall empty"]), 2)
        print("{}. {}:{} empty Squares F1: {} %, empty Squares precision: {} %, empty Squares recall: {} %".format(rank, key, " " * (11 - len(key)), f, "%.2f" % (evaluation[key]["precision empty"]), "%.2f" % evaluation[key]["recall empty"]))
        rank += 1
        mF += f
        mP += evaluation[key]["precision empty"]
        mR += evaluation[key]["recall empty"]
    print("F1 mean: {} %, precision mean: {} %, recall mean: {} %".format(round(mF / len(folders), 2), round(mP / len(folders), 2), round(mR / len(folders), 2)))
    print('------------------------------------------')

    print("Engines sorted by F1 mean:")
    keys = list(evaluation)
    copy = evaluation.copy()
    for engine in keys:
        if (evaluation[engine]["precision"] + evaluation[engine]["recall"]) == 0:
            del copy[engine]
            print("engine {} has {} wrong moves (precision {}, recall {})".format(engine, evaluation[engine]["wrong move"], evaluation[engine]["precision"], evaluation[engine]["recall"]))

    sortedKeys = sorted(copy, key=lambda x: 2 * ((evaluation[x]["precision"] * evaluation[x]["recall"]) / (evaluation[x]["precision"] + evaluation[x]["recall"])), reverse=True)  # sort engines according to the F1 mean
    rank = 1
    mF = 0
    mP = 0
    mR = 0
    for key in sortedKeys:
        print("{}. {}:{} wrong move: {}, F1: {} %, precision: {} %, recall: {} %".format(rank, key, " "*(11-len(key)), evaluation[key]["wrong move"], "%.2f" %(round(2 * ((evaluation[key]["precision"] * evaluation[key]["recall"]) / (evaluation[key]["precision"] + evaluation[key]["recall"])),2)), "%.2f" %(evaluation[key]["precision"]), "%.2f" %(evaluation[key]["recall"])))
        rank += 1
        mF += round(2 * ((evaluation[key]["precision"] * evaluation[key]["recall"]) / (evaluation[key]["precision"] + evaluation[key]["recall"])), 2)
        mP += evaluation[key]["precision"]
        mR += evaluation[key]["recall"]
    print("F1 mean: {} %, precision mean: {} %, recall mean: {} %".format(round(mF / 8, 2), round(mP / 8, 2), round(mR / 8, 2)))


def singleEngine_endgames_groundTruthEvaluation(directory1="evaluation/endgames/original/stockfish", directory2="evaluation/endgames/updated/stockfish"):
    """ Evaluates the endgame database's puzzles for a single engine with the original and updated SARFA implementation.

    :param directory1: path where first engine's outputs are stored
    :param directory2: path where second engine's outputs are stored
    :return:
    """

    folders = []
    di, engineName = os.path.split(directory1)
    _, name = os.path.split(di)
    folders.append(name)
    di, engineName = os.path.split(directory2)
    _, name = os.path.split(di)
    folders.append(name)
    with open('chess_saliency_databases/endgames/groundTruth.json', "r") as jsonFile:
        database = json.load(jsonFile)
    data = dict()

    evaluation = {f: {} for f in folders}
    print(evaluation)

    evaluation[folders[0]]["salient"] = 0
    evaluation[folders[0]]["missing"] = 0
    evaluation[folders[0]]["precision"] = 0
    evaluation[folders[0]]["recall"] = 0
    evaluation[folders[1]]["salient"] = 0
    evaluation[folders[1]]["missing"] = 0
    evaluation[folders[1]]["precision"] = 0
    evaluation[folders[1]]["recall"] = 0

    subset = []
    nr = 1
    while nr < 21:
        puzzleNr = "puzzle" + str(nr)

        if len(database[nr-1][puzzleNr]["best move"]) > 0:
            with open("{}/{}/data.json".format(directory1, puzzleNr), "r") as jsonFile:
                data[folders[0]] = json.load(jsonFile)
            with open("{}/{}/data.json".format(directory2, puzzleNr), "r") as jsonFile:
                data[folders[1]] = json.load(jsonFile)

            if data[folders[0]]["move1"]["move"] in database[nr-1][puzzleNr]["best move"] and data[folders[1]]["move1"]["move"] in database[nr-1][puzzleNr]["best move"]:
                subset.append(puzzleNr)
        nr += 1

    nr = 1
    total = 0
    for puzzle in database:
        puzzleNr = "puzzle" + str(nr)
        with open("{}/{}/data.json".format(directory1, puzzleNr), "r") as jsonFile:
            data[folders[0]] = json.load(jsonFile)
        with open("{}/{}/data.json".format(directory2, puzzleNr), "r") as jsonFile:
            data[folders[1]] = json.load(jsonFile)

        for x in subset:
            if puzzleNr == x:
                print("{} - {} squares salient".format(puzzleNr, len(puzzle[puzzleNr]["groundTruth"])))
                total += len(puzzle[puzzleNr]["groundTruth"])

                for f in data:
                    sal = len(data[f]["move1"]["sorted saliencies"]["above threshold"])    # puzzle's salient squares
                    evaluation[f]["salient"] += sal
                    miss = 0

                    for square in puzzle[puzzleNr]["groundTruth"]:
                        if square not in data[f]["move1"]["sorted saliencies"]["above threshold"]:
                            miss += 1                                                       # puzzle's missing ground truth
                        for sq in data[f]["move1"]["sorted saliencies"]:
                            if sq == square:
                                print(data[f]["move1"]["sorted saliencies"][sq])
                                break

                    evaluation[f]["missing"] += miss
                    pr = 0
                    re = 0
                    if sal > 0:
                        pr = (len(puzzle[puzzleNr]["groundTruth"]) - miss) / sal * 100                                      # puzzle's precision
                        re = (len(puzzle[puzzleNr]["groundTruth"]) - miss) / len(puzzle[puzzleNr]["groundTruth"]) * 100     # puzzle's recall
                    print("   {}: salient: {}, missing: {}, precision: {} %, recall: {} %".format(f, sal, miss, round(pr, 2), round(re, 2)))
                    evaluation[f]["precision"] += pr
                    evaluation[f]["recall"] += re

        nr += 1
    length = len(subset)
    evaluation[folders[0]]["precision"] = round(evaluation[folders[0]]["precision"]/len(subset), 2)
    evaluation[folders[0]]["recall"] = round(evaluation[folders[0]]["recall"] / len(subset), 2)
    evaluation[folders[1]]["precision"] = round(evaluation[folders[1]]["precision"] / len(subset), 2)
    evaluation[folders[1]]["recall"] = round(evaluation[folders[1]]["recall"] / len(subset), 2)

    print('------------------------------------------')
    print("In total {} squares from {} puzzles should be salient".format(total, length))
    print("Evaluation for {}: ".format(engineName))
    sortedKeys = sorted(evaluation, key=lambda x: 2*((evaluation[x]["precision"]*evaluation[x]["recall"])/(evaluation[x]["precision"]+evaluation[x]["recall"])), reverse=True) # sort engines according to their precision
    rank = 1

    for key in sortedKeys:
        print("{}. {}:{} F1: {} %, {}".format(rank, key, " "*(11-len(key)), "%.2f" %(round(2*((evaluation[key]["precision"]*evaluation[key]["recall"])/(evaluation[key]["precision"]+evaluation[key]["recall"])),2)), evaluation[key]))

        rank += 1
    print("\nmarked {} more squares as salient".format(evaluation[folders[0]]["missing"] - evaluation[folders[1]]["missing"]))
    if evaluation[folders[0]]["precision"] < evaluation[folders[1]]["precision"]:
        print("Update increases precision by {} %".format(round(evaluation[folders[1]]["precision"] - evaluation[folders[0]]["precision"],2)))
    else:
        print("Update decreases precision by {} %".format(round(evaluation[folders[0]]["precision"] - evaluation[folders[1]]["precision"],2)))
    if evaluation[folders[0]]["recall"] < evaluation[folders[1]]["recall"]:
        print("Update increases recall by {} %".format(round(evaluation[folders[1]]["recall"] - evaluation[folders[0]]["recall"],2)))
    else:
        print("Update decreases recall by {} %".format(round(evaluation[folders[0]]["recall"] - evaluation[folders[1]]["recall"]),2))


def endgames_calculateImprovements_TopEmptySquares(directory="evaluation/endgames/updated/"):
    """ Analyses the best amount of marked empty squares based on our endgame ground-truth.

    :param directory: path where evaluation of engines is written
    """

    import re
    folders = list(filter(lambda x: os.path.isdir(os.path.join(directory, x)), os.listdir(directory)))
    if len(folders) == 0:
        engineDir, file = os.path.split(directory)
        engineDir += '/'
        folders.append(file)
    print(folders)
    data = dict()
    evaluation = {f: {} for f in folders}

    with open("{}/groundTruth.json".format("chess_saliency_databases/endgames"), "r") as jsonFile:  # open positional or tactical test solution
        database = json.load(jsonFile)

    for engine in folders:
        evaluation[engine] = dict()
        evaluation[engine]["top"] = dict()
        evaluation[engine]["gT"] = 0
        data[engine] = dict()
        evaluation[engine]["answer"] = dict()  # engine's square data
        emptyGT = dict()
        evaluation[engine]["puzzles"] = 0

        for puzzleDir in list(filter(lambda x: os.path.isdir(os.path.join(directory + engine, x)), os.listdir(directory + engine))):
            path = directory + engine + "/" + puzzleDir + "/data.json"
            with open(path, "r") as jsonFile:
                data = json.load(jsonFile)
            path = directory + engine + "/" + puzzleDir + "/output.txt"
            with open(path, "r") as file:
                output = file.readlines()

            print(engine)
            print(puzzleDir)
            print(data)

            board = chess.Board(data["move1"]["fen"])
            x = []
            if len(database[int(puzzleDir.replace("puzzle",""))-1][puzzleDir]["best move"]) > 1:
                i = 0
                for m in database[int(puzzleDir.replace("puzzle",""))-1][puzzleDir]["best move"]:
                    if str(data["move1"]["move"]) in m:
                        break
                    i += 1
                if i < len(database[int(puzzleDir.replace("puzzle",""))-1][puzzleDir]["best move"]):
                    for gT in database[int(puzzleDir.replace("puzzle", "")) - 1][puzzleDir]["groundTruth"][i]:
                        if board.piece_type_at(chess.SQUARES[chess.parse_square(gT)]) is None:  # empty square
                            x.append(gT)
                else:
                    continue
            else:
                if str(data["move1"]["move"]) in database[int(puzzleDir.replace("puzzle",""))-1][puzzleDir]["best move"]:
                    for gT in database[int(puzzleDir.replace("puzzle",""))-1][puzzleDir]["groundTruth"]:
                        if board.piece_type_at(chess.SQUARES[chess.parse_square(gT)]) is None:  # empty square
                            x.append(gT)
                else:
                    continue
            if len(x) > 0:
                emptyGT[puzzleDir] = x
            evaluation[engine]["puzzles"] += 1

            i = 0
            # parse all available square data below threshold from output file into dictionary
            while i < len(output):
                if output[i].startswith("move1") and len(output[i]) < 15:
                    puzzleNr = puzzleDir
                    evaluation[engine]["answer"][puzzleNr] = dict()
                    board = chess.Board(data["move1"]["fen"])
                elif output[i].startswith("perturbing square = "):
                    sq = output[i].replace("perturbing square = ", "")
                    sq = sq.replace("\n", "")
                elif output[i].startswith("saliency for this square with player's pawn: "):
                    sal1 = re.findall(r'\d+(?:\.\d+)?', output[i])[0]
                    dP1 = re.findall(r'\d+(?:\.\d+)?', output[i])[1]
                    k1 = re.findall(r'\d+(?:\.\d+)?', output[i])[2]
                    if output[i].__contains__("e-"):
                        x = re.search(sal1, output[i]).end()
                        if output[i][x] == "e":
                            x += 2
                            y = ""
                            while output[i][x].isdigit():
                                if int(output[i][x]) == 0:
                                    if len(y) > 0:
                                        y += output[i][x]
                                else:
                                    y += output[i][x]
                                x += 1
                            if len(y) > 0:
                                sal1 = float(sal1) * float(1 / (pow(10, int(y))))
                        x = re.search(dP1, output[i]).end()
                        if output[i][x] == "e":
                            x += 2
                            y = ""
                            while output[i][x].isdigit():
                                if int(output[i][x]) == 0:
                                    if len(y) > 0:
                                        y += output[i][x]
                                else:
                                    y += output[i][x]
                                x += 1
                            if len(y) > 0:
                                dP1 = float(dP1) * float(1 / (pow(10, int(y))))
                        x = re.search(k1, output[i]).end()
                        if output[i][x] == "e":
                            x += 2
                            y = ""
                            while output[i][x].isdigit():
                                if int(output[i][x]) == 0:
                                    if len(y) > 0:
                                        y += output[i][x]
                                else:
                                    y += output[i][x]
                                x += 1
                            if len(y) > 0:
                                k1 = float(k1) * float(1 / (pow(10, int(y))))
                elif output[i].startswith("saliency for this square with opponent's pawn: "):
                    sal2 = re.findall(r'\d+(?:\.\d+)?', output[i])[0]
                    dP2 = re.findall(r'\d+(?:\.\d+)?', output[i])[1]
                    k2 = re.findall(r'\d+(?:\.\d+)?', output[i])[2]
                    if output[i].__contains__("e-"):
                        x = re.search(sal2, output[i]).end()
                        if output[i][x] == "e":
                            x += 2
                            y = ""
                            while output[i][x].isdigit():
                                if int(output[i][x]) == 0:
                                    if len(y) > 0:
                                        y += output[i][x]
                                else:
                                    y += output[i][x]
                                x += 1
                            if len(y) > 0:
                                sal2 = float(sal2) * float(1 / (pow(10, int(y))))
                        x = re.search(dP2, output[i]).end()
                        if output[i][x] == "e":
                            x += 2
                            y = ""
                            while output[i][x].isdigit():
                                if int(output[i][x]) == 0:
                                    if len(y) > 0:
                                        y += output[i][x]
                                else:
                                    y += output[i][x]
                                x += 1
                            if len(y) > 0:
                                dP2 = float(dP2) * float(1 / (pow(10, int(y))))
                        x = re.search(k2, output[i]).end()
                        if output[i][x] == "e":
                            x += 2
                            y = ""
                            while output[i][x].isdigit():
                                if int(output[i][x]) == 0:
                                    if len(y) > 0:
                                        y += output[i][x]
                                else:
                                    y += output[i][x]
                                x += 1
                            if len(y) > 0:
                                k2 = float(k2) * float(1 / (pow(10, int(y))))
                elif output[i].startswith("saliency calculated as max from pawn perturbation for this empty square: ") and board.piece_type_at(chess.SQUARES[chess.parse_square(sq)]) is None:  # empty square
                    evaluation[engine]["answer"][puzzleNr][sq] = dict()
                    evaluation[engine]["answer"][puzzleNr][sq]['saliency'] = float(max([float(sal1), float(sal2)]))
                    evaluation[engine][puzzleNr] = dict()
                    evaluation[engine][puzzleNr]["top"] = dict()
                    evaluation[engine][puzzleNr]["best"] = 0
                    evaluation[engine][puzzleNr]["pr"] = dict()
                    evaluation[engine][puzzleNr]["re"] = dict()
                    evaluation[engine][puzzleNr]["f1"] = dict()
                    evaluation[engine]["squares"] = 0

                i += 1

        for puzzleNr in evaluation[engine]["answer"].keys():
            evaluation[engine][puzzleNr]["top"][0] = 0
            evaluation[engine][puzzleNr]["pr"][0] = 10
            evaluation[engine][puzzleNr]["re"][0] = 0
            evaluation[engine][puzzleNr]["f1"][0] = 0

            if emptyGT[puzzleNr] is not None:
                print(puzzleNr, " ground-truth: ",len(emptyGT[puzzleNr]))
                print(evaluation[engine]["answer"][puzzleNr])
                evaluation[engine]["gT"] += len(emptyGT[puzzleNr])
                sortedKeys = sorted(evaluation[engine]["answer"][puzzleNr], key=lambda x: evaluation[engine]["answer"][puzzleNr][x]["saliency"], reverse=True)
                print(sortedKeys)

                i = 1
                while i < len(sortedKeys):
                    evaluation[engine][puzzleNr]["top"][i] = 0
                    evaluation[engine][puzzleNr]["pr"][i] = 0
                    evaluation[engine][puzzleNr]["re"][i] = 0
                    evaluation[engine][puzzleNr]["f1"][i] = 0
                    for k in sortedKeys[0:i]:
                        if k in emptyGT[puzzleNr]:
                            evaluation[engine][puzzleNr]["top"][i] += 1
                            if i not in evaluation[engine]["top"]:
                                evaluation[engine]["top"][i] = 0
                            evaluation[engine]["top"][i] += 1
                            break
                    if evaluation[engine][puzzleNr]["top"][i] > 0 and i > 0:
                        #print(i,": ", evaluation[engine][t][puzzleNr]["top"][i])
                        evaluation[engine][puzzleNr]["pr"][i] = round(evaluation[engine][puzzleNr]["top"][i]/i * 100, 2)
                        #print("pr: " , evaluation[engine][t][puzzleNr]["pr"][i])
                        evaluation[engine][puzzleNr]["re"][i] = round(evaluation[engine][puzzleNr]["top"][i] / len(emptyGT[puzzleNr]) * 100, 2)
                        #print("re: ",evaluation[engine][t][puzzleNr]["re"][i])
                        evaluation[engine][puzzleNr]["f1"][i] = round(2* evaluation[engine][puzzleNr]["pr"][i] * evaluation[engine][puzzleNr]["re"][i] / (evaluation[engine][puzzleNr]["pr"][i] + evaluation[engine][puzzleNr]["re"][i]), 2)
                        #print(evaluation[engine][t][puzzleNr]["f1"][i])
                        if evaluation[engine][puzzleNr]["f1"][i] > evaluation[engine][puzzleNr]["f1"][evaluation[engine][puzzleNr]["best"]]:
                            evaluation[engine][puzzleNr]["best"] = i
                    i+= 1

    print("-----------------------------------------------------------------------")
    for engine in folders:
        for puzzleNr in evaluation[engine]["answer"].keys():
            i = evaluation[engine][puzzleNr]["best"]
            print("best F1 mean for engine {} on {}: mark first {} empty squares with F1: {} %, precision: {} %, recall: {} % (true positive: {}, false positive: {})".format(
                    engine, puzzleNr, i, evaluation[engine][puzzleNr]["f1"][i],evaluation[engine][puzzleNr]["pr"][i], evaluation[engine][puzzleNr]["re"][i], evaluation[engine][puzzleNr]["top"][i], i - evaluation[engine][puzzleNr]["top"][i]))


    print("-----------------------------------------------------------------------")
    x = 0
    for engine in folders:
        bestpr = 0
        bestre = 0
        bestf1 = 0
        bestSq = 0
        for i in evaluation[engine]["top"]:
            if evaluation[engine]["top"][i] > 0 and i > 0:
                pr = round(evaluation[engine]["top"][i] / ((i*evaluation[engine]["puzzles"])-evaluation[engine]["top"][i]) * 100, 2)
                #print(pr)
                re = round(evaluation[engine]["top"][i] / evaluation[engine]["gT"] * 100, 2)
                #print(re)
                f1 = round(2 * pr * re / (pr + re), 2)
                #print(f1)
                if f1 > bestf1:
                    bestf1 = f1
                    bestpr = pr
                    bestre = re
                    bestSq = i
        x += bestSq
        print("engine {} should mark {} empty squares for maximum F1 score {} % (pr: {} %, re {} %)".format(engine, bestSq, bestf1, bestpr, bestre))
    print("overall around {} empty squares would be best".format(round(x/len(folders))))


def endgames_markEmptySquares(num):
    """ Changes updated endgame directory saliency maps with user specified number of empty squares.

    :param num: number of empty squares
    """

    for engine in list(filter(lambda x: os.path.isdir(os.path.join("evaluation/endgames/updated/", x)), os.listdir("evaluation/endgames/updated/"))):
        evaluation = dict()
        evaluation["answer"] = dict()  # engine's square data
        indices = dict()

        for puzzleDir in list(filter(lambda x: os.path.isdir(os.path.join("evaluation/endgames/updated/" + engine, x)), os.listdir("evaluation/endgames/updated/" + engine))):
            path = "evaluation/endgames/updated/" + engine + "/" + puzzleDir + "/data.json"
            with open(path, "r") as jsonFile:
                data = json.load(jsonFile)
            path = "evaluation/endgames/updated/" + engine + "/" + puzzleDir + "/output.txt"
            with open(path, "r") as file:
                output = file.readlines()

            i = 0
            # parse all available square data below threshold from output file into dictionary
            while i < len(output):
                if output[i].startswith("move1") and len(output[i]) < 15:
                    puzzleNr = puzzleDir
                    beforeP = None
                    evaluation["answer"][puzzleNr] = dict()
                    board = chess.Board(data["move1"]["fen"])
                elif output[i].startswith("perturbing square = "):
                    sq = output[i].replace("perturbing square = ", "")
                    sq = sq.replace("\n", "")
                elif num == 0 and output[i].startswith("square is part of original move and must remain empty"):
                    evaluation["answer"][puzzleNr][sq] = dict()
                    evaluation["answer"][puzzleNr][sq]['saliency'] = 0
                    evaluation[puzzleNr] = dict()
                    evaluation[puzzleNr]["top"] = dict()
                    evaluation[puzzleNr]["best"] = 0
                    evaluation[puzzleNr]["pr"] = dict()
                    evaluation[puzzleNr]["re"] = dict()
                    evaluation[puzzleNr]["f1"] = dict()
                elif output[i].startswith("saliency for this square with player's pawn: "):
                    sal1 = re.findall(r'\d+(?:\.\d+)?', output[i])[0]
                    dP1 = re.findall(r'\d+(?:\.\d+)?', output[i])[1]
                    k1 = re.findall(r'\d+(?:\.\d+)?', output[i])[2]
                    if output[i].__contains__("e-"):
                        x = re.search(sal1, output[i]).end()
                        if output[i][x] == "e":
                            x += 2
                            y = ""
                            while output[i][x].isdigit():
                                if int(output[i][x]) == 0:
                                    if len(y) > 0:
                                        y += output[i][x]
                                else:
                                    y += output[i][x]
                                x += 1
                            if len(y) > 0:
                                sal1 = float(sal1) * float(1 / (pow(10, int(y))))
                        x = re.search(dP1, output[i]).end()
                        if output[i][x] == "e":
                            x += 2
                            y = ""
                            while output[i][x].isdigit():
                                if int(output[i][x]) == 0:
                                    if len(y) > 0:
                                        y += output[i][x]
                                else:
                                    y += output[i][x]
                                x += 1
                            if len(y) > 0:
                                dP1 = float(dP1) * float(1 / (pow(10, int(y))))
                        x = re.search(k1, output[i]).end()
                        if output[i][x] == "e":
                            x += 2
                            y = ""
                            while output[i][x].isdigit():
                                if int(output[i][x]) == 0:
                                    if len(y) > 0:
                                        y += output[i][x]
                                else:
                                    y += output[i][x]
                                x += 1
                            if len(y) > 0:
                                k1 = float(k1) * float(1 / (pow(10, int(y))))
                elif output[i].startswith("saliency for this square with opponent's pawn: "):
                    sal2 = re.findall(r'\d+(?:\.\d+)?', output[i])[0]
                    dP2 = re.findall(r'\d+(?:\.\d+)?', output[i])[1]
                    k2 = re.findall(r'\d+(?:\.\d+)?', output[i])[2]
                    if output[i].__contains__("e-"):
                        x = re.search(sal2, output[i]).end()
                        if output[i][x] == "e":
                            x += 2
                            y = ""
                            while output[i][x].isdigit():
                                if int(output[i][x]) == 0:
                                    if len(y) > 0:
                                        y += output[i][x]
                                else:
                                    y += output[i][x]
                                x += 1
                            if len(y) > 0:
                                sal2 = float(sal2) * float(1 / (pow(10, int(y))))
                        x = re.search(dP2, output[i]).end()
                        if output[i][x] == "e":
                            x += 2
                            y = ""
                            while output[i][x].isdigit():
                                if int(output[i][x]) == 0:
                                    if len(y) > 0:
                                        y += output[i][x]
                                else:
                                    y += output[i][x]
                                x += 1
                            if len(y) > 0:
                                dP2 = float(dP2) * float(1 / (pow(10, int(y))))
                        x = re.search(k2, output[i]).end()
                        if output[i][x] == "e":
                            x += 2
                            y = ""
                            while output[i][x].isdigit():
                                if int(output[i][x]) == 0:
                                    if len(y) > 0:
                                        y += output[i][x]
                                else:
                                    y += output[i][x]
                                x += 1
                            if len(y) > 0:
                                k2 = float(k2) * float(1 / (pow(10, int(y))))
                    i += 1
                    if board.piece_type_at(chess.SQUARES[chess.parse_square(sq)]) is None:
                        evaluation["answer"][puzzleNr][sq] = dict()
                        evaluation["answer"][puzzleNr][sq]['saliency1'] = float(sal1)
                        evaluation["answer"][puzzleNr][sq]['dP1'] = float(dP1)
                        evaluation["answer"][puzzleNr][sq]['K1'] = float(k1)
                        evaluation["answer"][puzzleNr][sq]['saliency2'] = float(sal2)
                        evaluation["answer"][puzzleNr][sq]['dP2'] = float(dP2)
                        evaluation["answer"][puzzleNr][sq]['K2'] = float(k2)
                        evaluation["answer"][puzzleNr][sq]['saliency'] = float(max([float(sal1), float(sal2)]))
                        evaluation[puzzleNr] = dict()
                        evaluation[puzzleNr]["top"] = dict()
                        evaluation[puzzleNr]["best"] = 0
                        evaluation[puzzleNr]["pr"] = dict()
                        evaluation[puzzleNr]["re"] = dict()
                        evaluation[puzzleNr]["f1"] = dict()
                        if output[i].startswith("saliency calculated as max from pawn perturbation for this empty square: ") is False:
                            output.insert(i, "saliency calculated as max from pawn perturbation for this empty square: {}\n".format(
                                evaluation["answer"][puzzleNr][sq]['saliency']))
                            path = "evaluation/endgames/updated/" + engine + "/" + puzzleNr + "/output.txt"
                            with open(path, "w") as f:
                                output = "".join(output)
                                f.write(output)
                            with open(path, "r") as file:
                                output = file.readlines()
                            i += 1
                elif output[i].startswith("Q Values: {") and beforeP is None:
                    beforeP = output[i].replace("Q Values: {", "").split(",")
                    beforePdict = dict()
                    for x in beforeP:
                        key = ""
                        value = ""
                        m = re.search(r"[a-h][1-8][a-h][1-8]", x)
                        if m is not None:
                            index = m.span()
                            key = x[index[0]:index[1]]
                        m = re.findall(r"[-+]?\d*\.\d+|\d+", x)
                        if len(m) > 2:
                            value = m[2]
                        beforePdict[key] = float(value)
                elif output[i].startswith("inserted pawn makes king\'s move illegal\n"):
                    afterP2 = output[i-1].replace("Q Values: {", "").split(",")
                    afterP2dict = dict()
                    for x in afterP2:
                        key = ""
                        value = ""
                        m = re.search(r"[a-h][1-8][a-h][1-8]", x)
                        if m is not None:
                            index = m.span()
                            key = x[index[0]:index[1]]
                        m = re.findall(r"[-+]?\d*\.\d+|\d+", x)
                        if len(m) > 2:
                            value = m[2]
                        afterP2dict[key] = float(value)
                    move = chess.Move(chess.SQUARES[chess.parse_square(data["move1"]['move'][0:2])],
                                      chess.SQUARES[chess.parse_square(data["move1"]['move'][2:4])])
                    if board.piece_type_at(chess.SQUARES[move.from_square]) == chess.KING:  # be careful as opponents pawn can make original move illegal
                        if str(data["move1"]['move']) in afterP2dict:
                            saliency2, dP2, k2, qmax2, gapBefore2, gapAfter2, text = sarfa_saliency.computeSaliencyUsingSarfa(
                                str(data["move1"]["move"]), beforePdict, afterP2dict, None)
                            output.pop(i)
                            output.insert(i, "{}saliency for this square with opponent\'s pawn: \'saliency\': {}, \'dP\': {}, \'K\': {} \n".format(text, saliency2, dP2, k2))
                            with open("evaluation/endgames/updated/" + engine + "/" + puzzleNr + "/output.txt", "w") as f:
                                for line in output:
                                    f.write(line)
                            with open("evaluation/endgames/updated/" + engine + "/" + puzzleNr + "/output.txt", "r") as file:
                                output = file.readlines()

                elif output[i].startswith("considered salient:"):
                    sortedKeys = sorted(evaluation["answer"][puzzleNr], key=lambda x: evaluation["answer"][puzzleNr][x]['saliency'], reverse=True)
                    newtext = ""
                    for squarestring in sortedKeys:
                        if float(evaluation["answer"][puzzleNr][squarestring]['saliency']) > 0:
                            newtext += ("{}: max: {}, colour player: {}, colour opponent: {}\n".format(squarestring, round(float(evaluation["answer"][puzzleNr][squarestring]['saliency']), 10), round(float(
                            evaluation["answer"][puzzleNr][squarestring]['saliency1']), 10), round(float(evaluation["answer"][puzzleNr][squarestring]['saliency2']), 10)))
                    x = i + 1
                    y = i + 1
                    indices[puzzleNr] = x
                    while output[y].startswith("displaying top empty squares:") is False:
                        y += 1
                    with open("evaluation/endgames/updated/" + engine + "/" + puzzleNr + "/output.txt", "r") as f:
                        lines = f.readlines()
                    z = 0
                    while z < y-x:
                        lines.pop(x)
                        z += 1
                    lines.insert(x, newtext)
                    with open("evaluation/endgames/updated/" + engine + "/" + puzzleNr + "/output.txt", "w") as f:
                        for line in lines:
                            f.write(line)
                    with open("evaluation/endgames/updated/" + engine + "/" + puzzleNr + "/output.txt", "r") as file:
                        output = file.readlines()
                i += 1
        #print(evaluation)

        for puzzleNr in evaluation["answer"]:  # iterate puzzles
            path = "evaluation/endgames/updated/" + engine + "/" + puzzleNr + "/data.json"
            with open(path, 'r') as jsonFile:
                data = json.load(jsonFile)

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

            board = chess.Board(data["move1"]["fen"])
            move = chess.Move(answer[data["move1"]['move'][0:2]]['int'], answer[data["move1"]['move'][2:4]]['int'])

            sortedKeys = sorted(evaluation["answer"][puzzleNr], key=lambda x: evaluation["answer"][puzzleNr][x]["saliency"], reverse=True)

            above = data["move1"]["sorted saliencies"]["above threshold"]
            below = data["move1"]["sorted saliencies"]["below threshold"]
            insertAbove = dict()
            insertBelow = dict()

            moveSquares = get_moves_squares(board, move.from_square, move.to_square)

            i = 0
            th = (100 / 256)
            print(sortedKeys)

            aboveKeys = list(above.keys())
            for sq in aboveKeys:
                if (board.piece_type_at(chess.SQUARES[chess.parse_square(sq)]) is None and sq not in moveSquares) or (
                        board.piece_type_at(chess.SQUARES[chess.parse_square(sq)]) is None and num == 0):
                    del above[sq]

            if num > 0:
                for sq in moveSquares:
                    insertAbove[sq] = th

            for sq in sortedKeys:
                if float(evaluation["answer"][puzzleNr][sq]["saliency"]) > 0:
                    if i < num and sq not in moveSquares and board.piece_type_at(chess.SQUARES[chess.parse_square(sq)]) is None:
                        insertAbove[sq] = float(evaluation["answer"][puzzleNr][sq]["saliency"])
                        i += 1
                    else:
                        insertBelow[sq] = 0

            print(above)
            print(insertAbove)

            minSal = 1
            for key in insertAbove:
                if float(insertAbove[key]) < minSal:
                    minSal = float(insertAbove[key])
            if minSal < th:  # increase saliency
                for key in insertAbove:
                    insertAbove[key] = float(insertAbove[key]) + (th - minSal)
                    if insertAbove[key] > 1:
                        insertAbove[key] = 1

            above.update(insertAbove)
            print(above)

            board = chess.Board(data["move1"]['fen'])

            for sq in above:
                if sq in below:
                    del below[sq]
            for sq in below:
                answer[sq]['saliency'] = float(below[sq])
            for sq in above:
                answer[sq]['saliency'] = float(above[sq])

            import chess_saliency_chessSpecific as specific_saliency
            specific_saliency.generate_heatmap(board=board, bestmove=move, evaluation=answer,
                                               directory="evaluation/endgames/updated/" + engine  + "/" + puzzleNr,
                                               puzzle="move1", file=None)
            print("{}, {} updated".format(engine, puzzleNr))

            with open("evaluation/endgames/updated/" + engine + "/" + puzzleNr + "/output.txt", "r") as f:
                lines = f.readlines()
            if puzzleNr in indices:
                x = indices[puzzleNr]
                if x < len(lines):
                    while lines[x].startswith("displaying top empty squares:") is False:
                        x += 1
                        if x >= len(lines):
                            break
                    x += 1
                    if x < len(lines):
                        if len(insertAbove) > 0:
                            lines.pop(x)
                            lines.insert(x, '{}\n'.format(list(insertAbove.keys())))
                            with open("evaluation/endgames/updated/" + engine + "/" + puzzleNr + "/output.txt", "w") as f:
                                for line in lines:
                                    f.write(line)
                    with open("evaluation/endgames/updated/" + engine + "/" + puzzleNr + "/output.txt", "r") as f:
                        lines = f.readlines()
                    if x < len(lines):
                        while lines[x].startswith("Printing positive saliencies in order:") is False:
                            x += 1
                            if x >= len(lines):
                                break
                        x += 1
                        if x < len(lines):
                            y = x
                            while lines[y].startswith("-----------") is False:
                                y += 1
                            z = 0
                            while z < y - x:
                                lines.pop(x)
                                z += 1
                            sortedKeys = sorted(above, key=lambda x: above[x], reverse=False)
                            for key in sortedKeys:
                                lines.insert(x, "{}: {}\n".format(key, above[key]))
                            with open("evaluation/endgames/updated/" + engine + "/" + puzzleNr + "/output.txt", "w") as f:
                                for line in lines:
                                    f.write(line)

            data["move1"] = {
                "fen": data["move1"]['fen'],
                "move": data["move1"]["move"],
                "sorted saliencies": {
                    "above threshold": above,
                    "below threshold": below
                }
            }

            path = "evaluation/endgames/updated/" + engine + "/" + puzzleNr + "/data.json"
            with open(path, "w") as jsonFile:
                json.dump(data, jsonFile, indent=4)


async def rerunEndgames_qValues(directory="evaluation/endgames/updated/"):
    """Rerun all endgame puzzles in the given directory based on existing q_values (output.txt).

    :param directory: path where different engines' outputs are stored
    """

    folders = list(filter(lambda x: os.path.isdir(os.path.join(directory, x)), os.listdir(directory)))
    print(folders)
    if len(folders) == 0:
        directory, file = os.path.split(directory)
        directory += '/'
        folders.append(file)

    with open("chess_saliency_databases\endgames\groundTruth.json", "r") as jsonFile:  # open endgame solutions
        database = json.load(jsonFile)

    for engine in folders: # iterate engines
        print(engine)

        nr = 1

        for puzzle in database: # iterate puzzles
            puzzleNr = "puzzle" + str(nr)
            print(puzzleNr)

            path = "{}/{}/{}/data.json".format(directory, engine, puzzleNr)
            with open(path, "r") as jsonFile:
                data = json.load(jsonFile)

            board = chess.Board(data["move1"]["fen"])

            path = directory + engine + "/" + puzzleNr + "/" + "output.txt"
            with open(path, "r") as file:
                output = file.readlines()

            outputF = open("{}/{}/{}/output.txt".format(directory, engine, puzzleNr), "a")  # append mode
            outputF.truncate(0)

            qValuesEngine = dict()

            i = 0
            while output[i].startswith("move1") is False:
                i += 1

            while i < len(output):
                if output[i].startswith("move1") and len(output[i]) < 15:
                    beforeP = None
                    board = chess.Board(data["move1"]["fen"])
                elif output[i].startswith("move2") and len(output[i]) < 15:
                    break
                elif output[i].startswith("Q Values: {") and beforeP is None:
                    beforeP = output[i].replace("Q Values: {", "").split(",")
                    beforePdict = dict()
                    for x in beforeP:
                        key = ""
                        value = ""
                        import re
                        m = re.search(r"[a-h][1-8][a-h][1-8]", x)
                        if m is not None:
                            index = m.span()
                            key = x[index[0]:index[1]]
                        m = re.findall(r"[-+]?\d*\.\d+|\d+", x)
                        if len(m) > 2:
                            value = m[2]
                        beforePdict[key] = float(value)
                    print(beforePdict)
                elif output[i].startswith("perturbing square = "):
                    sq = output[i].replace("perturbing square = ", "")
                    sq = sq.replace("\n", "")
                    qValuesEngine[sq] = dict()
                elif output[i].startswith("querying engine with perturbed position"):
                    while output[i].startswith("------------------------------------------") is False:
                        if output[i].startswith("Q Values: {"):
                            afterP = output[i].replace("Q Values: {", "").split(",")
                            afterPdict = dict()
                            for x in afterP:
                                key = ""
                                value = ""
                                import re
                                m = re.search(r"[a-h][1-8][a-h][1-8]", x)
                                if m is not None:
                                    index = m.span()
                                    key = x[index[0]:index[1]]
                                m = re.findall(r"[-+]?\d*\.\d+|\d+", x)
                                if len(m) > 2:
                                    value = m[2]
                                afterPdict[key] = float(value)
                            break
                        i += 1
                    qValuesEngine[sq]["regular"] = afterPdict
                elif output[i].startswith("new pawn saliency for this square"):
                    y = i
                    while output[y].startswith("------------------------------------------") is False:
                        if output[y].startswith("Q Values: {"):
                            afterP = output[y].replace("Q Values: {", "").split(",")
                            afterPdict = dict()
                            for x in afterP:
                                key = ""
                                value = ""
                                m = re.search(r"[a-h][1-8][a-h][1-8]", x)
                                if m is not None:
                                    index = m.span()
                                    key = x[index[0]:index[1]]
                                m = re.findall(r"[-+]?\d*\.\d+|\d+", x)
                                if len(m) > 2:
                                    value = m[2]
                                afterPdict[key] = float(value)
                            break
                        y -= 1
                        qValuesEngine[sq]["pawn"] = afterPdict
                elif output[i].startswith("square is empty, so put a pawn from player's color here"):
                    afterP1 = None
                    afterP2 = None
                    while output[i].startswith("------------------------------------------") is False:
                        if output[i].startswith("Q Values: {") and afterP1 is None:
                            afterP1 = output[i].replace("Q Values: {", "").split(",")
                            afterP1dict = dict()
                            for x in afterP1:
                                key = ""
                                value = ""
                                m = re.search(r"[a-h][1-8][a-h][1-8]", x)
                                if m is not None:
                                    index = m.span()
                                    key = x[index[0]:index[1]]
                                m = re.findall(r"[-+]?\d*\.\d+|\d+", x)
                                if len(m) > 2:
                                    value = m[2]
                                afterP1dict[key] = float(value)
                        elif output[i].startswith("Q Values: {") and afterP2 is None:
                            afterP2 = output[i].replace("Q Values: {", "").split(",")
                            afterP2dict = dict()
                            for x in afterP2:
                                key = ""
                                value = ""
                                m = re.search(r"[a-h][1-8][a-h][1-8]", x)
                                if m is not None:
                                    index = m.span()
                                    key = x[index[0]:index[1]]
                                m = re.findall(r"[-+]?\d*\.\d+|\d+", x)
                                if len(m) > 2:
                                    value = m[2]
                                afterP2dict[key] = float(value)
                            break
                        i += 1
                    qValuesEngine[sq] = {
                        "player" : afterP1dict,
                        "opponent" : afterP2dict
                    }
                i += 1
            print("starting SARFA")
            original_move = data["move1"]["move"]
            ss = original_move[0:2]
            ds = original_move[2:4]
            move = chess.Move(chess.SQUARES[chess.parse_square(ss)], chess.SQUARES[chess.parse_square(ds)])
            outputF.write("move1\n")
            aboveThreshold, belowThreshold = await givenQValues_computeSaliency(board, move, data["move1"]["fen"], beforePdict, qValuesEngine, directory + engine + "/" + puzzleNr, "move1", outputF)

            path = directory + engine + "/" + puzzleNr + "/" + "data.json"

            data["move1"]["sorted saliencies"]["above threshold"] = aboveThreshold
            data["move1"]["sorted saliencies"]["below threshold"] = belowThreshold

            with open(path, "w") as jsonFile:
                json.dump(data, jsonFile, indent=4)
            nr += 1
