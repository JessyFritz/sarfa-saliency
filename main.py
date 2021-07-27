import asyncio
import chess.pgn
import chess_saliency_original as original_saliency
import chess_saliency_combination as updated_saliency
import chess_saliency_chessSpecific as specific_saliency
import chess_saliency_leela as leela_saliency
import databaseHandler as db
from evaluation_bratkoKopec import evaluateBratkoKopec, convertToPosition, \
    singleEngine_bratkoKopec_groundTruthEvaluation, \
    bratkoKopec_calculateImprovements_emptySquares, bratkoKopec_calculateImprovements_TopEmptySquares, \
    bratkoKopec_markEmptySquares, evaluateBratkoKopec_allPuzzles, rerunBratkoKopec_qValues
from evaluation_endgames import evaluate, singleEngine_endgames_groundTruthEvaluation, endgames_markEmptySquares, \
    endgames_calculateImprovements_TopEmptySquares, evaluateEndgames_allPuzzles, rerunEndgames_qValues
from evaluation_sarfaDataset import groundTruthEvaluation, missingGroundTruth, singleEngine_groundTruthEvaluation, \
    calculateImprovements_threshold, calculateImprovements_negative, calculateImprovements_positive, markEmptySquares, \
    rerun_qValues

updated_saliency.enableEmptySquares = True #enable empty squares
specific_saliency.enableEmptySquares = True
leela_saliency.enableEmptySquares = True

#**************************************************** run & evaluate sarfa dataset's 102 puzzles ****************************************************

#************************** create saliency maps
#db.runAll_engines("SARFA")
#db.runAll_engines("SARFA", specific_saliency)

#************************** evaluate saliency maps
#groundTruthEvaluation() # evaluate all 102 puzzles
#groundTruthEvaluation(subset=groundTruthEvaluation()) # evaluate only puzzles with correct move
#missingGroundTruth()
#groundTruthEvaluation(directory="evaluation/updated/")
#groundTruthEvaluation(directory="evaluation/updated/",subset=groundTruthEvaluation(directory="evaluation/updated/"))

#singleEngine_groundTruthEvaluation(subset=True)
#singleEngine_groundTruthEvaluation(directory1="evaluation/original/leela", directory2="evaluation/updated/leela",subset=True)
#singleEngine_groundTruthEvaluation(directory1="evaluation/original/stockfish12",   directory2="evaluation/updated/stockfish12",subset=True)
#singleEngine_groundTruthEvaluation(directory1="evaluation/original/slowchess", directory2="evaluation/updated/slowchess",subset=True)
#singleEngine_groundTruthEvaluation(directory1="evaluation/original/rybka", directory2="evaluation/updated/rybka",subset=True)
#singleEngine_groundTruthEvaluation(directory1="evaluation/original/fruit", directory2="evaluation/updated/fruit",subset=True)
#singleEngine_groundTruthEvaluation(directory1="evaluation/original/komodo", directory2="evaluation/updated/komodo",subset=True)
#singleEngine_groundTruthEvaluation(directory1="evaluation/original/octochess", directory2="evaluation/updated/octochess",subset=True)

#calculateImprovements_threshold()
#calculateImprovements_negative()
#calculateImprovements_positive()

#************************** modify saliency maps
'''asyncio.set_event_loop_policy(chess.engine.EventLoopPolicy())
asyncio.run(rerun_qValues())'''
#markEmptySquares(0)


#********************************** run & evaluate bratko-kopec test from http://kopecchess.com/bratko-kopec-test/ **********************************

#************************** create saliency maps
#db.runAll_engines("bratkoKopec")
#db.runAll_engines("bratkoKopec", updated_saliency)
#db.runAll_engines("bratkoKopec", specific_saliency)

#************************** evaluate saliency maps
#evaluateBratkoKopec()
#evaluateBratkoKopec("evaluation/bratko-kopec/updated")
'''asyncio.set_event_loop_policy(chess.engine.EventLoopPolicy())
asyncio.run(evaluateBratkoKopec_allPuzzles("evaluation/bratko-kopec/updated", mode="All"))'''

#convertToPosition()

#singleEngine_bratkoKopec_groundTruthEvaluation()
#singleEngine_bratkoKopec_groundTruthEvaluation(directory1="evaluation/bratko-kopec/original/leela", directory2="evaluation/bratko-kopec/updated/leela")
#singleEngine_bratkoKopec_groundTruthEvaluation(directory1="evaluation/bratko-kopec/original/stockfish12",   directory2="evaluation/bratko-kopec/updated/stockfish12")
#singleEngine_bratkoKopec_groundTruthEvaluation(directory1="evaluation/bratko-kopec/original/slowchess", directory2="evaluation/bratko-kopec/updated/slowchess")
#singleEngine_bratkoKopec_groundTruthEvaluation(directory1="evaluation/bratko-kopec/original/rybka", directory2="evaluation/bratko-kopec/updated/rybka")
#singleEngine_bratkoKopec_groundTruthEvaluation(directory1="evaluation/bratko-kopec/original/fruit", directory2="evaluation/bratko-kopec/updated/fruit")
#singleEngine_bratkoKopec_groundTruthEvaluation(directory1="evaluation/bratko-kopec/original/komodo", directory2="evaluation/bratko-kopec/updated/komodo")
#singleEngine_bratkoKopec_groundTruthEvaluation(directory1="evaluation/bratko-kopec/original/octochess", directory2="evaluation/bratko-kopec/updated/octochess")

