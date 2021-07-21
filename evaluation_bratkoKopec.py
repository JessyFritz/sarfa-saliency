import json
import os
import re
import chess
import numpy

import sarfa_saliency
from basicFunctions import get_moves_squares
from chess_saliency_chessSpecific import givenQValues_computeSaliency


def evaluateBratkoKopec(directory="evaluation/bratko-kopec/original"):
    """Evaluates bratko-kopec test in the given directory based on the ground-truth in the chess_saliency_databases folder and assings the correct score from the test.

    :param directory: path where different engines' outputs are stored
    """

    folders = list(filter(lambda x: os.path.isdir(os.path.join(directory, x)), os.listdir(directory)))
    print(folders)
    if len(folders) == 0:
        directory, file = os.path.split(directory)
        directory += '/'
        folders.append(file)

    outputF = open("{}/output.txt".format(directory), "a")
    outputF.truncate(0)

    jsonDatabaseFolder = "chess_saliency_databases/bratko-kopec"
    jsonFiles = list(filter(lambda x: os.path.isdir(os.path.join(jsonDatabaseFolder, x)), os.listdir(jsonDatabaseFolder)))
    if len(jsonFiles) == 0:
        jsonDatabaseFolder, engine = os.path.split(jsonDatabaseFolder)
        jsonFiles = [engine]

    data = dict()
    evaluation = {f: {} for f in folders}
    highestSal = 0
    highestSalEngine = ""

    for engine in folders: # iterate engines
        print(engine)
        outputF.write("engine: {}\n".format(engine))
        evaluation[engine]["score"] = 0                       # overall engine's score (max 24, calculated as described in http://kopecchess.com/bratko-kopec-test/)
        evaluation[engine]["positional score"] = 0            # engine's score for positional puzzles only (max 12)
        evaluation[engine]["tactical score"] = 0              # engine's score for tatcical puzzles only (max 12)
        evaluation[engine]["salient positional"] = 0          # number of salient marked squares for positional puzzles where engine executed solution move
        evaluation[engine]["salient tactical"] = 0            # number of salient marked squares for tactical puzzles where engine executed solution move
        evaluation[engine]["missing"] = 0                     # number of missing salient (false negative) squares for puzzles where engine executed solution move
        evaluation[engine]["precision"] = 0                   # precision over puzzles where engine executed solution move
        evaluation[engine]["recall"] = 0                      # recall over puzzles where engine executed solution move
        evaluation[engine]["precision positional"] = 0        # precision over positional puzzles where engine executed solution move
        evaluation[engine]["recall positional"] = 0           # recall over positional puzzles where engine executed solution move
        evaluation[engine]["precision tactical"] = 0          # precision over tactical puzzles where engine executed solution move
        evaluation[engine]["recall tactical"] = 0             # recall over tactical puzzles where engine executed solution move
        evaluation[engine]["precision positional piece"] = [] # precision over non-empty squares on positional puzzles where engine executed solution move
        evaluation[engine]["recall positional piece"] = []    # recall over non-empty squares on positional puzzles where engine executed solution move
        evaluation[engine]["precision tactical piece"] = []   # precision over non-empty squares on tactical puzzles where engine executed solution move
        evaluation[engine]["recall tactical piece"] = []      # recall over non-empty squares on tactical puzzles where engine executed solution move
        evaluation[engine]["precision positional empty"] = [] # precision over empty squares on positional puzzles where engine executed solution move
        evaluation[engine]["recall positional empty"] = []    # recall over empty squares on positional puzzles where engine executed solution move
        evaluation[engine]["precision tactical empty"] = []   # precision over empty squares on tactical puzzles where engine executed solution move
        evaluation[engine]["recall tactical empty"] = []      # recall over empty squares on tactical puzzles where engine executed solution move
        evaluation[engine]["wrong move positional"] = 0       # times that engine executed wrong move for positional puzzles
        evaluation[engine]["wrong move tactical"] = 0         # times that engine executed wrong move for tactical puzzles

        for jsonF in jsonFiles: # positional or tactical folder
            print(jsonF)
            outputF.write("{}\n".format(jsonF))
            with open("{}/{}/bratko-kopec.json".format(jsonDatabaseFolder, jsonF), "r") as jsonFile: # open positional or tactical test solution
                database = json.load(jsonFile)

            path = "{}/{}/{}/data.json".format(directory, engine, jsonF) # open engine's evaluation
            with open(path, "r") as jsonFile:
                data[engine] = json.load(jsonFile)

            with open("{}/{}/{}/output.txt".format(directory, engine, jsonF), "r") as file:
                output = file.readlines()

            nr = 1
            for puzzle in database: # iterate puzzles
                puzzleNr = "puzzle" + str(nr)
                board = chess.Board(puzzle["fen"])
                x = 0
                qValues = dict()
                current = None
                while x < len(output): # extract 4 best moves from engine
                    if output[x].startswith(puzzleNr):
                        current = puzzleNr
                    elif output[x].startswith("Q Values: {") and current == puzzleNr:
                        qvals = output[x].replace("Q Values: {", "").split(",")
                        for val in qvals:
                            val = val.replace(" ", "")
                            val = val.replace("}", "").split(":")
                            qValues[val[0]] = float(val[1])
                        break
                    x += 1
                num = 5
                moves = sorted(qValues, key=lambda x: qValues[x], reverse=True)[:num]
                if qValues[moves[len(moves)-3]] != 0:
                    while qValues[moves[len(moves)-4]] == qValues[moves[len(moves)-3]]:
                        num += 1
                        moves = sorted(qValues, key=lambda x: qValues[x], reverse=True)[:num]
                    while qValues[moves[len(moves)-3]] == qValues[moves[len(moves)-2]]:
                        num += 1
                        moves = sorted(qValues, key=lambda x: qValues[x], reverse=True)[:num]

                if qValues[moves[1]] == 0 and qValues[moves[3]] == 0:
                    moves = [moves[0]]
                first = None
                second = None
                third = None
                fourth = None
                j = 0

                if str(data[engine][puzzleNr]["move"]) not in str(moves[0]):
                    x = 1
                    while x < len(moves):
                        if str(data[engine][puzzleNr]["move"]) in moves[x]:
                            del moves[x]
                            break
                        x += 1
                    moves.insert(0, "\'{}\'".format(data[engine][puzzleNr]["move"]))
                while j < len(moves):
                    if first is None:
                        first = qValues[moves[j]]
                    elif second is None:
                        if j > 3:
                            moves = moves[0:j]
                            break
                        second = qValues[moves[j]]
                    elif third is None:
                        if j > 3:
                            moves = moves[0:j]
                            break
                        third = qValues[moves[j]]
                    elif fourth is None:
                        if j > 3:
                            moves = moves[0:j]
                            break
                        fourth = qValues[moves[j]]
                    else:
                        moves = moves[0:len(moves)-1]
                    j += 1

                print("{} - solution move is {}".format(puzzleNr, puzzle["best move"]))
                outputF.write("{} - solution move is {}\n".format(puzzleNr,puzzle["best move"]))
                i = 1
                for m in moves:
                    print("   {}. {}: {}".format(i,m,qValues[m]))
                    outputF.write("   {}: {}\n".format(m,qValues[m]))
                    i += 1
                move = data[engine][puzzleNr]["move"][0:4]
                i = 0
                sc = 0
                sal = 0
                miss = 0
                gTarray = None
                salEmpty = 0
                missEmpty = 0
                gTarrayEmpty = []
                while i < len(puzzle["best move"]):
                    j = 0
                    while j < len(moves):
                        current = moves[j].replace("'", "")
                        if current == str(puzzle["best move"][i]):
                            if j >= 0 and qValues[moves[j]] >= first and str(move) == current: # assign a score of 1/0.5/0.33/0.25 to puzzle
                                sc = 1
                                sal = len(data[engine][puzzleNr]["sorted saliencies"]["above threshold"])
                                if sal > highestSal:
                                    highestSal = sal
                                    highestSalEngine = "{} {}".format(engine, puzzleNr)
                                for m in data[engine][puzzleNr]["sorted saliencies"]["above threshold"]: # analyse all empty squares
                                    if board.piece_type_at(chess.SQUARES[chess.parse_square(m)]) is None:
                                        salEmpty += 1
                                gTarray = puzzle["groundTruth"]
                                if isinstance(puzzle["groundTruth"][0], list):
                                    gTarray = puzzle["groundTruth"][i]
                                for m in gTarray:
                                    if board.piece_type_at(chess.SQUARES[chess.parse_square(m)]) is None:
                                        gTarrayEmpty.append(m)
                                miss = 0
                                for sq in data[engine][puzzleNr]["sorted saliencies"]["above threshold"]:
                                    if sq in gTarray:
                                        miss += 1
                                    if sq in gTarrayEmpty:
                                        missEmpty += 1
                                miss = len(gTarray) - miss
                                missEmpty = len(gTarrayEmpty) - missEmpty
                                evaluation[engine]["salient {}".format(jsonF)] += sal
                                evaluation[engine]["missing"] += miss
                                break
                            elif j >= 1 and qValues[moves[j]] >= second and sc < 0.5:
                                sc = 0.5
                                break
                            elif j >= 2 and qValues[moves[j]] >= third and sc < 0.33:
                                sc = 0.33
                                break
                            elif j == 3 and qValues[moves[j]] >= fourth and sc < 0.25:
                                sc = 0.25
                                break
                        j += 1
                    i += 1
                if sc != 1:
                    evaluation[engine]["wrong move {}".format(jsonF)] += 1
                if sc == 0:
                    print("    {}'s 4 best moves are wrong".format(engine))

                evaluation[engine]["score"] += sc
                evaluation[engine]["{} score".format(jsonF)] += sc
                print("   {}'s score: {}".format(engine, evaluation[engine]["score"]))

                pr = 0
                re = 0
                if gTarray is not None: # calculate precision and recall
                    print("   {} squares should be salient".format(len(gTarray)))
                    if sal > 0:
                        pr = (len(gTarray) - miss) / sal * 100
                        re = (len(gTarray) - miss) / len(gTarray) * 100
                        print("   {}: salient: {}, missing: {}, precision: {} %, recall: {} %".format(engine, sal, miss, round(pr, 2), round(re, 2)))
                    if miss > 0:
                        print("      above threshold: ")
                        for m in data[engine][puzzleNr]["sorted saliencies"]["above threshold"]:
                            if m in gTarray:
                                print("      {}: {}".format(m, data[engine][puzzleNr]["sorted saliencies"]["above threshold"][m]))
                        print("      below threshold: ")
                        for m in data[engine][puzzleNr]["sorted saliencies"]["below threshold"]:
                            if m in gTarray:
                                print("      {}: {}".format(m, data[engine][puzzleNr]["sorted saliencies"]["below threshold"][m]))
                evaluation[engine]["precision"] += pr
                evaluation[engine]["precision {}".format(jsonF)] += pr
                evaluation[engine]["recall"] += re
                evaluation[engine]["recall {}".format(jsonF)] += re
                if gTarray is not None:
                    print("   {} piece squares should be salient".format(len(gTarray)-len(gTarrayEmpty))) # only non empty squares
                    if (sal-salEmpty) > 0:
                        pr = ((len(gTarray)-len(gTarrayEmpty))-(miss-missEmpty)) / (sal-salEmpty) * 100
                        re = ((len(gTarray)-len(gTarrayEmpty))-(miss-missEmpty)) / (len(gTarray)-len(gTarrayEmpty)) * 100
                        print("   {} piece squares: salient: {}, missing: {}, precision: {} %, recall: {} %".format(engine, sal-salEmpty, miss-missEmpty, round( pr, 2), round( re, 2)))
                        evaluation[engine]["precision {} piece".format(jsonF)].append(pr)
                        evaluation[engine]["recall {} piece".format(jsonF)].append(re)
                    if len(gTarrayEmpty) > 0:
                        print("   {} empty squares should be salient".format(len(gTarrayEmpty))) # only empty squares
                        if salEmpty > 0:
                            pr = (len(gTarrayEmpty) - missEmpty) / salEmpty * 100
                            re = (len(gTarrayEmpty) - missEmpty) / len(gTarrayEmpty) * 100
                            print("   {} empty squares: salient: {}, missing: {}, precision: {} %, recall: {} %".format(engine, salEmpty, missEmpty, round(pr, 2), round(re, 2)))
                        else:
                            pr = 0
                            re = 0
                            print("   {} empty squares: salient: {}, missing: {}, precision: {} %, recall: {} %".format(
                                    engine, salEmpty, missEmpty, 0, 0))
                        evaluation[engine]["precision {} empty".format(jsonF)].append(pr)
                        evaluation[engine]["recall {} empty".format(jsonF)].append(re)
                nr += 1

        evaluation[engine]["precision"] = round(evaluation[engine]["precision"] / (((nr - 1) * 2) - (evaluation[engine]["wrong move positional"]+evaluation[engine]["wrong move tactical"])), 2)  # calculate mean of all precision values
        evaluation[engine]["recall"] = round(evaluation[engine]["recall"] / (((nr - 1) * 2) - (evaluation[engine]["wrong move positional"]+evaluation[engine]["wrong move tactical"])), 2)        # calculate mean of all recall values
        evaluation[engine]["precision positional"] = round(evaluation[engine]["precision positional"] / ((nr - 1) - evaluation[engine]["wrong move positional"]),2)
        evaluation[engine]["recall positional"] = round(evaluation[engine]["recall positional"] / ((nr - 1) - evaluation[engine]["wrong move positional"]), 2)
        evaluation[engine]["precision tactical"] = round(evaluation[engine]["precision tactical"] / ((nr - 1) - evaluation[engine]["wrong move tactical"]), 2)
        evaluation[engine]["recall tactical"] = round(evaluation[engine]["recall tactical"] / ((nr - 1) - evaluation[engine]["wrong move tactical"]), 2)
        type1 = ["precision", "recall"]
        type2 = ["positional", "tactical"]
        for a in type1:
            for b in type2:
                x = 0
                for m in evaluation[engine]["{} {} empty".format(a, b)]:
                    x += m
                evaluation[engine]["{} {} empty".format(a, b)] = round(x/len(evaluation[engine]["{} {} empty".format(a, b)]),2)
                x = 0
                for m in evaluation[engine]["{} {} piece".format(a, b)]:
                    x += m
                evaluation[engine]["{} {} piece".format(a, b)] = round( x / len(evaluation[engine]["{} {} piece".format(a, b)]), 2)
        outputF.write('------------------------------------------\n')
        print('------------------------------------------')

    outputF.close()
    print('------------------------------------------')
    print("Evaluation:")
    print("highest number of marked squares: {}, {}".format(highestSalEngine, highestSal))
    print("Engines sorted by Total Score:")
    sortedKeys = sorted(evaluation, key=lambda x: evaluation[x]["score"], reverse=True) # sort engines according to their score
    rank = 1
    for key in sortedKeys:
        print("{}. {}:{} {}, wrong move: {}, precision: {} %, recall: {} %".format(rank, key, " "*(11-len(key)), "%.2f" %(evaluation[key]["score"]), (evaluation[key]["wrong move positional"]+evaluation[key]["wrong move tactical"]), evaluation[key]["precision"], evaluation[key]["recall"]))
        rank += 1
    print('------------------------------------------')

    print("Engines sorted by Score Average:")
    sortedKeys = sorted(evaluation, key=lambda x: (evaluation[x]["positional score"] + evaluation[x]["tactical score"]) / 2, reverse=True)  # sort engines according to their average score
    rank = 1
    for key in sortedKeys:
        print("{}. {}:{} average score: {}".format(rank, key, " " * (11 - len(key)), (
                    evaluation[key]["positional score"] + evaluation[key]["tactical score"]) / 2))
        rank += 1
    print('------------------------------------------')

    for t in type2: # Positional, Tactical Score
        print("Engines sorted by {} Score:".format(t.capitalize()))
        sortedKeys = sorted(evaluation, key=lambda x: evaluation[x]["{} score".format(t)],reverse=True) # sort engines according to their positional score
        rank = 1
        mF = 0
        mP = 0
        mR = 0
        avgMarkedSquares = 0
        for key in sortedKeys:
            avgSq = round(evaluation[key]["salient {}".format(t)]/(12-evaluation[key]["wrong move {}".format(t)]), 2)
            avgMarkedSquares += avgSq
            print("{}. {}:{} {} score: {}, wrong {} move: {}, salient: {}, avg square: {}, {} F1: {} %, {} precision: {} %, {} recall: {} %".format(rank, key, " "*(11-len(key)), t, "%.2f" %(evaluation[key]["{} score".format(t)]), t, evaluation[key]["wrong move {}".format(t)], evaluation[key]["salient {}".format(t)], avgSq, t, round(2*evaluation[key]["precision {}".format(t)]*evaluation[key]["recall {}".format(t)]/(evaluation[key]["precision {}".format(t)]+evaluation[key]["recall {}".format(t)]),2), t, "%.2f" %(evaluation[key]["precision {}".format(t)]), t, evaluation[key]["recall {}".format(t)]))
            rank += 1
            mF += round(2 * evaluation[key]["precision {}".format(t)] * evaluation[key]["recall {}".format(t)] / (evaluation[key]["precision {}".format(t)] + evaluation[key]["recall {}".format(t)]), 2)
            mP += evaluation[key]["precision {}".format(t)]
            mR += evaluation[key]["recall {}".format(t)]
        print("F1 mean: {} %, precision mean: {} %, recall mean: {} %, average marked squares: {}".format(round(mF/len(folders),2), round(mP/len(folders),2), round(mR/len(folders),2), round(avgMarkedSquares/len(folders), 2)))
        print('------------------------------------------')

    for t in type2:  # Positional, Tactical Analysis For Non-Empty Square
        print("Engines sorted by {} Non-Empty Squares:".format(t.capitalize()))
        sortedKeys = sorted(evaluation, key=lambda x: 2 * (evaluation[x]["precision {} piece".format(t)] * evaluation[x]["recall {} piece".format(t)] / (evaluation[x]["precision {} piece".format(t)] + evaluation[x]["recall {} piece".format(t)])), reverse=True)  # sort engines according to the F1 mean
        rank = 1
        mF = 0
        mP = 0
        mR = 0
        for key in sortedKeys:
            print("{}. {}:{} non-empty Squares {} F1: {} %, non-empty Squares {} precision: {} %, non-empty Squares {} recall: {} %".format(
                    rank, key, " " * (11 - len(key)), t,
                    round(2 * evaluation[key]["precision {} piece".format(t)] * evaluation[key]["recall {} piece".format(t)] / (
                            evaluation[key]["precision {} piece".format(t)] + evaluation[key]["recall {} piece".format(t)]), 2), t,
                               "%.2f" % (evaluation[key]["precision {} piece".format(t)]), t, "%.2f" % evaluation[key]["recall {} piece".format(t)]))
            rank += 1
            mF += round(2 * evaluation[key]["precision {} piece".format(t)] * evaluation[key]["recall {} piece".format(t)] / (
                    evaluation[key]["precision {} piece".format(t)] + evaluation[key]["recall {} piece".format(t)]), 2)
            mP += evaluation[key]["precision {} piece".format(t)]
            mR += evaluation[key]["recall {} piece".format(t)]
        print("F1 mean: {} %, precision mean: {} %, recall mean: {} %".format(round(mF / len(folders), 2), round(mP / len(folders), 2),
                                                                              round(mR / len(folders), 2)))
        print('------------------------------------------')

    for t in type2:  # Positional, Tactical Analysis For Empty Square
        print("Engines sorted by {} Empty Squares:".format(t.capitalize()))
        sortedKeys = sorted(evaluation, key=lambda x: 2 * (
                    evaluation[x]["precision {} empty".format(t)] * evaluation[x]["recall {} empty".format(t)] / (
                        evaluation[x]["precision {} empty".format(t)] + evaluation[x]["recall {} empty".format(t)]+1)),
                            reverse=True)  # sort engines according to the F1 mean
        rank = 1
        mF = 0
        mP = 0
        mR = 0
        for key in sortedKeys:
            f = 0
            if evaluation[key]["precision {} empty".format(t)] + evaluation[key]["recall {} empty".format(t)] != 0:
                f = round(2 * evaluation[key]["precision {} empty".format(t)] * evaluation[key]["recall {} empty".format(t)] / (evaluation[key]["precision {} empty".format(t)] + evaluation[key][
                              "recall {} empty".format(t)]), 2)
            print("{}. {}:{} empty Squares {} F1: {} %, empty Squares {} precision: {} %, empty Squares {} recall: {} %".format(
                    rank, key, " " * (11 - len(key)), t, f, t, "%.2f" % (evaluation[key]["precision {} empty".format(t)]), t, "%.2f" % evaluation[key]["recall {} empty".format(t)]))
            rank += 1
            mF += f
            mP += evaluation[key]["precision {} empty".format(t)]
            mR += evaluation[key]["recall {} empty".format(t)]
        print("F1 mean: {} %, precision mean: {} %, recall mean: {} %".format(round(mF / len(folders), 2), round(mP / len(folders), 2),
                                                                              round(mR / len(folders), 2)))
        print('------------------------------------------')

    print("Engines sorted by F1 mean:")
    sortedKeys = sorted(evaluation, key=lambda x: 2*((evaluation[x]["precision"]*evaluation[x]["recall"])/(evaluation[x]["precision"]+evaluation[x]["recall"])),reverse=True)  # sort engines according to the F1 mean
    rank = 1
    mF = 0
    mP = 0
    mR = 0
    for key in sortedKeys:
        print("{}. {}:{} wrong move: {}, F1: {} %, precision: {} %, recall: {} %".format(rank, key, " "*(11-len(key)), evaluation[key]["wrong move positional"]+evaluation[key]["wrong move tactical"], round(2*((evaluation[key]["precision"]*evaluation[key]["recall"])/(evaluation[key]["precision"]+evaluation[key]["recall"])),2), evaluation[key]["precision"], evaluation[key]["recall"]))
        rank += 1
        mF += round(2*((evaluation[key]["precision"]*evaluation[key]["recall"])/(evaluation[key]["precision"]+evaluation[key]["recall"])),2)
        mP += evaluation[key]["precision"]
        mR += evaluation[key]["recall"]
    print("F1 mean: {} %, precision mean: {} %, recall mean: {} %".format(round(mF / len(folders), 2), round(mP / len(folders), 2), round(mR / len(folders), 2)))


