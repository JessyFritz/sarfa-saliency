import asyncio
import json
import os
import re
import chess
import chess.pgn
import chess_saliency_original as original_saliency

datasetBestMoves = ["c3d5","f5h6","g3g8","b6d5","c4f4","d5e7","c3d5","f3h5","d5d6","e4c4","f6h8","h3h7","b2g7","a1a2","b1f5","g5g6","f5f8","f6e8","d6e7","d4d7","e4h7","g1g6","f3e5","e2e7","b6g6","e1e6","c1c6","e5d6","c1g5","c6b7","g1g7","f5e6","g4f6","b7b8","d1d7","d3h7","g3g7","e1c1","d2h6","b2a1","b6c7","d1e1","d1d7","d2d4","e4f6","h5h6","d4e4","e4e6","h5h6","e7e5","f1f5","a1b2","h4e4","d6f5","c1h6","f3g5","b3c4","e5e6","g4g6","f3d5","d7e7","h4h5","d3d4","d1d5","f4e6","e2d4","f1f8","h5h6","f4f7","g5g6","g1g6","e3g4","c7e7","c3b5","d5g8","h6h7","d2c2","c4e6","f1f7","a7a8","e5g6","f1f2","b3f7","b3d1","d6d7","d5f6","f3f8","b1g6","d5f7","e1e6","e4e5","d1d7","b3d4","h3h4","d3h7","f7g7","e5g7","d6f8","g7g6","c4c5","c6c8","b7b4"]


def runDatabase(path, engineLocation="engines/stockfish-11-win/stockfish-11-win/Windows/stockfish_20011801_32bit.exe", saliency=None):
    """ Runs a given json database with a given engine against a given saliency implementation.

    :param path: path from content root which contains json file with puzzles in FEN notation
    :param engineLocation: engine's executable file
    :param saliency: None or chess_saliency implementation
    :return:
    """

    if saliency is None:
        saliency = original_saliency

    with open("{}/data.json".format(path), "r") as jsonFile:
        data = json.load(jsonFile)

    file = open("{}/output.txt".format(path), "a")
    file.truncate(0)

    for puzzleNr in data: # run all puzzles from database
        print(puzzleNr)
        file.write("{}\n".format(puzzleNr))
        puzzle = data[puzzleNr]
        print(puzzle)
        FEN = puzzle['fen']

        asyncio.set_event_loop_policy(chess.engine.EventLoopPolicy())
        _, aboveThreshold, belowThreshold, original_move, _, _ =  asyncio.run(saliency.computeSaliency(engineLocation, FEN, path, puzzleNr, file=file))
        puzzle['best move'] = str(original_move)
        puzzle['sorted saliencies'] = {"above threshold": aboveThreshold,"below threshold": belowThreshold}
        with open("{}/data.json".format(path), "w") as jsonFile:
            json.dump(data, jsonFile, indent=4)


