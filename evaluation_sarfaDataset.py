import json
import os
import re
import chess
import numpy
import sarfa_saliency
from basicFunctions import get_moves_squares
from chess_saliency_chessSpecific import givenQValues_computeSaliency

datasetBestMoves = ["c3d5","f5h6","g3g8","b6d5","c4f4","d5e7","c3d5","f3h5","d5d6","e4c4","f6h8","h3h7","b2g7","a1a2","b1f5","g5g6","f5f8","f6e8","d6e7","d4d7","e4h7","g1g6","f3e5","e2e7","b6g6","e1e6","c1c6","e5d6","c1g5","c6b7","g1g7","f5e6","g4f6","b7b8","d1d7","d3h7","g3g7","e1c1","d2h6","b2a1","b6c7","d1e1","d1d7","d2d4","e4f6","h5h6","d4e4","e4e6","h5h6","e7e5","f1f5","a1b2","h4e4","d6f5","c1h6","f3g5","b3c4","e5e6","g4g6","f3d5","d7e7","h4h5","d3d4","d1d5","f4e6","e2d4","f1f8","h5h6","f4f7","g5g6","g1g6","e3g4","c7e7","c3b5","d5g8","h6h7","d2c2","c4e6","f1f7","a7a8","e5g6","f1f2","b3f7","b3d1","d6d7","d5f6","f3f8","b1g6","d5f7","e1e6","e4e5","d1d7","b3d4","h3h4","d3h7","f7g7","e5g7","d6f8","g7g6","c4c5","c6c8","b7b4"]


def groundTruthEvaluation(directory="evaluation/original/", subset=None):
    """ Evaluates the SARFA database's puzzles in the given directory based on the ground-truth in the chess_saliency_databases folder.

    :param directory: path where different engine outputs are stored
    :param subset: path where different engine outputs are stored
    """

    folders = list(filter(lambda x: os.path.isdir(os.path.join(directory, x)), os.listdir(directory)))
    print(folders)
    print(folders)
    if len(folders) == 0:
        directory, file = os.path.split(directory)
        directory += '/'
        folders.append(file)
    with open('chess_saliency_databases/chess-saliency-dataset-v1.json', "r") as jsonFile:
        database = json.load(jsonFile)
    database = database['puzzles']
    data = dict()

    evaluation = {f: {} for f in folders}
    print(evaluation)
    highestSal = 0
    highestSalEngine = ""

    for engine in folders:
        path = directory+engine+"/"+"data.json"
        with open(path, "r") as jsonFile:
            data[engine] = json.load(jsonFile)
        evaluation[engine]["salient"] = 0        # number of salient marked squares for all puzzles or for given subset
        evaluation[engine]["missing"] = 0        # number of missing salient (false negative) squares for all puzzles or for given subset
        evaluation[engine]["precision"] = 0      # precision over all puzzles or over given subset
        evaluation[engine]["recall"] = 0         # recall over all puzzles or over given subset
        evaluation[engine]["wrong move"] = 0     # times that engine executed wrong move

    nr = 1
    total = 0
    allMiss = dict()
    rightMoves = []
    for puzzle in database: # iterate puzzles
        puzzleNr = "puzzle" + str(nr)
        if subset is None: # iterate all puzzles
            print("{} - {} squares salient".format(puzzleNr, len(puzzle["saliencyGroundTruth"])))
            total += len(puzzle["saliencyGroundTruth"])
            rightMoves.append(puzzleNr)

            count = 1
            for engine in data: # iterate engines
                with open("{}{}/output.txt".format(directory, engine), "r") as file:
                    outputF = file.readlines()
                idx = 0

                while outputF[idx].startswith(puzzleNr) is False:
                    idx += 1
                idx += 2
                if outputF[idx].startswith("assigned new best move to engine") and puzzleNr in rightMoves:
                    rightMoves.remove(puzzleNr)

                sal = len(data[engine][puzzleNr]["sorted saliencies"]["above threshold"])    # puzzle's salient squares
                if sal > highestSal:
                    highestSal = sal
                    highestSalEngine = "{} {}".format(engine, puzzleNr)
                evaluation[engine]["salient"] += sal
                miss = 0
                if data[engine][puzzleNr]["missing ground truth"]["squares"] != 0:
                    miss = len(data[engine][puzzleNr]["missing ground truth"]["squares"])    # puzzle's missing ground truth
                    if count < len(data):
                        if puzzleNr in allMiss:
                            temp = allMiss[puzzleNr]
                            new = set(temp) & set(data[engine][puzzleNr]["missing ground truth"]["squares"])
                            if len(new) != 0:
                                allMiss[puzzleNr] = new
                            else:
                                del allMiss[puzzleNr]
                        else:
                            allMiss[puzzleNr] = data[engine][puzzleNr]["missing ground truth"]["squares"]
                elif puzzleNr in allMiss:
                        del allMiss[puzzleNr]
                evaluation[engine]["missing"] += miss
                move = data[engine][puzzleNr]["best move"][0:4]
                if move != datasetBestMoves[nr-1]:
                    print("wrong move from engine {} at {}: {} is not {}".format(engine, puzzleNr, move, datasetBestMoves[nr-1]))
                    evaluation[engine]["wrong move"] += 1
                    if puzzleNr in rightMoves:
                        rightMoves.remove(puzzleNr)
                pr = 0
                re = 0
                if sal > 0:
                    pr = (len(puzzle["saliencyGroundTruth"]) - miss) / sal * 100                                  # puzzle's precision
                    re = (len(puzzle["saliencyGroundTruth"]) - miss) / len(puzzle["saliencyGroundTruth"]) * 100   # puzzle's recall
                print("   {}: salient: {}, missing: {}, precision: {} %, recall: {} %".format(engine, sal, miss, round(pr, 2), round(re, 2)))
                if miss > 0:
                    print("      above threshold: ")
                    for m in data[engine][puzzleNr]["sorted saliencies"]["above threshold"]:
                        if m in data[engine][puzzleNr]["saliency ground truth"]:
                            print("         {}: {}".format(m, data[engine][puzzleNr]["sorted saliencies"]["above threshold"][m]))
                    print("      below threshold: ")
                    for m in data[engine][puzzleNr]["sorted saliencies"]["below threshold"]:
                        if m in data[engine][puzzleNr]["saliency ground truth"]:
                            print("         {}: {}".format(m, data[engine][puzzleNr]["sorted saliencies"]["below threshold"][m]))
                evaluation[engine]["precision"] += pr
                evaluation[engine]["recall"] += re
                count += 1
            nr += 1
        else: # iterate only puzzles from subset
            for x in subset:
                if puzzleNr == x:
                    print("{} - {} squares salient".format(puzzleNr, len(puzzle["saliencyGroundTruth"])))
                    total += len(puzzle["saliencyGroundTruth"])
                    for engine in data:
                        sal = len(data[engine][puzzleNr]["sorted saliencies"]["above threshold"])    # puzzle's salient squares
                        if sal > highestSal:
                            highestSal = sal
                            highestSalEngine = "{} {}".format(engine, puzzleNr)
                        evaluation[engine]["salient"] += sal
                        miss = 0
                        if data[engine][puzzleNr]["missing ground truth"]["squares"] != 0:
                            miss = len(data[engine][puzzleNr]["missing ground truth"]["squares"])    # puzzle's missing ground truth
                        elif puzzleNr in allMiss:
                            del allMiss[puzzleNr]
                        evaluation[engine]["missing"] += miss
                        pr = 0
                        re = 0
                        if sal > 0:
                            pr = (len(puzzle["saliencyGroundTruth"]) - miss) / sal * 100                                    # puzzle's precision
                            re = (len(puzzle["saliencyGroundTruth"]) - miss) / len(puzzle["saliencyGroundTruth"]) * 100     # puzzle's recall
                        print("   {}: salient: {}, missing: {}, precision: {} %, recall: {} %".format(engine, sal, miss, round(pr, 2), round(re, 2)))
                        if miss > 0:
                            print("      above threshold: ")
                            for m in data[engine][puzzleNr]["sorted saliencies"]["above threshold"]:
                                if m in data[engine][puzzleNr]["saliency ground truth"]:
                                    print("         {}: {}".format(m, data[engine][puzzleNr]["sorted saliencies"]["above threshold"][m]))
                            print("      below threshold: ")
                            for m in data[engine][puzzleNr]["sorted saliencies"]["below threshold"]:
                                if m in data[engine][puzzleNr]["saliency ground truth"]:
                                    print("         {}: {}".format(m, data[engine][puzzleNr]["sorted saliencies"]["below threshold"][m]))
                        evaluation[engine]["precision"] += pr
                        evaluation[engine]["recall"] += re
            nr += 1
    length = 102
    for engine in data:
        if subset is None:
            evaluation[engine]["precision"] = round(evaluation[engine]["precision"]/(nr-1), 2)    # calculate mean of all precision values
            evaluation[engine]["recall"] = round(evaluation[engine]["recall"] / (nr - 1), 2)      # calculate mean of all recall values
        else:
            evaluation[engine]["precision"] = round(evaluation[engine]["precision"]/len(subset), 2)
            evaluation[engine]["recall"] = round(evaluation[engine]["recall"] / len(subset), 2)
            length = len(subset)
    print("highest number of marked squares: {}, {}".format(highestSalEngine, highestSal))
    print('------------------------------------------')
    print("In total {} squares from {} puzzles should be salient".format(total, length))
    print("Evaluation:")
    sortedKeys = sorted(evaluation, key=lambda x: 2*((evaluation[x]["precision"]*evaluation[x]["recall"])/(evaluation[x]["precision"]+evaluation[x]["recall"])), reverse=True) # sort engines according to their precision
    rank = 1
    mF = 0
    mP = 0
    mR = 0
    for key in sortedKeys:
        mF += 2*(evaluation[key]["precision"]*evaluation[key]["recall"])/(evaluation[key]["precision"]+evaluation[key]["recall"])
        mP += evaluation[key]["precision"]
        mR += evaluation[key]["recall"]
        print("{}. {}:{} F1: {} %, {}".format(rank, key, " "*(11-len(key)), "%.2f" %(round(2*((evaluation[key]["precision"]*evaluation[key]["recall"])/(evaluation[key]["precision"]+evaluation[key]["recall"])),2)), evaluation[key]))
        rank += 1
    print("F1 mean: {} %, precision mean: {} %, recall mean: {} %".format(round(mF / len(folders), 2), round(mP / len(folders), 2), round(mR / len(folders), 2)))

    if subset is None:
        print("Squares missed by all engines: ", allMiss)
        #print("Puzzles with right best move by all engines: ", rightMoves)
        #print("   total: {}".fomat(len(rightMoves)))
        return rightMoves
    return None


