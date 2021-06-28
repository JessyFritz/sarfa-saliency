import json
import os
import chess
import numpy


def evaluateBratkoKopec(directory="evaluation/bratko-kopec/original"):
    """
    evaluates the bratko-kopec test & assigns scores to engines
    Input :
        directory : path where different engines' outputs are stored
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
                first = -100
                second = -100
                third = -100
                fourth = -100
                j = 0
                while j < len(moves):
                    if qValues[moves[j]] >= first:
                        first = qValues[moves[j]]
                    elif qValues[moves[j]] >= second:
                        if second == -100 and j > 3:
                            moves = moves[0:j]
                            break
                        second = qValues[moves[j]]
                    elif qValues[moves[j]] >= third:
                        if third == -100 and j > 3:
                            moves = moves[0:j]
                            break
                        third = qValues[moves[j]]
                    elif qValues[moves[j]] >= fourth:
                        if fourth == -100 and j > 3:
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
    print("Engines sorted by Total Score:")
    sortedKeys = sorted(evaluation, key=lambda x: evaluation[x]["score"], reverse=True) # sort engines according to their score
    rank = 1
    for key in sortedKeys:
        print("{}. {}:{} {}, wrong move: {}, precision: {} %, recall: {} %".format(rank, key, " "*(11-len(key)), "%.2f" %(evaluation[key]["score"]), (evaluation[key]["wrong move positional"]+evaluation[key]["wrong move tactical"]), evaluation[key]["precision"], evaluation[key]["recall"]))
        rank += 1
    print('------------------------------------------')

    print("Engines sorted by Score Average:")
    sortedKeys = sorted(evaluation,
                        key=lambda x: (evaluation[x]["positional score"] + evaluation[x]["tactical score"]) / 2,
                        reverse=True)  # sort engines according to their average score
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
        for key in sortedKeys:
            print("{}. {}:{} {} score: {}, wrong {} move: {}, salient: {}, {} F1: {} %, {} precision: {} %, {} recall: {} %".format(rank, key, " "*(11-len(key)), t, "%.2f" %(evaluation[key]["{} score".format(t)]), t, evaluation[key]["wrong move {}".format(t)], evaluation[key]["salient {}".format(t)], t, round(2*evaluation[key]["precision {}".format(t)]*evaluation[key]["recall {}".format(t)]/(evaluation[key]["precision {}".format(t)]+evaluation[key]["recall {}".format(t)]),2), t, "%.2f" %(evaluation[key]["precision {}".format(t)]), t, evaluation[key]["recall {}".format(t)]))
            rank += 1
            mF += round(2 * evaluation[key]["precision {}".format(t)] * evaluation[key]["recall {}".format(t)] / (evaluation[key]["precision {}".format(t)] + evaluation[key]["recall {}".format(t)]), 2)
            mP += evaluation[key]["precision {}".format(t)]
            mR += evaluation[key]["recall {}".format(t)]
        print("F1 mean: {} %, precision mean: {} %, recall mean: {} %".format(round(mF/len(folders),2), round(mP/len(folders),2), round(mR/len(folders),2)))
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


def convertToPosition(directory="evaluation/bratko-kopec/original/output.txt"):
    """
    sorts the engines' evaluation based on the puzzle order they appear in http://www.kopecchess.com/bktest/Bktest.html
    Input :
        directory : path where different engines' output file is stored
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
    """
    evaluates the bratko-kopec puzzles for a single engine with the original and updated code
    Input :
        directory1 : path where first engine's outputs are stored
        directory2 : path where second engine's outputs are stored
        subset : give subset of puzzles if not all should be evaluated
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
    """
    searches for improvements over all engines' ground-truths empty squares
    Input :
        directory : path where evaluation of engines is written
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
                    evaluation[engine][t]["answer"][puzzleNr][sq]['K'] = max(evaluation[engine][t]["answer"][puzzleNr][sq]['dP1'], evaluation[engine][t]["answer"][puzzleNr][sq]['dP2'])
                    evaluation[engine][t]["answer"][puzzleNr][sq]['dP'] = max(evaluation[engine][t]["answer"][puzzleNr][sq]['K1'], evaluation[engine][t]["answer"][puzzleNr][sq]['K2'])
                i += 1
            #print(evaluation[engine][t])
    maxF1 = dict()
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
                                                    if float(evaluation[engine][t]["answer"][puzzleNr][sq]['dP']) >= float(abovedP1) and float(evaluation[engine][t]["answer"][puzzleNr][sq]['dP']) <= float(belowdP1) \
                                                            and float(evaluation[engine][t]["answer"][puzzleNr][sq]['K']) >= float(aboveK1) and float(evaluation[engine][t]["answer"][puzzleNr][sq]['K']) <= float(belowK1) and \
                                                            float(evaluation[engine][t]["answer"][puzzleNr][sq]['dP']) >= float(abovedP2) and float(evaluation[engine][t]["answer"][puzzleNr][sq]['dP']) <= float(belowdP2) \
                                                            and float(evaluation[engine][t]["answer"][puzzleNr][sq]['K']) >= float(aboveK2) and float(evaluation[engine][t]["answer"][puzzleNr][sq]['K']) <= float(belowK2):
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
                                            above_dP_1 = abovedP1
                                            below_dP_1 = belowdP1
                                            above_K_1 = aboveK1
                                            below_K_1 = belowK1
                                            above_dP_2 = abovedP2
                                            below_dP_2 = belowdP2
                                            above_K_2 = aboveK2
                                            below_K_2 = belowK2
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
        print("player perturbation: dP between {} and {}, K between {} and {}, opponent perturbation: dP between {} and {}, K between {} and {}".format(above_dP_1, below_dP_1, above_K_1, below_K_1, above_dP_2, below_dP_2, above_K_2, below_K_2))
        for engine in folders:
            pr = round(evaluation[engine][t]["engines F1_tP"] / (
                        evaluation[engine][t]["engines F1_tP"] + evaluation[engine][t]["engines F1_fP"]) * 100, 2)
            re = round(evaluation[engine][t]["engines F1_tP"] / evaluation[engine][t]["total"] * 100, 2)
            f1 = round(2 * ((pr * re) / (pr + re)), 2)
            print("   {}:{} F1: {} %, precision: {} %, recall: {} % (true positive: {}, false positive: {})".format(engine,  " " * ( 11 - len(engine)), "%.2f" % f1, "%.2f" % pr, "%.2f" % re, evaluation[engine][t]["engines F1_tP"], evaluation[engine][t][ "engines F1_fP"]))