async def evaluateBratkoKopec_allPuzzles(directory="evaluation/bratko-kopec/original", mode="All"):
    """Evaluates all bratko-kopec puzzles in the given directory based on the ground-truth in the chess_saliency_databases folder.

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

    outputF = open("{}/output.txt".format(directory), "a")
    outputF.truncate(0)

    jsonDatabaseFolder = "chess_saliency_databases/bratko-kopec"
    jsonFiles = list(filter(lambda x: os.path.isdir(os.path.join(jsonDatabaseFolder, x)), os.listdir(jsonDatabaseFolder)))
    if len(jsonFiles) == 0:
        jsonDatabaseFolder, engine = os.path.split(jsonDatabaseFolder)
        jsonFiles = [engine]

    evaluation = {f: {} for f in folders}
    highestF1 = 0

    for engine in folders: # iterate engines
        print(engine)
        outputF.write("engine: {}\n".format(engine))
        evaluation[engine]["salient positional"] = 0          # number of salient marked squares for positional puzzles where engine executed solution move
        evaluation[engine]["salient tactical"] = 0            # number of salient marked squares for tactical puzzles where engine executed solution move
        evaluation[engine]["missing"] = 0                     # number of missing salient (false negative) squares for puzzles where engine executed solution move
        evaluation[engine]["precision"] = 0                   # precision over puzzles where engine executed solution move
        evaluation[engine]["recall"] = 0                      # recall over puzzles where engine executed solution move
        evaluation[engine]["precision positional"] = 0        # precision over positional puzzles where engine executed solution move
        evaluation[engine]["recall positional"] = 0           # recall over positional puzzles where engine executed solution move
        evaluation[engine]["precision tactical"] = 0          # precision over tactical puzzles where engine executed solution move
        evaluation[engine]["recall tactical"] = 0             # recall over tactical puzzles where engine executed solution move
        evaluation[engine]["precision positional piece"] = [] # precision over non-empty squares on positional puzzles where engine executed solution move
        evaluation[engine]["recall positional piece"] = []    # recall over non-empty squares on positional puzzles where engine executed solution move
        evaluation[engine]["precision tactical piece"] = []   # precision over non-empty squares on tactical puzzles where engine executed solution move
        evaluation[engine]["recall tactical piece"] = []      # recall over non-empty squares on tactical puzzles where engine executed solution move
        evaluation[engine]["precision positional empty"] = [] # precision over empty squares on positional puzzles where engine executed solution move
        evaluation[engine]["recall positional empty"] = []    # recall over empty squares on positional puzzles where engine executed solution move
        evaluation[engine]["precision tactical empty"] = []   # precision over empty squares on tactical puzzles where engine executed solution move
        evaluation[engine]["recall tactical empty"] = []      # recall over empty squares on tactical puzzles where engine executed solution move
        evaluation[engine]["wrong move positional"] = 0       # times that engine executed wrong move for positional puzzles
        evaluation[engine]["wrong move tactical"] = 0         # times that engine executed wrong move for tactical puzzles

        if mode != "Right":
            if not os.path.exists(pathDir+"/"+engine):
                os.makedirs(pathDir+"/"+engine)
                print("created directory")

        for jsonF in jsonFiles: # positional or tactical folder
            print(jsonF)
            outputF.write("{}\n".format(jsonF))
            with open("{}/{}/bratko-kopec.json".format(jsonDatabaseFolder, jsonF), "r") as jsonFile: # open positional or tactical test solution
                database = json.load(jsonFile)

            path = "{}/{}/{}/data.json".format(directory, engine, jsonF) # open engine's evaluation
            with open(path, "r") as jsonFile:
                data = json.load(jsonFile)

            backupIndex = 0
            nr = 1

            for puzzle in database: # iterate puzzles
                puzzleNr = "puzzle" + str(nr)
                print(puzzleNr)
                board = chess.Board(puzzle["fen"])

                miss = 0
                salEmpty = 0
                missEmpty = 0
                precision = 0
                recall = 0
                if data[puzzleNr]["move"] in puzzle["best move"]:
                    if mode == "All" or mode == "Right":
                        gTarray = puzzle["groundTruth"]
                        if gTarray is not None:  # calculate precision and recall
                            print("   {} squares should be salient".format(len(gTarray)))

                            gTarrayEmpty = []
                            sal = len(data[puzzleNr]["sorted saliencies"]["above threshold"])
                            for m in data[puzzleNr]["sorted saliencies"]["above threshold"]:  # analyse all empty squares
                                if board.piece_type_at(chess.SQUARES[chess.parse_square(m)]) is None:
                                    salEmpty += 1
                            for m in gTarray:
                                if board.piece_type_at(chess.SQUARES[chess.parse_square(m)]) is None:
                                    gTarrayEmpty.append(m)
                            for sq in data[puzzleNr]["sorted saliencies"]["above threshold"]:
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
                                for m in data[puzzleNr]["sorted saliencies"]["above threshold"]:
                                    if m in gTarray:
                                        print("      {}: {}".format(m, data[puzzleNr]["sorted saliencies"][
                                            "above threshold"][m]))
                                print("      below threshold: ")
                                for m in data[puzzleNr]["sorted saliencies"]["below threshold"]:
                                    if m in gTarray:
                                        print("      {}: {}".format(m, data[puzzleNr]["sorted saliencies"][
                                            "below threshold"][m]))

                            evaluation[engine]["precision"] += precision
                            evaluation[engine]["precision {}".format(jsonF)] += precision
                            evaluation[engine]["recall"] += recall
                            evaluation[engine]["recall {}".format(jsonF)] += recall
                            f1 = 2*precision*recall/(precision+recall)
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
                                evaluation[engine]["precision {} piece".format(jsonF)].append(precision)
                                evaluation[engine]["recall {} piece".format(jsonF)].append(recall)
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
                                evaluation[engine]["precision {} empty".format(jsonF)].append(precision)
                                evaluation[engine]["recall {} empty".format(jsonF)].append(recall)
                else:
                    print("wrong move")
                    evaluation[engine]["wrong move {}".format(jsonF)] += 1
                    if mode == "Wrong" or mode == "All":
                        if not os.path.exists(pathDir + "/" + engine + "/" + jsonF):
                            os.makedirs(pathDir + "/" + engine + "/" + jsonF)
                            print("created directory")

                        path = directory + "/" + engine + "/" + jsonF + "/" + "output.txt"
                        with open(path, "r") as file:
                            output = file.readlines()

                        i = backupIndex
                        qValuesEngine = dict()

                        while output[i].startswith(puzzleNr) is False:
                            i += 1

                        while i < len(output):
                            if output[i].startswith(puzzleNr) and len(output[i]) < 15:
                                beforeP = None
                                board = chess.Board(data[puzzleNr]["fen"])
                                stop = int(puzzleNr.replace("puzzle", ""))
                            elif output[i].startswith("puzzle{}".format(stop+1)) and len(output[i]) < 15:
                                backupIndex = i
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
                        aboveThreshold, _ = await givenQValues_computeSaliency(board, move, puzzle["fen"], beforePdict, qValuesEngine, pathDir + "/" + engine + "/" + jsonF, puzzleNr)

                        gTarray = puzzle["groundTruth"]
                        if gTarray is not None:  # calculate precision and recall
                            print("   {} squares should be salient".format(len(gTarray)))

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
                            evaluation[engine]["precision {}".format(jsonF)] += precision
                            evaluation[engine]["recall"] += recall
                            evaluation[engine]["recall {}".format(jsonF)] += recall
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
                                evaluation[engine]["precision {} piece".format(jsonF)].append(precision)
                                evaluation[engine]["recall {} piece".format(jsonF)].append(recall)
                            if len(gTarrayEmpty) > 0:
                                print("   {} empty squares should be salient".format(
                                    len(gTarrayEmpty)))  # only empty squares
                                if salEmpty > 0:
                                    precision = (len(gTarrayEmpty) - missEmpty) / salEmpty * 100
                                    recall = (len(gTarrayEmpty) - missEmpty) / len(gTarrayEmpty) * 100
                                    print("   {} empty squares: salient: {}, missing: {}, precision: {} %, recall: {} %".format(engine, salEmpty, missEmpty, round(precision, 2), round(recall, 2)))
                                else:
                                    precision = 0
                                    recall = 0
                                    print("   {} empty squares: salient: {}, missing: {}, precision: {} %, recall: {} %".format(engine, salEmpty, missEmpty, 0, 0))
                                evaluation[engine]["precision {} empty".format(jsonF)].append(precision)
                                evaluation[engine]["recall {} empty".format(jsonF)].append(recall)
                nr += 1


        if mode == "All":
            print("{}\'s averages are calculated over all {} puzzles".format(engine, (nr - 1) * 2))
            evaluation[engine]["precision"] = round(evaluation[engine]["precision"] / ((nr - 1) * 2), 2)  # calculate mean of all precision values
            evaluation[engine]["recall"] = round(evaluation[engine]["recall"] / ((nr - 1) * 2), 2)        # calculate mean of all recall values
            evaluation[engine]["precision positional"] = round(evaluation[engine]["precision positional"] / (nr - 1), 2)
            evaluation[engine]["recall positional"] = round(evaluation[engine]["recall positional"] / (nr - 1), 2)
            evaluation[engine]["precision tactical"] = round(evaluation[engine]["precision tactical"] / (nr - 1), 2)
            evaluation[engine]["recall tactical"] = round(evaluation[engine]["recall tactical"] / (nr - 1), 2)
        elif mode == "Right":
            print("{}\'s averages are calculated over {} puzzles".format(engine, ((nr - 1) * 2) - (evaluation[engine]["wrong move positional"] + evaluation[engine]["wrong move tactical"])))
            evaluation[engine]["precision"] = round(evaluation[engine]["precision"] / (((nr - 1) * 2) - (evaluation[engine]["wrong move positional"] + evaluation[engine]["wrong move tactical"])), 2)  # calculate mean of all precision values
            evaluation[engine]["recall"] = round(evaluation[engine]["recall"] / (((nr - 1) * 2) - (evaluation[engine]["wrong move positional"] + evaluation[engine]["wrong move tactical"])), 2)  # calculate mean of all recall values
            evaluation[engine]["precision positional"] = round(evaluation[engine]["precision positional"] / (nr - 1 - evaluation[engine]["wrong move positional"]), 2)
            evaluation[engine]["recall positional"] = round(evaluation[engine]["recall positional"] / (nr - 1 - evaluation[engine]["wrong move positional"]), 2)
            evaluation[engine]["precision tactical"] = round(evaluation[engine]["precision tactical"] / (nr - 1 - evaluation[engine]["wrong move tactical"]), 2)
            evaluation[engine]["recall tactical"] = round(evaluation[engine]["recall tactical"] / (nr - 1 - evaluation[engine]["wrong move tactical"]), 2)
        elif mode == "Wrong":
            print("{}\'s averages are calculated over {} puzzles".format(engine, evaluation[engine]["wrong move positional"] + evaluation[engine]["wrong move tactical"]))
            if (evaluation[engine]["wrong move positional"] + evaluation[engine]["wrong move tactical"]) > 0:
                evaluation[engine]["precision"] = round(evaluation[engine]["precision"] / (evaluation[engine]["wrong move positional"] + evaluation[engine]["wrong move tactical"]), 2)  # calculate mean of all precision values
                evaluation[engine]["recall"] = round(evaluation[engine]["recall"] / (evaluation[engine]["wrong move positional"] + evaluation[engine]["wrong move tactical"]), 2)  # calculate mean of all recall values
            if evaluation[engine]["wrong move positional"] > 0:
                evaluation[engine]["precision positional"] = round(evaluation[engine]["precision positional"] / evaluation[engine]["wrong move positional"], 2)
                evaluation[engine]["recall positional"] = round(evaluation[engine]["recall positional"] / evaluation[engine]["wrong move positional"], 2)
            if evaluation[engine]["wrong move tactical"] > 0:
                evaluation[engine]["precision tactical"] = round(evaluation[engine]["precision tactical"] / evaluation[engine]["wrong move tactical"], 2)
                evaluation[engine]["recall tactical"] = round(evaluation[engine]["recall tactical"] / evaluation[engine]["wrong move tactical"], 2)

        type1 = ["precision", "recall"]
        type2 = ["positional", "tactical"]
        for a in type1:
            for b in type2:
                if len(evaluation[engine]["{} {} empty".format(a, b)]) > 0:
                    x = 0
                    for m in evaluation[engine]["{} {} empty".format(a, b)]:
                        x += m
                    evaluation[engine]["{} {} empty".format(a, b)] = round(x/len(evaluation[engine]["{} {} empty".format(a, b)]),2)
                else:
                    evaluation[engine]["{} {} empty".format(a, b)] = 0
                if len(evaluation[engine]["{} {} piece".format(a, b)]) > 0:
                    x = 0
                    for m in evaluation[engine]["{} {} piece".format(a, b)]:
                        x += m
                    evaluation[engine]["{} {} piece".format(a, b)] = round( x / len(evaluation[engine]["{} {} piece".format(a, b)]), 2)
                else:
                    evaluation[engine]["{} {} piece".format(a, b)] = 0
        outputF.write('------------------------------------------\n')
        print('------------------------------------------')

    outputF.close()

    if mode == "Right":
        keys = list(evaluation)
        print(keys)
        for engine in keys:
            if evaluation[engine]["wrong move positional"] == 12 and evaluation[engine]["wrong move tactical"] == 12:
                print("engine {} deleted".format(engine))
                folders.remove(engine)
                del evaluation[engine]
    elif mode == "Wrong":
        keys = list(evaluation)
        for engine in keys:
            if evaluation[engine]["wrong move positional"] == 0 and evaluation[engine]["wrong move tactical"] == 0:
                print("engine {} deleted".format(engine))
                folders.remove(engine)
                del evaluation[engine]

    for t in type2: # Positional, Tactical Overall
        print("Engines sorted by {} F1:".format(t.capitalize()))
        keys = list(evaluation)
        copy = evaluation.copy()
        for engine in keys:
            if (evaluation[engine]["precision {}".format(t)] + evaluation[engine]["recall {}".format(t)]) == 0:
                del copy[engine]
                print("engine {} has {} {} wrong moves (precision {}, recall {})".format(engine, evaluation[engine]["wrong move {}".format(t)], t, evaluation[engine]["precision {}".format(t)], evaluation[engine]["recall {}".format(t)]))
        sortedKeys = sorted(copy, key=lambda x: round(2*evaluation[x]["precision {}".format(t)]*evaluation[x]["recall {}".format(t)]/(evaluation[x]["precision {}".format(t)]+evaluation[x]["recall {}".format(t)]),2),reverse=True) # sort engines according to their positional score
        rank = 1
        mF = 0
        mP = 0
        mR = 0
        avgMarkedSquares = 0
        for key in sortedKeys:
            avgSq = round(evaluation[key]["salient {}".format(t)]/(12-evaluation[key]["wrong move {}".format(t)]), 2)
            avgMarkedSquares += avgSq
            print("{}. {}:{} {} wrong moves: {}, {} F1: {} %, {} precision: {} %, {} recall: {} %".format(rank, key, " "*(11-len(key)), t, evaluation[key]["wrong move {}".format(t)], t, round(2*evaluation[key]["precision {}".format(t)]*evaluation[key]["recall {}".format(t)]/(evaluation[key]["precision {}".format(t)]+evaluation[key]["recall {}".format(t)]),2), t, "%.2f" %(evaluation[key]["precision {}".format(t)]), t, evaluation[key]["recall {}".format(t)]))
            rank += 1
            mF += round(2 * evaluation[key]["precision {}".format(t)] * evaluation[key]["recall {}".format(t)] / (evaluation[key]["precision {}".format(t)] + evaluation[key]["recall {}".format(t)]), 2)
            mP += evaluation[key]["precision {}".format(t)]
            mR += evaluation[key]["recall {}".format(t)]
        print("F1 mean: {} %, precision mean: {} %, recall mean: {} %, average marked squares: {}".format(round(mF/len(folders),2), round(mP/len(folders),2), round(mR/len(folders),2), round(avgMarkedSquares/len(folders), 2)))
        print('------------------------------------------')

    for t in type2:  # Positional, Tactical Analysis For Non-Empty Square
        print("Engines sorted by {} Non-Empty Squares:".format(t.capitalize()))
        keys = list(evaluation)
        copy = evaluation.copy()
        for engine in keys:
            if (evaluation[engine]["precision {} piece".format(t)] + evaluation[engine]["recall {} piece".format(t)]) == 0:
                del copy[engine]
                print("engine {} has {} {} wrong moves (precision {}, recall {})".format(engine, evaluation[engine]["wrong move {}".format(t)], t, evaluation[engine]["precision {}".format(t)], evaluation[engine]["recall {}".format(t)]))
        sortedKeys = sorted(copy, key=lambda x: 2 * (evaluation[x]["precision {} piece".format(t)] * evaluation[x]["recall {} piece".format(t)] / (evaluation[x]["precision {} piece".format(t)] + evaluation[x]["recall {} piece".format(t)])), reverse=True)  # sort engines according to the F1 mean
        rank = 1
        mF = 0
        mP = 0
        mR = 0
        for key in sortedKeys:
            print("{}. {}:{} non-empty Squares {} F1: {} %, non-empty Squares {} precision: {} %, non-empty Squares {} recall: {} %".format(
                    rank, key, " " * (11 - len(key)), t,
                    round(2 * evaluation[key]["precision {} piece".format(t)] * evaluation[key]["recall {} piece".format(t)] / (
                            evaluation[key]["precision {} piece".format(t)] + evaluation[key]["recall {} piece".format(t)]), 2), t,
                               "%.2f" % (evaluation[key]["precision {} piece".format(t)]), t, "%.2f" % evaluation[key]["recall {} piece".format(t)]))
            rank += 1
            mF += round(2 * evaluation[key]["precision {} piece".format(t)] * evaluation[key]["recall {} piece".format(t)] / (
                    evaluation[key]["precision {} piece".format(t)] + evaluation[key]["recall {} piece".format(t)]), 2)
            mP += evaluation[key]["precision {} piece".format(t)]
            mR += evaluation[key]["recall {} piece".format(t)]
        print("F1 mean: {} %, precision mean: {} %, recall mean: {} %".format(round(mF / len(folders), 2), round(mP / len(folders), 2), round(mR / len(folders), 2)))
        print('------------------------------------------')

    for t in type2:  # Positional, Tactical Analysis For Empty Square
        print("Engines sorted by {} Empty Squares:".format(t.capitalize()))
        keys = list(evaluation)
        copy = evaluation.copy()
        for engine in keys:
            if (evaluation[engine]["precision {} empty".format(t)] + evaluation[engine]["recall {} empty".format(t)]) == 0:
                del copy[engine]
                print("engine {} has {} {} wrong moves (precision {}, recall {})".format(engine, evaluation[engine]["wrong move {}".format(t)], t, evaluation[engine]["precision {}".format(t)], evaluation[engine]["recall {}".format(t)]))
        sortedKeys = sorted(copy, key=lambda x: 2 * ( evaluation[x]["precision {} empty".format(t)] * evaluation[x]["recall {} empty".format(t)] / (
                    evaluation[x]["precision {} empty".format(t)] + evaluation[x]["recall {} empty".format(t)]+1)), reverse=True)  # sort engines according to the F1 mean
        rank = 1
        mF = 0
        mP = 0
        mR = 0
        for key in sortedKeys:
            f = round(2 * evaluation[key]["precision {} empty".format(t)] * evaluation[key]["recall {} empty".format(t)] / (evaluation[key]["precision {} empty".format(t)] + evaluation[key]["recall {} empty".format(t)]), 2)
            print("{}. {}:{} empty Squares {} F1: {} %, empty Squares {} precision: {} %, empty Squares {} recall: {} %".format(
                    rank, key, " " * (11 - len(key)), t, f, t, "%.2f" % (evaluation[key]["precision {} empty".format(t)]), t, "%.2f" % evaluation[key]["recall {} empty".format(t)]))
            rank += 1
            mF += f
            mP += evaluation[key]["precision {} empty".format(t)]
            mR += evaluation[key]["recall {} empty".format(t)]
        print("F1 mean: {} %, precision mean: {} %, recall mean: {} %".format(round(mF / len(folders), 2), round(mP / len(folders), 2), round(mR / len(folders), 2)))
        print('------------------------------------------')

    print("Engines sorted by F1 mean:")
    sortedKeys = sorted(evaluation, key=lambda x: 2*((evaluation[x]["precision"]*evaluation[x]["recall"])/(evaluation[x]["precision"]+evaluation[x]["recall"])),reverse=True)  # sort engines according to the F1 mean
    rank = 1
    mF = 0
    mP = 0
    mR = 0
    for key in sortedKeys:
        print("{}. {}:{} F1: {} %, precision: {} %, recall: {} %".format(rank, key, " "*(11-len(key)), round(2*((evaluation[key]["precision"]*evaluation[key]["recall"])/(evaluation[key]["precision"]+evaluation[key]["recall"])),2), evaluation[key]["precision"], evaluation[key]["recall"]))
        rank += 1
        mF += round(2*((evaluation[key]["precision"]*evaluation[key]["recall"])/(evaluation[key]["precision"]+evaluation[key]["recall"])),2)
        mP += evaluation[key]["precision"]
        mR += evaluation[key]["recall"]
    print("F1 mean: {} %, precision mean: {} %, recall mean: {} %".format(round(mF / len(folders), 2), round(mP / len(folders), 2), round(mR / len(folders), 2)))


def convertToPosition(directory="evaluation/bratko-kopec/original/output.txt"):
    """ Sorts the engines' evaluation based on the puzzle order they appear in http://www.kopecchess.com/bktest/Bktest.html.

    :param directory: path where different engines' output file is stored
    """

    if os.path.exists(directory) is False:
        print("Could mot find output file. Run evaluateBratkoKopec() to create it!")
        return
    with open(directory, "r") as file:
        output = file.readlines()

    order = dict()

    folders = list(filter(lambda x: os.path.isdir(os.path.join(directory.replace("output.txt", ""), x)), os.listdir(directory.replace("output.txt", ""))))
    print(folders)
    for engine in folders:
        order[engine] = [0]*24

    engine = None
    orderTactical = [0,4,6,9,11,13,14,15,17,18,20,21]
    orderPositional = [1,2,3,5,7,8,10,12,16,19,22,23]
    pos = False
    tact = False
    i = 0
    while i < len(output):
        if output[i].startswith("engine: "):
            engine = output[i].replace("engine: ","")
            engine = engine.replace("\n", "")
        elif output[i].startswith("positional"):
            pos = True
            tact = False
            index = 0
        elif output[i].startswith("tactical"):
            pos = False
            tact = True
            index = 0
        elif output[i].startswith("puzzle"):
            move = output[i].split("[")[1]
            move = move.replace("]\n","")
            puzzleNr = output[i].split(" ")[0]
            if pos:
                puzzle = output[i].replace(puzzleNr,"position {}".format(orderPositional[index]+1))
            elif tact:
                puzzle = output[i].replace(puzzleNr,"position {}".format(orderTactical[index]+1))
            temp = ''
            i += 1
            while output[i].startswith("   "):
                temp += output[i]
                if "'" in output[i]:
                    key = output[i].split("'")[1]
                    if key in move:
                        puzzle += temp
                        if pos:
                            order[engine][orderPositional[index]] = puzzle
                        elif tact:
                            order[engine][orderTactical[index]] = puzzle
                        break
                i += 1
            i -= 1
            index += 1
        i += 1

    for e in order:
        print(e)
        i = 0
        while i < len(order[e]):
            if order[e][i] == 0:
                print("position {} is to be skipped\n".format(i+1))
            else:
                print(order[e][i])
            i += 1


def singleEngine_bratkoKopec_groundTruthEvaluation(directory1="evaluation/bratko-kopec/original/stockfish", directory2="evaluation/bratko-kopec/updated/stockfish"):
    """ Evaluates the bratko-kopec puzzles for a single engine with the original and updated SARFA implementation.

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

    jsonDatabaseFolder = "chess_saliency_databases/bratko-kopec"
    jsonFiles = list(filter(lambda x: os.path.isdir(os.path.join(jsonDatabaseFolder, x)), os.listdir(jsonDatabaseFolder)))
    if len(jsonFiles) == 0:
        jsonDatabaseFolder, engine = os.path.split(jsonDatabaseFolder)
        jsonFiles = [engine]

    positional = []
    tactical = []
    nr = 1
    for jsonF in jsonFiles:  # positional or tactical folder
        subset = []
        with open("{}/{}/output.txt".format(directory1, jsonF), "r") as file:
            output1 = file.readlines()
        with open("{}/{}/output.txt".format(directory2, jsonF), "r") as file:
            output2 = file.readlines()
        i1 = 0
        i2 = 0
        while nr < 13:
            puzzleNr = "puzzle" + str(nr)
            while output1[i1].startswith(puzzleNr) is False:
                i1 += 1
            i1 += 2
            while output1[i2].startswith(puzzleNr) is False:
                i2 += 1
            i2 += 2
            subset.append(puzzleNr)
            if (output1[i1].startswith("assigned new best move to engine") or output2[i2].startswith("assigned new best move to engine")) and puzzleNr in subset:
                subset.remove(puzzleNr)
            nr += 1
            if i1 < len(output1):
                i1 += 1
            if i2 < len(output2):
                i2 += 1
        if len(positional) == 0:
            positional = subset
        elif len(tactical) == 0:
            tactical = subset

    total = 0
    count = 0
    data = dict()
    for jsonF in jsonFiles:  # positional or tactical folder
        nr = 1
        print(jsonF)
        with open("{}/{}/bratko-kopec.json".format(jsonDatabaseFolder, jsonF),"r") as jsonFile:  # open positional or tactical test solution
            database = json.load(jsonFile)

        with open("{}/{}/data.json".format(directory1, jsonF), "r") as jsonFile:
            data[folders[0]] = json.load(jsonFile)
        with open("{}/{}/data.json".format(directory2, jsonF), "r") as jsonFile:
            data[folders[1]] = json.load(jsonFile)

        if jsonF.__contains__("positional"):
            subset = positional
        else:
            subset = tactical

        for puzzle in database:
            puzzleNr = "puzzle" + str(nr)

            for x in subset:
                if puzzleNr == x:
                    count += 1
                    print("{} - {} squares salient".format(puzzleNr, len(puzzle["groundTruth"])))
                    total += len(puzzle["groundTruth"])

                    for f in data:
                        sal = len(data[f][puzzleNr]["sorted saliencies"]["above threshold"])    # puzzle's salient squares
                        evaluation[f]["salient"] += sal
                        miss = 0

                        for square in puzzle["groundTruth"]:
                            if square not in data[f][puzzleNr]["sorted saliencies"]["above threshold"]:
                                miss += 1                                                       # puzzle's missing ground truth
                            for sq in data[f][puzzleNr]["sorted saliencies"]:
                                if sq == square:
                                    print(data[f][puzzleNr]["sorted saliencies"][sq])
                                    break

                        evaluation[f]["missing"] += miss
                        pr = 0
                        re = 0
                        if sal > 0:
                            pr = (len(puzzle["groundTruth"]) - miss) / sal * 100                                    # puzzle's precision
                            re = (len(puzzle["groundTruth"]) - miss) / len(puzzle["groundTruth"]) * 100             # puzzle's recall
                        print("   {}: salient: {}, missing: {}, precision: {} %, recall: {} %".format(f, sal, miss, round(pr, 2), round(re, 2)))
                        evaluation[f]["precision"] += pr
                        evaluation[f]["recall"] += re
            nr += 1
    for f in data:
        evaluation[f]["precision"] = round(evaluation[f]["precision"]/count,2) # calculate mean of all precision values
        evaluation[f]["recall"] = round(evaluation[f]["recall"] /count, 2)     # calculate mean of all recall values

    print('------------------------------------------')
    print("In total {} squares from {} puzzles should be salient".format(total, count))
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