def newGameDatabase(fen='rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1', moveNr='move1', directory="evaluation/games/original/stockfish", engineLocation="engines/stockfish-11-win/stockfish-11-win/Windows/stockfish_20011801_32bit.exe", saliency=None):
    """ Plays a whole game by itself starting from a given fen notation.

    :param fen: starting position in Forsyth–Edwards Notation
    :param moveNr: name of inital puzzle
    :param directory: path from content root to which the output will be written
    :param engineLocation: engine's executable file
    :param saliency: None or chess_saliency implementation
    """

    if saliency is None:
        saliency = original_saliency

    fileName = fen.replace("/",".")
    if directory.__contains__("dataset/games"):
        directory = directory+'/'+str(fileName)
    if not os.path.exists(directory):
        os.makedirs(directory)
        print("created directory")
    path = "{}/data.json".format(directory)
    with open(path, 'w+') as jsonFile:
        jsonFile.write('{}')
    y = {moveNr: {
        "fen": fen,
        "move": "",
        "sorted saliencies": {}
    }}
    with open(path, "r+") as jsonFile:
        data = json.load(jsonFile)
        data.update(y)
        jsonFile.seek(0)
        json.dump(data, jsonFile, indent=4)

    outputF = open("{}/output.txt".format(directory), "a")
    outputF.truncate(0)

    while True: # play until game-over
        print(moveNr)
        outputF.write("{}\n".format(moveNr))
        with open(path, "r")  as jsonFile:
            data = json.load(jsonFile)

        puzzle = data[moveNr]
        FEN = puzzle['fen']
        board = chess.Board(FEN)
        directory, file = os.path.split(path)

        asyncio.set_event_loop_policy(chess.engine.EventLoopPolicy())
        _, aboveThreshold, belowThreshold, original_move, _, _ = asyncio.run(saliency.computeSaliency(engineLocation, chess.Board.fen(board), directory, moveNr, file=outputF))
        puzzle['move'] = str(original_move)
        puzzle['sorted saliencies'] = {
            "above threshold": aboveThreshold,
            "below threshold": belowThreshold
        }
        board.push(chess.Move.from_uci(str(original_move)))

        with open(path, "w") as jsonFile:
            json.dump(data, jsonFile, indent=4)

        file = moveNr.rstrip('0123456789')
        index = moveNr.replace(file, '')
        index = int(index) + 1
        moveNr = file + str(index)

        if board.is_game_over():
            break
        elif len(data) < index:
            y = {moveNr: {
                "fen": board.fen(),
                "move": "",
                "sorted saliencies": {}
            }}

            with open(path, "r+") as jsonFile:
                data = json.load(jsonFile)
                data.update(y)
                jsonFile.seek(0)
                json.dump(data, jsonFile, indent=4)
        else:
            puzzle = data[moveNr]
            puzzle['fen'] = board.fen()
            with open(path, "w") as jsonFile:
                json.dump(data, jsonFile, indent=4)


def runSarfaDataset(directory, engineLocation, saliency=None):
    """ Runs the SARFA database puzzles with a given engine and evaluates missing squares from ground truth.

    :param directory: path to which the evaluation will be written
    :param engineLocation: engine's executable file
    :param saliency: None or chess_saliency implementation
    """

    if saliency is None:
        saliency = original_saliency

    if not os.path.exists(directory):
        os.makedirs(directory)
        print("created directory")
    path = "{}/data.json".format(directory)
    with open(path, 'w+') as jsonFile:
        jsonFile.write('{}')

    file = open("{}/output.txt".format(directory), "a")  # append mode
    file.truncate(0)

    with open('chess_saliency_databases/chess-saliency-dataset-v1.json', "r") as jsonFile:
        data = json.load(jsonFile)
    data = data['puzzles']

    nr = 1
    for puzzle in data: # run all puzzles from database
        puzzleNr = "puzzle" + str(nr)
        print(puzzleNr)
        file.write("{}\n".format(puzzleNr))
        board = chess.Board(puzzle['fen'])
        asyncio.set_event_loop_policy(chess.engine.EventLoopPolicy())
        evaluation, aboveThreshold, belowThreshold, original_move, _, _ = asyncio.run(saliency.computeSaliency(engineLocation, chess.Board.fen(board), directory, puzzleNr, datasetBestMoves[nr - 1], file))

        missing = []
        for square in puzzle['saliencyGroundTruth']:
            if square not in aboveThreshold:
                missing.append(square)
        details = dict()
        if len(missing) == 0:
            file.write("puzzle marked all squares from ground truth as salient\n")
            file.write('------------===============------------===============\n\n')
            missing = 0
        else:
           for square in missing:
               details[square] = evaluation[square]

        y = {puzzleNr: {
           "fen": puzzle['fen'],
           "best move": str(original_move),
           "sorted saliencies": {
               "above threshold": aboveThreshold,
               "below threshold": belowThreshold
           },
           "saliency ground truth": puzzle['saliencyGroundTruth'],
           "missing ground truth": {
               "squares": missing,
               "details": details
           }
        }}

        with open(path, "r+") as jsonFile:
            data = json.load(jsonFile)
            data.update(y)
            jsonFile.seek(0)
            json.dump(data, jsonFile, indent=4)
        nr += 1
    file.close()


