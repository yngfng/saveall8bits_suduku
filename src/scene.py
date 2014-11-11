import os

import pygame
import pygame.locals as pl

from const import *
import board
import hud
import cell
import rstore
import score
import tutorial
from basescene import Scene

def _get_level(fname):
    """Return full path to level file."""
    return os.path.join(rstore.base_path, 'level', fname)
    

class PlayScene(Scene):
    def __init__(self, game):
        super(PlayScene, self).__init__()

        self.game = game

        self._board = board.GameBoard()
        self._hud = hud.Hud(self, self._board)

        self.levnum = 1
        #tutorial.is_active = False
        self.load_level()

    def load_level(self, reset=False):
        # load the data onto the board
        fname = 'l{0}.txt'.format(self.levnum)
        self._board.setup_board(_get_level(fname))
        # update the HUD
        self._hud.set_data(self.levnum)
        # reset any game state
        self._isplayer = True
        # bullet sprites
        self._bullets = []
        # store clicked board cell
        self._clickcell = None
        # cell positions of any bits the tutorial wants to flash
        self._tutflash = []
        # load the relevant tutorial
        if tutorial.is_active and not reset:
            self._tutorial = tutorial.Tutorial(self)
        else:
            self._tutorial = tutorial.DummyTutorial()
        # play sound for the start of the tutorial
        if self._tutorial.step is not None:
            self.game.juke.play_sfx('turn')

        self.next = self

    def mouseup_board(self, pos):
        if (board.get_clicked_cell(pos) == self._clickcell):
            if self._tutorial.is_allowed(self._clickcell):
                self.handle_board_click(self._clickcell)
                self._clickcell = None

    def mousedown_board(self, pos):
        self._clickcell = board.get_clicked_cell(pos)
        pass

    def mouseover_board(self, pos):
        pass
    
    def mouseup_hud(self, pos):
        if self._tutorial.is_finished():
            # send the position w.r.t. the top left of the HUD
            hudpos = (pos[0] - HUD_POS[0], pos[1] - HUD_POS[1])
            hud_event = self._hud.handle_mouse_up(hudpos)
            if (hud_event == hud.EVENT_NEXT):
                if (self.levnum != NUM_LEVELS):
                    self.levnum += 1
                    self.load_level()
            elif (hud_event == hud.EVENT_PREVIOUS):
                if (self.levnum != 1):
                    self.levnum -= 1
                    self.load_level()
            elif (hud_event == hud.EVENT_RESET):
                # don't restart the tutorial
                self.load_level(reset=True)
            elif (hud_event == hud.EVENT_MAIN):
                self.next = TitleScene(self.game)

    def mousedown_hud(self, pos):
        pass
            
    def mousedown_tutorial(self, pos):
        pass

    def mouseover_hud(self, pos):
        # the HUD isn't active until the tutorial is finished
        if self._tutorial.is_finished():
            # send the position w.r.t. the top left of the HUD
            hudpos = (pos[0] - HUD_POS[0], pos[1] - HUD_POS[1])
            self._hud.handle_cursor_position(hudpos)

    def mouseup_tutorial(self, pos):
        if self._tutorial.try_advance():
            self.game.juke.play_sfx('turn')

    def mouseover_board(self, pos):
        pass

    def process_input(self, events, dt):
        # mouse position
        mpos = pygame.mouse.get_pos()

        # send position to the appropriate handler
        if hud.pos_on_hud(mpos):
            self.mouseover_hud(mpos)
        elif board.pos_on_board(mpos):
            self.mouseover_board(mpos)

        for ev in events:
            if (ev.type == pl.MOUSEBUTTONDOWN):
                if tutorial.pos_on_tutorial(ev.pos):
                    self.mousedown_tutorial(ev.pos)
                elif board.pos_on_board(ev.pos):
                    self.mousedown_board(ev.pos)
                elif hud.pos_on_hud(ev.pos):
                    self.mousedown_hud(ev.pos)
            elif (ev.type == pl.MOUSEBUTTONUP):
                if tutorial.pos_on_tutorial(ev.pos):
                    self.mouseup_tutorial(ev.pos)
                elif board.pos_on_board(ev.pos):
                    self.mouseup_board(ev.pos)
                elif hud.pos_on_hud(ev.pos):
                    self.mouseup_hud(ev.pos)

    def handle_board_click(self, pos):
        if not self._isplayer:
            return
        # can we move to this position
        if self._board.is_move_cell(pos):
            if self._board.is_goal_cell(pos):
                self.game.juke.play_sfx('goal')
            else:
                self.game.juke.play_sfx('click')
            self._board.make_move(pos)
            # update the hud
            self._hud.set_moves(self._board.nmoves)
            self._hud.set_saved(self._board.nsaved)
            self.finish_player_move()
        elif self._board.is_player_cell(pos):
            self.game.juke.play_sfx('click')
            self._board.set_selected(pos)
        else:
            pass
            #self.game.juke.play_sfx('error')

    def finish_player_move(self):
        """Called at the end of the player move"""
        self._isplayer = False
        # create bullets
        playercells = self._board.get_cells_by_type(cell.C_PLAYER)
        guncells = self._board.get_cells_by_type(cell.C_GUN)
        for g in guncells:
            p = [g.pos[0] * CSIZE + OUTLINE, g.pos[1] * CSIZE + OUTLINE]
            if self._board.can_hit(g):
                self._bullets.append(cell.BulletSprite(p, g.direction))
                # we hit the player
                self.game.juke.play_sfx('shoot')

    def finish_opponent_move(self):
        pass

    def handle_tutorial_cells(self):
        """Make the right bits flash for this stage of the tutorial."""
        # set any currently flashing bits to not flash
        for cpos in self._tutflash:
            c = self._board.get_cell(cpos)
            if c is not None:
                c.set_flash(False)
        self._tutflash = []
        # check if there are any new bits to flash
        allowed_pos = self._tutorial.get_allowed_cells()
        for cpos in allowed_pos:
            #if self._board.is_player_cell(cpos):
            self._tutflash.append(cpos)
            c = self._board.get_cell_or_move_cell(cpos)
            c.set_flash(True)

    def update(self, dt):

        for c in self._board.get_cells():
            c.update(dt)
        for c in self._board.get_move_cells():
            c.update(dt)
    
        if self._isplayer:
            self.update_player(dt)
        else:
            self.update_opponent(dt)

        # update tutorial
        if self._tutorial.changed:
            self.handle_tutorial_cells()
        self._tutorial.update(dt)

    def update_player(self, dt):
        if not self._board.can_move():
            score = (self._board.nsaved, self._board.nmoves)
            # level 'complete', change scene
            if (self._board.nsaved + self._board.nlost != 8):
                self.next = StrandedScene(self, score)
            else:
                self.next = LevelCompleteScene(self, score)
        else:
            pass

    def update_opponent(self, dt):
        # advance bullets
        playercells = self._board.get_cells_by_type(cell.C_PLAYER)
        for b in list(self._bullets):
            b.update(dt)
            # remove if off screen
            if not board.brect.colliderect(b):
                self._bullets.remove(b)
            # check for collision with player
            for p in playercells:
                if pygame.sprite.collide_rect(b, p):
                    self._bullets.remove(b)
                    p.health -= 1
                    if (p.health == 0):
                        self.game.juke.play_sfx('shatter')
                        self._board.nlost += 1
                        self._hud.set_lost(self._board.nlost)
                        self._board.remove_cell(p.pos)
                
        # check if all bullets are gone, and if so give player control
        # back
        if not self._bullets:
            self._isplayer = True
            self.finish_opponent_move()

    def render(self, screen):
        # blit background
        screen.blit(rstore.images['bg'], (0, 0))

        # render to the board surface
        board.draw_board(self._board, self._bullets)

        # render to the HUD surface
        self._hud.draw()

        # render to the tutorial surface
        tutorial.draw_tutorial(self._tutorial)

        # blit the board surface to the screen
        screen.blit(board.bsurf, (XOFF, YOFF))

        # blit the hud surface to the screen
        screen.blit(hud.hsurf, HUD_POS)

        # blit the tutorial surface to the screen
        screen.blit(tutorial.tsurf, TUT_POS)

