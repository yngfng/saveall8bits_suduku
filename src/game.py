import pygame
import pygame.locals as pl

import rstore
import score
from scene import TitleScene, OptionsScene
import tutorial
import const

class JukeBox(object):
    """Game jukebox that handles music and sfx.

    We have three attributes that are important:
    soundon - this will be true unless we couldn't initialize pygame music
    musicon - this can be set by the user via the menu
    sfxon   - this can be set by the user via the menu
    """

    def __init__(self):
        try:
            pygame.mixer.init()
        except: 
            self.soundon = False
        else:
            self.soundon = True

        # mapping of file names to sound effects and music
        self.sfx = rstore.sfx
        self.music = rstore.music

        self.playing = None

        # we let the user configure these
        self._sfxon = True
        self._musicon = True

    def play_music(self, name):
        if self.soundon and self._musicon:
            pygame.mixer.music.load(self.music[name])
            # -1 means repeat
            pygame.mixer.music.play(-1)
            self.playing = name

    def play_music_if(self, name):
        """Play music if not already playing."""

        if self.playing != name:
            self.play_music(name)

    def stop_music(self):
        pygame.mixer.music.stop()

    def play_sfx(self, name):
        if self.soundon and self._sfxon:
            self.sfx[name].play()

    def toggle_sfx(self):
        self._sfxon = not self._sfxon

    def toggle_music(self):
        if self._musicon:
            self.stop_music()
            self._musicon = False
        else:
            self._musicon = True
            self.play_music(self.playing)

    def is_sfx_on(self):
        return self._sfxon

    def is_music_on(self):
        return self._musicon


class Game(object):
    def __init__(self):
        """Setup pygame, display, resource loading etc."""

        pygame.init()
        self.screen = pygame.display.set_mode(const.SCREEN_SIZE)
        pygame.display.set_caption('Save all 8 bits')
        self.clock = pygame.time.Clock()

        # load images, fonts and sounds
        rstore.load_resources()

        # high scores
        score.load_high_scores()

        self.juke = JukeBox()

        self.juke.play_music('reawakening')

        pygame.mouse.set_cursor(*pygame.cursors.tri_left)

    def toggle_option(self, option_name):
        """Change option (tutorial, music, sfx).""" 
        if (option_name == OptionsScene.OPTION_TUTORIAL):
            tutorial.is_active = not tutorial.is_active
        elif (option_name == OptionsScene.OPTION_MUSIC):
            self.juke.toggle_music()
        elif (option_name == OptionsScene.OPTION_SFX):
            self.juke.toggle_sfx()

    def get_options(self):
        """Return current state of options available for options menu screen."""
        return {OptionsScene.OPTION_TUTORIAL: tutorial.is_active,
                OptionsScene.OPTION_MUSIC: self.juke.is_music_on(),
                OptionsScene.OPTION_SFX: self.juke.is_sfx_on()}

    def mainloop(self):

        # first scene of the game
        ascene = TitleScene(self)

        # initialize clock
        dt = self.clock.tick(const.FPS) / 1000.0

        while ascene != None:
            # get all events we are interested in.
            quitevent = False
            events = []
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    quitevent = True
                if ((event.type == pl.MOUSEBUTTONDOWN) or 
                    (event.type == pl.MOUSEBUTTONUP)):
                    events.append(event)

            # scene specific updating based on events.
            ascene.process_input(events, dt)

            # update not based on events.
            ascene.update(dt)

            # draw to the screen.
            ascene.render(self.screen)

            # possible change to new scene.
            ascene = ascene.next

            # draw to the screen!
            pygame.display.flip()

            # delay for correct time here.
            dt = self.clock.tick(const.FPS) / 1000.0

            if quitevent:
                ascene = None
                pygame.quit()

def main():
    gm = Game()
    gm.mainloop()
