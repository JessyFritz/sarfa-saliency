import json
import os


def evaluate(directory="evaluation/endgames/original/"):
    """
    evaluate the endgame puzzles per engine
    Input :
        directory : path where different engines' outputs are stored
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

    for engine in folders: # iterate engines
        print(engine)
        evaluation[engine]["salient"] = 0                # number of salient marked squares for puzzles where engine executed solution move
        evaluation[engine]["missing"] = 0                # number of missing salient (false negative) squares for puzzles where engine executed solution move
        evaluation[engine]["precision"] = 0              # precision over puzzles where engine executed solution move
        evaluation[engine]["recall"] = 0                 # recall over puzzles where engine executed solution move
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

            path = "{}/{}/{}/data.json".format(directory, engine, puzzleNr)
            with open(path, "r") as jsonFile:
                data[engine] = json.load(jsonFile)

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
                        evaluation[engine]["salient"] += sal
                        gT = puzzle["groundTruth"]
                        if len(puzzle["best move"]) > 1:
                            gT = puzzle["groundTruth"][j]
                        for sq in gT:
                            i = 0
                            for key in data[engine]["move1"]["sorted saliencies"]["above threshold"]:
                                if sq == key:
                                    break
                                i += 1
                                if i == len(data[engine]["move1"]["sorted saliencies"]["above threshold"]):
                                    miss += 1  # puzzle's missing ground truth
                        evaluation[engine]["missing"] += miss
                        pr = 0
                        re = 0
                        if sal > 0:
                            pr = (len(gT) - miss) / sal * 100       # puzzle's precision
                            re = (len(gT) - miss) / len(gT) * 100   # puzzle's recall
                            print("    {}: salient: {}, missing: {}, precision: {}, recall: {}".format(engine, sal, miss, round(pr, 2), round(re, 2)))
                        evaluation[engine]["precision"] += pr
                        evaluation[engine]["recall"] += re
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
                    break

            result = " "

            if "1/2-1/2" in result: # count result occurrences
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
                print("    result as expected: {}".format(result)) # result equals Larsson's expected possible outcome
            elif "available result" in puzzle:
                print("    according to Larsson {} is also possible".format(puzzle["available result"]))
                if result in puzzle["available result"]:
                    evaluation[engine]["better result"] += 1
                    print("    good result: {}".format(result)) # result equals Larsson's proposed (not expected) possible outcome
                elif ("1-0" in puzzle["expected result"] and result == "0-1" and color == "black") or ("0-1" in puzzle["expected result"] and result == "1-0" and color == "white"):
                    evaluation[engine]["better result"] += 1
                    print("    better result: {}".format(result)) # result is even better than Larsson's proposed (not expected) possible outcome
                else:
                    evaluation[engine]["worse result"] += 1  # result is worse than Larsson's expected result and proposed possible outcome
                    if "note" in puzzle:
                        print("    worst result: {} (\"{}\")".format(result, puzzle["note"]))
                    else:
                        print("    worst result: {}".format(result))
            elif "1/2-1/2" in puzzle["expected result"] and ((result == "0-1" and color == "black") or (result == "1-0" and color == "white")):
                evaluation[engine]["better result"] += 1
                print("    unexpected result {} better than Larsson's expected".format(result))
            elif ("0-1" in puzzle["expected result"] and color == "white") or ("1-0" in puzzle["expected result"] and color == "black"):
                evaluation[engine]["better result"] += 1
                print("    unexpected result {} better than Larsson's expected".format(result))
            elif "1/2-1/2" in puzzle["expected result"] and ((result == "0-1" and color == "white") or (result == "1-0" and color == "black")):
                evaluation[engine]["worse result"] += 1
                print("    unexpected result {} worse than Larsson's expected".format(result))
            elif ("1-0" in puzzle["expected result"] and color == "white") or ("0-1" in puzzle["expected result"] and color == "black"):
                evaluation[engine]["worse result"] += 1
                print("    unexpected result {} worse than Larsson's expected".format(result))

            nr += 1

        evaluation[engine]["precision"] = round(evaluation[engine]["precision"] / (nr-1-evaluation[engine]["wrong move"]-notGiven),2)  # calculate mean of all precision values
        evaluation[engine]["recall"] = round(evaluation[engine]["recall"] / (nr-1-evaluation[engine]["wrong move"]-notGiven), 2)       # calculate mean of all recall values
        print('------------------------------------------')

    print('------------------------------------------')
    print("Evaluation:")
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


def singleEngine_endgames_groundTruthEvaluation(directory1="evaluation/endgames/original/stockfish", directory2="evaluation/endgames/updated/stockfish"):
    """
    evaluates the endgame database's puzzles for a single engine with the original and updated code
    Input :
        directory1 : path where first engine's outputs are stored
        directory2 : path where second engine's outputs are stored
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