class StrandedScene(Scene):
    # total time spent in this scene
    _TTOT = 2
    # delay before doing anything
    _DELAY = 0.2
    def __init__(self, pscene, score):
        super(StrandedScene, self).__init__()
        self._pscene = pscene
        self._score = score
        self._juke = self._pscene.game.juke

        self._played_sfx = False
        self._tpassed = 0
        self._stranded_txt = rstore.fonts['finish'].render('Stranded', False, WHITE)

        # rate of changing alpha with time for fading out
        self._alpharate = 255 / (self._TTOT - self._DELAY)

    def update(self, dt):
        self._tpassed += dt
        # fade text out
        alpha = max(255 - self._alpharate * self._tpassed, 0)
        self._stranded_txt.set_alpha(alpha)
        if self._tpassed > self._TTOT:
            self.next = LevelCompleteScene(self._pscene, self._score)

    def render(self, screen):
        self._pscene.render(screen)
        if (self._tpassed > self._DELAY):
            screen.blit(self._stranded_txt, (165, 200))
            if not self._played_sfx:
                self._juke.play_sfx('stranded')
                self._played_sfx = True

class LevelCompleteScene(Scene):
    def __init__(self, pscene, sc):
        super(LevelCompleteScene, self).__init__()
        self.pscene = pscene
        if score.is_better(pscene.levnum, sc):
            score.update_high_scores(pscene.levnum, sc)
            # don't show the 'high score text if we didn't save any
            # bits!
            if (self.pscene._board.nsaved > 0):
                self.high = True
            else:
                self.high = False
        else:
            self.high = False
        self.played_high_sound = False
        self.played_complete_sound = False
        if (sc[0] == 8):
            txt = 'All 8 bits saved!'
        else:
            txt = 'Saved {0}/{1} bits'.format(sc[0], 8)
        # todo: play something different if stranded
        self.juke = self.pscene.game.juke

        self.complete_txt = rstore.fonts['finish'].render(txt, True, WHITE)
        self.high_txt = rstore.fonts['finish'].render('New high score!', True, RED1)
        self.pscene = pscene
        self.tpassed = 0

    def update(self, dt):
        self.tpassed += dt
        if self.tpassed > 3:
            if (self.pscene.levnum == NUM_LEVELS):
                self.next = TitleScene(self.pscene.game)
            else:
                self.pscene.levnum += 1
                self.pscene.load_level()
                self.next = self.pscene

    def render(self, screen):
        # keep rendering the play scene
        self.pscene.render(screen)

        if (self.tpassed > 0.1):
            screen.blit(self.complete_txt, (150, 200))
            if not self.played_complete_sound:
                self.juke.play_sfx('complete')
                self.played_complete_sound = True
        if self.high and self.tpassed > 1:
            if not self.played_high_sound:
                self.juke.play_sfx('highscore')
                self.played_high_sound = True
            screen.blit(self.high_txt, (150, 250))