def bratkoKopec_calculateImprovements_emptySquares(directory="evaluation/bratko-kopec/updated/"):
    """ Searches for improvements over all engines' ground-truths empty squares.

    :param directory: path where evaluation of engines is written
    """

    import re
    folders = list(filter(lambda x: os.path.isdir(os.path.join(directory, x)), os.listdir(directory)))
    engineDir = directory
    if len(folders) == 0:
        engineDir, file = os.path.split(directory)
        engineDir += '/'
        folders.append(file)
    print(folders)
    data = dict()
    output = dict()
    evaluation = {f: {} for f in folders}
    emptyGT = dict()

    for t in ["positional", "tactical"]:
        with open("{}/{}/bratko-kopec.json".format("chess_saliency_databases/bratko-kopec", t),
                  "r") as jsonFile:  # open positional or tactical test solution
            database = json.load(jsonFile)

        emptyGT[t] = []
        i = 0
        for puzzle in database:
            board = chess.Board(puzzle["fen"])
            x = []
            for gT in puzzle["groundTruth"]:
                if board.piece_type_at(chess.SQUARES[chess.parse_square(gT)]) is None:  # empty square
                    x.append(gT)
            emptyGT[t].append(x)
            i += 1

    for engine in folders:
        evaluation[engine] = dict()
        data[engine] = dict()
        output[engine] = dict()
        for t in ["positional", "tactical"]:
            with open("{}/{}/bratko-kopec.json".format("chess_saliency_databases/bratko-kopec", t), "r") as jsonFile:  # open positional or tactical test solution
                database = json.load(jsonFile)

            path = engineDir + engine + "/" + t + "/" +"data.json"
            with open(path, "r") as jsonFile:
                data[engine][t] = json.load(jsonFile)
            path = engineDir + engine + "/" + t + "/" + "output.txt"
            with open(path, "r") as file:
                output[engine][t] = file.readlines()

            evaluation[engine][t] = dict()
            evaluation[engine][t]["answer"] = dict()     # engine's square data
            evaluation[engine][t]["total"] = 0           # number of empty ground-truth squares for puzzles where engine executed solution move
            evaluation[engine][t]["lowest"] = 1         # lowest saliency value out of all false positive squares
            evaluation[engine][t]["highest"] = 0        # highest saliency value out of all false positive squares
            evaluation[engine][t]["mean"] = 0           # mean saliency value out of all false positive squares
            evaluation[engine][t]["lowest True"] = 1    # lowest saliency value out of all true positive squares
            evaluation[engine][t]["highest True"] = 0   # highest saliency value out of all true positive squares
            evaluation[engine][t]["mean True"] = 0      # mean saliency value out of all true positive squares
            evaluation[engine][t]["F1"] = -1            # engine's last retrieved F1 mean
            evaluation[engine][t]["tP"] = -1            # engine's last retrieved number of true positive squares
            evaluation[engine][t]["fP"] = -1            # engine's last retrieved number of false positive squares
            evaluation[engine][t]["best F1 mean"] = -1  # engine's highest F1 mean
            evaluation[engine][t]["above dP 1"] = -1    # engine's above dP value for highest F1 mean
            evaluation[engine][t]["below dP 1"] = -1    # engine's below dP value for highest F1 mean
            evaluation[engine][t]["above K 1"] = -1     # engine's above K value for highest F1 mean
            evaluation[engine][t]["below K 1"] = -1     # engine's below K value for highest F1 mean
            evaluation[engine][t]["above dP 2"] = -1    # engine's above dP value for highest F1 mean
            evaluation[engine][t]["below dP 2"] = -1    # engine's below dP value for highest F1 mean
            evaluation[engine][t]["above K 2"] = -1     # engine's above K value for highest F1 mean
            evaluation[engine][t]["below K 2"] = -1     # engine's below K value for highest F1 mean
            evaluation[engine][t]["best tP"] = -1       # engine's number of true positive squares for highest F1 mean
            evaluation[engine][t]["best fP"] = -1       # engine's number of false positive squares for highest F1 mean
            evaluation[engine][t]["engines F1_tP"] = -1 # engine's number of true positive squares for overall highest F1 mean over all engines
            evaluation[engine][t]["engines F1_tP"] = -1 # engine's number of false positive squares for overall highest F1 mean over all engines

            i = 0
            # parse all available square data below threshold from output file into dictionary
            while i < len(output[engine][t]):
                if output[engine][t][i].startswith("puzzle") and len(output[engine][t][i]) < 15:
                    puzzleNr = output[engine][t][i].replace("\n", "")
                    evaluation[engine][t]["answer"][puzzleNr] = dict()
                    board = chess.Board(database[int(puzzleNr.replace("puzzle",""))-1]["fen"])
                elif output[engine][t][i].startswith("perturbing square = "):
                    sq = output[engine][t][i].replace("perturbing square = ", "")
                    sq = sq.replace("\n", "")
                elif output[engine][t][i].startswith("saliency for this square with player's pawn: "):
                    sal1 = re.findall(r'\d+(?:\.\d+)?', output[engine][t][i])[0]
                    dP1 = re.findall(r'\d+(?:\.\d+)?', output[engine][t][i])[1]
                    k1 = re.findall(r'\d+(?:\.\d+)?', output[engine][t][i])[2]
                elif output[engine][t][i].startswith("saliency for this square with opponent's pawn: "):
                    sal2 = re.findall(r'\d+(?:\.\d+)?', output[engine][t][i])[0]
                    dP2 = re.findall(r'\d+(?:\.\d+)?', output[engine][t][i])[1]
                    k2 = re.findall(r'\d+(?:\.\d+)?', output[engine][t][i])[2]
                elif output[engine][t][i].startswith("saliency calculated as max from pawn perturbation for this empty square: ") and board.piece_type_at(chess.SQUARES[chess.parse_square(sq)]) is None:  # empty square
                    evaluation[engine][t]["total"] += 1
                    evaluation[engine][t]["answer"][puzzleNr][sq] = dict()
                    evaluation[engine][t]["answer"][puzzleNr][sq]['saliency1'] = sal1
                    evaluation[engine][t]["answer"][puzzleNr][sq]['dP1'] = dP1
                    evaluation[engine][t]["answer"][puzzleNr][sq]['K1'] = k1
                    evaluation[engine][t]["answer"][puzzleNr][sq]['saliency2'] = sal2
                    evaluation[engine][t]["answer"][puzzleNr][sq]['dP2'] = dP2
                    evaluation[engine][t]["answer"][puzzleNr][sq]['K2'] = k2
                    evaluation[engine][t]["answer"][puzzleNr][sq]['saliency'] = re.findall(r'\d+(?:\.\d+)?', output[engine][t][i])[0]
                i += 1
            #print(evaluation[engine][t])
    maxF1 = dict()
    above_dP_1 = dict()
    below_dP_1 = dict()
    above_K_1 = dict()
    below_K_1 = dict()
    above_dP_2 = dict()
    below_dP_2 = dict()
    above_K_2 = dict()
    below_K_2 = dict()
    for t in ["positional", "tactical"]:
        print("calculate best threshold for each engine on {} puzzles:".format(t))
        maxF1[t] = 0
        for abovedP1 in numpy.arange(0, 1, 0.1):  # count K and dP appearances above values
            abovedP1 = round(abovedP1, 2)
            for abovedP2 in numpy.arange(0, 1, 0.1):
                abovedP2 = round(abovedP2, 2)
                for aboveK1 in numpy.arange(0, 1, 0.1):
                    aboveK1 = round(aboveK1, 2)
                    for aboveK2 in numpy.arange(0, 1, 0.1):
                        aboveK2 = round(aboveK2, 2)
                        for belowdP1 in numpy.arange(1, 0, -0.1):
                            belowdP1 = round(belowdP1, 2)
                            if abovedP1 >= belowdP1:
                                break
                            for belowdP2 in numpy.arange(1, 0, -0.1):
                                belowdP2 = round(belowdP2, 2)
                                if abovedP2 >= belowdP2:
                                    break
                                for belowK1 in numpy.arange(1, 0, -0.1):
                                    belowK1 = round(belowK1, 2)
                                    if aboveK1 >= belowK1:
                                        break
                                    for belowK2 in numpy.arange(1, 0, -0.1):
                                        belowK2 = round(belowK2, 2)
                                        if aboveK2 >= belowK2:
                                            break

                                        print("check improvement for all engines with player perturbation dp {} - {}, K {} - {} and opponent perturbation dp {} - {}, K {} - {}".format(abovedP1, belowdP1, aboveK1, belowK1, abovedP2, belowdP2, aboveK2, belowK2))
                                        meanF1 = 0
                                        count = 0
                                        for engine in folders:
                                            count += 1
                                            tP = 0
                                            fP = 0
                                            for puzzleNr in evaluation[engine][t]["answer"]:  # calculate precision over all squares below threshold

                                                for sq in evaluation[engine][t]["answer"][puzzleNr]:
                                                    if float(evaluation[engine][t]["answer"][puzzleNr][sq]['dP1']) >= float(abovedP1) and float(evaluation[engine][t]["answer"][puzzleNr][sq]['dP1']) <= float(belowdP1) \
                                                            and float(evaluation[engine][t]["answer"][puzzleNr][sq]['K1']) >= float(aboveK1) and float(evaluation[engine][t]["answer"][puzzleNr][sq]['K1']) <= float(belowK1) and \
                                                            float(evaluation[engine][t]["answer"][puzzleNr][sq]['dP2']) >= float(abovedP2) and float(evaluation[engine][t]["answer"][puzzleNr][sq]['dP2']) <= float(belowdP2) \
                                                            and float(evaluation[engine][t]["answer"][puzzleNr][sq]['K2']) >= float(aboveK2) and float(evaluation[engine][t]["answer"][puzzleNr][sq]['K2']) <= float(belowK2):
                                                        fP += 1
                                                        for gT in emptyGT[t][int(puzzleNr.replace("puzzle", ""))-1]:
                                                            if sq == gT:
                                                                tP += 1
                                                                fP -= 1
                                                                break
                                            if tP > 0:
                                                pr = tP / (tP + fP)
                                                re = tP / evaluation[engine][t]["total"]
                                                if (pr + re) > 0:
                                                    f1 = round(2 * ((pr * re) / (pr + re)) * 100, 2)
                                                    evaluation[engine][t]["F1"] = f1
                                                    evaluation[engine][t]["tP"] = tP
                                                    evaluation[engine][t]["fP"] = fP
                                                    if f1 > evaluation[engine][t]["best F1 mean"]:
                                                        evaluation[engine][t]["best F1 mean"] = f1
                                                        evaluation[engine][t]["above dP 1"] = abovedP1
                                                        evaluation[engine][t]["below dP 1"] = belowdP1
                                                        evaluation[engine][t]["above K 1"] = aboveK1
                                                        evaluation[engine][t]["below K 1"] = belowK1
                                                        evaluation[engine][t]["above dP 2"] = abovedP2
                                                        evaluation[engine][t]["below dP 2"] = belowdP2
                                                        evaluation[engine][t]["above K 2"] = aboveK2
                                                        evaluation[engine][t]["below K 2"] = belowK2
                                                        evaluation[engine][t]["best tP"] = tP
                                                        evaluation[engine][t]["best fP"] = fP
                                                    meanF1 += f1
                                                    print( "   {}: F1: {} % (true positive: {} ({} %), false positive: {})".format(engine, f1, tP, round(tP /evaluation[engine][t]["total"] * 100,2), fP))

                                        mean = round(meanF1 / count, 3)
                                        if mean > maxF1[t]:  # new best F1 mean over all engines
                                            maxF1[t] = mean
                                            above_dP_1[t] = abovedP1
                                            below_dP_1[t] = belowdP1
                                            above_K_1[t] = aboveK1
                                            below_K_1[t] = belowK1
                                            above_dP_2[t] = abovedP2
                                            below_dP_2[t] = belowdP2
                                            above_K_2[t] = aboveK2
                                            below_K_2[t] = belowK2
                                            for engine in folders:
                                                evaluation[engine][t]["engines F1_tP"] = evaluation[engine][t]["tP"]
                                                evaluation[engine][t]["engines F1_fP"] = evaluation[engine][t]["fP"]

    for t in ["positional", "tactical"]:
        print("-----------------------------------------------------------------------")
        print(t)
        for engine in folders:
            print("best F1 mean for engine {}:{} F1: {} %, precision: {} %, recall: {} % (true positive: {}, false positive: {}), player perturbation (dp {} - {}, K {} - {}), opponent perturbation (dp {} - {}, K {} - {})".format(
                    engine, " " * (11 - len(engine)), evaluation[engine][t]["best F1 mean"],
                    round(evaluation[engine][t]["best tP"] / (
                                evaluation[engine][t]["best tP"] + evaluation[engine][t]["best fP"]) * 100, 2),
                    round(evaluation[engine][t]["best tP"] / evaluation[engine][t]["total"] * 100, 2),
                    evaluation[engine][t]["best tP"], evaluation[engine][t]["best fP"], evaluation[engine][t]["above dP 1"],
                    evaluation[engine][t]["below dP 1"], evaluation[engine][t]["above K 1"], evaluation[engine][t]["below K 1"], evaluation[engine][t]["above dP 2"],
                    evaluation[engine][t]["below dP 2"], evaluation[engine][t]["above K 2"], evaluation[engine][t]["below K 2"]))

        print("-----------------------------------------------------------------------")
        print("best F1 mean for all engines with {} %: ".format(maxF1[t]))
        print("player perturbation: dP between {} and {}, K between {} and {}, opponent perturbation: dP between {} and {}, K between {} and {}".format(above_dP_1[t], below_dP_1[t], above_K_1[t], below_K_1[t], above_dP_2[t], below_dP_2[t], above_K_2[t], below_K_2[t]))
        for engine in folders:
            pr = round(evaluation[engine][t]["engines F1_tP"] / (
                        evaluation[engine][t]["engines F1_tP"] + evaluation[engine][t]["engines F1_fP"]) * 100, 2)
            re = round(evaluation[engine][t]["engines F1_tP"] / evaluation[engine][t]["total"] * 100, 2)
            f1 = round(2 * ((pr * re) / (pr + re)), 2)
            print("   {}:{} F1: {} %, precision: {} %, recall: {} % (true positive: {}, false positive: {})".format(engine,  " " * ( 11 - len(engine)), "%.2f" % f1, "%.2f" % pr, "%.2f" % re, evaluation[engine][t]["engines F1_tP"], evaluation[engine][t][ "engines F1_fP"]))


