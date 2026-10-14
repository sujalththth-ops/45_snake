
import pygame
import array
import math

from .snake import Snake
from .food import Food


WHITE = (255, 255, 255)
GREEN = (0, 200, 0)
RED = (220, 60, 60)
BLACK = (0, 0, 0)
YELLOW = (255, 220, 0)


def create_tone(frequency, duration, volume=0.3):
    sample_rate = 22050
    sample_count = int(sample_rate * duration)
    samples = array.array("h")

    for i in range(sample_count):
        fade = 1 - (i / sample_count)
        sample = int(
            32767
            * volume
            * fade
            * math.sin(
                2 * math.pi * frequency * i / sample_rate
            )
        )
        samples.append(sample)

    return pygame.mixer.Sound(buffer=samples.tobytes())


class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.cell_size = 20
        self.grid_width = width // self.cell_size
        self.grid_height = height // self.cell_size

        self.score = 0
        self.font = pygame.font.SysFont("Arial", 30)
        self.game_over_font = pygame.font.SysFont(
            "Arial", 48, bold=True
        )
        self.message_font = pygame.font.SysFont("Arial", 24)

        self.eat_sound = None
        self.game_over_sound = None

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(
                    frequency=22050, size=-16, channels=1
                )

            self.eat_sound = create_tone(880, 0.12, 0.25)
            self.game_over_sound = create_tone(220, 0.35, 0.3)
        except pygame.error:
            print(
                "Audio is unavailable; the game will continue silently."
            )

        self.difficulties = {
            "Easy": 5,
            "Medium": 8,
            "Hard": 14,
        }
        self.difficulty_names = [
            "Easy", "Medium", "Hard", "Exit"
        ]
        self.selected_option = 1
        self.difficulty = "Medium"
        self.moves_per_second = self.difficulties[
            self.difficulty
        ]

        self._frame_counter = 0
        self.game_over = False
        self.exiting = False

        self._create_new_game()

    def _create_new_game(self):
        self.snake = Snake(
            self.grid_width // 2,
            self.grid_height // 2,
            self.cell_size,
        )
        self.food = Food(
            self.grid_width,
            self.grid_height,
            self.cell_size,
        )
        self.score = 0
        self._frame_counter = 0
        self.game_over = False

    def handle_keydown(self, key):
        if self.exiting:
            return

        if self.game_over:
            if key in (pygame.K_UP, pygame.K_w):
                self.selected_option = (
                    self.selected_option - 1
                ) % len(self.difficulty_names)
            elif key in (pygame.K_DOWN, pygame.K_s):
                self.selected_option = (
                    self.selected_option + 1
                ) % len(self.difficulty_names)
            elif key in (pygame.K_RETURN, pygame.K_SPACE):
                choice = self.difficulty_names[
                    self.selected_option
                ]

                if choice == "Exit":
                    self.exiting = True
                else:
                    self.difficulty = choice
                    self.moves_per_second = (
                        self.difficulties[choice]
                    )
                    self._create_new_game()
            return

        if key in (pygame.K_UP, pygame.K_w):
            self.snake.set_direction(0, -1)
        elif key in (pygame.K_DOWN, pygame.K_s):
            self.snake.set_direction(0, 1)
        elif key in (pygame.K_LEFT, pygame.K_a):
            self.snake.set_direction(-1, 0)
        elif key in (pygame.K_RIGHT, pygame.K_d):
            self.snake.set_direction(1, 0)

    def handle_input(self):
        pass

    def update(self):
        if self.game_over or self.exiting:
            return

        self._frame_counter += 1
        frames_per_move = max(
            1, 60 // self.moves_per_second
        )
        if self._frame_counter < frames_per_move:
            return

        self._frame_counter = 0
        self.snake.move()

        if self.snake.collides_with_wall(
            self.grid_width, self.grid_height
        ):
            self.game_over = True
            if self.game_over_sound:
                self.game_over_sound.play()
            return

        if self.snake.collides_with_self():
            self.game_over = True
            if self.game_over_sound:
                self.game_over_sound.play()
            return

        if self.snake.head_rect().colliderect(
            self.food.rect()
        ):
            self.snake.grow()
            self.score += 1

            if self.eat_sound:
                self.eat_sound.play()

            self.food.respawn(self.snake.body)

    def render(self, screen):
        screen.fill(BLACK)

        if self.game_over:
            title = self.game_over_font.render(
                "GAME OVER", True, RED
            )
            final_score = self.font.render(
                f"Final Score: {self.score}", True, WHITE
            )
            instruction = self.message_font.render(
                "Use UP/DOWN and ENTER to choose",
                True,
                WHITE,
            )

            screen.blit(
                title,
                title.get_rect(
                    center=(
                        self.width // 2,
                        self.height // 2 - 130,
                    )
                ),
            )
            screen.blit(
                final_score,
                final_score.get_rect(
                    center=(
                        self.width // 2,
                        self.height // 2 - 75,
                    )
                ),
            )
            screen.blit(
                instruction,
                instruction.get_rect(
                    center=(
                        self.width // 2,
                        self.height // 2 - 35,
                    )
                ),
            )

            for index, option in enumerate(
                self.difficulty_names
            ):
                color = (
                    YELLOW
                    if index == self.selected_option
                    else WHITE
                )
                option_text = self.font.render(
                    option, True, color
                )
                screen.blit(
                    option_text,
                    option_text.get_rect(
                        center=(
                            self.width // 2,
                            self.height // 2
                            + index * 42
                            + 10,
                        )
                    ),
                )
            return

        pygame.draw.rect(screen, RED, self.food.rect())

        for rect in self.snake.segment_rects():
            pygame.draw.rect(screen, GREEN, rect)

        score_text = self.font.render(
            f"Score: {self.score}  Difficulty: {self.difficulty}",
            True,
            WHITE,
        )
        screen.blit(score_text, (10, 10))
