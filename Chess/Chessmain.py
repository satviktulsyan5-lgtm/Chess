'''
This is our main driver file. It will be responsible for handling our user input and displaying the current Gamestate object.
'''
import warnings
warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API") #due to pygame being recalled many times, we must filter warning
import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"      #same with os message as above
import pygame as p
from Chess import ChessEngine, SmartMoveFinder

from multiprocessing import Process, Queue      #added so as to enable us to do other work while ai thinks

BOARD_WIDTH = BOARD_HEIGHT = 640 # can use 400 pixels as any higher means low res picture, can also use 640 pixels but need to find better qual imgs
MOVE_LOG_PANEL_WIDTH = 250
MOVE_LOG_PANEL_HEIGHT = 640
DIMENSION = 8  # chessboard is 8x8
SQ_SIZE = BOARD_HEIGHT//DIMENSION
MAX_FPS = 15  # for animation and stuff later on
IMAGES = {}
'''
Sound Initialization
'''
p.mixer.init()
sound_files = {
    'move-self': p.mixer.Sound('Sound/move-self.mp3'),
    'capture': p.mixer.Sound('Sound/capture.mp3'),
    'castle': p.mixer.Sound('Sound/castle.mp3'),
    'move-check': p.mixer.Sound('Sound/move-check.mp3'),
    'notify': p.mixer.Sound('Sound/notify.mp3'),
    'promote': p.mixer.Sound('Sound/promote.mp3')
}
soundOn = True
'''
initialize a global dictionary of images. this will be called exactly once in this main for it is too expensive to run repeatedly
'''
def loadImages():
    pieces = ['wP', 'wR', 'wB', 'wN', 'wQ',
              'wK', 'bP', 'bR', 'bN', 'bQ', 'bK', 'bB']
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(p.image.load(
            "images/" + piece + '.png'), (SQ_SIZE, SQ_SIZE))
    "Note: we can access images easily by just saying  ex.- IMAGES[wP] "
'''
a menu to select a gamemode
'''
def showmenu(screen, clock):
    # Fonts
    font = p.font.SysFont('Arial', 50, True)
    smallFont = p.font.SysFont('Arial', 30, False)
    # Menu choices
    choices = [
        '1. Play as White vs AI',
        '2. Play as Black vs AI',
        '3. Human vs Human',
        '4. AI vs AI'
    ]
    choice_rects = []
    y_start = 200
    for t in choices:
        textObj = smallFont.render(t, True, p.Color('black'))
        rect = textObj.get_rect(topleft=(150, y_start))
        choice_rects.append(rect)
        y_start += 60
    # Load background image
    bg = p.image.load("images/chessbgimg.jpg").convert()
    bg = p.transform.scale(bg, (screen.get_width(), screen.get_height()))
    while True:
        screen.blit(bg, (0, 0))  # draw background
        # Title
        title = font.render('Select Gamemode', True, p.Color('Gold'))
        screen.blit(title, (80, 50))
        mouse_pos = p.mouse.get_pos()
        y_start = 200
        for i, t in enumerate(choices):
            rect = choice_rects[i]
            rect.topleft = (100, y_start)

            # Create glow/translucent box behind text
            glow_surf = p.Surface((rect.width + 20, rect.height + 10), p.SRCALPHA)
            glow_color = (255, 255, 0, 120) if rect.collidepoint(mouse_pos) else (0, 0, 0, 100)
            glow_surf.fill(glow_color)
            screen.blit(glow_surf, (rect.x - 10, rect.y - 5))

            # Draw text
            color = p.Color('red') if rect.collidepoint(mouse_pos) else p.Color('white')
            textObj = smallFont.render(t, True, color)
            screen.blit(textObj, rect.topleft)
            y_start += 60

        p.display.flip()
        clock.tick(60)

        # Event handling
        for event in p.event.get():
            if event.type == p.QUIT:
                exit()
            elif event.type == p.MOUSEBUTTONDOWN:
                for i, rect in enumerate(choice_rects):
                    if rect.collidepoint(mouse_pos):
                        if i == 0:
                            return True, False
                        if i == 1:
                            return False, True
                        if i == 2:
                            return True, True
                        if i == 3:
                            return False, False                   