def evaluateFeature(directory="evaluation/updated/leela", feature="different best move", variable=None, criteria=None, symbol=">"):
    """ Evaluates a given feature inside a given directory with optional improvement proposals.

    :param directory: path where engine's evaluation is written
    :param feature: feature to evaluate
    :param variable: aspect to check, f.e. "dP" or "K"
    :param criteria: value of variable, f.e. 0.5
    :param symbol: greater or smaller, f.e. ">"
    """

    if not os.path.exists(directory):
        raise IOError ('directory does not exist: %s' %directory)
    dataPath = "{}/data.json".format(directory)
    Outputpath = "{}/output.txt".format(directory)
    if not os.path.exists(dataPath):
        raise IOError('file does not exist: %s' % dataPath)
    if not os.path.exists(Outputpath):
        raise IOError ('file does not exist: %s' %Outputpath)

    featureOcc = 0
    salientOcc = 0
    with open(Outputpath, "r") as file:
        output = file.readlines()
    with open(dataPath, "r") as jsonFile:
        data = json.load(jsonFile)
    positive = 0
    negative = 0
    nr = 1
    sq = None
    sqData = None
    salSquares = dict()
    falseSalSquares = dict()
    newMissed = dict()
    falseMarked = dict()
    idx = 0
    while idx < len(output):
        line = output[idx]
        if line.startswith("puzzle"):
            nr = line.replace("\n","")
        elif output[idx].startswith("assigned new best move to engine"):
            while output[idx].startswith("saliency for this square = ") is False:
                idx += 1
        elif line.startswith("perturbing square = "):
            sq = line.replace("perturbing square = ", "")[0:2]
            sqData = sq
        elif line.startswith("perturbed reward Q"):
            reward = line.split(", ")[0].split(":")[1]
        elif line.__contains__("saliency for this square"):
            sqData = {sq: line}
        elif line.__contains__(feature):
            featureOcc += 1
            if line.__contains__("="):
                i = 0
                while i < len(line):
                    if line[i].isdigit() and line[i-1] != " " and line[i-1] != "." and line[i-1].isdigit() is False:
                        sq = line[i-1:i+1]
                        break
                    i += 1
            if sq is None or sq == sqData:
                j = idx
                sqs = re.search(r"[a-h][1-8]", line)
                if sqs is not None:
                    square = sqs.group(0)
                    while output[j].__contains__("perturbing square = {}".format(square)) is False:
                        j -= 1
                    sq = square
                while output[j].__contains__("saliency for this square") is False:
                    j += 1
                sqData = {sq: output[j]}

            variables = str(sqData).split(',')
            for x in variables:
                if x.__contains__("\'{}\': ".format(variable)):
                     value = x.replace("\'{}\': ".format(variable), "")

            if variable is not None and "reward" in variable:
                value = reward

            i = 0
            while i < len(data[nr]["saliency ground truth"]):
                if str(data[nr]["saliency ground truth"][i]) == str(sq):
                    salientOcc += 1
                    if nr in salSquares:
                        temp = set(salSquares[nr])
                        temp.add(sq)
                        salSquares[nr] = temp
                    else:
                        salSquares[nr] = {sq}
                    if variable is not None:
                        if symbol == "<":
                            if float(value) < criteria:
                                positive += 1
                            else:
                                if nr in newMissed:
                                    temp = set(newMissed[nr])
                                    temp.add(sq)
                                    newMissed[nr] = temp
                                else:
                                    newMissed[nr] = {sq}
                        elif symbol == ">":
                            if float(value) > criteria:
                                positive += 1
                            else:
                                if nr in newMissed:
                                    temp = set(newMissed[nr])
                                    temp.add(sq)
                                    newMissed[nr] = temp
                                else:
                                    newMissed[nr] = {sq}
                        break
                i += 1
                if (nr in salSquares and sq not in salSquares[nr]) or nr not in salSquares:
                    if i == len(data[nr]["saliency ground truth"]):
                        if nr in falseSalSquares:
                            temp = set(falseSalSquares[nr])
                            temp.add(sq)
                            falseSalSquares[nr] = temp
                        else:
                            falseSalSquares[nr] = {sq}
                        if variable is not None:
                            if symbol == "<":
                                if float(value) < criteria:
                                    negative += 1
                                else:
                                    if nr in falseMarked:
                                        temp = set(falseMarked[nr])
                                        temp.add(sq)
                                        falseMarked[nr] = temp
                                    else:
                                        falseMarked[nr] = {sq}
                            elif symbol == ">":
                                if float(value) > criteria:
                                    negative += 1
                                else:
                                    if nr in falseMarked:
                                        temp = set(falseMarked[nr])
                                        temp.add(sq)
                                        falseMarked[nr] = temp
                                    else:
                                        falseMarked[nr] = {sq}
                            break
            sq = None
            sqData = None
        idx += 1
    print("\n{} out of {} occurences of feature \"{}\" are actually salient".format(salientOcc, featureOcc, feature))
    if featureOcc > 0:
        print("precision of feature \"{}\" is {} %".format(feature,round(100/featureOcc*salientOcc,2)))
    if variable is not None:
        print("applied {} {} {} to this feature".format(variable,symbol,criteria))
        print("  true salient: {} out of {}".format(positive, salientOcc))
        print("  false salient: {} out of {}".format(negative, featureOcc-salientOcc))
        if (positive+negative) > 0:
            print("  new precision would be {} %".format(round(100/(positive+negative)*positive,2)))
            print("  recall decreases to {} %".format(round(100/salientOcc * positive, 2)))
            print("  new missed salient squares: ")
            print("  ",newMissed)
            print("  remaining wrongly marked squares: ")
            print("  ",falseMarked)
    elif featureOcc > 0:
        print("  salient squares: ")
        print("  ", salSquares)
        print("  wrongly marked squares: ")
        print("  ", falseSalSquares)


