import sys

# The major, minor version numbers your require
MIN_VER = (3, 6)

if sys.version_info[:2] < MIN_VER:
    sys.exit("This game requires Python {}.{}.".format(*MIN_VER))

from derplings.bootstrap import bootstrap_game
from zkit import config

import pygame.mixer
import os.path

if __name__ == "__main__":
    if config.getboolean("general", "profile"):
        import cProfile
        import pstats

        game = bootstrap_game()
        cProfile.run("game.loop()", "results.prof")
        p = pstats.Stats("results.prof")
        p.strip_dirs()
        p.sort_stats("cumulative").print_stats(50)

    else:
        try:
            game = bootstrap_game()
            game.loop()
            pygame.mixer.music.stop()
        except:
            import pygame  # wtf does this do?

            pygame.quit()
            raise
