'''
This class is responsible for storing all the information about the current state of a chess game. It's also 
responsible for determining the valid moves at the current state. It will also keep a move log. 
'''
class Gamestate():  # making a class
    def __init__(self):  # making a constructor using __int__
        # chess board is 8x8, this is 2d list with each element
        # being 2 characters, '--' is empty piece
        self.board = [
            # 2D list for p2p  --- use numpy array for more ai efficiency
            ["bR", 'bN', 'bB', 'bQ', 'bK', 'bB', 'bN', 'bR'],
            ['bP', 'bP', 'bP', 'bP', 'bP', 'bP', 'bP', 'bP'],
            ['--', '--', '--', '--', '--', '--', '--', '--'],
            ['--', '--', '--', '--', '--', '--', '--', '--'],
            ['--', '--', '--', '--', '--', '--', '--', '--'],   
            ['--', '--', '--', '--', '--', '--', '--', '--'],
            ['wP', 'wP', 'wP', 'wP', 'wP', 'wP', 'wP', 'wP'],
            ["wR", 'wN', 'wB', 'wQ', 'wK', 'wB', 'wN', 'wR']]
        self.moveFunctions = {'P': self.getPawnMoves,'R': self.getRookMoves, 'N': self.getKnightMoves,
                               'B': self.getBishopMoves, 'Q': self.getQueenMoves,'K': self.getKingMoves}
        self.whitetomove = True  # created to store the turns of each color
        self.movelog = []
        #to keep track of where the kings are
        self.whiteKinglocation=(7,4)
        self.blackKinglocation=(0,4)
        #needed to check if pinned or check
        self.incheck = False
        self.pins = []
        self.checks = []
        self.enpassantPossible = () #coords of square where enpassant capture possible
        self.enpassantPossibleLog = [self.enpassantPossible]  #needed to store previous enpassant move for undoing  
        self.checkmate=False
        self.stalemate=False
        self.currentCastlingRight = CastleRights(True,True,True,True)         
        self.castleRightlog = [CastleRights(self.currentCastlingRight.wks,self.currentCastlingRight.wqs,self.currentCastlingRight.bks,self.currentCastlingRight.bqs)]
    '''
    Takes a Move as a parameter and executes it (won't work for castling,pawn promotion and en passant)
    '''
    def makeMove(self,move):
        self.board[move.endRow][move.endCol] = move.pieceMoved
        self.board[move.startRow][move.startCol] = '--'
        self.movelog.append(move)       #log move to display or undo later
        self.whitetomove = not self.whitetomove  #switch turns              
        #update King's position
        if move.pieceMoved == 'wK':
            self.whiteKinglocation=(move.endRow,move.endCol)
        elif move.pieceMoved == 'bK':
            self.blackKinglocation=(move.endRow,move.endCol)
        #if pawn moves twice,next move can be enpassant
        move.enpassantPossible = self.enpassantPossible
        if move.pieceMoved[1] == 'P' and abs (move.startRow - move.endRow) == 2:
            self.enpassantPossible = ((move.endRow + move.startRow)//2, move.endCol)
        else:
            self.enpassantPossible=()
        #if enpassant move, must update the board to capture the pawn
        if move.isEnpassantMove:
            self.board[move.startRow][move.endCol] = '--'

        #pawn promotion
        if move.isPawnPromotion:
            self.board[move.endRow][move.endCol] = move.pieceMoved[0]+move.promotionChoice

        self.enpassantPossibleLog.append(self.enpassantPossible)

        #update castling rights - whenever rook or king move
        self.updateCastleRights(move)
        self.castleRightlog.append(CastleRights(self.currentCastlingRight.wks,self.currentCastlingRight.wqs,self.currentCastlingRight.bks,self.currentCastlingRight.bqs))
        
        #castle move
        if move.isCastleMove:
            if move.endCol - move.startCol == 2: #it is king side castle (diff is 2)
                self.board[move.endRow][move.endCol-1] = self.board[move.endRow][move.endCol+1] #moves the rook
                self.board[move.endRow][move.endCol +1] = '--' #erase old rook     
            else: #queen side castle (diff not 2)
                self.board[move.endRow][move.endCol +1] = self.board[move.endRow][move.endCol-2] #move rook
                self.board[move.endRow][move.endCol-2] = '--' #erase old rook    
    '''
    Undo the last move
    '''
    def undoMove(self):
        if len(self.movelog)!=0: #make sure movelog is not 0 
            move = self.movelog.pop() 
            self.board[move.startRow][move.startCol]=move.pieceMoved
            self.board[move.endRow][move.endCol]=move.pieceCaptured
            self.whitetomove = not self.whitetomove   #swap players again 
            #update King's position
            if move.pieceMoved =='wK':
                self.whiteKinglocation = (move.startRow, move.startCol)
            elif move.pieceMoved =='bK':
                self.blackKinglocation = (move.startRow, move.startCol)
            # undo enpassant is present
            if move.isEnpassantMove:
                self.board[move.endRow][move.endCol] = '--' #removes pawn from wrong square
                self.board[move.startRow][move.endCol] = move.pieceCaptured #puts the pawn back to the correct square it was captured from

            self.enpassantPossibleLog.pop()
            self.enpassantPossible = self.enpassantPossibleLog[-1]

            self.checkmate= False
            self.stalemate=False
            #undo Castling Rights
            self.castleRightlog.pop()  #get rid of new castle rights from move we are undoing
            self.currentCastlingRight = self.castleRightlog[-1] #set the current castle rights to last one in list
            #undo castling move
            if move.isCastleMove:
                if move.endCol - move.startCol == 2: #kingside
                    self.board[move.endRow][move.endCol+1] = self.board[move.endRow][move.endCol-1]
                    self.board[move.endRow][move.endCol-1] = '--'
                else:
                    self.board[move.endRow][move.endCol-2] = self.board[move.endRow][move.endCol+1]
                    self.board[move.endRow][move.endCol+1] ='--'
            
            self.checkmate = False;
            self.stalemate = False;
    def inCheck(self):
        if self.whitetomove: 
            return self.squareUnderAttack(self.whiteKinglocation[0],self.whiteKinglocation[1])
        else:
            return self.squareUnderAttack(self.blackKinglocation[0],self.blackKinglocation[1])
    
    def squareUnderAttack(self,r,c):
        self.whitetomove = not self.whitetomove #switch to opponent turn
        oppMoves = self.getAllPossibleMoves()
        self.whitetomove = not self.whitetomove #switch turn back
        for move in oppMoves:
            if move.endRow == r and move.endCol == c: #square under attack
                return True
        return False        
    '''
    Update the Castle rights for a given move
    '''
    def updateCastleRights(self,move):
        if move.pieceMoved == 'wK':
            self.currentCastlingRight.wks = False
            self.currentCastlingRight.wqs = False
        elif move.pieceMoved == 'bK':
            self.currentCastlingRight.bks = False
            self.currentCastlingRight.bqs = False
        
        elif move.pieceMoved == 'wR':
            if move.startRow == 7:
                if move.startCol == 0: #left rook
                    self.currentCastlingRight.wqs = False
                elif move.startCol == 7: #right rook
                    self.currentCastlingRight.wks = False
        elif move.pieceMoved == 'bR':
            if move.startRow == 0:
                if move.startCol == 0: #left rook
                    self.currentCastlingRight.bqs = False
                elif move.startCol == 7:
                    self.currentCastlingRight.bks = False
        
         #if a rook is captured
        if move.pieceCaptured == 'wR':
            if move.endRow == 7:
                if move.endCol == 0:
                    self.currentCastlingRight.wqs = False
                elif move.endCol == 7:
                    self.currentCastlingRight.wks = False
        elif move.pieceCaptured == 'bR':
            if move.endRow == 0:
                if move.endCol == 0:
                    self.currentCastlingRight.bqs = False
                elif move.endCol == 7:
                    self.currentCastlingRight.bks = False                
    ''''
    all moves considering checks (we consider a move valid to move only if king is safe)
    '''
    def getValidMoves(self):
        moves = []
        self.inCheck, self.pins, self.checks = self.checkForPinsAndChecks()
        if self.whitetomove:
            kingRow = self.whiteKinglocation[0]
            kingCol = self.whiteKinglocation[1]
        else:
            kingRow = self.blackKinglocation[0]
            kingCol = self.blackKinglocation[1]
        if self.inCheck:
            if len(self.checks) == 1: #only 1 check, block the check or move the king
                moves = self.getAllPossibleMoves()
                # to block a check, you must place a piece in front of enemy and king
                check = self.checks[0] #check information
                checkRow = check[0]
                checkCol = check[1]
                pieceChecking = self.board[checkRow][checkCol]  #enemy piece causing check
                validSquares = [] #squares that piece can move to
                #if knight, capture knight or move king, other pieces can be blocked
                if pieceChecking[1] == 'N':
                    validSquares = [(checkRow,checkCol)]
                else:
                    for i in range(1,8):
                        validSquare = (kingRow + check[2]*i, kingCol + check[3]*i) #check[2] and check[3] are the check direction
                        validSquares.append(validSquare)
                        if validSquare[0] == checkRow and validSquare[1] == checkCol: # once you get to piece and checks
                            break
                #get rid of any moves that do not block check or move king
                for i in range(len(moves) -1 , -1 ,-1): #go through backwards when you are removing from a list as iterating
                    if moves[i].pieceMoved[1] != 'K': # move doesn't move king so must block or capture
                        if not (moves[i].endRow, moves[i].endCol) in validSquares: #move doesn't block check or capture piece
                            moves.remove(moves[i])
            else: #double check, king has to move
                self.getKingMoves(kingRow,kingCol,moves)
        else: #not in check so all moves are fine
            moves = self.getAllPossibleMoves()

        #check for checkmate = in check and no valid moves, stalemate = not in check and no valid moves
        if len(moves) == 0: #either checkmate or stalemate
            if self.inCheck:
                self.checkmate = True
            else:
                self.stalemate= True
        else:
            self.checkmate= False
            self.stalemate=False
        #castling
        tempCastleRights = CastleRights(self.currentCastlingRight.wks,self.currentCastlingRight.wqs,
                                        self.currentCastlingRight.bks,self.currentCastlingRight.bqs) #copies current castling rights
        if self.whitetomove:
            self.getCastleMoves(self.whiteKinglocation[0],self.whiteKinglocation[1],moves)
        else:
            self.getCastleMoves(self.blackKinglocation[0],self.blackKinglocation[1],moves)
        self.currentCastlingRight = tempCastleRights
        
        return moves
    '''
    all moves without considering checks
    '''
    def getAllPossibleMoves(self):
        moves=[]
        for r in range(len(self.board)):# no. of rows   
            for c in range(len(self.board[r])):# no. of columns
                turn = self.board[r][c][0]
                if (turn == 'w' and self.whitetomove) or (turn =='b' and not self.whitetomove):
                    piece = self.board[r][c][1]
                    self.moveFunctions[piece](r,c,moves) #calls the appropriate move functions based on piece type
        return moves
    '''
    Get all the Pawn moves for the pawn located at row, column and add those moves to the list
    '''
    def getPawnMoves(self,r,c,moves):
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins)-1,-1,-1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2],self.pins[i][3])
                self.pins.remove(self.pins[i])
                break
     
        if self.whitetomove: #white pawn moves
            kingRow,kingCol = self.whiteKinglocation
            if self.board[r-1][c] == '--': # 1 square pawn advance
                if not piecePinned or pinDirection == (-1,0):
                    moves.append(Move((r,c),(r-1,c),self.board)) 
                    if r==6 and self.board[r-2][c] == '--': # 2 square pawn advance
                        moves.append(Move((r,c),(r-2,c),self.board))
            #captures
            if c-1 >= 0: # captures to the left
                if self.board[r-1][c-1][0] == 'b': # enenmy piece to capture
                    if not piecePinned or pinDirection == (-1,-1):
                        moves.append(Move((r,c),(r-1,c-1),self.board))
                elif (r-1,c-1) == self.enpassantPossible:
                        attackingPiece = blockingPiece = False
                        if kingRow  == r: # to check if king in same row as pawn
                            if kingCol<c: # to check if king is left of pawn
                                #inside b/w king and pawn and outside b/w pawn and border
                                insideRange = range(kingCol + 1, c-1)
                                outsideRange = range(c+1,8)
                            else:#king right of pawn
                                insideRange = range(kingCol-1,c,-1)
                                outsideRange = range(c-2,-1,-1)
                            for i in insideRange:
                                if self.board[r][i] != '--': #some other piece beside enpassant pawns blocks
                                    blockingPiece = True
                            for i in outsideRange:
                                square =  self.board[r][i]
                                if square[0] == 'b' and (square[1]=='R' or square[1] == 'Q'):
                                    attackingPiece = True
                                elif square != '--':
                                    blockingPiece = True
                        if not attackingPiece or blockingPiece:
                            moves.append(Move((r,c),(r-1,c-1),self.board,isEnpassantMove=True))

            if c+1<=7: #captures to the right
                if self.board[r-1][c+1][0] == 'b': #enemy piece to capture
                    if not piecePinned or pinDirection == (-1,1):
                        moves.append(Move((r,c),(r-1,c+1),self.board))
                elif (r-1,c+1) == self.enpassantPossible:
                        attackingPiece = blockingPiece = False
                        if kingRow  == r: # to check if king in same row as pawn
                            if kingCol<c: # to check if king is left of pawn
                                #inside b/w king and pawn and outside b/w pawn and border
                                insideRange = range(kingCol + 1, c)
                                outsideRange = range(c+2,8)
                            else:#king right of pawn
                                insideRange = range(kingCol-1,c+1,-1)
                                outsideRange = range(c-1,-1,-1)
                            for i in insideRange:
                                if self.board[r][i] != '--': #some other piece beside enpassant pawns blocks
                                    blockingPiece = True
                            for i in outsideRange:
                                square =  self.board[r][i]
                                if square[0] == 'b' and (square[1]=='R' or square[1] == 'Q'):
                                    attackingPiece = True
                                elif square != '--':
                                    blockingPiece = True
                        if not attackingPiece or blockingPiece:
                            moves.append(Move((r,c),(r-1,c+1),self.board,isEnpassantMove=True))

        else: #black pawns to move
            kingRow,kingCol = self.blackKinglocation
            if self.board[r+1][c] == '--': # 1 square pawn advance
                if not piecePinned or pinDirection == (1,0):
                    moves.append(Move((r,c),(r+1,c),self.board))
                    if r==1 and self.board[r+2][c] == '--': #2 sqaure pawn advance
                        moves.append(Move((r,c),(r+2,c),self.board))
            
            #captures
            if c-1 >= 0: # captures to the left
                if self.board[r+1][c-1][0] == 'w': # enenmy piece to capture
                    if not piecePinned or pinDirection == (1,-1):
                        moves.append(Move((r,c),(r+1,c-1),self.board))
                elif (r+1,c-1) == self.enpassantPossible:
                        attackingPiece = blockingPiece = False
                        if kingRow  == r: # to check if king in same row as pawn
                            if kingCol<c: # to check if king is left of pawn
                                #inside b/w king and pawn and outside b/w pawn and border
                                insideRange = range(kingCol + 1, c-1)
                                outsideRange = range(c+1,8)
                            else:#king right of pawn
                                insideRange = range(kingCol-1,c,-1)
                                outsideRange = range(c-2,-1,-1)
                            for i in insideRange:
                                if self.board[r][i] != '--': #some other piece beside enpassant pawns blocks
                                    blockingPiece = True
                            for i in outsideRange:
                                square =  self.board[r][i]
                                if square[0] == 'w' and (square[1]=='R' or square[1] == 'Q'):
                                    attackingPiece = True
                                elif square != '--':
                                    blockingPiece = True
                        if not attackingPiece or blockingPiece:
                            moves.append(Move((r,c),(r+1,c-1),self.board,isEnpassantMove=True))
            if c+1<=7: #captures to the right
                if self.board[r+1][c+1][0] == 'w': #enemy piece to capture
                    if not piecePinned or pinDirection == (1,1): 
                        moves.append(Move((r,c),(r+1,c+1),self.board))
                elif (r+1,c+1) == self.enpassantPossible:
                        attackingPiece = blockingPiece = False
                        if kingRow  == r: # to check if king in same row as pawn
                            if kingCol<c: # to check if king is left of pawn
                                #inside b/w king and pawn and outside b/w pawn and border
                                insideRange = range(kingCol + 1, c)
                                outsideRange = range(c+2,8)
                            else:#king right of pawn
                                insideRange = range(kingCol-1,c+1,-1)
                                outsideRange = range(c-1,-1,-1)
                            for i in insideRange:
                                if self.board[r][i] != '--': #some other piece beside enpassant pawns blocks
                                    blockingPiece = True
                            for i in outsideRange:
                                square =  self.board[r][i]
                                if square[0] == 'w' and (square[1]=='R' or square[1] == 'Q'):
                                    attackingPiece = True
                                elif square != '--':
                                    blockingPiece = True
                        if not attackingPiece or blockingPiece:
                            moves.append(Move((r,c),(r+1,c+1),self.board,isEnpassantMove=True))
                        #moves.append(Move((r,c),(r+1,c+1),self.board,isEnpassantMove=True))
    '''
    Get all the Rook moves for the pawn located at row, column and add those moves to the list
    '''
    def getRookMoves(self,r,c,moves):
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins)-1,-1,-1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2],self.pins[i][3])
                if self.board[r][c][1] != 'Q' :  #can't remove queen from pin on rook moves, only remove  it on bishop moves
                    self.pins.remove(self.pins[i])
                break
        directions = ((-1,0),(0,-1),(1,0),(0,1)) #defining the directions rook moves (4)
        enemycolor = 'b' if self.whitetomove else 'w'
        for d in directions:
            for i in range(1,8):
                endRow = r + d[0]*i
                endCol = c + d[1]*i
                if 0 <= endRow < 8 and 0 <= endCol <8: #on board
                    if not piecePinned or pinDirection == d or pinDirection == (-d[0],-d[1]):
                        endPiece= self.board[endRow][endCol]
                        if endPiece == '--': # empty space (valid)
                            moves.append(Move((r,c),(endRow,endCol),self.board))
                        elif endPiece[0] == enemycolor : #valid as enemy
                            moves.append(Move((r,c),(endRow,endCol),self.board))
                            break
                        else: #friendly piece
                            break
                else: #off board
                    break
    '''
    Get all the Knight moves for the pawn located at row, column and add those moves to the list
    '''
    def getKnightMoves(self,r,c,moves):
        piecePinned = False
        for i in range(len(self.pins)-1,-1,-1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                self.pins.remove(self.pins[i])
                break
        
        knightMoves = ((-2,-1),(-2,1),(-1,-2),(1,-2),(1,2),(2,-1),(2,1),(-1,2)) # the 8 directions knight can move
        allycolor = 'w' if self.whitetomove else 'b'
        for m in knightMoves:
            endRow = r + m[0]
            endCol = c + m[1]
            if 0<=endRow<8 and 0<=endCol<8:
                if not piecePinned:
                    endPiece = self.board[endRow][endCol]
                    if endPiece[0] != allycolor: # not ally = enemy or empty
                        moves.append(Move((r,c),(endRow,endCol),self.board))
    '''
    Get all the Bishop moves for the pawn located at row, column and add those moves to the list
    '''
    def getBishopMoves(self,r,c,moves):
        piecePinned = False
        pieceDirection = ()
        for i in range(len(self.pins)-1,-1,-1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2],self.pins[i][3])
                self.pins.remove(self.pins[i])
                break
        directions = ((-1,-1),(-1,1),(1,-1),(1,1)) #defining the directions bishop moves (4)
        enemycolor = 'b' if self.whitetomove else 'w'
        for d in directions:
            for i in range(1,8):
                endRow = r + d[0]*i
                endCol = c + d[1]*i
                if 0 <= endRow < 8 and 0 <= endCol <8: #on board
                    if not piecePinned or pinDirection == d or pinDirection == (-d[0],-d[1]):
                        endPiece= self.board[endRow][endCol]
                        if endPiece == '--': # empty space (valid)
                            moves.append(Move((r,c),(endRow,endCol),self.board))
                        elif endPiece[0] == enemycolor : #valid as enemy
                            moves.append(Move((r,c),(endRow,endCol),self.board))
                            break
                        else: #friendly piece
                            break
                else: #off board
                    break
    '''
    Get all the Queen moves for the pawn located at row, column and add those moves to the list
    '''
    def getQueenMoves(self,r,c,moves):
        self.getRookMoves(r,c,moves)
        self.getBishopMoves(r,c,moves)
    '''
    Get all the King moves for the pawn located at row, column and add those moves to the list
    '''
    def getKingMoves(self,r,c,moves):
        kingMoves = ((-1,-1),(-1,0),(-1,1),(0,1),(0,-1),(1,0),(1,1),(1,-1))
        allycolor= 'w' if self.whitetomove else 'b'
        for i in range(8):
            endRow = r + kingMoves[i][0]
            endCol = c + kingMoves[i][1]
            if 0<=endRow<8 and 0<=endCol<8:
                endPiece = self.board[endRow][endCol]
                if endPiece[0] != allycolor: #enemy piece or empty square
                    #temporarily place king on square and check if in check
                    if allycolor == 'w':
                        self.whiteKinglocation = (endRow,endCol)
                    else:
                        self.blackKinglocation = (endRow,endCol)
                    inCheck, pins ,checks = self.checkForPinsAndChecks()
                    if not inCheck:
                        moves.append(Move((r,c),(endRow,endCol),self.board))
                    #if in check, place king back
                    if allycolor == 'w':
                        self.whiteKinglocation= (r,c)
                    else:
                        self.blackKinglocation= (r,c)
    '''
    Generate all valid castle movesfor the king at (r,c) and add them to the list of moves
    '''
    def getCastleMoves(self,r,c,moves):
        if self.squareUnderAttack(r,c):
            return #no castling if in check
        if (self.whitetomove and self.currentCastlingRight.wks) or (not self.whitetomove and self.currentCastlingRight.bks):
            self.getKingSideCastleMoves(r,c,moves)
        if (self.whitetomove and self.currentCastlingRight.wqs) or (not self.whitetomove and self.currentCastlingRight.bqs):
            self.getQueenSideCastleMoves(r,c,moves)
    
    def getKingSideCastleMoves(self,r,c,moves):
        if c+2>= 8:
            return
        if self.board[r][c+1] == '--' and self.board[r][c+2] == '--':  #check if empty square
            if not self.squareUnderAttack(r,c+1) and not self.squareUnderAttack(r,c+2):
                moves.append(Move((r,c),(r,c+2),self.board,isCastleMove = True))

    def getQueenSideCastleMoves(self,r,c,moves):
        if c-2<0:
            return
        if self.board[r][c-1] == '--' and self.board[r][c-2] == '--' and self.board[r][c-3] == '--': #check if empty square
            if not self.squareUnderAttack(r,c-1) and not self.squareUnderAttack(r,c-2):
                moves.append(Move((r,c),(r,c-2),self.board,isCastleMove=True ))
    '''
    Returns if player is in check, a list of pins and a list of checks
    '''    
    def checkForPinsAndChecks(self):
        pins =[] #squares where the applied pinned piece is and direction pinned from
        checks = []#squares where enemy is applying check
        inCheck  = False
        if self.whitetomove:
            enemycolor = 'b'
            allycolor = 'w'
            startRow = self.whiteKinglocation[0]
            startCol = self.whiteKinglocation[1]
        else: 
            enemycolor = 'w'
            allycolor = 'b'
            startRow= self.blackKinglocation[0]
            startCol = self.blackKinglocation[1]
        #check outward from King for pins and checks,keep track of pins
        directions = ((-1,0), (0,-1),(1,0),(0,1),(1,-1),(-1,1),(1,1),(-1,-1))      
        for j in range (len(directions)):
            d = directions[j]
            possiblePin = ()#reset possible pins
            for i in range(1,8):
                endRow = startRow + d[0]*i
                endCol = startCol + d[1]*i
                if 0<=endRow <8 and 0<=endCol <8:
                    endPiece = self.board[endRow][endCol]
                    if endPiece[0] == allycolor and endPiece[1]!= 'K':                                 
                        #checks if allied pieces are surrounding king and whether removing them could mean check or pin
                        if possiblePin == (): #1st allied piece could be pinned
                            possiblePin = (endRow, endCol, d[0],d[1])
                        else: 
                            #2nd allied piece so no pin or check possible in this direction
                            break
                    elif endPiece[0] == enemycolor:
                        type = endPiece[1]      #checking which piece surrounds the king
                        #5 possibilities here in this complex conditional
                        #1: orthogonally away from king and piece is rook
                        #2: diagonally away from king and piece is bishop
                        #3: 1 square away from king diagonally and piece is pawn
                        #4: any direction and piece is queen
                        #5: any direction 1 square away from king and piece is king (this is necessary to prevent a king move to a square controlled by another king)
                        if (0 <= j <= 3 and type=='R') or \
                                (4<= j <= 7 and type=='B')or \
                                (type == 'Q') or \
                                (i == 1 and type == 'P' and
                                ((enemycolor == 'w' and j in (6,7)) or
                                (enemycolor == 'b' and j in (4,5)))) or\
                                (i == 1 and type =='P' and ((enemycolor == 'w' and 6 <=j<=7) or (enemycolor =='b' and 4<=j<=5))) or \
                                (type == 'Q') or (i == 1 and type == 'K'):
                            if possiblePin ==(): #no piece blocking enemy, so check
                                inCheck = True
                                checks.append((endRow,endCol,d[0],d[1]))
                                break
                            else: #piece blocking so pin     
                                pins.append(possiblePin)
                                break
                        else: #enemy piece not applying check
                            break
                else:
                    break #offboard
        #check for Knight moves
        knightMoves = ((-2,-1),(2,-1),(-1,-2),(-1,2),(1,-2),(1,2),(-2,1),(2,1))
        for m in knightMoves:
            endRow = startRow + m[0]
            endCol = startCol + m[1]
            if 0<= endRow <8 and 0<=endCol < 8:
                endPiece = self.board[endRow][endCol]
                if endPiece[0] == enemycolor and endPiece[1] == 'N': #enemy Knight is attacking
                    inCheck = True
                    checks.append((endRow,endCol, m[0],m[1]))
        return inCheck,pins, checks