def getMean(directory="evaluation/original/", variable="perturbed reward", subset=None):
    """ Calculates mean variable over a given directory. Optional only over a given subset.

    :param directory: path where different engines' outputs are stored
    :param variable: calculate average over this
    :param subset: average only over given subset
    """

    folders = list(filter(lambda x: os.path.isdir(os.path.join(directory, x)), os.listdir(directory)))
    if len(folders) == 0:
        directory, file = os.path.split(directory)
        directory += '/'
        folders.append(file)

    mean = 0
    for engine in folders:
        path = directory+engine+"/"+"output.txt"
        with open(path, "r") as file:
            output = file.readlines()

        value = 0
        count = 0
        for line in output:
            if line.startswith("puzzle"):
                puzzleNr = line.replace("\n","")
            if subset is None or (subset is not None and puzzleNr in subset):
                if variable in line and "perturbed" in variable:
                    value += float(line.split(", ")[0].split(":")[1])
                    count += 1
                elif variable in line and "original" in variable:
                    value += float(line.split(", ")[1].split(":")[1])
                    count += 1
                elif line.__contains__("saliency for this square"):
                    evals = line.split(",")
                    i = 1
                    while i < len(evals):
                        l = evals[i]
                        if variable in l:
                            value += float(l.replace("\'{}\': ".format(variable), " "))
                            count += 1
                            break
                        i += 1

        mean += value/count
        print("{} mean for {}:{} {}".format(variable, engine, " "*(11-len(engine)), round(value/count,2)))
    print("Total mean is {}".format(round(mean/len(folders),2)))