#bratkoKopec_calculateImprovements_emptySquares()
#bratkoKopec_calculateImprovements_TopEmptySquares()

#************************** modify saliency maps
'''asyncio.set_event_loop_policy(chess.engine.EventLoopPolicy())
asyncio.run(rerunBratkoKopec_qValues())'''
#bratkoKopec_markEmptySquares(3)


#****************************** run & evaluate 20 endgame puzzles from https://www.stmintz.com/ccc/index.php?id=476109 ******************************

#************************** create saliency maps
#db.runAll_engines("endgame")
#db.runAll_engines("endgame", updated_saliency)
#db.runAll_engines("endgame", specific_saliency)

#************************** evaluate saliency maps
#evaluate()
#evaluate("evaluation/endgames/updated/")
'''asyncio.set_event_loop_policy(chess.engine.EventLoopPolicy())
asyncio.run(evaluateEndgames_allPuzzles("evaluation/endgames/updated", mode="All"))'''

#singleEngine_endgames_groundTruthEvaluation()
#singleEngine_endgames_groundTruthEvaluation(directory1="evaluation/endgames/original/leela", directory2="evaluation/endgames/updated/leela")
#singleEngine_endgames_groundTruthEvaluation(directory1="evaluation/endgames/original/stockfish12",   directory2="evaluation/endgames/updated/stockfish12")
#singleEngine_endgames_groundTruthEvaluation(directory1="evaluation/endgames/original/slowchess", directory2="evaluation/endgames/updated/slowchess")
#singleEngine_endgames_groundTruthEvaluation(directory1="evaluation/endgames/original/rybka", directory2="evaluation/endgames/updated/rybka")
#singleEngine_endgames_groundTruthEvaluation(directory1="evaluation/endgames/original/fruit", directory2="evaluation/endgames/updated/fruit")
#singleEngine_endgames_groundTruthEvaluation(directory1="evaluation/endgames/original/komodo", directory2="evaluation/endgames/updated/komodo")
#singleEngine_endgames_groundTruthEvaluation(directory1="evaluation/endgames/original/octochess", directory2="evaluation/endgames/updated/octochess")

#endgames_calculateImprovements_TopEmptySquares()

#************************** modify saliency maps
'''asyncio.set_event_loop_policy(chess.engine.EventLoopPolicy())
asyncio.run(rerunEndgames_qValues())'''
#endgames_markEmptySquares(3)


#****************************************** run some generally problematic maps & more posiitonal puzzles *******************************************

#db.runAll_engines("general")
#db.runAll_engines("positional")
#db.runAll_engines("general", saliency=specific_saliency)
#db.runAll_engines("positional", saliency=specific_saliency)


#********************************************************** basic analyisis functions ***************************************************************

#subset = groundTruthEvaluation()
#db.getMean(variable="dP", subset=subset)
#db.getMean(variable="K", subset=subset)
#db.getMean(variable="saliency", subset=subset)
#db.getQValues()
#db.getMean(variable="original reward")
#db.getMean()
#db.getMinMax(variable="reward Q(s',â)", mode="max")
#db.getMinMax(variable="reward Q(s',â)", mode="min")
#db.getMinMax(variable="reward Q(s,â)", mode="max")
#db.getMinMax(variable="reward Q(s,â)", mode="min")
#db.getMinMax(variable="K", mode="min")


#************************************************** evaluate features for updated implementation ***************************************************

'''db.evaluateFeature("evaluation/updated/leela",feature="is under attack")
db.evaluateFeature("evaluation/updated/leela",feature="pawn promotion on this square")
db.evaluateFeature("evaluation/updated/leela",feature="opponent is in check after best move")
db.evaluateFeature("evaluation/updated/leela",feature="saliency calculated as max from pawn perturbation")
db.evaluateFeature("evaluation/updated/leela",feature="king is salient because of check")
db.evaluateFeature("evaluation/updated/leela",feature="already pawn here")
db.evaluateFeature("evaluation/updated/leela",feature="new pawn saliency for this square")
db.evaluateFeature("evaluation/updated/leela",feature="guards best move")
db.evaluateFeature("evaluation/updated/leela",feature="piece is no longer blocked")'''


#*************************************************************** try it out yourself ****************************************************************

'''asyncio.set_event_loop_policy(chess.engine.EventLoopPolicy())
asyncio.run(specific_saliency.computeSaliency('engines/stockfish_12_win_x64_bmi2/stockfish_20090216_x64_bmi2.exe'))'''