def bratkoKopec_calculateImprovements_TopEmptySquares(directory="evaluation/bratko-kopec/updated/"):
    """ Analyses the best amount of marked empty squares based on our bratko-kopec ground-truth.

    :param directory: path where evaluation of engines is written
    """

    import re
    folders = list(filter(lambda x: os.path.isdir(os.path.join(directory, x)), os.listdir(directory)))
    engineDir = directory
    if len(folders) == 0:
        engineDir, file = os.path.split(directory)
        engineDir += '/'
        folders.append(file)
    print(folders)
    data = dict()
    output = dict()
    evaluation = {f: {} for f in folders}
    emptyGT = dict()

    for t in ["positional", "tactical"]:
        with open("{}/{}/bratko-kopec.json".format("chess_saliency_databases/bratko-kopec", t),
                  "r") as jsonFile:  # open positional or tactical test solution
            database = json.load(jsonFile)

        emptyGT[t] = []
        i = 0
        for puzzle in database:
            board = chess.Board(puzzle["fen"])
            x = []
            for gT in puzzle["groundTruth"]:
                if board.piece_type_at(chess.SQUARES[chess.parse_square(gT)]) is None:  # empty square
                    x.append(gT)
            emptyGT[t].append(x)
            i += 1
        #print(emptyGT)

    for engine in folders:
        evaluation[engine] = dict()
        evaluation[engine]["top"] = dict()
        evaluation[engine]["gT"] = 0
        data[engine] = dict()
        output[engine] = dict()
        evaluation[engine]["puzzles"] = 0
        for t in ["positional", "tactical"]:
            with open("{}/{}/bratko-kopec.json".format("chess_saliency_databases/bratko-kopec", t), "r") as jsonFile:  # open positional or tactical test solution
                database = json.load(jsonFile)

            path = engineDir + engine + "/" + t + "/" +"data.json"
            with open(path, "r") as jsonFile:
                data[engine][t] = json.load(jsonFile)
            path = engineDir + engine + "/" + t + "/" + "output.txt"
            with open(path, "r") as file:
                output[engine][t] = file.readlines()

            evaluation[engine][t] = dict()
            evaluation[engine][t]["answer"] = dict()     # engine's square data

            i = 0
            # parse all available square data below threshold from output file into dictionary
            while i < len(output[engine][t]):
                if output[engine][t][i].startswith("puzzle") and len(output[engine][t][i]) < 15:
                    puzzleNr = output[engine][t][i].replace("\n", "")
                    if data[engine][t][puzzleNr]["move"] in database[int(puzzleNr.replace("puzzle",""))-1]["best move"]:
                        evaluation[engine][t]["answer"][puzzleNr] = dict()
                        board = chess.Board(database[int(puzzleNr.replace("puzzle",""))-1]["fen"])
                        evaluation[engine]["puzzles"] += 1
                    else:
                        i += 1
                        while output[engine][t][i].startswith("puzzle") is False:
                            i += 1
                            if i >= len(output[engine][t]):
                                break
                        i -= 1
                elif output[engine][t][i].startswith("perturbing square = "):
                    sq = output[engine][t][i].replace("perturbing square = ", "")
                    sq = sq.replace("\n", "")
                elif output[engine][t][i].startswith("saliency for this square with player's pawn: "):
                    sal1 = re.findall(r'\d+(?:\.\d+)?', output[engine][t][i])[0]
                    dP1 = re.findall(r'\d+(?:\.\d+)?', output[engine][t][i])[1]
                    k1 = re.findall(r'\d+(?:\.\d+)?', output[engine][t][i])[2]
                    if output[engine][t][i].__contains__("e-"):
                        x = re.search(sal1, output[engine][t][i]).end()
                        if output[engine][t][i][x] == "e":
                            x += 2
                            y = ""
                            while output[engine][t][i][x].isdigit():
                                if int(output[engine][t][i][x]) == 0:
                                    if len(y) > 0:
                                        y += output[engine][t][i][x]
                                else:
                                    y += output[engine][t][i][x]
                                x += 1
                            if len(y) > 0:
                                sal1 = float(sal1) * float(1 / (pow(10, int(y))))
                        x = re.search(dP1, output[engine][t][i]).end()
                        if output[engine][t][i][x] == "e":
                            x += 2
                            y = ""
                            while output[engine][t][i][x].isdigit():
                                if int(output[engine][t][i][x]) == 0:
                                    if len(y) > 0:
                                        y += output[engine][t][i][x]
                                else:
                                    y += output[engine][t][i][x]
                                x += 1
                            if len(y) > 0:
                                dP1 = float(dP1) * float(1 / (pow(10, int(y))))
                        x = re.search(k1, output[engine][t][i]).end()
                        if output[engine][t][i][x] == "e":
                            x += 2
                            y = ""
                            while output[engine][t][i][x].isdigit():
                                if int(output[engine][t][i][x]) == 0:
                                    if len(y) > 0:
                                        y += output[engine][t][i][x]
                                else:
                                    y += output[engine][t][i][x]
                                x += 1
                            if len(y) > 0:
                                k1 = float(k1) * float(1 / (pow(10, int(y))))
                elif output[engine][t][i].startswith("saliency for this square with opponent's pawn: "):
                    sal2 = re.findall(r'\d+(?:\.\d+)?', output[engine][t][i])[0]
                    dP2 = re.findall(r'\d+(?:\.\d+)?', output[engine][t][i])[1]
                    k2 = re.findall(r'\d+(?:\.\d+)?', output[engine][t][i])[2]
                    if output[engine][t][i].__contains__("e-"):
                        x = re.search(sal2, output[engine][t][i]).end()
                        if output[engine][t][i][x] == "e":
                            x += 2
                            y = ""
                            while output[engine][t][i][x].isdigit():
                                if int(output[engine][t][i][x]) == 0:
                                    if len(y) > 0:
                                        y += output[engine][t][i][x]
                                else:
                                    y += output[engine][t][i][x]
                                x += 1
                            if len(y) > 0:
                                sal2 = float(sal2) * float(1 / (pow(10, int(y))))
                        x = re.search(dP2, output[engine][t][i]).end()
                        if output[engine][t][i][x] == "e":
                            x += 2
                            y = ""
                            while output[engine][t][i][x].isdigit():
                                if int(output[engine][t][i][x]) == 0:
                                    if len(y) > 0:
                                        y += output[engine][t][i][x]
                                else:
                                    y += output[engine][t][i][x]
                                x += 1
                            if len(y) > 0:
                                dP2 = float(dP2) * float(1 / (pow(10, int(y))))
                        x = re.search(k2, output[engine][t][i]).end()
                        if output[engine][t][i][x] == "e":
                            x += 2
                            y = ""
                            while output[engine][t][i][x].isdigit():
                                if int(output[engine][t][i][x]) == 0:
                                    if len(y) > 0:
                                        y += output[engine][t][i][x]
                                else:
                                    y += output[engine][t][i][x]
                                x += 1
                            if len(y) > 0:
                                k2 = float(k2) * float(1 / (pow(10, int(y))))
                elif output[engine][t][i].startswith("saliency calculated as max from pawn perturbation for this empty square: ") and board.piece_type_at(chess.SQUARES[chess.parse_square(sq)]) is None:  # empty square
                    evaluation[engine][t]["answer"][puzzleNr][sq] = dict()
                    evaluation[engine][t]["answer"][puzzleNr][sq]['saliency'] = float(max([float(sal1), float(sal2)]))
                    evaluation[engine][t][puzzleNr] = dict()
                    evaluation[engine][t][puzzleNr]["top"] = dict()
                    evaluation[engine][t][puzzleNr]["best"] = 0
                    evaluation[engine][t][puzzleNr]["pr"] = dict()
                    evaluation[engine][t][puzzleNr]["re"] = dict()
                    evaluation[engine][t][puzzleNr]["f1"] = dict()
                    evaluation[engine][t]["squares"] = 0

                i += 1

            for puzzleNr in evaluation[engine][t]["answer"].keys():
                print(puzzleNr, " ground-truth: ",len(emptyGT[t][int(puzzleNr.replace("puzzle",""))-1]))
                print(evaluation[engine][t]["answer"][puzzleNr])
                evaluation[engine]["gT"] += len(emptyGT[t][int(puzzleNr.replace("puzzle",""))-1])
                sortedKeys = sorted(evaluation[engine][t]["answer"][puzzleNr], key=lambda x: evaluation[engine][t]["answer"][puzzleNr][x]["saliency"], reverse=True)
                print(sortedKeys)

                evaluation[engine][t][puzzleNr]["top"][0] = 0
                evaluation[engine][t][puzzleNr]["pr"][0] = 10
                evaluation[engine][t][puzzleNr]["re"][0] = 0
                evaluation[engine][t][puzzleNr]["f1"][0] = 0
                i = 1
                while i < len(sortedKeys):
                    evaluation[engine][t][puzzleNr]["top"][i] = 0
                    evaluation[engine][t][puzzleNr]["pr"][i] = 0
                    evaluation[engine][t][puzzleNr]["re"][i] = 0
                    evaluation[engine][t][puzzleNr]["f1"][i] = 0
                    for k in sortedKeys[0:i]:
                        if k in emptyGT[t][int(puzzleNr.replace("puzzle",""))-1]:
                            evaluation[engine][t][puzzleNr]["top"][i] += 1
                            if i not in evaluation[engine]["top"]:
                                evaluation[engine]["top"][i] = 0
                            evaluation[engine]["top"][i] += 1
                            break
                    if evaluation[engine][t][puzzleNr]["top"][i] > 0 and i > 0:
                        #print(i,": ", evaluation[engine][t][puzzleNr]["top"][i])
                        evaluation[engine][t][puzzleNr]["pr"][i] = round(evaluation[engine][t][puzzleNr]["top"][i]/i * 100, 2)
                        #print("pr: " , evaluation[engine][t][puzzleNr]["pr"][i])
                        evaluation[engine][t][puzzleNr]["re"][i] = round(evaluation[engine][t][puzzleNr]["top"][i] / len(emptyGT[t][int(puzzleNr.replace("puzzle",""))-1]) * 100, 2)
                        #print("re: ",evaluation[engine][t][puzzleNr]["re"][i])
                        evaluation[engine][t][puzzleNr]["f1"][i] = round(2* evaluation[engine][t][puzzleNr]["pr"][i] * evaluation[engine][t][puzzleNr]["re"][i] / (evaluation[engine][t][puzzleNr]["pr"][i] + evaluation[engine][t][puzzleNr]["re"][i]), 2)
                        #print(evaluation[engine][t][puzzleNr]["f1"][i])
                        #print(evaluation[engine][t][puzzleNr]["f1"][evaluation[engine][t][puzzleNr]["best"]])
                        if evaluation[engine][t][puzzleNr]["f1"][i] > evaluation[engine][t][puzzleNr]["f1"][evaluation[engine][t][puzzleNr]["best"]]:
                            evaluation[engine][t][puzzleNr]["best"] = i
                    i+= 1
                print(evaluation[engine][t][puzzleNr]["top"])

    for t in ["positional", "tactical"]:
        print("-----------------------------------------------------------------------")
        print(t)
        for engine in folders:
            x = 0
            for puzzleNr in evaluation[engine][t]["answer"].keys():
                #print(evaluation[engine][t][puzzleNr]["top"])
                if len(emptyGT[t][int(puzzleNr.replace("puzzle",""))-1]) > 0:
                    x += 1
                    if puzzleNr in evaluation[engine][t].keys() and "best" in evaluation[engine][t][puzzleNr].keys():
                        i = evaluation[engine][t][puzzleNr]["best"]
                        evaluation[engine][t]["squares"] += i
                        print("best F1 mean for engine {} on {}: mark first {} empty squares with F1: {} %, precision: {} %, recall: {} % (true positive: {}, false positive: {})".format(
                            engine, puzzleNr, i, evaluation[engine][t][puzzleNr]["f1"][i],
                            evaluation[engine][t][puzzleNr]["pr"][i], evaluation[engine][t][puzzleNr]["re"][i],
                            evaluation[engine][t][puzzleNr]["top"][i], i - evaluation[engine][t][puzzleNr]["top"][i]))
            evaluation[engine][t]["squares"] = evaluation[engine][t]["squares"]/x

    for t in ["positional", "tactical"]:
        print("-----------------------------------------------------------------------")
        print(t)
        for engine in folders:
            print("engine {} should mark {} empty squares for maximum F1 score".format(engine, int(evaluation[engine][t]["squares"])))

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