_FILL_COL = ORANGEY

def _get_title_surfaces(txt, border=10, off=10):
    """Return surface when not selected and when selected."""
    
    tsurf = rstore.fonts['menu'].render(txt, True, BLACK)
    tsize = tsurf.get_size()

    # create two larger surfaces for border and offset
    extra = 2 * (border + off)
    not_selected_surf = pygame.Surface((tsize[0] + extra, tsize[1] + extra))
    selected_surf = pygame.Surface((tsize[0] + extra, tsize[1] + extra))

    not_selected_surf.fill(_FILL_COL)

    selected_surf.fill(BLACK)
    selected_surf_mid = pygame.Surface((tsize[0] + 2 * off, tsize[1] + 2 * off))
    selected_surf_mid.fill(_FILL_COL)
    selected_surf.blit(selected_surf_mid, (border, border))

    not_selected_surf.blit(tsurf, (off + border, off + border))
    selected_surf.blit(tsurf, (off + border, off + border))

    return not_selected_surf, selected_surf

class TextClickingScene(Scene):
    """Base class for screens with clickable text."""
    def __init__(self, game, options):
        super(TextClickingScene, self).__init__()
        self._game = game
        self.options = options

        # the actual surfaces
        self.surfaces = {}
        # rects for checking mouse hover
        self.rects = {}
        for opt in self.options:
            name = self.options[opt][0]
            pos = self.options[opt][1]
            not_selected_surf, selected_surf = _get_title_surfaces(name)
            # rect for mouse hover
            self.surfaces[opt] = [not_selected_surf, selected_surf]
            # apply the position offset to the rect for easy
            # comparison with mouse position.
            new_rect = not_selected_surf.get_rect()
            new_rect.x += pos[0]
            new_rect.y += pos[1]
            self.rects[opt] = new_rect

        # have we clicked to switch the scene?
        self.switch = False
        self.new_scene = None
        # time waited so far since clicking
        self.dtswitch = 0
        # time to wait between clicking and switching to the scene
        self.wait_time = 0
    
    def process_input(self, events, dt):
        if self.switch:
            # we are in the process of scene switching, just waiting
            # for the timeout
            return

        pos = pygame.mouse.get_pos()
        for opt, r in self.rects.items():
            if r.collidepoint(pos):
                self.options[opt][2] = True
            else:
                self.options[opt][2] = False

        for e in events:
            if (e.type == pl.MOUSEBUTTONUP):
                # did we click one of the options?
                for opt, r in self.rects.items():
                    if r.collidepoint(pos):
                        # we clicked on a button
                        self._game.juke.play_sfx('menuclick')
                        newscene_name = self.options[opt][3]
                        try:
                            # time to pause before switching screen
                            self.wait_time = self.options[opt][4]
                        except:
                            self.wait_time = 0
                        self.new_scene = get_scene(newscene_name)
                        self.switch = True
                        self.dtswitch = 0

    def update(self, dt):
        if self.switch:
            self.dtswitch += dt
            if (self.dtswitch > self.wait_time):
                # create the new scene object
                newscene = self.new_scene(self._game)
                self.next = newscene

    def render(self, screen):
        # blit background
        screen.blit(rstore.images['bg'], (0, 0))

        for opt, val in self.options.items():
            surfs = self.surfaces[opt]
            pos = val[1]
            selected = val[2]
            if (selected):
                # not selected
                screen.blit(surfs[1], pos)                
            else:
                screen.blit(surfs[0], pos)

