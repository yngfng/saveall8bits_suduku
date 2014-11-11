FPS = 30

SCREEN_SIZE = (800, 600)

# colors for the cells
# Player cells
PCOL = {
    1: '#c9bab0',
    2: '#435662',
    3: '#28333b',
    4: '#2f4f4f',
    5: '#701010',
    6: '#63260A',
    8: '#701010'
}
# possible move cells
MOVCOL = (255, 249, 183)
# goal cells
GCOL = (103, 159, 245)
# obstacle cells
OCOL = (255, 210, 236)
# bullet cells
BULLETCOL = (200, 100, 80)
# color for border around player when selected
SELCOL = (255, 255, 0)

# some other colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
# used in menus and around playscene
ORANGEY = (239, 212, 122)

# color used for text
GREY1 = (68, 68, 68)
# color of reset button and new high score
RED1 = (166, 0, 0)
# color of main menu button
BLUE1 = (16, 30, 81)

# board cell size in px
CSIZE = 50
# outline in px (note the grid is only actually 1 px)
OUTLINE = 2

# topleft of board is at (XOFF, YOFF)
XOFF = 80
YOFF = 80

# show the grid?
SHOWGRID = True

HUD_SIZE = (200, 400)
HUD_POS = (550, 80)

TUT_SIZE = (400, 0)
TUT_BORDER = 4
TUT_OFFSET = 4
TUT_LINE_PAD = 4
TUT_POS = (80, 400)

# note level indexes start at 1, so final level number is NUM_LEVELS
NUM_LEVELS = 8