def getMinMax(directory="evaluation/original/", variable="reward Q(s',â)", mode="max"):
    """ Searches for minimum or maximum variable inside a given directory.

    :param directory: path where different engines' outputs are stored
    :param variable: search min or max from this
    :param mode: min or max
    """

    folders = list(filter(lambda x: os.path.isdir(os.path.join(directory, x)), os.listdir(directory)))
    print(folders)
    if len(folders) == 0:
        directory, file = os.path.split(directory)
        directory += '/'
        folders.append(file)

    for engine in folders:
        path = directory+engine+"/"+"output.txt"
        with open(path, "r") as file:
            output = file.readlines()

        minMax = 0
        if "min" == mode:
            minMax = 1000
        for line in output:
            if variable in line and "reward" in variable:
                if '\'' in variable: #perturbed
                    value = float(line.split(", ")[0].split(":")[1])
                else: #original
                    value = float(line.split(", ")[1].split(":")[1])
                if "max" == mode and value > minMax:
                    minMax = value
                elif "min" == mode and value < minMax:
                    minMax = value
            elif line.__contains__("saliency for this square"):
                evals = line.split(",")
                i = 1
                while i < len(evals):
                    l = evals[i]
                    if variable in l:
                        value = float(l.replace("\'{}\': ".format(variable), " "))
                        if "max" == mode and value > minMax:
                            minMax = value
                        elif "min" == mode and value < minMax:
                            minMax = value
                        break
                    i += 1
        print("{} {} for engine {}:{} {}".format(variable, mode, engine," "*(11-len(engine)),round(minMax,2)))


def getQValues(directory="evaluation/original/", puzzle="puzzle1"):
    """ Prints overview of different engines' q-values for a given puzzle number.

    :param directory: path where different engines' outputs are stored
    :param puzzle: puzzle to analyse q-values from
    """

    folders = list(filter(lambda x: os.path.isdir(os.path.join(directory, x)), os.listdir(directory)))
    print(folders)
    if len(folders) == 0:
        directory, file = os.path.split(directory)
        directory += '/'
        folders.append(file)

    for engine in folders:
        path = directory+engine+"/"+"output.txt"
        with open(path, "r") as file:
            output = file.readlines()

        min = 100
        max = -100
        avg = 0
        i = 0
        while i < len(output):
            if puzzle in output[i]:
                while output[i].startswith("Q Values: {") is False:
                    if output[i].startswith("Total Legal Moves : "):
                        moves = float(output[i].replace("Total Legal Moves : ", ""))
                    i += 1
                values = output[i].replace("Q Values: {", "")
                values = values.split(",")
                for val in values:
                    num = str(val.split()[1])
                    if num[len(num)-1] == '}':
                        num = num[0:len(num)-1]
                    num = float(num)
                    avg += num
                    if num > max:
                        max = num
                    elif num < min:
                        min = num
                avg = avg/moves
                break
            i += 1
        print("q_values from {} for engine {}:{} average: {}, max: {}, min: {}".format(puzzle, engine," "*(11-len(engine)), round(avg,2), max, min))


def runPGNFolder(directory="chess_saliency_databases/positional", destination="evaluation/chess/positional/original/stockfish", engineLocation="engines/stockfish-11-win/stockfish-11-win/Windows/stockfish_20011801_32bit.exe", saliency=None):
    """ Runs a pgn database folder with a given engine.

    :param directory: path from content root which contains pgn files
    :param destination: path from content root where output should be written
    :param engineLocation: engine's executable file
    :param saliency: None or chess_saliency implementation
    """

    if saliency is None:
        saliency = original_saliency

    if not os.path.exists(destination):
        os.makedirs(destination)
        print("created directory")
    path = "{}/data.json".format(destination)
    with open(path, 'w+') as jsonFile:
        jsonFile.write('{}')

    file = open("{}/output.txt".format(destination), "a")  # append mode
    file.truncate(0)

    for pgnGame in os.listdir(directory):
        print(pgnGame)
        board = chess.pgn.read_game(open(os.path.join(directory, pgnGame),errors='ignore')).board()
        file.write("{}\n".format(pgnGame.replace(".pgn","")))
        fen = str(board.fen).split("'")[1]
        print(fen)

        asyncio.set_event_loop_policy(chess.engine.EventLoopPolicy())
        _, aboveThreshold, belowThreshold, original_move, _, _ = asyncio.run(saliency.computeSaliency(engineLocation, chess.Board.fen(board), destination, pgnGame.replace(".pgn",""), file=file))

        y = {pgnGame.replace(".pgn",""): {
            "fen": fen,
            "best move": str(original_move),
            "sorted saliencies": {
                "above threshold": aboveThreshold,
                "below threshold": belowThreshold
            }
        }}
        with open(path, "r+") as jsonFile:
            data = json.load(jsonFile)
            data.update(y)
            jsonFile.seek(0)
            json.dump(data, jsonFile, indent=4)
    file.close()