# data for the back button in all screens
_back_data = ['Back', (220, 400), False, 'title']

class ToggleButton(object):
    def __init__(self, image_on, image_off, pos, on=True):
        self.image_on = image_on
        self.image_off = image_off
        if on:
            self.image = self.image_on
        else:
            self.image = self.image_off

        self.rect = self.image.get_rect()
        self.rect.x += pos[0]
        self.rect.y += pos[1]

    def toggle(self):
        if (self.image == self.image_on):
            self.image = self.image_off
        else:
            self.image = self.image_on

    def set_hover(self, hover):
        # can change image here if we are hovering
        pass


class OptionsScene(TextClickingScene):
    options = {'back': _back_data}
    ON_COL = (55, 117, 61)
    OFF_COL = (166, 0, 0)
    SIZE = 60
    OPTION_TUTORIAL = 'tutorial'
    OPTION_MUSIC = 'music'
    OPTION_SFX = 'sfx'
    button_data = [(OPTION_TUTORIAL, (340, 130)), (OPTION_MUSIC, (340, 210)), 
                   (OPTION_SFX, (340, 290))]
    def __init__(self, game):

        super(OptionsScene, self).__init__(game, self.options)
        self._game = game

        self._tut_text = rstore.fonts['highscore'].render('Tutorial', True, BLACK)
        self._music_text = rstore.fonts['highscore'].render('Music', True, BLACK)
        self._sfx_text = rstore.fonts['highscore'].render('SFX', True, BLACK)

        self._buttons = {}
        # create ToggleButtons
        self.create_buttons()

    def create_buttons(self):
        on_text = rstore.fonts['highscore'].render('on', True, BLACK)
        off_text = rstore.fonts['highscore'].render('off', True, BLACK)
        # get the state of the buttons!
        bstate = self._game.get_options()
        for bname, bpos in self.button_data:
            on_surf = pygame.Surface((self.SIZE, self.SIZE))
            on_surf.fill(self.ON_COL)
            on_surf.blit(on_text, (10, 10))
            off_surf = pygame.Surface((self.SIZE, self.SIZE))
            off_surf.fill(self.OFF_COL)
            off_surf.blit(off_text, (10, 10))
            self._buttons[bname] = ToggleButton(on_surf, off_surf, bpos,
                                                on=bstate[bname])

    def process_input(self, events, dt):
        super(OptionsScene, self).process_input(events, dt)

        # check if any buttons clicked and toggle their image if so
        for ev in events:
            if (ev.type == pl.MOUSEBUTTONUP):
                for butname, but in self._buttons.items():
                    if but.rect.collidepoint(ev.pos):
                        self._game.juke.play_sfx('menuclick')                        
                        but.toggle()
                        # change the option i.e. switch off the sound
                        # etc.
                        self._game.toggle_option(butname)

        # hovering
        pos = pygame.mouse.get_pos()
        for butname, but in self._buttons.items():
            if but.rect.collidepoint(pos):
                but.set_hover(True)
            else:
                but.set_hover(False)
    
    def render(self, screen):
        super(OptionsScene, self).render(screen)

        screen.blit(self._tut_text, (220, 140))
        screen.blit(self._music_text, (220, 220))
        screen.blit(self._sfx_text, (220, 300))

        for but in self._buttons.values():
            screen.blit(but.image, but.rect)