def singleEngine_groundTruthEvaluation(directory1="evaluation/original/stockfish", directory2="evaluation/updated/stockfish", subset=False):
    """ Evaluates the SARFA database's puzzles for a single engine with the original and updated SARFA implementation.

    :param directory1: path where first engine's outputs are stored
    :param directory2: path where second engine's outputs are stored
    :param subset: give subset of puzzles if not all should be evaluated
    """

    folders = []
    di, engineName = os.path.split(directory1)
    _, name = os.path.split(di)
    folders.append(name)
    di, engineName = os.path.split(directory2)
    _, name = os.path.split(di)
    folders.append(name)
    with open('chess_saliency_databases/chess-saliency-dataset-v1.json', "r") as jsonFile:
        database = json.load(jsonFile)
    database = database['puzzles']
    data = dict()

    evaluation = {f: {} for f in folders}
    print(evaluation)

    path = directory1+"/"+"data.json"
    with open(path, "r") as jsonFile:
        data[folders[0]] = json.load(jsonFile)
    evaluation[folders[0]]["salient"] = 0
    evaluation[folders[0]]["missing"] = 0
    evaluation[folders[0]]["precision"] = 0
    evaluation[folders[0]]["recall"] = 0
    path = directory2 + "/" + "data.json"
    with open(path, "r") as jsonFile:
        data[folders[1]] = json.load(jsonFile)
    evaluation[folders[1]]["salient"] = 0
    evaluation[folders[1]]["missing"] = 0
    evaluation[folders[1]]["precision"] = 0
    evaluation[folders[1]]["recall"] = 0

    if type(subset) == bool and subset is True:
        subset = []
        nr = 1
        with open("{}/output.txt".format(directory1), "r") as file:
            output1 = file.readlines()
        with open("{}/output.txt".format(directory2), "r") as file:
            output2 = file.readlines()
        i1 = 0
        i2 = 0
        while nr < 103:
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

    nr = 1
    total = 0
    for puzzle in database:
        puzzleNr = "puzzle" + str(nr)
        if subset is False:
            print("{} - {} squares salient".format(puzzleNr, len(puzzle["saliencyGroundTruth"])))
            total += len(puzzle["saliencyGroundTruth"])

            for f in data:
                sal = len(data[f][puzzleNr]["sorted saliencies"]["above threshold"])    # puzzle's salient squares
                evaluation[f]["salient"] += sal
                miss = 0

                for square in puzzle["saliencyGroundTruth"]:
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
                    pr = (len(puzzle["saliencyGroundTruth"]) - miss) / sal * 100                                    # puzzle's precision
                    re = (len(puzzle["saliencyGroundTruth"]) - miss) / len(puzzle["saliencyGroundTruth"]) * 100     # puzzle's recall
                print("   {}: salient: {}, missing: {}, precision: {} %, recall: {} %".format(f, sal, miss, round(pr, 2), round(re, 2)))
                evaluation[f]["precision"] += pr
                evaluation[f]["recall"] += re
        else:
            for x in subset:
                if puzzleNr == x:
                    print("{} - {} squares salient".format(puzzleNr, len(puzzle["saliencyGroundTruth"])))
                    total += len(puzzle["saliencyGroundTruth"])

                    for f in data:
                        sal = len(data[f][puzzleNr]["sorted saliencies"]["above threshold"])    # puzzle's salient squares
                        evaluation[f]["salient"] += sal
                        miss = 0

                        for square in puzzle["saliencyGroundTruth"]:
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
                            pr = (len(puzzle["saliencyGroundTruth"]) - miss) / sal * 100                                    # puzzle's precision
                            re = (len(puzzle["saliencyGroundTruth"]) - miss) / len(puzzle["saliencyGroundTruth"]) * 100     # puzzle's recall
                        print("   {}: salient: {}, missing: {}, precision: {} %, recall: {} %".format(f, sal, miss, round(pr, 2), round(re, 2)))
                        evaluation[f]["precision"] += pr
                        evaluation[f]["recall"] += re

        nr += 1
    length = 102

    for f in data:
        if subset is False:
            evaluation[f]["precision"] = round(evaluation[f]["precision"]/(nr-1),2) #calculate mean of all precision values
            evaluation[f]["recall"] = round(evaluation[f]["recall"] /(nr-1), 2)     # calculate mean of all recall values
        else:
            length = len(subset)
            evaluation[f]["precision"] = round(evaluation[f]["precision"]/len(subset), 2)
            evaluation[f]["recall"] = round(evaluation[f]["recall"] / len(subset), 2)

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


