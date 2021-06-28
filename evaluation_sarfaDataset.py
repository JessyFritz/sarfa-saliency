import json
import os
import numpy

datasetBestMoves = ["c3d5","f5h6","g3g8","b6d5","c4f4","d5e7","c3d5","f3h5","d5d6","e4c4","f6h8","h3h7","b2g7","a1a2","b1f5","g5g6","f5f8","f6e8","d6e7","d4d7","e4h7","g1g6","f3e5","e2e7","b6g6","e1e6","c1c6","e5d6","c1g5","c6b7","g1g7","f5e6","g4f6","b7b8","d1d7","d3h7","g3g7","e1c1","d2h6","b2a1","b6c7","d1e1","d1d7","d2d4","e4f6","h5h6","d4e4","e4e6","h5h6","e7e5","f1f5","a1b2","h4e4","d6f5","c1h6","f3g5","b3c4","e5e6","g4g6","f3d5","d7e7","h4h5","d3d4","d1d5","f4e6","e2d4","f1f8","h5h6","f4f7","g5g6","g1g6","e3g4","c7e7","c3b5","d5g8","h6h7","d2c2","c4e6","f1f7","a7a8","e5g6","f1f2","b3f7","b3d1","d6d7","d5f6","f3f8","b1g6","d5f7","e1e6","e4e5","d1d7","b3d4","h3h4","d3h7","f7g7","e5g7","d6f8","g7g6","c4c5","c6c8","b7b4"]


def groundTruthEvaluation(directory="evaluation/original/", subset=None):
    """
    evaluates the SARFA database's puzzles per engine based on missing ground truth
    Input :
        directory : path where different engine outputs are stored
        subset : give subset of puzzles if not all should be evaluated
    """

    folders = list(filter(lambda x: os.path.isdir(os.path.join(directory, x)), os.listdir(directory)))
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
    print('------------------------------------------')
    print("In total {} squares from {} puzzles should be salient".format(total, length))
    print("Evaluation:")
    sortedKeys = sorted(evaluation, key=lambda x: 2*((evaluation[x]["precision"]*evaluation[x]["recall"])/(evaluation[x]["precision"]+evaluation[x]["recall"])), reverse=True) # sort engines according to their precision
    rank = 1
    for key in sortedKeys:
        print("{}. {}:{} F1: {} %, {}".format(rank, key, " "*(11-len(key)), "%.2f" %(round(2*((evaluation[key]["precision"]*evaluation[key]["recall"])/(evaluation[key]["precision"]+evaluation[key]["recall"])),2)), evaluation[key]))
        rank += 1
    if subset is None:
        print("Squares missed by all engines: ", allMiss)
        #print("Puzzles with right best move by all engines: ", rightMoves)
        #print("   total: {}".fomat(len(rightMoves)))
        return rightMoves
    return None