'''
Sound Playing Function
'''
def playSoundForMove(gs,move,sound_files,soundOn):
    if not soundOn:
        return
    #1) Promotion
    if move.isPawnPromotion:
        sound_files['promote'].play()
        return
    #2) Castling
    if move.isCastleMove:
        sound_files['castle'].play()
        return
    #3) Captre
    if move.pieceCaptured != '--':
        sound_files['capture'].play()
        return
    #4) if move delivers check
    if gs.inCheck:
        sound_files['move-check'].play()
        return
    #5) normal move
    sound_files['move-self'].play()

def playCheckmateSound(sound_files, soundOn):
    if soundOn:
        sound_files["notify"].play()
'''
Display pawn promotion options
'''
def showPromotionMenu(screen, whiteTurn):
    """
    Display a vertical pawn promotion menu dynamically inside the move log panel.
    Pieces are stacked vertically and always fully visible, adjusting to panel size.
    """
    pieces = ['Q', 'R', 'B', 'N']
    color = 'w' if whiteTurn else 'b'

    # Dynamic sizing
    panelX = BOARD_WIDTH
    panelY = 0
    panelWidth = MOVE_LOG_PANEL_WIDTH
    panelHeight = MOVE_LOG_PANEL_HEIGHT

    paddingTop = 20
    paddingBottom = 20
    paddingBetweenTitleAndPieces = 10
    paddingBetweenPieces = 10

    # Calculate available height for pieces
    font = p.font.SysFont('arial', 18, True)
    titleHeight = font.get_height()
    availableHeight = panelHeight - paddingTop - paddingBottom - titleHeight - paddingBetweenTitleAndPieces
    pieceSize = min(SQ_SIZE, (availableHeight - (len(pieces)-1)*paddingBetweenPieces)//len(pieces))

    # X position: center pieces horizontally inside panel
    pieceX = panelX + (panelWidth - pieceSize)//2
    # Y positions: stacked vertically
    piecerects = []
    for i in range(len(pieces)):
        rectY = paddingTop + titleHeight + paddingBetweenTitleAndPieces + i*(pieceSize + paddingBetweenPieces)
        piecerects.append(p.Rect(pieceX, rectY, pieceSize, pieceSize))

    selected = None
    running = True

    while running:
        for event in p.event.get():
            if event.type == p.QUIT:
                p.quit()
                exit()
            elif event.type == p.MOUSEBUTTONDOWN:
                mouseX, mouseY = p.mouse.get_pos()
                for i, rect in enumerate(piecerects):
                    if rect.collidepoint(mouseX, mouseY):
                        selected = pieces[i]
                        running = False
                        break

        # Draw semi-transparent panel background
        menu_bg = p.Surface((panelWidth, panelHeight))
        menu_bg.set_alpha(220)
        menu_bg.fill(p.Color('gray80'))
        screen.blit(menu_bg, (panelX, panelY))

        # Draw title
        titleText = font.render("Promote Pawn To:", True, p.Color('black'))
        titleRect = titleText.get_rect(center=(panelX + panelWidth//2, paddingTop + titleHeight//2))
        screen.blit(titleText, titleRect)

        # Draw pieces and hover highlight
        for i, rect in enumerate(piecerects):
            piece_image = IMAGES[color + pieces[i]]
            piece_image = p.transform.scale(piece_image, (pieceSize, pieceSize))
            screen.blit(piece_image, rect)

            if rect.collidepoint(p.mouse.get_pos()):
                highlight = p.Surface((pieceSize, pieceSize))
                highlight.set_alpha(120)
                highlight.fill(p.Color('yellow'))
                screen.blit(highlight, rect)

        p.display.flip()
        p.time.delay(10)

    return selected
'''
Dropdown menu with keybinds and then back to menu option
'''
class Dropdown:
    def __init__(self, move_log_rect, font, options, callback=None):
        """
        move_log_rect: pygame.Rect of the move log panel
        font: pygame.font.Font object
        options: dict of option_name : displayed_value
        callback: function(option_name) when selected
        """
        self.font = font
        self.options = list(options.keys())
        self.values = list(options.values())
        self.callback = callback
        self.expanded = False
        self.hover_index = -1

        # Arrow button (20×20)
        self.width = 20
        self.height = 20
        self.x = move_log_rect.right - self.width - 5
        self.y = move_log_rect.top + 5
        self.rect = p.Rect(self.x, self.y, self.width, self.height)

        # Option box size
        self.option_width = 180
        self.option_height = 25

    def draw(self, screen):
        # Draw arrow button
        p.draw.rect(screen, p.Color("gray60"), self.rect)

        # Draw arrow
        arrow = "▼" if not self.expanded else "▲"
        arrow_surf = self.font.render(arrow, True, p.Color("black"))
        screen.blit(arrow_surf, (self.rect.x + 3, self.rect.y + 1))

        # Draw options if expanded
        if self.expanded:
            for i, opt in enumerate(self.options):
                # box appears left of arrow
                option_rect = p.Rect(
                    self.rect.right - self.option_width,
                    self.rect.y + (i + 1) * self.option_height,
                    self.option_width,
                    self.option_height
                )

                # hover highlight
                color = p.Color("lightgray") if i != self.hover_index else p.Color("yellow")
                p.draw.rect(screen, color, option_rect)

                # Display keybind + value
                val = self.values[i] if self.values[i] is not None else "Click"
                text = f"{opt}: {val}"
                screen.blit(self.font.render(text, True, p.Color("black")),
                            (option_rect.x + 5, option_rect.y + 4))

    def handle_event(self, event):
        if event.type == p.MOUSEBUTTONDOWN:
            # Click arrow button
            if self.rect.collidepoint(event.pos):
                self.expanded = not self.expanded
                return

            # Click on option
            if self.expanded:
                for i, opt in enumerate(self.options):
                    option_rect = p.Rect(
                        self.rect.right - self.option_width,
                        self.rect.y + (i + 1) * self.option_height,
                        self.option_width,
                        self.option_height
                    )

                    if option_rect.collidepoint(event.pos):
                        if self.callback:
                            self.callback(opt)
                        self.expanded = False
                        return

        elif event.type == p.MOUSEMOTION and self.expanded:
            self.hover_index = -1
            for i in range(len(self.options)):
                option_rect = p.Rect(
                    self.rect.right - self.option_width,
                    self.rect.y + (i + 1) * self.option_height,
                    self.option_width,
                    self.option_height
                )
                if option_rect.collidepoint(event.pos):
                    self.hover_index = i
                    break
'''
main driver for the code, for user input and updating our graphics
'''
def main():
    p.init()        #initialize pygame
    screen = p.display.set_mode((BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH, BOARD_HEIGHT))  # display variable
    clock = p.time.Clock()
    screen.fill(p.Color("white"))
    playerOne,playerTwo = showmenu(screen,clock)  #who plays which side and if ai or human
    global p1,p2
    p1,p2 = playerOne,playerTwo
    moveLogFont = p.font.SysFont('Arial',14,False,False)     #defining a variable for font size to be used for move log
    global gs
    gs = ChessEngine.Gamestate()
    validMoves = gs.getValidMoves()
    moveMade = False #flag variable for when a move is made
    print(gs.board)
    animate = False #flag variable for when to animate
    dropdownFont = p.font.SysFont('Arial', 18, True)
    
    sqSelected = () #no square initially selected (tuple(row,col) used to store last click of user)
    playerClicks = [] #keep track of the player clicks (2 tuples)
    gameOver = False
    #playerOne = True #if human is playing white,then this will be true, if AI is playing then false
    #playerTwo = False #if human is playing black, then true, if AI then false
    AIThinking = False
    moveFinderProcess= None
    moveUndone = False
    global soundOn
    soundOn = True
    checkmateSoundPlayed = False
    # Move log panel rect for dropdown alignment
    move_log_rect = p.Rect(BOARD_WIDTH, 0, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_HEIGHT)
    keybinds = {
        "Undo Move": "Z",
        "Reset Board": "R",
        "Flip Board": "F",
        "Auto Flip": "A",
        "Show Enemy Moves": "E",
        "Mute/Unmute Sound": "M",
        "Back to Main Menu": "Click"
    }
    # Callback for dropdown selection
    def dropdown_callback(option_text):
        global gs
        nonlocal playerOne, playerTwo, validMoves
        if option_text == "Back to Main Menu":
            playerOne, playerTwo = showmenu(screen, clock)
            gs = ChessEngine.Gamestate()
            validMoves = gs.getValidMoves()
    
    dropdownFont = p.font.SysFont('Arial', 18, True)
    keybind_dropdown = Dropdown(move_log_rect, dropdownFont, keybinds, callback=dropdown_callback)
    loadImages()  # will only do it once, before the while loop
    running = True

    flipBlockingInput = False

    global boardFlipped,showEnemyMoves
    if not playerOne and playerTwo:  # Black vs AI
        boardFlipped = True
    else:
        boardFlipped = False
    autoFlip = True # auto flips after each move
    fixedBlackPOV = not p1 and p2 #stays in black pov
    
    showEnemyMoves = False #shows enemy moves
    
    while running:
        humanTurn = (gs.whitetomove and playerOne) or (not gs.whitetomove and playerTwo)
        for e in p.event.get():
            keybind_dropdown.handle_event(e)
            if e.type == p.QUIT:
                running = False  
            #mouse handlers
            elif e.type == p.MOUSEBUTTONDOWN:
                if not gameOver and not flipBlockingInput:    
                    location = p.mouse.get_pos()  #(x,y) position of the mouse
                    col = location[0]//SQ_SIZE
                    row = location[1]//SQ_SIZE
                    if row>=DIMENSION or col>= DIMENSION:  # condition to check whether user has pressed same square twice or clicked the log part
                        sqSelected=() #deselect
                        playerClicks= []    #player clicks resetted     
                        continue        #skip and continue
                    if boardFlipped:
                        col = 7-col
                        row = 7-row    
                    clickedSquare = (row,col)                
                    if playerClicks and clickedSquare == playerClicks[-1]:          #added to deselect if tapped twice or empty square
                        sqSelected = ()
                        playerClicks= []
                    elif gs.board[row][col] != '--' and gs.board[row][col][0] == ('w' if gs.whitetomove else 'b'): 
                        sqSelected = clickedSquare
                        playerClicks.append(clickedSquare)
                    else:
                        sqSelected=(row,col)
                        playerClicks.append(sqSelected) #append for both 1st and 2nd clicks
                    #validMoves = gs.getValidMoves()
                    if len(playerClicks) >0:
                        if gs.board[playerClicks[0][0]][playerClicks[0][1]] == "--":
                            sqSelected = ()  # Reset the sqSelected value.
                            playerClicks = []  # Reset the playerClicks list.
                    if len(playerClicks) == 2 and humanTurn:  #after 2nd click
                        for move in validMoves:
                            if move.startRow==playerClicks[0][0] and move.startCol==playerClicks[0][1] and\
                                move.endRow==playerClicks[1][0] and move.endCol==playerClicks[1][1]:
                                if move.isPawnPromotion:
                                    promotionChoice = showPromotionMenu(screen, gs.whitetomove) 
                                    move.promotionChoice = promotionChoice
                                gs.makeMove(move)
                                moveMade=True
                                animate = True
                                sqSelected =()   #reset the user clicks
                                playerClicks =[]
                                playSoundForMove(gs, move, sound_files, soundOn)

                                break

                        if not moveMade:
                            playerClicks = [sqSelected]
            #key handler
            elif e.type== p.KEYDOWN:
                if e.key == p.K_z: #undo when z is pressed (if want to change then sub z with other)
                    gs.undoMove()
                    moveMade = True
                    animate = False
                    gameOver = False
                    if AIThinking:
                        moveFinderProcess.terminate()
                        AIThinking = False
                    moveUndone = True
                if e.key == p.K_r: # reset board when r pressed
                    gs = ChessEngine.Gamestate()
                    validMoves = gs.getValidMoves()
                    sqSelected = ()
                    playerClicks = []
                    moveMade = False
                    animate = False
                    gameOver = False
                    if AIThinking:
                        moveFinderProcess.terminate()
                        AIThinking = False
                    moveUndone = True
                    if fixedBlackPOV:
                        boardFlipped = True
                    else:
                        boardFlipped = False
                if e.key == p.K_f:      #toggle flip
                    boardFlipped = not boardFlipped
                if e.key == p.K_a:      #toggle autoflip
                    autoFlip =not autoFlip
                if e.key == p.K_e:      #toggle enemy moves visibility
                    showEnemyMoves = not showEnemyMoves
                if e.key == p.K_m:  #mute or unmute sound
                    soundOn = not soundOn

        #AI move finder logic
        if not gameOver and not humanTurn and not moveUndone:
            if gs.checkmate or gs.stalemate:
                gameOver = True
            if not AIThinking:
                AIThinking = True
                returnQueue = Queue() #used to pass data between threads LIFO
                moveFinderProcess = Process(target=SmartMoveFinder.findBestMove, args= (gs,validMoves,returnQueue))
                moveFinderProcess.start() #call findbestmove(gs,validmoves,returnqueue)
            if not moveFinderProcess.is_alive():
                AIMove = returnQueue.get()
                if AIMove is None:
                    AIMove = SmartMoveFinder.findRandomMove(validMoves)
                    p.time.delay(150)
                gs.makeMove(AIMove)
                p.time.delay(150)
                moveMade=True
                animate= True
                AIThinking = False
                playSoundForMove(gs,AIMove,sound_files,soundOn)

        if moveMade:
            if animate:
                animateMove(gs.movelog[-1],screen,gs.board,clock,sqSelected,boardFlipped)
                p.time.delay(750) #delay after move done
            validMoves = gs.getValidMoves()
            if autoFlip and not fixedBlackPOV:
                boardFlipped = not boardFlipped
            moveMade = False
            animate = False
            moveUndone = False
        
        drawGamestate(screen, gs,validMoves,sqSelected,moveLogFont,boardFlipped,showEnemyMoves)  # function to draw the stuff
        
        keybind_dropdown.draw(screen)

        if gs.checkmate or gs.stalemate:
            gameOver = True
            if not checkmateSoundPlayed:
                playCheckmateSound(sound_files,soundOn)
                checkmateSoundPlayed = True
            drawEndGameText(screen, 'Stalemate' if gs.stalemate else 'Black wins by checkmate' if gs.whitetomove else  'White wins by Checkmate')
        
        clock.tick(MAX_FPS)
        p.display.flip()
'''
Responsible for all the graphics in the current gamestate 
'''
def drawGamestate(screen, gs, validMoves, sqSelected,moveLogFont,boardFlipped,showEnemyMoves):
    drawBoard(screen)  # to draw the squares on the board
    highlightSquares(screen,gs,validMoves,sqSelected,boardFlipped,showEnemyMoves)
    drawPieces(screen, gs.board,sqSelected,boardFlipped)  # to draw pieces onto the squares
    drawMoveLog(screen,gs,moveLogFont)

'''
Draw the squares on the board: : Top left square is always light
'''
def drawBoard(screen):
    global colors
    colors = [p.Color("Beige"), p.Color("Saddle Brown")]
    for r in range(DIMENSION): 
        for c in range(DIMENSION):
            color = colors[((r+c) % 2)]
            p.draw.rect(screen, color, p.Rect(
                c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))

'''
Highlight square selected and moves of the piece selected
'''
def highlightSquares(screen,gs,validMoves,sqSelected,boardFlipped,showEnemyMoves):
    if sqSelected != ():        #checks if square selected
        board_r,board_c = sqSelected
        screen_r, screen_c = (7 - board_r, 7- board_c) if boardFlipped else (board_r,board_c)

        if gs.board[board_r][board_c][0] == ('w' if gs.whitetomove else 'b'): #selected peice can be moved
            #highlight selected square
            s = p.Surface((SQ_SIZE,SQ_SIZE))
            s.set_alpha(100) #transparency value, (0->fully transparent: 255 -> opaque)
            s.fill(p.Color('blue'))
            screen.blit(s,(screen_c*SQ_SIZE,screen_r*SQ_SIZE))
            #highlight moves from that square
            s.fill(p.Color('yellow'))
            for move in validMoves:
                if move.startRow == board_r and move.startCol == board_c:
                    end_screen_r,end_screen_c = move.endRow,move.endCol
                    if boardFlipped:
                        end_screen_r,end_screen_c = 7- move.endRow,7- move.endCol
                    screen.blit(s,(end_screen_c*SQ_SIZE,end_screen_r*SQ_SIZE))
            if showEnemyMoves:
                enemy_color = ('b' if gs.whitetomove else 'w')
                s_enemy = p.Surface((SQ_SIZE,SQ_SIZE))
                s_enemy.set_alpha(50)
                s_enemy.fill(p.Color('brown'))
                for move in validMoves:
                    if move.pieceMoved[0] == enemy_color:  # Enemy piece moves
                        end_screen_r, end_screen_c = move.endRow, move.endCol
                        if boardFlipped:
                            end_screen_r, end_screen_c = 7 - move.endRow, 7 - move.endCol
                        screen.blit(s_enemy, (end_screen_c * SQ_SIZE, end_screen_r * SQ_SIZE))

'''
Draw the Pieces on the board using current gamestates board variable
'''
def drawPieces(screen, board, sqSelected, boardFlipped):
    for r in range(DIMENSION):  # screen row
        for c in range(DIMENSION):  # screen col
            # Convert screen to board coordinates
            board_r, board_c = r, c
            if boardFlipped:
                board_r, board_c = 7-r, 7-c
            
            piece = board[board_r][board_c]
            if piece != '--':
                # ALWAYS draw the piece - never skip!
                screen.blit(IMAGES[piece], p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))

'''
Draws the move log
'''
def drawMoveLog(screen,gs,font):
    moveLogRect = p.Rect(BOARD_WIDTH, 0, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_HEIGHT)
    p.draw.rect(screen,p.Color('Black'), moveLogRect)
    moveLog = gs.movelog
    moveTexts = []
    for i in range(0,len(moveLog),2):
        moveString = str(i//2 + 1) + '.' + str(moveLog[i]) + ' '
        if i+1<len(moveLog): #makes sure black made a move
            moveString+= str(moveLog[i+1]) + '  '
        moveTexts.append(moveString)
    movesPerRow = 3
    padding = 5
    lineSpacing = 3
    textY = padding
    for i in range(0,len(moveTexts),movesPerRow):
        text = ''
        for j in range(movesPerRow):
            if i+j <len(moveTexts):
                text+= moveTexts[i+j] 
        textObject = font.render(text,True,p.Color('White'))
        textLocation = moveLogRect.move(padding,textY)
        screen.blit(textObject,textLocation)    
        textY += textObject.get_height() + lineSpacing

'''
Animating a move
'''
def animateMove(move,screen,board,clock,sqSelected,boardFlipped):
    global colors
    coords = [] #list of coords animation moves through
    dR  = move.endRow - move.startRow
    dC = move.endCol - move.startCol
    framesPerSquare = 10 #frames per square
    frameCount = (abs(dR) + abs(dC) )*framesPerSquare
    startRow,startCol = move.startRow,move.startCol
    endRow,endCol = move.endRow,move.endCol
    for frame in range(frameCount+1):
        r = startRow + dR * frame/frameCount
        c = startCol + dC * frame/frameCount

        drawBoard(screen)
        drawPieces(screen,board,sqSelected,boardFlipped)

        if boardFlipped:
            r_screen = 7-r
            c_screen = 7-c
            endRow_screen = 7 - endRow
            endCol_screen = 7- endCol
        else:
            r_screen = r
            c_screen = c
            endRow_screen = endRow
            endCol_screen = endCol
        #erase the piece moved from its ending square
        color = colors[(move.endRow + move.endCol)%2]
        endSquare = p.Rect(endCol_screen*SQ_SIZE, endRow_screen*SQ_SIZE, SQ_SIZE, SQ_SIZE)
        p.draw.rect(screen,color,endSquare)
        # draw captured piece onto rectangle
        if move.pieceCaptured != '--':
            capturedRow = move.endRow
            capturedCol = move.endCol
            if move.isEnpassantMove:
                enPassantRow = (move.endRow + 1) if move.pieceCaptured[0] == 'b' else move.endRow - 1
            if boardFlipped:
                capturedRow = 7 - capturedRow
                capturedCol = 7- capturedCol
            capturedSurface = IMAGES[move.pieceCaptured].copy()
            alpha = int(270*(1-frame/frameCount)) #fade from 255 to 0
            capturedSurface.set_alpha(alpha)
            capturedRect = p.Rect(capturedCol * SQ_SIZE,capturedRow*SQ_SIZE,SQ_SIZE,SQ_SIZE)
            screen.blit(capturedSurface,capturedRect)
        #draw moving piece
        screen.blit(IMAGES[move.pieceMoved],p.Rect(c_screen*SQ_SIZE, r_screen*SQ_SIZE, SQ_SIZE,SQ_SIZE))
        
        p.display.flip()
        clock.tick(60)
    
'''
Draws game end text like checkmate or stalemate
'''
def drawEndGameText(screen,text):
    font = p.font.SysFont('Helvitica',32,True,False)
    textObject = font.render(text,0,p.Color('black'))
    textLocation = p.Rect(0,0,BOARD_WIDTH,BOARD_HEIGHT).move(BOARD_WIDTH/2 - textObject.get_width()/2, BOARD_HEIGHT/2 - textObject.get_height()/2)
    screen.blit(textObject,textLocation)
    #textObject = font.render(text,0,p.Color('Black'))      if you want layering
    #screen.blit(textObject,textLocation.move(2,3))     

if __name__ == "__main__":
    main()