def runPGNGame(directory="chess_saliency_databases/positional", destination="evaluation/chess/positional/updated/stockfish", pgnGame=None, engineLocation="engines/stockfish-11-win/stockfish-11-win/Windows/stockfish_20011801_32bit.exe", saliency=None):
    """ Runs a single pgn game according to a given directory.

    :param directory: path from content root which contains pgn files
    :param destination: path from content root where output should be written
    :param pgnGame: name of pgn file
    :param engineLocation: engine's executable file
    :param saliency: None or chess_saliency implementation
    """

    if saliency is None:
        saliency = original_saliency

    if not os.path.exists(destination):
        os.makedirs(destination)
        print("created directory")
    path = "{}/data.json".format(destination)
    with open(path, 'w+') as jsonFile:
        jsonFile.write('{}')

    print(pgnGame)
    board = chess.pgn.read_game(open(os.path.join(directory, pgnGame), errors='ignore')).board()
    fen = str(board.fen).split("'")[1]
    print(fen)

    asyncio.set_event_loop_policy(chess.engine.EventLoopPolicy())
    _, aboveThreshold, belowThreshold, original_move, _, _ = asyncio.run(saliency.computeSaliency(engineLocation, chess.Board.fen(board), destination, pgnGame.replace(".pgn", "")))

    y = {pgnGame.replace(".pgn", ""): {
        "fen": fen,
        "best move": str(original_move),
        "sorted saliencies": {
            "above threshold": aboveThreshold,
            "below threshold": belowThreshold
        }
    }}
    with open(path, "r+") as jsonFile:
        data = json.load(jsonFile)
        data.update(y)
        jsonFile.seek(0)
        json.dump(data, jsonFile, indent=4)


def runPGNMultipleFiles(directory="chess_saliency_databases/endgames/endgames.pgn", destination="evaluation/endgames/original/stockfish", engineLocation="engines/stockfish-11-win/stockfish-11-win/Windows/stockfish_20011801_32bit.exe", saliency=None):
    """ Runs a pgn file with multiple games

    :param directory: path from content root which contains pgn file
    :param destination: path from content root where output should be written
    :param engineLocation:  engine's executable file
    :param saliency: None or chess_saliency implementation
    """

    if saliency is None:
        saliency = original_saliency

    if not os.path.exists(destination):
        os.makedirs(destination)
        print("created directory")
    path = "{}/data.json".format(destination)
    with open(path, 'w+') as jsonFile:
        jsonFile.write('{}')

    png_folder = open(directory)
    nr = 1
    pgnGame = chess.pgn.read_game(png_folder)
    while pgnGame is not None:
        print(pgnGame)
        board = pgnGame.board()
        fen = str(board.fen).split("'")[1]
        print(fen)
        newGameDatabase(fen, directory="{}/{}".format(destination,"puzzle" + str(nr)),engineLocation=engineLocation, saliency=saliency)
        nr += 1
        pgnGame = chess.pgn.read_game(png_folder)