class TitleScene(TextClickingScene):
    # name of button, position, whether it is selected, scene name it
    # leads to, how long to pause for before changing scene.
    options = {'new': ['Play', (220, 150), False, 'play', 0.8],
               'options': ['Options', (220, 250), False, 'options'],
               'high': ['High Scores', (220, 350), False, 'high'],
               'quit': ['Quit', (220, 450), False, 'quit']}

    def __init__(self, game):
        self._game = game
        self._title_text = rstore.fonts['title'].render('SAVE ALL       BITS', True, BLACK)
        self._title_pos = (150, 50)
        cell_im = cell.PlayerCellSprite([0, 0], **{'health': 8}).image
        self._cell_im = cell_im
        super(TitleScene, self).__init__(self._game, self.options)

    def render(self, screen):
        super(TitleScene, self).render(screen)
        screen.blit(self._title_text, self._title_pos)
        screen.blit(self._cell_im, (390, 65))


class HighScoreScene(TextClickingScene):
    options = {'back': _back_data}

    def __init__(self, game):
        self._game = game
        super(HighScoreScene, self).__init__(self._game, self.options)

        self.title_text = rstore.fonts['menu'].render('High Scores', True, BLACK)
        self.head_text = rstore.fonts['highscore'].render('Level Saved Moves', True, BLACK)

        self._score_text = []
        self.set_score_text()

    def set_score_text(self):
        scs = score.scores
        levs = scs.keys()
        levs.sort()
        for lev in levs:
            nsaved, nmoved = score.scores[lev]
            nmovedstr = score.get_score_string(nmoved)
            if nsaved == score.NO_SCORE:
                nsavedstr = ' - '
            else:
                nsavedstr = str(nsaved) + '/8'
            txt = rstore.fonts['highscore'].render('{0}    {1}    {2}'.format(lev, nsavedstr, nmovedstr), True, BLACK)
            self._score_text.append(txt)

    def render(self, screen):
        super(HighScoreScene, self).render(screen)

        screen.blit(self.title_text, (220, 80))
        screen.blit(self.head_text, (220, 140))

        for (i, line) in enumerate(self._score_text):
            screen.blit(line, (245, 180 + i*25))


class QuitScene(Scene):
    def __init__(self, game):
        self.next = None

SCENE_MAP = {'title': TitleScene,
             'options': OptionsScene,
             'play': PlayScene,
             'high': HighScoreScene,
             'quit': QuitScene}
             
def get_scene(name):
    return SCENE_MAP[name]