def bratkoKopec_markEmptySquares(num):
    """ Changes updated bratko-kopec directory saliency maps with user specified number of empty squares.

    :param num: number of empty squares
    """

    for engine in list(filter(lambda x: os.path.isdir(os.path.join("evaluation/bratko-kopec/updated/", x)), os.listdir("evaluation/bratko-kopec/updated/"))):
        for t in ["positional", "tactical"]:
            evaluation = dict()
            with open("{}/{}/bratko-kopec.json".format("chess_saliency_databases/bratko-kopec", t),
                      "r") as jsonFile:  # open positional or tactical test solution
                database = json.load(jsonFile)

            path = "evaluation/bratko-kopec/updated/" + engine + "/" + t + "/" + "data.json"
            with open(path, "r") as jsonFile:
                data = json.load(jsonFile)
            path = "evaluation/bratko-kopec/updated/" + engine + "/" + t + "/" + "output.txt"
            with open(path, "r") as file:
                output = file.readlines()

            evaluation = dict()
            evaluation["answer"] = dict()  # engine's square data
            indices = dict()

            i = 0
            # parse all available square data below threshold from output file into dictionary
            while i < len(output):
                if output[i].startswith("puzzle") and len(output[i]) < 15:
                    puzzleNr = output[i].replace("\n", "")
                    evaluation["answer"][puzzleNr] = dict()
                    beforeP = None
                    board = chess.Board(database[int(puzzleNr.replace("puzzle", "")) - 1]["fen"])
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
                            path = "evaluation/bratko-kopec/updated/" + engine + "/" + t + "/" + "output.txt"
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
                elif output[i].startswith("inserted pawn makes king\'s move illegal"):
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
                    move = chess.Move(chess.SQUARES[chess.parse_square(data[puzzleNr]['move'][0:2])],
                                      chess.SQUARES[chess.parse_square(data[puzzleNr]['move'][2:4])])
                    if board.piece_type_at(chess.SQUARES[move.from_square]) == chess.KING:  # be careful as opponents pawn can make original move illegal
                        if str(data[puzzleNr]['move']) in afterP2dict:
                            saliency2, dP2, k2, qmax2, gapBefore2, gapAfter2, text = sarfa_saliency.computeSaliencyUsingSarfa(str(data[puzzleNr]["move"]), beforePdict, afterP2dict, None)
                            output.pop(i)
                            output.insert(i, "{}saliency for this square with opponent\'s pawn: \'saliency\': {}, \'dP\': {}, \'K\': {} \n".format(text, saliency2, dP2, k2))
                            with open("evaluation/bratko-kopec/updated/" + engine  + "/" + t + "/output.txt", "w") as f:
                                for line in output:
                                    f.write(line)
                            with open("evaluation/bratko-kopec/updated/" + engine  + "/" + t +  "/output.txt", "r") as file:
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
                    with open("evaluation/bratko-kopec/updated/" + engine + "/" + t + "/" + "output.txt", "r") as f:
                        lines = f.readlines()
                    z = 0
                    while z < y-x:
                        lines.pop(x)
                        z += 1
                    lines.insert(x, newtext)
                    with open("evaluation/bratko-kopec/updated/" + engine + "/" + t + "/" + "output.txt", "w") as f:
                        for line in lines:
                            f.write(line)
                    with open("evaluation/bratko-kopec/updated/" + engine + "/" + t + "/" + "output.txt", "r") as file:
                        output = file.readlines()
                i += 1
            #print(evaluation)

            path = "evaluation/bratko-kopec/updated/" + engine + "/" + t + "/" + "data.json"
            with open(path, 'r') as jsonFile:
                data = json.load(jsonFile)
            for puzzleNr in evaluation["answer"]:  # iterate puzzles

                print(puzzleNr)

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

                board = chess.Board(data[puzzleNr]["fen"])
                move = chess.Move(answer[data[puzzleNr]['move'][0:2]]['int'], answer[data[puzzleNr]['move'][2:4]]['int'])

                sortedKeys = sorted(evaluation["answer"][puzzleNr], key=lambda x: evaluation["answer"][puzzleNr][x]["saliency"], reverse=True)

                above = data[puzzleNr]["sorted saliencies"]["above threshold"]
                below = data[puzzleNr]["sorted saliencies"]["below threshold"]
                insertAbove = dict()
                insertBelow = dict()

                moveSquares = get_moves_squares(board, move.from_square, move.to_square)

                i = 0
                th = (100 / 256)
                print(sortedKeys)

                aboveKeys = list(above.keys())
                for sq in aboveKeys:
                    if (board.piece_type_at(chess.SQUARES[chess.parse_square(sq)]) is None and sq not in moveSquares) or (board.piece_type_at(chess.SQUARES[chess.parse_square(sq)]) is None and num == 0):
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

                board = chess.Board(data[puzzleNr]['fen'])

                for sq in above:
                    if sq in below:
                        del below[sq]
                for sq in answer:
                    if sq in above:
                        answer[sq]['saliency'] = float(above[sq])
                    elif sq in below:
                        answer[sq]['saliency'] = float(below[sq])

                import chess_saliency_chessSpecific as specific_saliency
                specific_saliency.generate_heatmap(board=board, bestmove=move, evaluation=answer,
                                                   directory="evaluation/bratko-kopec/updated/" + engine + "/" + t,
                                                   puzzle=puzzleNr, file=None)
                print("{}, {} ({}) updated".format(engine, puzzleNr, t))

                with open("evaluation/bratko-kopec/updated/" + engine + "/" + t + "/" + "output.txt", "r") as f:
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
                                with open("evaluation/bratko-kopec/updated/" + engine + "/" + t + "/" + "output.txt", "w") as f:
                                    for line in lines:
                                        f.write(line)
                        with open("evaluation/bratko-kopec/updated/" + engine + "/" + t + "/" + "output.txt", "r") as f:
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
                                with open("evaluation/bratko-kopec/updated/" + engine + "/" + t + "/" + "output.txt", "w") as f:
                                    for line in lines:
                                        f.write(line)

                data[puzzleNr] = {
                    "fen": data[puzzleNr]['fen'],
                    "move": data[puzzleNr]["move"],
                    "sorted saliencies": {
                        "above threshold": above,
                        "below threshold": below
                    }
                }

                path = "evaluation/bratko-kopec/updated/" + engine + "/" + t + "/" + "data.json"
                with open(path, "w") as jsonFile:
                    json.dump(data, jsonFile, indent=4)


