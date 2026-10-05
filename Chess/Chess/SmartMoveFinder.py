import random

pieceScore = {'K':0,'Q':10,'R':5,'B':3,'N':3,'P':1} #assigning some values to the pieces to make AI know who to go for

knightScores = [[1,1,1,1,1,1,1,1],
                [1,2,2,2,2,2,2,1],
                [1,2,3,3,3,3,2,1],
                [1,2,3,4,4,3,2,1],
                [1,2,3,4,4,3,2,1],
                [1,2,3,3,3,3,2,1],
                [1,2,2,2,2,2,2,1],
                [1,1,1,1,1,1,1,1]]
bishopScores = [[4,3,2,1,1,2,3,4],
                [3,4,3,2,2,3,4,3],
                [2,3,4,3,3,4,3,2],
                [1,2,3,4,4,3,2,1],
                [1,2,3,4,4,3,2,1],
                [2,3,4,3,3,4,3,2],
                [3,4,3,2,2,3,4,3],
                [4,3,2,1,1,2,3,4]]
queenScores = [[1,1,1,3,1,1,1,1],
                [1,2,3,3,3,1,1,1],
                [1,4,3,3,3,4,2,1],
                [1,2,3,3,3,2,2,1],
                [1,2,3,3,3,2,2,1],
                [1,1,2,3,3,1,1,1],
                [1,1,1,3,1,1,1,1],
                [1,1,1,1,1,1,1,1]]
rookScores = [[4,3,4,4,4,4,3,4],
                [4,4,4,4,4,4,4,4],
                [1,1,2,3,3,2,1,1],
                [1,2,3,4,4,3,2,1],
                [1,2,3,4,4,3,2,1],
                [1,1,2,2,2,2,1,1],
                [4,4,4,4,4,4,4,4],
                [4,3,4,4,4,4,3,4]]
whitePawnScores = [[8,8,8,8,8,8,8,8],
                [8,8,8,8,8,8,8,8],
                [5,6,6,7,7,6,6,5],
                [2,3,3,5,5,3,3,2],
                [1,2,3,4,4,3,2,1],                
                [1,1,2,3,3,2,1,1],
                [1,1,1,0,0,1,1,1],
                [0,0,0,0,0,0,0,0]]
blackPawnScores =[[0,0,0,0,0,0,0,0],
                [1,1,1,0,0,1,1,1],
                [1,1,2,3,3,2,1,1],
                [1,2,3,4,4,3,2,1],
                [2,3,3,5,5,3,3,2],
                [5,6,6,7,7,6,6,5],
                [8,8,8,8,8,8,8,8],
                [8,8,8,8,8,8,8,8]]

piecePositionScores = {'N':knightScores,'Q':queenScores,'B':bishopScores,'R':rookScores,'bP': blackPawnScores,'wP':whitePawnScores}

CHECKMATE = 1000
STALEMATE = 0
DEPTH = 3
'''
Picks and returns a random move
'''
def findRandomMove(validMoves):
    return validMoves[random.randint(0,len(validMoves)-1)]
'''
Picks and returns the best move based on material alone, no recursion
'''

def findBestMoveMinMaxNoRecursion(gs,validMoves):
    turnMultiplier = 1 if gs.whitetomove else -1

    opponentMinMaxScore = CHECKMATE        #opponents minimum maximum score (the minimize the maximum lead opponent can get)
    bestPlayerMove = None
    random.shuffle(validMoves)   #for now ai only sees 2 moves ahead, to prevent an infinite loop, we use random so that it messes up and attempts to fix it
    for playerMove in validMoves:       #for loop -> get opponent moves and set max to be low, then find max and then my moves, what is opponent max response to that, if less than previous max, then that is my new move and then keep reducing 
        gs.makeMove(playerMove)
        opponentsMoves = gs.getValidMoves()
        if gs.stalemate:
            opponentsMaxScore = STALEMATE
        elif gs.checkmate:
            opponentsMaxScore = -CHECKMATE    
        else:
            opponentsMaxScore = -CHECKMATE
            for opponentMove in opponentsMoves:
                gs.makeMove(opponentMove)
                gs.getValidMoves()
                if gs.checkmate:
                    score = CHECKMATE
                elif gs.stalemate:
                    score = STALEMATE
                else:
                    score = -turnMultiplier * scoreMaterial(gs.board)
                if (score > opponentsMaxScore):
                    opponentsMaxScore = score
                gs.undoMove()
        if opponentsMaxScore < opponentMinMaxScore:
            opponentMinMaxScore = opponentsMaxScore
            bestPlayerMove = playerMove
        gs.undoMove()
    return bestPlayerMove