def missingGroundTruth(directory="evaluation/original/stockfish", variable=None, criteria=None, symbol=">"):
    """ Prints given engine's missing ground truth into console.
    Optionally searches after a given variable and criteria in the missing ground-truth.

    :param directory: path where evaluation of engine is written
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

    with open(Outputpath, "r") as file:
        output = file.readlines()

    with open(dataPath, "r") as jsonFile:
        data = json.load(jsonFile)

    positive = 0
    miss = 0
    nr = 1
    sq = None
    for line in output:
        if line.startswith("puzzle"):
            nr = line.replace("\n","")
        elif line.startswith("perturbing square = "):
            sq = line.replace("perturbing square = ", "")[0:2]
        elif line.startswith("perturbed reward Q"):
            reward = line.split(", ")[0].split(":")[1]
        elif line.__contains__("saliency for this square"):
            sqData = {sq: line}
            if data[nr]["missing ground truth"]["squares"] != 0:
                i = 0
                while i < len(data[nr]["missing ground truth"]["squares"]):
                    if str(data[nr]["missing ground truth"]["squares"][i]) == str(sq):
                        print("{} {}".format(nr, sqData))
                        miss += 1
                        if variable is not None:
                            variables = str(sqData).split(',')
                            for x in variables:
                                if x.__contains__("\'{}\': ".format(variable)):
                                    value = x.replace("\'{}\': ".format(variable), "")
                            if "reward" in variable:
                                value = reward
                            if symbol == "<" and float(value) < criteria:
                                positive += 1
                            elif symbol == ">" and float(value) > criteria:
                                positive += 1
                        break
                    i += 1
    print("The engine still misses {} salient squares".format(miss))
    if variable is not None:
        print("applied {} {} {} to missing squares".format(variable,symbol,criteria))
        print("  true salient: {} out of {}".format(positive, miss))


def calculateImprovements_threshold(directory="evaluation/original/"):
    """ Searches for improvements over all engines' missing ground-truths.

    :param directory: path where evaluation of engines is written
    """

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

    for engine in folders:
        path = engineDir + engine + "/" + "data.json"
        with open(path, "r") as jsonFile:
            data[engine] = json.load(jsonFile)
        path = engineDir + engine + "/" + "output.txt"
        with open(path, "r") as file:
            output[engine] = file.readlines()

        evaluation[engine]["answer"] = dict()     # engine's square data
        evaluation[engine]["total"] = 0           # number of ground-truth squares for puzzles where engine executed solution move
        evaluation[engine]["best Th"] = 0         # engine's threshold for highest F1 measure
        evaluation[engine]["F1"] = 0              # engine's highest F1 measure
        evaluation[engine]["tP"] = 0              # engine's number of true positive squares for highest F1 measure
        evaluation[engine]["fP"] = 0              # engine's number of false positive squares for highest F1 measure

        i = 0
        # parse all available square data below threshold from output file into dictionary
        while i < len(output[engine]):
            if output[engine][i].startswith("puzzle") and len(output[engine][i]) < 15:
                puzzleNr = output[engine][i].replace("\n", "")
                evaluation[engine]["answer"][puzzleNr] = dict()
            elif output[engine][i].startswith("assigned new best move to engine"):
                while output[engine][i].startswith("saliency for this square = ") is False:
                    i += 1
            elif output[engine][i].startswith("perturbing square = "):
                sq = output[engine][i].replace("perturbing square = ", "")
                sq = sq.replace("\n", "")
            elif output[engine][i].startswith("saliency for this square = "):
                if sq in data[engine][puzzleNr]["saliency ground truth"]:
                    evaluation[engine]["total"] += 1
                variables = str(output[engine][i]).split(',')
                evaluation[engine]["answer"][puzzleNr][sq] = dict()
                for x in variables:
                    if x.__contains__("\'{}\': ".format('saliency')):
                        evaluation[engine]["answer"][puzzleNr][sq]['saliency'] = x.replace(
                            "\'{}\': ".format('saliency'), "")
                    elif x.__contains__("\'{}\': ".format('K')):
                        evaluation[engine]["answer"][puzzleNr][sq]['K'] = x.replace("\'{}\': ".format('K'), "")
                    elif x.__contains__("\'{}\': ".format('dP')):
                        evaluation[engine]["answer"][puzzleNr][sq]['dP'] = x.replace("\'{}\': ".format('dP'), "")
            i += 1
    print("calculate best threshold for each engine:")
    for engine in folders:
        print(engine)
        for th in numpy.arange(0.99, -0.05, -0.0001):
            th = round(th, 4)
            tP = 0
            fP = 0
            for puzzleNr in evaluation[engine]["answer"]:
                for sq in evaluation[engine]["answer"][puzzleNr]:
                    if float(evaluation[engine]["answer"][puzzleNr][sq]['saliency']) > float(th):
                        if sq in data[engine][puzzleNr]["saliency ground truth"]:
                            tP += 1
                        else:
                            fP += 1

            if tP > 0:
                pr = tP / (tP + fP)
                re = tP / evaluation[engine]["total"]
                if (pr + re) > 0:
                    f1 = round(2 * ((pr * re) / (pr + re)) * 100, 2)
                    if th == 0.3906:
                        print("   current th {} with F1: {} % (true positive: {}, false positive: {})".format(th, f1, tP, fP))
                    if th > 0.390625:
                        #print("   increasing {}'s threshold to {}: {} %".format(engine, th, f1))
                        if f1 > evaluation[engine]["F1"]:
                            evaluation[engine]["best Th"] = th
                            evaluation[engine]["F1"] = f1
                            evaluation[engine]["tP"] = tP
                            evaluation[engine]["fP"] = fP
                    else:
                        #print("   decreasing {}'s threshold to {}: {} %".format(engine, th, f1))
                        if f1 > evaluation[engine]["F1"]:
                            evaluation[engine]["best Th"] = th
                            evaluation[engine]["F1"] = f1
                            evaluation[engine]["tP"] = tP
                            evaluation[engine]["fP"] = fP
        print("   best threshold is {} with F1: {} % (true positive: {}, false positive: {})".format(evaluation[engine]["best Th"], evaluation[engine]["F1"], evaluation[engine]["tP"], evaluation[engine]["fP"]))


def calculateImprovements_positive(directory="evaluation/original/", feature=None):
    """ Calculates best occurrence (in precison and recall) of dP and K over the (true and false) positive class. Optional analysis over a given feature.

    :param directory: path where evaluation of engines is written
    :param feature: message from chess_saliency (f.e. "guards best move")
    """

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

    for engine in folders:
        print(engine)
        path = engineDir + engine + "/" + "data.json"
        with open(path, "r") as jsonFile:
            data[engine] = json.load(jsonFile)
        path = engineDir + engine + "/" + "output.txt"
        with open(path, "r") as file:
            output[engine] = file.readlines()

        evaluation[engine]["answer"] = dict()     # engine's square data
        evaluation[engine]["lowest"] = 1          # lowest saliency value out of all false positive squares
        evaluation[engine]["highest"] = 0         # highest saliency value out of all false positive squares
        evaluation[engine]["mean"] = 0            # mean saliency value out of all false positive squares
        evaluation[engine]["lowest True"] = 1     # lowest saliency value out of all true positive squares
        evaluation[engine]["highest True"] = 0    # highest saliency value out of all true positive squares
        evaluation[engine]["mean True"] = 0       # mean saliency value out of all true positive squares
        evaluation[engine]["total"] = 0           # number of currently true positive squares for puzzles where engine executed solution move
        evaluation[engine]["F1"] = -1             # engine's last retrieved F1 mean
        evaluation[engine]["tP"] = -1             # engine's last retrieved number of true positive squares
        evaluation[engine]["fP"] = -1             # engine's last retrieved number of false positive squares
        evaluation[engine]["best F1 mean"] = -1   # engine's highest F1 mean
        evaluation[engine]["above dP"] = -1       # engine's above dP value for highest F1 mean
        evaluation[engine]["below dP"] = -1       # engine's below dP value for highest F1 mean
        evaluation[engine]["above K"] = -1        # engine's above K value for highest F1 mean
        evaluation[engine]["below K"] = -1        # engine's below K value for highest F1 mean
        evaluation[engine]["best tP"] = -1        # engine's number of true positive squares for highest F1 mean
        evaluation[engine]["best fP"] = -1        # engine's number of false positive squares for highest F1 mean
        evaluation[engine]["engines F1_tP"] = -1  # engine's number of true positive squares for overall highest F1 mean over all engines
        evaluation[engine]["engines F1_tP"] = -1  # engine's number of false positive squares for overall highest F1 mean over all engines

        featureOccurrence = False
        i = 0
        last = "puzzle1"
        # parse all available square data below threshold from output file into dictionary
        while i < len(output[engine]):
            if output[engine][i].startswith("puzzle") and len(output[engine][i]) < 15:
                puzzleNr = output[engine][i].replace("\n", "")
                evaluation[engine]["answer"][puzzleNr] = dict()
                evaluation[engine]["answer"][puzzleNr]["above"] = dict()
                evaluation[engine]["answer"][puzzleNr]["below"] = dict()
            elif output[engine][i].startswith("assigned new best move to engine"):
                while output[engine][i].startswith("threshold:") is False:
                    i += 1
                    if i > len(output[engine][i]):
                        break
            elif output[engine][i].startswith("perturbing square = "):
                if featureOccurrence == True:
                    j = i
                    while output[engine][j].startswith("saliency for this square") is False:
                        j -= 1
                    if output[engine][j].startswith("saliency for this square") and sq in \
                            data[engine][last]["sorted saliencies"]["above threshold"] and (
                            feature is None or (feature is not None and featureOccurrence)):
                        if sq in data[engine][last]["saliency ground truth"]:
                            evaluation[engine]["total"] += 1
                        variables = str(output[engine][j]).split(',')
                        evaluation[engine]["answer"][last]["above"][sq] = dict()
                        for x in variables:
                            if x.__contains__("\'{}\': ".format('saliency')):
                                evaluation[engine]["answer"][last]["above"][sq]['saliency'] = x.replace("\'{}\': ".format('saliency'), "")
                            elif x.__contains__("\'{}\': ".format('K')):
                                evaluation[engine]["answer"][last]["above"][sq]['K'] = x.replace("\'{}\': ".format('K'), "")
                            elif x.__contains__("\'{}\': ".format('dP')):
                                evaluation[engine]["answer"][last]["above"][sq]['dP'] = x.replace("\'{}\': ".format('dP'), "")
                    elif output[engine][j].last("saliency for this square = ") and sq in \
                            data[engine][puzzleNr]["sorted saliencies"]["below threshold"] and (
                            feature is None or (feature is not None and featureOccurrence)):
                        variables = str(output[engine][j]).split(',')
                        evaluation[engine]["answer"][last]["below"][sq] = dict()
                        for x in variables:
                            if x.__contains__("\'{}\': ".format('saliency')):
                                evaluation[engine]["answer"][last]["below"][sq]['saliency'] = x.replace("\'{}\': ".format('saliency'), "")
                            elif x.__contains__("\'{}\': ".format('K')):
                                evaluation[engine]["answer"][last]["below"][sq]['K'] = x.replace("\'{}\': ".format('K'), "")
                            elif x.__contains__("\'{}\': ".format('dP')):
                                evaluation[engine]["answer"][last]["below"][sq]['dP'] = x.replace("\'{}\': ".format('dP'), "")
                sq = output[engine][i].replace("perturbing square = ", "")
                sq = sq.replace("\n", "")
                featureOccurrence = False
            elif feature is not None and output[engine][i].__contains__(feature):
                featureOccurrence = True
                last = puzzleNr
            elif output[engine][i].startswith("saliency for this square") and sq in data[engine][puzzleNr]["sorted saliencies"]["above threshold"] and (feature is None or (feature is not None and featureOccurrence)):
                if sq in data[engine][puzzleNr]["saliency ground truth"]:
                    evaluation[engine]["total"] += 1
                variables = str(output[engine][i]).split(',')
                evaluation[engine]["answer"][puzzleNr]["above"][sq] = dict()
                for x in variables:
                    if x.__contains__("\'{}\': ".format('saliency')):
                        evaluation[engine]["answer"][puzzleNr]["above"][sq]['saliency'] = x.replace("\'{}\': ".format('saliency'), "")
                    elif x.__contains__("\'{}\': ".format('K')):
                        evaluation[engine]["answer"][puzzleNr]["above"][sq]['K'] = x.replace("\'{}\': ".format('K'), "")
                    elif x.__contains__("\'{}\': ".format('dP')):
                        evaluation[engine]["answer"][puzzleNr]["above"][sq]['dP'] = x.replace("\'{}\': ".format('dP'), "")
                featureOccurrence = False
            elif output[engine][i].startswith("saliency for this square = ") and sq in data[engine][puzzleNr]["sorted saliencies"]["below threshold"] and (feature is None or (feature is not None and featureOccurrence)):
                print("here")
                variables = str(output[engine][i]).split(',')
                evaluation[engine]["answer"][puzzleNr]["below"][sq] = dict()
                for x in variables:
                    if x.__contains__("\'{}\': ".format('saliency')):
                        evaluation[engine]["answer"][puzzleNr]["below"][sq]['saliency'] = x.replace("\'{}\': ".format('saliency'), "")
                    elif x.__contains__("\'{}\': ".format('K')):
                        evaluation[engine]["answer"][puzzleNr]["below"][sq]['K'] = x.replace("\'{}\': ".format('K'), "")
                    elif x.__contains__("\'{}\': ".format('dP')):
                        evaluation[engine]["answer"][puzzleNr]["below"][sq]['dP'] = x.replace("\'{}\': ".format('dP'), "")
                featureOccurrence = False
            i += 1

        print(evaluation[engine])

        count_True = 0
        count_False = 0
        for puzzleNr in data[engine]:
            puzzle = data[engine][puzzleNr]
            for square in puzzle["sorted saliencies"]["above threshold"]:
                if square in data[engine][puzzleNr]["saliency ground truth"]:
                    evaluation[engine]["mean True"] +=  puzzle["sorted saliencies"]["above threshold"][square]
                    count_True += 1
                    if puzzle["sorted saliencies"]["above threshold"][square] > evaluation[engine]["highest True"]:
                        evaluation[engine]["highest True"] = puzzle["sorted saliencies"]["above threshold"][square]
                    if puzzle["sorted saliencies"]["above threshold"][square] < evaluation[engine]["lowest True"]:
                        evaluation[engine]["lowest True"] = puzzle["sorted saliencies"]["above threshold"][square]
                else:
                    evaluation[engine]["mean"] += puzzle["sorted saliencies"]["above threshold"][square]
                    count_False += 1
                    if puzzle["sorted saliencies"]["above threshold"][square] > evaluation[engine]["highest"]:
                        evaluation[engine]["highest"] = puzzle["sorted saliencies"]["above threshold"][square]
                    if puzzle["sorted saliencies"]["above threshold"][square] < evaluation[engine]["lowest"]:
                        evaluation[engine]["lowest"] = puzzle["sorted saliencies"]["above threshold"][square]
        if count_True > 0 and count_False > 0:
            evaluation[engine]["mean True"] = evaluation[engine]["mean True"] / count_True
            evaluation[engine]["mean"] = evaluation[engine]["mean"] / count_False

            print("True Positive Squares: mean: {}, lowest: {}, highest: {}".format(evaluation[engine]["mean True"], evaluation[engine]["lowest True"], evaluation[engine]["lowest True"]))
            print("False Positive Squares: mean: {}, lowest: {}, highest: {}".format(evaluation[engine]["mean"], evaluation[engine]["lowest"], evaluation[engine]["highest"]))
            if evaluation[engine]["lowest"] < evaluation[engine]["lowest True"]:
                print("lowest salient square is False Positive ({}), threshold can be increased to {} for improvement".format(evaluation[engine]["lowest"], evaluation[engine]["lowest True"]))
            print("-----------------------------------------------------------------------")

    maxF1 = 0
    above_dP = -1
    below_dP = -1
    above_K = -1
    below_K = -1
    for abovedP in numpy.arange(0, 1, 0.05): # count K and dP appearances above values
        abovedP = round(abovedP,2)
        for aboveK in numpy.arange(0, 1, 0.05):
            aboveK = round(aboveK, 2)
            for belowdP in numpy.arange(1, 0, -0.05):
                belowdP = round(belowdP, 2)
                if abovedP >= belowdP:
                    break
                for belowK in numpy.arange(1, 0, -0.05):
                    belowK = round(belowK, 2)
                    if aboveK >= belowK:
                        break

                    print("check improvement for all engines with dp {} - {}, K {} - {}".format(abovedP, belowdP, aboveK, belowK))
                    meanF1 = 0
                    count = 0
                    for engine in folders:
                        count += 1
                        tP = 0
                        fP = 0
                        for puzzleNr in evaluation[engine]["answer"]:  # calculate precision over all squares below threshold
                            for sq in evaluation[engine]["answer"][puzzleNr]["above"]:
                                if float(evaluation[engine]["answer"][puzzleNr]["above"][sq]['dP']) >= float(abovedP) and float(evaluation[engine]["answer"][puzzleNr]["above"][sq]['dP']) <= float(belowdP) and float(evaluation[engine]["answer"][puzzleNr]["above"][sq]['K']) >= float(aboveK) and float(evaluation[engine]["answer"][puzzleNr]["above"][sq]['K']) <= float(belowK):
                                    if sq in data[engine][puzzleNr]["saliency ground truth"]:
                                        tP += 1
                                    else:
                                        fP += 1
                        if tP > 0:
                            pr = tP / (tP + fP)
                            re = tP / evaluation[engine]["total"]
                            if (pr + re) > 0:
                                f1 = round(2 * ((pr * re) / (pr + re)) * 100, 2)
                                evaluation[engine]["F1"] = f1
                                evaluation[engine]["tP"] = tP
                                evaluation[engine]["fP"] = fP
                                if f1 > evaluation[engine]["best F1 mean"]:
                                    evaluation[engine]["best F1 mean"] = f1
                                    evaluation[engine]["above dP"] = abovedP
                                    evaluation[engine]["below dP"] = belowdP
                                    evaluation[engine]["above K"] = aboveK
                                    evaluation[engine]["below K"] = belowK
                                    evaluation[engine]["best tP"] = tP
                                    evaluation[engine]["best fP"] = fP
                                meanF1 += f1
                                print("   {}: F1: {} % (true positive: {} ({} %), false positive: {})".format(engine, f1,tP, round(tP / evaluation[engine]["total"] * 100, 2), fP))

                    mean = round(meanF1 / count, 3)
                    if mean > maxF1: # new best F1 mean over all engines
                        maxF1 = mean
                        above_dP = abovedP
                        below_dP = belowdP
                        above_K = aboveK
                        below_K = belowK
                        for engine in folders:
                            evaluation[engine]["engines F1_tP"] = evaluation[engine]["tP"]
                            evaluation[engine]["engines F1_fP"] = evaluation[engine]["fP"]

    print("-----------------------------------------------------------------------")
    if feature is not None:
        for engine in folders:
            if (evaluation[engine]["best tP"] + evaluation[engine]["best fP"]) > 0:
                print("best F1 mean for feature \"{}\" with engine {}:{} F1: {} %, precision: {} %, recall: {} % true positive: {}, false positive: {}), (dp {} - {}, K {} - {})".format(
                        feature, engine, " " * (11 - len(engine)), evaluation[engine]["best F1 mean"],
                        round(evaluation[engine]["best tP"] / (evaluation[engine]["best tP"] + evaluation[engine]["best fP"]) * 100, 2), round(evaluation[engine]["best tP"] / evaluation[engine]["total"] * 100, 2), evaluation[engine]["best tP"],
                        evaluation[engine]["best fP"], evaluation[engine]["above dP"], evaluation[engine]["below dP"],
                        evaluation[engine]["above K"], evaluation[engine]["below K"]))
            else:
                print("engine {} has no feature \"{}\"".format(engine, feature))
    else:
        for engine in folders:
            print("best F1 mean for engine {}:{} F1: {} %, precision: {} %, recall: {} % (true positive: {}, false positive: {}), (dp {} - {}, K {} - {})".format(engine, " " * (11 - len(engine)), evaluation[engine]["best F1 mean"],
                    round(evaluation[engine]["best tP"] / (evaluation[engine]["best tP"] + evaluation[engine]["best fP"]) * 100, 2), round(evaluation[engine]["best tP"] / evaluation[engine]["total"] * 100, 2),
                    evaluation[engine]["best tP"], evaluation[engine]["best fP"], evaluation[engine]["above dP"], evaluation[engine]["below dP"], evaluation[engine]["above K"], evaluation[engine]["below K"]))

        print("-----------------------------------------------------------------------")
        print("best F1 mean for all engines with {} %: ".format(maxF1))
        print("dP between {} and {}, K between {} and {}".format(above_dP, below_dP, above_K, below_K))
        for engine in folders:
            pr = round(evaluation[engine]["engines F1_tP"] / (evaluation[engine]["engines F1_tP"] + evaluation[engine]["engines F1_fP"]) * 100, 2)
            re = round(evaluation[engine]["engines F1_tP"] / evaluation[engine]["total"] * 100, 2)
            f1 = round(2 * ((pr * re) / (pr + re)), 2)
            print("   {}:{} F1: {} %, precision: {} %, recall: {} % (true positive: {}, false positive: {})".format(engine, " " * (11 - len(engine)), "%.2f" % f1, "%.2f" % pr, "%.2f" % re,
                evaluation[engine]["engines F1_tP"], evaluation[engine]["engines F1_fP"]))


def calculateImprovements_negative(directory="evaluation/original/", feature=None):
    """ Calculates best occurrence (in precison and recall) of dP and K over the (true and false) negative class. Optional analysis over a given feature.

    :param directory: path where evaluation of engines is written
    :param feature: message from chess_saliency (f.e. "guards best move")
    """

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

    for engine in folders:
        path = engineDir + engine + "/" + "data.json"
        with open(path, "r") as jsonFile:
            data[engine] = json.load(jsonFile)
        path = engineDir + engine + "/" + "output.txt"
        with open(path, "r") as file:
            output[engine] = file.readlines()

        evaluation[engine]["answer"] = dict()        # engine's square data
        evaluation[engine]["total"] = 0              # number of missing salient (false negative) squares for puzzles where engine executed solution move
        evaluation[engine]["F1"] = -1                # engine's last retrieved F1 mean
        evaluation[engine]["tP"] = -1                # engine's last retrieved number of true positive squares
        evaluation[engine]["fP"] = -1                # engine's last retrieved number of false positive squares
        evaluation[engine]["best F1 mean"] = -1      # engine's highest F1 mean
        evaluation[engine]["above dP"] = -1          # engine's above dP value for highest F1 mean
        evaluation[engine]["below dP"] = -1          # engine's below dP value for highest F1 mean
        evaluation[engine]["above K"] = -1           # engine's above K value for highest F1 mean
        evaluation[engine]["below K"] = -1           # engine's below K value for highest F1 mean
        evaluation[engine]["best tP"] = -1           # engine's number of true positive squares for highest F1 mean
        evaluation[engine]["best fP"] = -1           # engine's number of false positive squares for highest F1 mean
        evaluation[engine]["engines F1_tP"] = -1     # engine's number of true positive squares for overall highest F1 mean over all engines
        evaluation[engine]["engines F1_tP"] = -1     # engine's number of false positive squares for overall highest F1 mean over all engines

        featureOccurrence = False
        i = 0
        last = "puzzle1"
        # parse all available square data below threshold from output file into dictionary
        while i < len(output[engine]):
            if output[engine][i].startswith("puzzle") and len(output[engine][i]) < 15:
                puzzleNr = output[engine][i].replace("\n","")
                evaluation[engine]["total"] += len(data[engine][puzzleNr]["missing ground truth"]["details"])
                evaluation[engine]["answer"][puzzleNr] = dict()
            elif output[engine][i].startswith("assigned new best move to engine"):
                while output[engine][i].startswith("saliency for this square = ") is False:
                    i += 1
                evaluation[engine]["total"] -= len(data[engine][puzzleNr]["missing ground truth"]["details"])
            elif output[engine][i].startswith("perturbing square = "):
                if featureOccurrence == True:
                    j = i
                    while output[engine][j].startswith("saliency for this square") is False:
                        j -= 1
                    if output[engine][i].startswith("saliency for this square = ") and sq not in data[engine][last]["sorted saliencies"]["above threshold"] and (
                            feature is None or (feature is not None and featureOccurrence)):
                        variables = str(output[engine][i]).split(',')
                        evaluation[engine]["answer"][last][sq] = dict()
                        for x in variables:
                            if x.__contains__("\'{}\': ".format('saliency')):
                                evaluation[engine]["answer"][last][sq]['saliency'] = x.replace(
                                    "\'{}\': ".format('saliency'), "")
                            elif x.__contains__("\'{}\': ".format('K')):
                                evaluation[engine]["answer"][last][sq]['K'] = x.replace("\'{}\': ".format('K'), "")
                            elif x.__contains__("\'{}\': ".format('dP')):
                                evaluation[engine]["answer"][last][sq]['dP'] = x.replace("\'{}\': ".format('dP'),"")
                sq = output[engine][i].replace("perturbing square = ","")
                sq = sq.replace("\n","")
                featureOccurrence = False
            elif feature is not None and output[engine][i].__contains__(feature):
                featureOccurrence = True
                last = puzzleNr
            elif output[engine][i].startswith("saliency for this square = ") and sq not in data[engine][puzzleNr]["sorted saliencies"]["above threshold"] and (feature is None or (feature is not None and featureOccurrence is False)):
                variables = str(output[engine][i]).split(',')
                evaluation[engine]["answer"][puzzleNr][sq] = dict()
                for x in variables:
                    if x.__contains__("\'{}\': ".format('saliency')):
                        evaluation[engine]["answer"][puzzleNr][sq]['saliency'] = x.replace("\'{}\': ".format('saliency'), "")
                    elif x.__contains__("\'{}\': ".format('K')):
                        evaluation[engine]["answer"][puzzleNr][sq]['K'] = x.replace("\'{}\': ".format('K'), "")
                    elif x.__contains__("\'{}\': ".format('dP')):
                        evaluation[engine]["answer"][puzzleNr][sq]['dP'] = x.replace("\'{}\': ".format('dP'), "")
            i += 1

    maxF1 = 0
    above_dP = -1
    below_dP = -1
    above_K = -1
    below_K = -1
    for abovedP in numpy.arange(0, 1, 0.05): # count K and dP appearances above values
        abovedP = round(abovedP,2)
        for aboveK in numpy.arange(0, 1, 0.05):
            aboveK = round(aboveK, 2)
            for belowdP in numpy.arange(1, 0, -0.05):
                belowdP = round(belowdP, 2)
                if abovedP >= belowdP:
                    break
                for belowK in numpy.arange(1, 0, -0.05):
                    belowK = round(belowK, 2)
                    if aboveK >= belowK:
                        break

                    print("check improvement for all engines with dp {} - {}, K {} - {}".format(abovedP, belowdP, aboveK, belowK))
                    evaluation, mean = checkImprovementForOtherEngines(directory, evaluation, data, belowdP,abovedP, belowK, aboveK)

                    if mean > maxF1: # new best F1 mean over all engines
                        maxF1 = mean
                        above_dP = abovedP
                        below_dP = belowdP
                        above_K = aboveK
                        below_K = belowK
                        for engine in folders:
                            evaluation[engine]["engines F1_tP"] = evaluation[engine]["tP"]
                            evaluation[engine]["engines F1_fP"] = evaluation[engine]["fP"]

    print("-----------------------------------------------------------------------")
    if feature is not None:
        for engine in folders:
            print("best F1 mean for feature \"{}\" with engine {}:{} F1: {} %, precision: {} %, recall: {} %, (true positive: {}, false positive: {}), (dp {} - {}, K {} - {})".format(
                    feature, engine, " " * (11 - len(engine)), evaluation[engine]["best F1 mean"], round(evaluation[engine]["best tP"]/(evaluation[engine]["best tP"] + evaluation[engine]["best fP"])*100,2),
                    round(evaluation[engine]["best tP"] / evaluation[engine]["total"] * 100, 2), evaluation[engine]["best tP"], evaluation[engine]["best fP"], evaluation[engine]["above dP"], evaluation[engine]["below dP"],
                    evaluation[engine]["above K"], evaluation[engine]["below K"]))
    else:
        # get the overall best improvement
        for engine in folders:
            print("best F1 mean for engine {}:{} F1: {} %, precision: {} %, recall: {} %, (true positive: {}, false positive: {}), (dp {} - {}, K {} - {})".format(engine, " "*(11-len(engine)),
                    evaluation[engine]["best F1 mean"],round(evaluation[engine]["best tP"]/(evaluation[engine]["best tP"] + evaluation[engine]["best fP"])*100,2),round(evaluation[engine]["best tP"] / evaluation[engine]["total"] * 100, 2),
                    evaluation[engine]["best tP"],evaluation[engine]["best fP"],evaluation[engine]["above dP"],evaluation[engine]["below dP"],evaluation[engine]["above K"],evaluation[engine]["below K"]))
        print("-----------------------------------------------------------------------")
        print("best F1 mean for all engines with {} %: ".format(maxF1))
        print("dP between {} and {}, K between {} and {}".format(above_dP,below_dP,above_K,below_K))
        for engine in folders:
            pr = round(evaluation[engine]["engines F1_tP"]/(evaluation[engine]["engines F1_tP"] + evaluation[engine]["engines F1_fP"])*100,2)
            re = round(evaluation[engine]["engines F1_tP"]/evaluation[engine]["total"]*100,2)
            f1 = round(2 * ((pr * re) / (pr + re)), 2)
            print("   {}:{} F1: {} %, precision: {} %, recall: {} %, (true positive: {}, false positive: {})".format(engine, " " * (11-len(engine)), "%.2f" % f1, "%.2f" % pr, "%.2f" % re, evaluation[engine]["engines F1_tP"], evaluation[engine]["engines F1_fP"]))


def checkImprovementForOtherEngines(directory, evaluation, data, below_dP=1, above_dP=0, below_K=1, above_K=0):
    """ Tries an given improvement proposal for all engines.

    :param directory: path where evaluation of engine is written
    :param evaluation: dictionary containing all squares
    :param data: dictionary containing all engines' data files
    :param below_dP: improved dP below this value
    :param above_dP: improved dP above this value
    :param below_K: improved K below this value
    :param above_K: improved K above this value
    """

    folders = list(filter(lambda x: os.path.isdir(os.path.join(directory, x)), os.listdir(directory)))
    if len(folders) == 0:
        _, file = os.path.split(directory)
        folders.append(file)
    meanF1 = 0
    count = 0
    for engine in folders:
        count += 1
        tP = 0
        fP = 0
        for puzzleNr in evaluation[engine]["answer"]:  # calculate precision over all squares below threshold
            for sq in evaluation[engine]["answer"][puzzleNr]:
                if float(evaluation[engine]["answer"][puzzleNr][sq]['dP']) >= float(above_dP) and float(evaluation[engine]["answer"][puzzleNr][sq]['dP']) <= float(below_dP) and float(evaluation[engine]["answer"][puzzleNr][sq]['K']) >= float(above_K) and float(evaluation[engine]["answer"][puzzleNr][sq]['K']) <= float(below_K):
                    if "squares" in data[engine][puzzleNr]["missing ground truth"] and sq in data[engine][puzzleNr]["missing ground truth"]["details"]:
                        tP += 1
                    else:
                        fP += 1
        if tP > 0:
            pr = tP / (tP + fP)
            re = tP / evaluation[engine]["total"]
            if (pr + re) > 0:
                f1 = round(2 * ((pr * re) / (pr + re)) *100,2)
                evaluation[engine]["F1"] = f1
                evaluation[engine]["tP"] = tP
                evaluation[engine]["fP"] = fP
                if f1 > evaluation[engine]["best F1 mean"]:
                    evaluation[engine]["best F1 mean"] = f1
                    evaluation[engine]["above dP"] = above_dP
                    evaluation[engine]["below dP"] = below_dP
                    evaluation[engine]["above K"] = above_K
                    evaluation[engine]["below K"] = below_K
                    evaluation[engine]["best tP"] = tP
                    evaluation[engine]["best fP"] = fP
                meanF1 += f1
                print("   {}: F1: {} % (true positive: {} ({} %), false positive: {})".format(engine, f1, tP, round(tP/evaluation[engine]["total"]*100,2), fP))

    return evaluation, round(meanF1/count,3)


def markEmptySquares(num):
    """ Changes updated SARFA directory saliency maps with user specified number of empty squares.

    :param num: number of empty squares
    """

    dirPath = "evaluation/updated"
    for engine in list(filter(lambda x: os.path.isdir(os.path.join(dirPath, x)), os.listdir(dirPath))):
        evaluation = dict()

        path = dirPath + "/" + engine + "/" + "data.json"
        with open(path, "r") as jsonFile:
            data = json.load(jsonFile)
        path = dirPath + "/" + engine + "/" + "output.txt"
        with open(path, "r") as file:
            output = file.readlines()

        evaluation = dict()
        evaluation["answer"] = dict()  # engine's square data
        indices = dict()

        print(engine)

        i = 0
        # parse all available square data below threshold from output file into dictionary
        while i < len(output):
            if output[i].startswith("************"):
                puzzleNr = output[i-1].replace("\n", "")
                evaluation["answer"][puzzleNr] = dict()
                board = chess.Board(data[puzzleNr]["fen"])
            elif output[i].startswith("perturbing square = "):
                sq = output[i].replace("perturbing square = ", "")
                sq = sq.replace("\n", "")
            elif num == 0 and output[i].startswith("square is part of original move and must remain empty"):
                evaluation["answer"][puzzleNr][sq] = dict()
                evaluation["answer"][puzzleNr][sq]['saliency'] = 0
                evaluation["answer"][puzzleNr][sq]['dP'] = 0
                evaluation["answer"][puzzleNr][sq]['K'] = 0
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
            elif output[i].startswith("saliency for this square with opponent's pawn:"):
                sal2 = re.findall(r'\d+(?:\.\d+)?', output[i])[0]
                if len(re.findall(r'\d+(?:\.\d+)?', output[i])) < 3:
                    dP2 = 0
                    k2 = 0
                else:
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
                    if float(max([float(sal1), float(sal2)])) == float(sal1):
                        evaluation["answer"][puzzleNr][sq]['dP'] = float(dP1)
                        evaluation["answer"][puzzleNr][sq]['K'] = float(k1)
                    else:
                        evaluation["answer"][puzzleNr][sq]['dP'] = float(dP2)
                        evaluation["answer"][puzzleNr][sq]['K'] = float(k2)
                    evaluation[puzzleNr] = dict()
                    evaluation[puzzleNr]["top"] = dict()
                    evaluation[puzzleNr]["best"] = 0
                    evaluation[puzzleNr]["pr"] = dict()
                    evaluation[puzzleNr]["re"] = dict()
                    evaluation[puzzleNr]["f1"] = dict()
                    if output[i].startswith("saliency calculated as max from pawn perturbation for this empty square: ") is False:
                        output.insert(i, "saliency calculated as max from pawn perturbation for this empty square: {}\n".format(
                            evaluation["answer"][puzzleNr][sq]['saliency']))
                        path = dirPath + "/" + engine + "/output.txt"
                        with open(path, "w") as f:
                            output = "".join(output)
                            f.write(output)
                        with open(path, "r") as file:
                            output = file.readlines()
                        i += 1
            elif output[i].startswith("considered salient:"):
                sortedKeys = sorted(evaluation["answer"][puzzleNr], key=lambda x: evaluation["answer"][puzzleNr][x]['saliency'], reverse=True)
                newtext = ""
                for squarestring in sortedKeys:
                    #print(evaluation["answer"][puzzleNr][squarestring])
                    if float(evaluation["answer"][puzzleNr][squarestring]['saliency']) > 0:
                        newtext += ("{}: max: {}, colour player: {}, colour opponent: {}\n".format(squarestring, round(float(evaluation["answer"][puzzleNr][squarestring]['saliency']), 10), round(float(
                        evaluation["answer"][puzzleNr][squarestring]['saliency1']), 10), round(float(evaluation["answer"][puzzleNr][squarestring]['saliency2']), 10)))
                    #print(newtext)
                x = i + 1
                y = i + 1
                indices[puzzleNr] = x
                while output[y].startswith("displaying top empty squares:") is False:
                    y += 1
                with open(dirPath + "/"  +  engine + "/output.txt", "r") as f:
                    lines = f.readlines()
                z = 0
                while z < y-x:
                    lines.pop(x)
                    z += 1
                lines.insert(x, newtext)
                with open(dirPath + "/" + engine + "/output.txt", "w") as f:
                    for line in lines:
                        f.write(line)
                with open(dirPath + "/"  +  engine + "/output.txt", "r") as file:
                    output = file.readlines()
            i += 1
        print(evaluation)

        path = dirPath + "/"  +   engine + "/data.json"
        with open(path, 'r') as jsonFile:
            data = json.load(jsonFile)
        for puzzleNr in evaluation["answer"]:  # iterate puzzles

            print(evaluation["answer"][puzzleNr])

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
            move = chess.Move(answer[data[puzzleNr]['best move'][0:2]]['int'], answer[data[puzzleNr]['best move'][2:4]]['int'])

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
                if (board.piece_type_at(chess.SQUARES[chess.parse_square(sq)]) is None and sq not in moveSquares) or (
                        board.piece_type_at(chess.SQUARES[chess.parse_square(sq)]) is None and num == 0):
                    del above[sq]

            if num > 0:
                for sq in moveSquares:
                    insertAbove[sq] = th

            for sq in sortedKeys:
                if float(evaluation["answer"][puzzleNr][sq]["saliency"]) > 0:
                    if i < num and sq not in moveSquares and board.piece_type_at(
                            chess.SQUARES[chess.parse_square(sq)]) is None:
                        insertAbove[sq] = float(evaluation["answer"][puzzleNr][sq]["saliency"])
                        i += 1
                    else:
                        insertBelow[sq] = 0

            print(above)
            print(insertAbove)
            print(insertBelow)

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

            print(answer)

            import chess_saliency_chessSpecific as specific_saliency
            specific_saliency.generate_heatmap(board=board, bestmove=move, evaluation=answer,
                                               directory=dirPath + "/"  +  engine,
                                               puzzle=puzzleNr, file=None)
            print("{}, {} updated".format(engine, puzzleNr))

            with open(dirPath + "/"  +  engine + "/output.txt", "r") as f:
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
                            with open(dirPath + "/"  +  engine + "/output.txt", "w") as f:
                                for line in lines:
                                    f.write(line)
                    with open(dirPath + "/"  +  engine + "/output.txt", "r") as f:
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
                            with open(dirPath + "/"  +  engine + "/output.txt", "w") as f:
                                for line in lines:
                                    f.write(line)

            data[puzzleNr] = {
                "fen": data[puzzleNr]['fen'],
                "best move": data[puzzleNr]["best move"],
                "sorted saliencies": {
                    "above threshold": above,
                    "below threshold": below
                }
            }

            if dirPath == "evaluation/updated":
                path = "chess_saliency_databases\chess-saliency-dataset-v1.json"
                with open(path, "r") as jsonFile:
                    database = json.load(jsonFile)

                missing = []
                for sq in database["puzzles"][int(puzzleNr.replace("puzzle",""))-1]["saliencyGroundTruth"]:
                    if sq not in above:
                        missing.append(sq)
                details = dict()
                if len(missing) == 0:
                    missing = 0
                else:
                    for sq in missing:
                        if sq in evaluation["answer"][puzzleNr]:
                            sal = evaluation["answer"][puzzleNr][sq]['saliency']
                        elif sq in above:
                            sal = above[sq]
                        elif sq in below:
                            sal = below[sq]
                        else:
                            sal = 0
                        details[sq] = {sq: {
                            "int": answer[sq]["int"],
                            "saliency": sal
                        }}

                data[puzzleNr] = {
                    "fen": data[puzzleNr]['fen'],
                    "best move": data[puzzleNr]["best move"],
                    "sorted saliencies": {
                        "above threshold": above,
                        "below threshold": below
                    }, "saliency ground truth": database["puzzles"][int(puzzleNr.replace("puzzle",""))-1]["saliencyGroundTruth"],
                    "missing ground truth": {
                        "squares": missing,
                        "details": details
                    }
                }

            path = dirPath + "/"  +  engine + "/data.json"
            with open(path, "w") as jsonFile:
                json.dump(data, jsonFile, indent=4)


async def rerun_qValues(directory="evaluation/updated/"):
    """Rerun all bratko-kopec puzzles in the given directory based on existing q_values (output.txt).

    :param directory: path where different engines' outputs are stored
    """

    folders = list(filter(lambda x: os.path.isdir(os.path.join(directory, x)), os.listdir(directory)))
    print(folders)
    if len(folders) == 0:
        directory, file = os.path.split(directory)
        directory += '/'
        folders.append(file)

    jsonDatabaseFolder = "chess_saliency_databases\chess-saliency-dataset-v1.json"
    for engine in folders: # iterate engines
        print(engine)

        with open(jsonDatabaseFolder, "r") as jsonFile: # open positional or tactical test solution
            database = json.load(jsonFile)["puzzles"]

        path = "{}/{}/data.json".format(directory, engine) # open engine's evaluation
        with open(path, "r") as jsonFile:
            data = json.load(jsonFile)

        path = directory + "/" + engine + "/" + "output.txt"
        with open(path, "r") as file:
            output = file.readlines()

        outputF = open(directory + "/" + engine + "/" + "output.txt", "a")  # append mode
        outputF.truncate(0)

        backupIndex = 0
        nr = 1

        for puzzle in database: # iterate puzzles
            puzzleNr = "puzzle" + str(nr)
            print(puzzleNr)
            board = chess.Board(puzzle["fen"])
            assignedBestMove = False

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
                elif output[i].startswith("assigned new best move to engine"):
                    assignedBestMove = True
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
                    i += 1
                    if output[i].startswith("square is empty"):
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
                            "player": afterP1dict,
                            "opponent": afterP2dict
                        }
                    else:
                        while output[i].startswith("------------------------------------------") is False:
                            if output[i].startswith("Q Values: {") and "regular" not in qValuesEngine[sq]:
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
                                qValuesEngine[sq]["regular"] = afterPdict
                            elif output[i].startswith("perturbing this square with pawn"):
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
                                    y += 1
                                    qValuesEngine[sq]["pawn"] = afterPdict
                                break
                            i += 1
                i += 1
            print("starting SARFA")
            original_move = data[puzzleNr]["best move"]
            ss = original_move[0:2]
            ds = original_move[2:4]
            move = chess.Move(chess.SQUARES[chess.parse_square(ss)], chess.SQUARES[chess.parse_square(ds)])
            outputF.write("{}\n".format(puzzleNr))
            aboveThreshold, belowThreshold = await givenQValues_computeSaliency(board, move, data[puzzleNr]["fen"], beforePdict, qValuesEngine, assignedBestMove, directory + "/" + engine, puzzleNr, outputF)

            path = directory + engine + "/" + "data.json"

            data[puzzleNr]["sorted saliencies"]["above threshold"] = aboveThreshold
            data[puzzleNr]["sorted saliencies"]["below threshold"] = belowThreshold

            with open(path, "w") as jsonFile:
                json.dump(data, jsonFile, indent=4)
            nr += 1