def runBratkoKopec(destination, engineLocation, saliency=None):
    """ Runs the bratko-kopec test with a given engine.

    :param destination: path to which the evaluation will be written
    :param engineLocation: engine's executable file
    :param saliency: None or chess_saliency implementation
    """

    if not os.path.exists(destination):
        os.makedirs(destination)
        print("created directory")

    if saliency is None:
        saliency = original_saliency

    directory = "chess_saliency_databases/bratko-kopec"
    folders = list(filter(lambda x: os.path.isdir(os.path.join(directory, x)), os.listdir(directory)))
    if len(folders) == 0:
        directory, f = os.path.split(directory)
        folders = [f]

    for f in folders:
        if not os.path.exists("{}/{}".format(destination, f)):
            os.makedirs("{}/{}".format(destination, f))
            print("created directory")

        print(f)
        path = "{}/{}/data.json".format(destination,f)
        with open(path, 'w+') as jsonFile:
            jsonFile.write('{}')

        file = open("{}/{}/output.txt".format(destination,f), "a")  # append mode
        file.truncate(0)

        with open("{}/{}/bratko-kopec.json".format(directory,f), "r") as jsonFile:
            data = json.load(jsonFile)

        nr = 1
        for puzzle in data:
            puzzleNr = "puzzle" + str(nr)
            print(puzzleNr)
            file.write("{}\n".format(puzzleNr))
            board = chess.Board(puzzle['fen'])

            asyncio.set_event_loop_policy(chess.engine.EventLoopPolicy())
            _, aboveThreshold, belowThreshold, original_move, _, _ = asyncio.run(saliency.computeSaliency(engineLocation, chess.Board.fen(board), "{}/{}".format(destination,f), puzzleNr, file=file))

            y = {puzzleNr: {
                "fen": puzzle['fen'],
                "move": str(original_move),
                "sorted saliencies": {
                    "above threshold": aboveThreshold,
                    "below threshold": belowThreshold
                }
            }}

            with open(path, "r+") as jsonFile:
                data = json.load(jsonFile)
                data.update(y)
                jsonFile.seek(0)
                json.dump(data, jsonFile, indent=4)
            nr += 1
        file.close()


def run_engine(function, engineLocation, engineName, saliency=None):
    """ Runs a function with a given engine.

    :param function: method to use ("SARFA", "bratko", "endgame", "general", "positional")
    :param engineLocation: engine's executable file
    :param engineName: name of the engine
    :param saliency: None or chess_saliency implementation
    """

    folder = "updated"
    if saliency is None:
        saliency = original_saliency
        folder = "original"
    elif saliency.__name__.__contains__("leela"):
        folder = "leela"

    if str(function).__contains__("SARFA"):
        runSarfaDataset(directory="evaluation/{}/{}".format(folder,engineName), engineLocation=engineLocation, saliency=saliency)
    elif str(function).__contains__("bratko"):
        runBratkoKopec(destination="evaluation/bratko-kopec/{}/{}".format(folder,engineName), engineLocation=engineLocation, saliency=saliency)
    elif str(function).__contains__("endgame"):
        runPGNMultipleFiles(destination="evaluation/endgames/{}/{}".format(folder,engineName),engineLocation=engineLocation, saliency=saliency)
    elif str(function).__contains__("general"):
        runDatabase(path="evaluation/chess/general/{}/{}".format(folder,engineName), engineLocation=engineLocation,saliency=saliency)
    elif str(function).__contains__("positional"):
        runPGNFolder(destination="evaluation/chess/positional/{}/{}".format(folder,engineName),engineLocation=engineLocation, saliency=saliency)


def runAll_engines(function, saliency=None):
    """ Runs a function with all engines.

    :param function: method to use ("SARFA", "bratko", "endgame", "general", "positional")
    :param saliency: None or chess_saliency implementation
    """

    run_engine(function, 'engines/stockfish_12_win_x64_bmi2/stockfish_20090216_x64_bmi2.exe', "stockfish12", saliency)
    run_engine(function, 'engines/lc0-v0.26.3-windows-gpu-nvidia-cudnn/lc0.exe', "leela", saliency)
    run_engine(function, 'engines/stockfish-11-win/stockfish-11-win/Windows/stockfish_20011801_32bit.exe', "stockfish", saliency)
    run_engine(function, 'engines/octochess-r5190/octochess-windows-sse4-r5190.exe', "octochess", saliency)
    run_engine(function, 'engines/komodo/Windows/komodo-12.1.1-64bit.exe', "komodo", saliency)
    run_engine(function, 'engines/SlowChessClassic-2.4/slow64.exe', "slowchess", saliency)
    run_engine(function, 'engines/rybka/Rybkav2.3.2a.mp.x64.exe', "rybka", saliency)
    run_engine(function, 'engines/fruit/Fruit2.2.1.exe', "fruit", saliency)