'''
Helper method for 1st recursive call
'''
def findBestMove(gs,validMoves,returnqueue):
    if(len(validMoves)==0):
        return None
    global nextMove, counter
    nextMove = None
    random.shuffle(validMoves)
    counter = 0
    #findMoveNegaMax(gs,validMoves,DEPTH, 1 if gs.whitetomove else -1)
    findMoveNegaMaxAlphaBeta(gs,validMoves,DEPTH, -CHECKMATE,CHECKMATE, 1 if gs.whitetomove else -1)
    print(counter)
    returnqueue.put(nextMove)
'''
Improved findBestMove
'''
def findMoveMinMax(gs,validMoves,depth, whiteToMove):         
    global nextMove
    if depth == 0:
        return scoreMaterial(gs.board)
    

    if whiteToMove:
        maxScore = -CHECKMATE
        for move in validMoves:
            gs.makeMove(move)
            nextMoves = gs.getValidMoves()
            score = findMoveMinMax(gs,nextMoves,depth-1, False)
            if score> maxScore:             #purpose is to find best move in branch(depth) and making that my move
                maxScore = score            
                if depth == DEPTH:
                    nextMove = move
            gs.undoMove()
        return maxScore

    else:
        minScore = CHECKMATE
        for move in validMoves:
            gs.makeMove(move)
            nextMoves = gs.getValidMoves()
            score = findMoveMinMax(gs,nextMoves,depth - 1,True)
            if score < minScore:
                minScore = score
                if depth == DEPTH:
                    nextMove = move
            gs.undoMove()
        return minScore
    

def findMoveNegaMax(gs,validMoves,depth, turnMultiplier):       #improved findMoveMinMax
    global nextMove,counter
    counter += 1
    if depth == 0:
        return turnMultiplier * scoreBoard(gs)

    maxScore = -CHECKMATE
    for move in validMoves:
        gs.makeMove(move)
        nextMoves = gs.getValidMoves()
        score = -findMoveNegaMax(gs,nextMoves,depth - 1, -turnMultiplier)
        if score>maxScore:
            maxScore = score
            if depth == DEPTH:
                nextMove = move
        gs.undoMove()
    return maxScore

def findMoveNegaMaxAlphaBeta(gs,validMoves,depth,alpha,beta, turnMultiplier):       #improved findMoveNegamax
    global nextMove,counter
    counter += 1
    if depth == 0:
        return turnMultiplier * scoreBoard(gs)

    #move ordering - implement later
    maxScore = -CHECKMATE
    for move in validMoves:
        gs.makeMove(move)
        nextMoves = gs.getValidMoves()
        score = -findMoveNegaMaxAlphaBeta(gs,nextMoves,depth - 1,-beta,-alpha, -turnMultiplier)
        if score>maxScore:
            maxScore = score
            if depth == DEPTH:
                nextMove = move
        gs.undoMove()
        if maxScore>alpha:  #pruning
            alpha = maxScore
        if alpha>=beta:
            break
    return maxScore
'''
Positive score good for white and negative score good for black
'''    
def scoreBoard(gs):
    if gs.checkmate:
        if gs.whitetomove:
            return -CHECKMATE # black wins
        else:
            return CHECKMATE # white wins
    elif gs.stalemate:
        return STALEMATE
    score = 0
    for row in range(len(gs.board)):
        for col in range(len(gs.board[row])):
            square = gs.board[row][col]
            if square != '--':
                #score based on position
                piecePositionScore = 0
                if square[1] != 'K':
                    if square[1] == 'P':
                        piecePositionScore = piecePositionScores[square][row][col]       #for pawns
                    else:
                        piecePositionScore = piecePositionScores[square[1]][row][col]   #for other pieces
                
                if square[0] == 'w':
                    score += pieceScore[square[1]] + piecePositionScore * .1     #multiplier to make it a good option but not the only option
                elif square[0] == 'b':
                    score -= pieceScore[square[1]] + piecePositionScore * .1 
    return score
'''
Score board based on material
'''
def scoreMaterial(board):
    score = 0
    for row in board:
        for square in row:
            if square[0] == 'w':
                score += pieceScore[square[1]]
            elif square[0] == 'b':
                score -= pieceScore[square[1]]
    return score
