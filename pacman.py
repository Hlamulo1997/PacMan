import pygame
import sys
import random
import os
from enum import Enum

# ============================================================
# PAC-MAN GAME
# ============================================================

# ---------- Constants ----------
TILE = 24
ROWS = 20
COLS = 19

WIDTH = COLS * TILE
HEIGHT = ROWS * TILE + 40

FPS = 60

# ---------- Colours ----------
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 235, 59)
BLUE = (25, 25, 112)
RED = (255, 82, 82)
PINK = (255, 143, 171)
CYAN = (0, 229, 255)
ORANGE = (255, 160, 0)
FRIGHT = (33, 33, 222)

# ---------- Maze ----------
# # = wall
# . = normal dot
# o = power pellet
# space = empty
# - = ghost door

MAZE = [
    "###################",
    "#........#........#",
    "#o##.###.#.###.##o#",
    "#.................#",
    "#.##.#.#####.#.##.#",
    "#....#...#...#....#",
    "####.###.#.###.####",
    "####.#.......#.####",
    "####.#.##-##.#.####",
    "#......#---#......#",
    "####.#.#####.#.####",
    "####.#.......#.####",
    "####.#.#####.#.####",
    "#........#........#",
    "#.##.###.#.###.##.#",
    "#o..#..........#..#",
    "###.#.#.#####.#.###",
    "###.#.#.....#.#.###",
    "#.....#.###.#.....#",
    "###################",
]


# ============================================================
# Direction Enum
# ============================================================

class Dir(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)


# ============================================================
# Pygame Setup
# ============================================================

pygame.init()

# Initialize mixer for sound
try:
    pygame.mixer.init()
    SOUND_ENABLED = True
except pygame.error:
    print("Warning: Sound could not be initialized.")
    SOUND_ENABLED = False


screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("PAC-MAN")

clock = pygame.time.Clock()

font = pygame.font.Font(None, 28)
big_font = pygame.font.Font(None, 56)


# ============================================================
# SOUND SYSTEM
# ============================================================

# The sounds folder is automatically located next to pacman.py
SOUND_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "sounds"
)


def load_sound(filename):
    """
    Load a sound from the sounds folder.

    If the file does not exist, the game continues without it.
    """

    if not SOUND_ENABLED:
        return None

    path = os.path.join(SOUND_DIR, filename)

    try:
        return pygame.mixer.Sound(path)

    except (pygame.error, FileNotFoundError):
        print(f"Warning: Sound file not found: {path}")
        return None


def play_sound(sound):
    """Play a sound if it was loaded successfully."""

    if sound is not None:
        try:
            sound.play()
        except pygame.error:
            pass


# Load game sounds
sound_dot = load_sound("dot.wav")
sound_power = load_sound("power.wav")
sound_ghost = load_sound("eat_ghost.wav")
sound_death = load_sound("death.wav")
sound_win = load_sound("win.wav")


# ============================================================
# OPTIONAL BACKGROUND MUSIC
# ============================================================

music_path = os.path.join(
    SOUND_DIR,
    "music.wav"
)

if SOUND_ENABLED and os.path.exists(music_path):

    try:
        pygame.mixer.music.load(music_path)

        # Volume from 0.0 to 1.0
        pygame.mixer.music.set_volume(0.35)

        # -1 means loop forever
        pygame.mixer.music.play(-1)

    except pygame.error:
        print("Warning: Could not load music.wav")


# ============================================================
# Board Class
# ============================================================

class Board:

    def __init__(self, layout):

        self.grid = [list(row) for row in layout]

        self.dots = 0

        for y, row in enumerate(self.grid):

            for x, ch in enumerate(row):

                if ch == "." or ch == "o":
                    self.dots += 1

    def is_wall(self, x, y):

        if 0 <= x < COLS and 0 <= y < ROWS:

            return self.grid[y][x] == "#"

        return True

    def at(self, x, y):

        if 0 <= x < COLS and 0 <= y < ROWS:

            return self.grid[y][x]

        return "#"

    def eat(self, x, y):

        if not (0 <= x < COLS and 0 <= y < ROWS):
            return None

        if self.grid[y][x] == ".":

            self.grid[y][x] = " "
            self.dots -= 1

            return "dot"

        if self.grid[y][x] == "o":

            self.grid[y][x] = " "
            self.dots -= 1

            return "power"

        return None