async def rerunBratkoKopec_qValues(directory="evaluation/bratko-kopec/updated/"):
    """Rerun all bratko-kopec puzzles in the given directory based on existing q_values (output.txt).

    :param directory: path where different engines' outputs are stored
    """

    folders = list(filter(lambda x: os.path.isdir(os.path.join(directory, x)), os.listdir(directory)))
    print(folders)
    if len(folders) == 0:
        directory, file = os.path.split(directory)
        directory += '/'
        folders.append(file)

    jsonDatabaseFolder = "chess_saliency_databases/bratko-kopec"
    jsonFiles = list(filter(lambda x: os.path.isdir(os.path.join(jsonDatabaseFolder, x)), os.listdir(jsonDatabaseFolder)))
    if len(jsonFiles) == 0:
        jsonDatabaseFolder, engine = os.path.split(jsonDatabaseFolder)
        jsonFiles = [engine]

    for engine in folders: # iterate engines
        print(engine)

        for jsonF in jsonFiles: # positional or tactical folder
            print(jsonF)
            with open("{}/{}/bratko-kopec.json".format(jsonDatabaseFolder, jsonF), "r") as jsonFile: # open positional or tactical test solution
                database = json.load(jsonFile)

            path = "{}/{}/{}/data.json".format(directory, engine, jsonF) # open engine's evaluation
            with open(path, "r") as jsonFile:
                data = json.load(jsonFile)

            path = directory + "/" + engine + "/" + jsonF + "/" + "output.txt"
            with open(path, "r") as file:
                output = file.readlines()

            outputF = open(directory + "/" + engine + "/" + jsonF + "/" + "output.txt", "a")  # append mode
            outputF.truncate(0)

            backupIndex = 0
            nr = 1

            for puzzle in database: # iterate puzzles
                puzzleNr = "puzzle" + str(nr)
                print(puzzleNr)
                board = chess.Board(puzzle["fen"])

                i = backupIndex
                qValuesEngine = dict()

                while output[i].startswith(puzzleNr) is False:
                    i += 1

                while i < len(output):
                    if output[i].startswith(puzzleNr) and len(output[i]) < 15:
                        beforeP = None
                        board = chess.Board(data[puzzleNr]["fen"])
                        stop = int(puzzleNr.replace("puzzle", ""))
                    elif output[i].startswith("puzzle{}".format(stop+1)) and len(output[i]) < 15:
                        backupIndex = i
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
                original_move = data[puzzleNr]["move"]
                ss = original_move[0:2]
                ds = original_move[2:4]
                move = chess.Move(chess.SQUARES[chess.parse_square(ss)], chess.SQUARES[chess.parse_square(ds)])
                outputF.write("{}\n".format(puzzleNr))
                aboveThreshold, belowThreshold = await givenQValues_computeSaliency(board, move, data[puzzleNr]["fen"], beforePdict, qValuesEngine, directory + "/" + engine + "/" + jsonF, puzzleNr, outputF)

                path = directory + engine + "/" + jsonF + "/" + "data.json"

                data[puzzleNr]["sorted saliencies"]["above threshold"] = aboveThreshold
                data[puzzleNr]["sorted saliencies"]["below threshold"] = belowThreshold

                with open(path, "w") as jsonFile:
                    json.dump(data, jsonFile, indent=4)
                nr += 1