def singleEngine_groundTruthEvaluation(directory1="evaluation/original/stockfish", directory2="evaluation/updated/stockfish", subset=False):
    """
    evaluates the SARFA database's puzzles for a single engine with the original and updated code
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
    """
    prints given engine's missing ground truth into console
    optionally searches after a given variable and criteria in the missing ground-truth
    Input :
        directory : path where evaluation of engine is written
        variable : aspect to check, f.e. "dP" or "K"
        criteria : value of variable, f.e. 0.5
        symbol : greater or smaller, f.e. ">"
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
    """
    searches for improvements over all engines' missing ground-truths
    Input :
        directory : path where evaluation of engines is written
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
    """
    calculates best occurrence (in precison and recall) of dP and K over the (true and false) positive class
    Input :
        directory : path where evaluation of engines is written
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
        # parse all available square data below threshold from output file into dictionary
        while i < len(output[engine]):
            if output[engine][i].startswith("puzzle") and len(output[engine][i]) < 15:
                puzzleNr = output[engine][i].replace("\n", "")
                evaluation[engine]["answer"][puzzleNr] = dict()
                evaluation[engine]["answer"][puzzleNr]["above"] = dict()
                evaluation[engine]["answer"][puzzleNr]["below"] = dict()
            elif output[engine][i].startswith("assigned new best move to engine"):
                while output[engine][i].startswith("saliency for this square = ") is False:
                    i += 1
            elif output[engine][i].startswith("perturbing square = "):
                sq = output[engine][i].replace("perturbing square = ", "")
                sq = sq.replace("\n", "")
                featureOccurrence = False
            elif feature is not None and output[engine][i].__contains__(feature):
                featureOccurrence = True
            elif output[engine][i].startswith("saliency for this square = ") and sq in data[engine][puzzleNr]["sorted saliencies"]["above threshold"] and (feature is None or (feature is not None and featureOccurrence)):
                if sq in data[engine][puzzleNr]["saliency ground truth"]:
                    evaluation[engine]["total"] += 1
                variables = str(output[engine][i]).split(',')
                evaluation[engine]["answer"][puzzleNr]["above"][sq] = dict()
                for x in variables:
                    if x.__contains__("\'{}\': ".format('saliency')):
                        evaluation[engine]["answer"][puzzleNr]["above"][sq]['saliency'] = x.replace(
                            "\'{}\': ".format('saliency'), "")
                    elif x.__contains__("\'{}\': ".format('K')):
                        evaluation[engine]["answer"][puzzleNr]["above"][sq]['K'] = x.replace("\'{}\': ".format('K'), "")
                    elif x.__contains__("\'{}\': ".format('dP')):
                        evaluation[engine]["answer"][puzzleNr]["above"][sq]['dP'] = x.replace("\'{}\': ".format('dP'), "")
            elif output[engine][i].startswith("saliency for this square = ") and sq in data[engine][puzzleNr]["sorted saliencies"]["below threshold"] and (feature is None or (feature is not None and featureOccurrence)):
                variables = str(output[engine][i]).split(',')
                evaluation[engine]["answer"][puzzleNr]["below"][sq] = dict()
                for x in variables:
                    if x.__contains__("\'{}\': ".format('saliency')):
                        evaluation[engine]["answer"][puzzleNr]["below"][sq]['saliency'] = x.replace(
                            "\'{}\': ".format('saliency'), "")
                    elif x.__contains__("\'{}\': ".format('K')):
                        evaluation[engine]["answer"][puzzleNr]["below"][sq]['K'] = x.replace("\'{}\': ".format('K'), "")
                    elif x.__contains__("\'{}\': ".format('dP')):
                        evaluation[engine]["answer"][puzzleNr]["below"][sq]['dP'] = x.replace("\'{}\': ".format('dP'), "")
            i += 1

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
            print("best F1 mean for feature \"{}\" with engine {}:{} F1: {} %, precision: {} %, recall: {} % true positive: {}, false positive: {}), (dp {} - {}, K {} - {})".format(
                    feature, engine, " " * (11 - len(engine)), evaluation[engine]["best F1 mean"],
                    round(evaluation[engine]["best tP"] / (evaluation[engine]["best tP"] + evaluation[engine]["best fP"]) * 100, 2), round(evaluation[engine]["best tP"] / evaluation[engine]["total"] * 100, 2), evaluation[engine]["best tP"],
                    evaluation[engine]["best fP"], evaluation[engine]["above dP"], evaluation[engine]["below dP"],
                    evaluation[engine]["above K"], evaluation[engine]["below K"]))
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
    """
    calculates best occurrence (in precison and recall) of dP and K over the (true and false) negative class
    Input :
        directory : path where evaluation of engines is written
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
                sq = output[engine][i].replace("perturbing square = ","")
                sq = sq.replace("\n","")
                featureOccurrence = False
            elif feature is not None and output[engine][i].__contains__(feature):
                featureOccurrence = True
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
    """
    tries an improvement proposal for all engines
    Input :
        directory : path where evaluation of engine is written
        evaluation : dictionary containing all squares
        data : dictionary containing all engines' data files
        below_dP : improved dP below this value
        above_dP : improved dP above this value
        below_K : improved K below this value
        above_K : improved K above this value
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