class CastleRights():
    def __init__(self,wks,wqs,bks,bqs):  # wks and bks is castleing from king side and wqs,bqs is casteling from queen side
        self.wks = wks
        self.wqs = wqs
        self.bks = bks
        self.bqs = bqs

class Move():
    # maps keys to values
    # key : value
    rankstoRows = {"1":7,"2":6,"3":5,"4":4,"5":3,"6":2,"7":1,"8":0}
    rowstoRanks = {v: k for k,v in rankstoRows.items()}
    filestoCols = {"a":0,"b":1,"c":2,"d":3,"e":4,"f":5,"g":6,"h":7}
    colstoFiles = {v: k for k,v in filestoCols.items()}
        
    def __init__(self,startSq,endSq,board,isEnpassantMove = False,isCastleMove = False,promotionChoice = None):
        self.startRow = startSq[0]
        self.startCol = startSq[1]
        self.endRow = endSq[0]
        self.endCol = endSq[1]
        self.pieceMoved = board[self.startRow][self.startCol]
        self.pieceCaptured = board[self.endRow][self.endCol]
        self.moveID = self.startRow*1000 + self.startCol*100 + self.endRow*10 + self.endCol  # giving each move a unique id
        #print(self.moveID) #print unique id
        #pawn promotion
        self.isPawnPromotion= (self.pieceMoved == 'wP' and self.endRow == 0) or (self.pieceMoved == 'bP' and self.endRow == 7)
        #enpassant
        self.isEnpassantMove = isEnpassantMove
        if self.isEnpassantMove:
            # Captured pawn is not on the target square in en passant
            self.pieceCaptured = 'bP' if self.pieceMoved == 'wP' else 'wP'
        #else:
            #self.pieceCaptured = board[self.endRow][self.endCol]
        self.isCapture = self.pieceCaptured != '--'
        self.enpassantPossible = ()

        if self.isPawnPromotion:
            self.promotionChoice = promotionChoice if promotionChoice else 'Q' #defaults to queen
        else:
            self.promotionChoice = None
        
        self.enpassantPossible=()
        #castle Move
        self.isCastleMove = isCastleMove
        
    '''
    Overriding the equals method
    '''
    def __eq__(self,other): #other there so as to compare an object with 'other' object
        if isinstance(other,Move):
            return self.moveID==other.moveID
        return False

    def getChessNotation(self):
        #you can add more to make it more like actual stuff like chess.com
        return self.getRankfile(self.startRow,self.startCol) + self.getRankfile(self.endRow,self.endCol)
    
    def getRankfile(self,r,c):
        return self.colstoFiles[c] + self.rowstoRanks[r]

    #overriding string function for the move log display
    def __str__(self):
        #castle move
        if self.isCastleMove:
            return 'O-O' if self.endCol == 6 else 'O-O-O'  #king side and then queen side castle
        
        endSquare = self.getRankfile(self.endRow,self.endCol)
        #pawn moves
        if self.pieceMoved[1] == 'P':
            moveString = ''
            if self.isCapture:
                moveString =  self.colstoFiles[self.startCol] +'x' + endSquare
            else:
                moveString = endSquare
            #pawn promotion 
        if self.isPawnPromotion:
            moveString += '=' + self.promotionChoice
            return moveString
        #two of the same type of piece moving to a square, Nbd3 if both knight can move to d3
        # also adding + for check move, and # for checkmate move
        #piece moves
        moveString = self.pieceMoved[1]
        if self.isCapture:
            moveString+='x'
        return moveString + endSquare