# ============================================================
# Actor Class
# ============================================================

class Actor:

    def __init__(self, x, y, color, speed):

        self.tile_x = x
        self.tile_y = y

        self.px = x * TILE
        self.py = y * TILE

        self.color = color
        self.speed = speed

        self.dir = None
        self.next_dir = None

        self.mouth = 0

    def tile_centered(self):

        return (
            self.px % TILE == 0
            and self.py % TILE == 0
        )

    def update_tile(self):

        self.tile_x = round(self.px / TILE)
        self.tile_y = round(self.py / TILE)

    def can_move(self, direction, board):

        if direction is None:
            return False

        dx, dy = direction.value

        nx = self.tile_x + dx
        ny = self.tile_y + dy

        return not board.is_wall(nx, ny)


# ============================================================
# Pac-Man Class
# ============================================================

class Pacman(Actor):

    def __init__(self, x, y):

        super().__init__(
            x,
            y,
            YELLOW,
            3
        )

    def move(self, board):

        if self.tile_centered():

            self.update_tile()

            # Try buffered direction first
            if (
                self.next_dir is not None
                and self.can_move(self.next_dir, board)
            ):

                self.dir = self.next_dir

            # Stop if current direction is blocked
            if not self.can_move(self.dir, board):

                self.dir = None

        if self.dir:

            dx, dy = self.dir.value

            self.px += dx * self.speed
            self.py += dy * self.speed

            self.mouth = (self.mouth + 1) % 30

    def draw(self, surface):

        cx = self.px + TILE // 2
        cy = self.py + TILE // 2 + 40

        # Direction of Pac-Man's mouth
        if self.dir == Dir.LEFT:

            base_angle = 180

        elif self.dir == Dir.UP:

            base_angle = 270

        elif self.dir == Dir.DOWN:

            base_angle = 90

        else:

            base_angle = 0

        # Mouth animation
        mouth_angle = (
            15 + 15 * abs(15 - self.mouth) // 15
        )

        # Pac-Man body
        pygame.draw.circle(
            surface,
            YELLOW,
            (cx, cy),
            TILE // 2 - 2
        )

        # Mouth
        v1 = pygame.math.Vector2(
            1,
            0
        ).rotate(
            base_angle - mouth_angle
        )

        v2 = pygame.math.Vector2(
            1,
            0
        ).rotate(
            base_angle + mouth_angle
        )

        pygame.draw.polygon(
            surface,
            BLACK,
            [
                (cx, cy),

                (
                    cx + (TILE // 2) * v1.x,
                    cy + (TILE // 2) * v1.y
                ),

                (
                    cx + (TILE // 2) * v2.x,
                    cy + (TILE // 2) * v2.y
                )
            ]
        )


# ============================================================
# Ghost Class
# ============================================================

class Ghost(Actor):

    COLORS = [
        RED,
        PINK,
        CYAN,
        ORANGE
    ]

    def __init__(self, x, y, index):

        super().__init__(
            x,
            y,
            self.COLORS[index],
            2
        )

        self.home = (x, y)

        self.frightened = 0

    def choose_direction(self, board, pacman):

        options = []

        for direction in Dir:

            if self.can_move(direction, board):

                options.append(direction)

        # Avoid immediately reversing
        if self.dir is not None and len(options) > 1:

            reverse = Dir(
                (
                    -self.dir.value[0],
                    -self.dir.value[1]
                )
            )

            options = [
                d for d in options
                if d != reverse
            ]

        if not options:

            return None

        # Frightened ghosts move randomly
        if self.frightened > 0:

            return random.choice(options)

        # Otherwise chase Pac-Man
        best_direction = None
        best_distance = float("inf")

        for direction in options:

            dx, dy = direction.value

            nx = self.tile_x + dx
            ny = self.tile_y + dy

            distance = (
                (nx - pacman.tile_x) ** 2
                +
                (ny - pacman.tile_y) ** 2
            )

            if distance < best_distance:

                best_distance = distance
                best_direction = direction

        return best_direction

    def move(self, board, pacman):

        if self.frightened > 0:

            self.frightened -= 1

        if self.tile_centered():

            self.update_tile()

            self.dir = self.choose_direction(
                board,
                pacman
            )

        if self.dir:

            dx, dy = self.dir.value

            self.px += dx * self.speed
            self.py += dy * self.speed

    def respawn(self):

        self.px = self.home[0] * TILE
        self.py = self.home[1] * TILE

        self.tile_x = self.home[0]
        self.tile_y = self.home[1]

        self.frightened = 0
        self.dir = None

    def draw(self, surface):

        cx = self.px + TILE // 2
        cy = self.py + TILE // 2 + 40

        if self.frightened > 0:

            color = FRIGHT

        else:

            color = self.color

        # Ghost body
        pygame.draw.circle(
            surface,
            color,
            (cx, cy - 2),
            TILE // 2 - 2
        )

        pygame.draw.rect(
            surface,
            color,
            (
                cx - TILE // 2 + 2,
                cy - 2,
                TILE - 4,
                TILE // 2
            )
        )

        # Eyes
        pygame.draw.circle(
            surface,
            WHITE,
            (cx - 5, cy - 4),
            3
        )

        pygame.draw.circle(
            surface,
            WHITE,
            (cx + 5, cy - 4),
            3
        )

        # Pupils
        pygame.draw.circle(
            surface,
            BLUE,
            (cx - 5, cy - 4),
            1
        )

        pygame.draw.circle(
            surface,
            BLUE,
            (cx + 5, cy - 4),
            1
        )


# ============================================================
# Create Game
# ============================================================

def create_game():

    board = Board(MAZE)

    pacman = Pacman(9, 15)

    ghosts = [

        Ghost(8, 9, 0),
        Ghost(9, 9, 1),
        Ghost(10, 9, 2),
        Ghost(9, 8, 3)

    ]

    score = 0
    lives = 3

    return board, pacman, ghosts, score, lives


# ============================================================
# Draw Maze
# ============================================================

def draw_maze(board):

    for y, row in enumerate(board.grid):

        for x, character in enumerate(row):

            rect = pygame.Rect(
                x * TILE,
                y * TILE + 40,
                TILE,
                TILE
            )

            # Walls
            if character == "#":

                pygame.draw.rect(
                    screen,
                    BLUE,
                    rect
                )

            # Normal dots
            elif character == ".":

                pygame.draw.circle(
                    screen,
                    WHITE,
                    rect.center,
                    3
                )

            # Power pellets
            elif character == "o":

                pygame.draw.circle(
                    screen,
                    WHITE,
                    rect.center,
                    7
                )


# ============================================================
# Main Game
# ============================================================

def main():

    board, pacman, ghosts, score, lives = create_game()

    state = "play"

    key_map = {

        pygame.K_UP: Dir.UP,
        pygame.K_DOWN: Dir.DOWN,
        pygame.K_LEFT: Dir.LEFT,
        pygame.K_RIGHT: Dir.RIGHT,

        pygame.K_w: Dir.UP,
        pygame.K_s: Dir.DOWN,
        pygame.K_a: Dir.LEFT,
        pygame.K_d: Dir.RIGHT

    }

    running = True

    while running:

        clock.tick(FPS)

        # ----------------------------------------------------
        # EVENTS
        # ----------------------------------------------------

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:

                # Movement
                if event.key in key_map:

                    pacman.next_dir = key_map[event.key]

                # Restart
                if (
                    event.key == pygame.K_r
                    and state != "play"
                ):

                    board, pacman, ghosts, score, lives = (
                        create_game()
                    )

                    state = "play"

                    # Restart background music
                    if SOUND_ENABLED and os.path.exists(music_path):

                        try:

                            pygame.mixer.music.play(-1)

                        except pygame.error:

                            pass

        # ----------------------------------------------------
        # UPDATE GAME
        # ----------------------------------------------------

        if state == "play":

            # Move Pac-Man
            pacman.move(board)

            # Move ghosts
            for ghost in ghosts:

                ghost.move(
                    board,
                    pacman
                )

            # ------------------------------------------------
            # EAT DOTS
            # ------------------------------------------------

            item = board.eat(
                pacman.tile_x,
                pacman.tile_y
            )

            if item == "dot":

                score += 10

                # Dot sound
                play_sound(sound_dot)

            elif item == "power":

                score += 50

                # Power pellet sound
                play_sound(sound_power)

                # Frighten all ghosts
                for ghost in ghosts:

                    ghost.frightened = 400

            # ------------------------------------------------
            # GHOST COLLISIONS
            # ------------------------------------------------

            for ghost in ghosts:

                if (
                    ghost.tile_x == pacman.tile_x
                    and
                    ghost.tile_y == pacman.tile_y
                ):

                    # ----------------------------------------
                    # Frightened ghost
                    # ----------------------------------------

                    if ghost.frightened > 0:

                        score += 200

                        # Ghost eating sound
                        play_sound(sound_ghost)

                        ghost.respawn()

                    # ----------------------------------------
                    # Normal ghost
                    # ----------------------------------------

                    else:

                        lives -= 1

                        # Death sound
                        play_sound(sound_death)

                        pacman = Pacman(9, 15)

                        for other_ghost in ghosts:

                            other_ghost.respawn()

                        if lives <= 0:

                            state = "gameover"

                            # Stop music
                            if SOUND_ENABLED:

                                pygame.mixer.music.stop()

            # ------------------------------------------------
            # WIN
            # ------------------------------------------------

            if board.dots == 0 and state == "play":

                state = "win"

                # Win sound
                play_sound(sound_win)

                # Stop background music
                if SOUND_ENABLED:

                    pygame.mixer.music.stop()

        # ----------------------------------------------------
        # DRAW
        # ----------------------------------------------------

        screen.fill(BLACK)

        # Maze
        draw_maze(board)

        # HUD
        score_text = font.render(
            f"SCORE: {score}",
            True,
            WHITE
        )

        lives_text = font.render(
            f"LIVES: {'●' * lives}",
            True,
            YELLOW
        )

        screen.blit(
            score_text,
            (10, 8)
        )

        screen.blit(
            lives_text,
            (WIDTH - 130, 8)
        )

        # Pac-Man
        pacman.draw(screen)

        # Ghosts
        for ghost in ghosts:

            ghost.draw(screen)

        # ----------------------------------------------------
        # WIN / GAME OVER MESSAGE
        # ----------------------------------------------------

        if state == "win":

            message = "YOU WIN!  PRESS R"

            text = big_font.render(
                message,
                True,
                YELLOW
            )

            screen.blit(
                text,
                (
                    WIDTH // 2 - text.get_width() // 2,
                    HEIGHT // 2 - 20
                )
            )

        elif state == "gameover":

            message = "GAME OVER  PRESS R"

            text = big_font.render(
                message,
                True,
                RED
            )

            screen.blit(
                text,
                (
                    WIDTH // 2 - text.get_width() // 2,
                    HEIGHT // 2 - 20
                )
            )

        # Update screen
        pygame.display.flip()


# ============================================================
# Start Program
# ============================================================

if __name__ == "__main__":

    try:

        main()

    finally:

        pygame.quit()
