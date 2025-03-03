import pygame
import random

# Initialize Pygame
pygame.init()

# Set up the display
GRID_SIZE = 5
CELL_SIZE = 100
WINDOW_SIZE = GRID_SIZE * CELL_SIZE
screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
pygame.display.set_caption("Chicken Shooter")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)

# Set up the game
positions = [(i, j) for i in range(GRID_SIZE) for j in range(GRID_SIZE) if (i, j) != (2, 2)]
chickens = random.sample(positions, 3)  # 3 unique positions not at (2,2)
crosshair = [2, 2]  # Start at center (list for mutability)
score = 0
font = pygame.font.SysFont(None, 36)

# Game loop
running = True
while running and len(chickens) > 0:
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            # Move crosshair with arrow keys
            if event.key == pygame.K_UP and crosshair[0] > 0:
                crosshair[0] -= 1
            elif event.key == pygame.K_DOWN and crosshair[0] < GRID_SIZE - 1:
                crosshair[0] += 1
            elif event.key == pygame.K_LEFT and crosshair[1] > 0:
                crosshair[1] -= 1
            elif event.key == pygame.K_RIGHT and crosshair[1] < GRID_SIZE - 1:
                crosshair[1] += 1
            # Shoot with spacebar
            elif event.key == pygame.K_SPACE:
                shot_pos = (crosshair[0], crosshair[1])
                if shot_pos in chickens:
                    chickens.remove(shot_pos)
                    score += 1
                    print("Hit!")
                else:
                    print("Miss!")
                # Move remaining chickens
                for i in range(len(chickens)):
                    directions = [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]
                    dx, dy = random.choice(directions)
                    new_row = chickens[i][0] + dx
                    new_col = chickens[i][1] + dy
                    if 0 <= new_row < GRID_SIZE and 0 <= new_col < GRID_SIZE:
                        chickens[i] = (new_row, new_col)

    # Draw the grid
    screen.fill(WHITE)
    for i in range(GRID_SIZE + 1):
        pygame.draw.line(screen, BLACK, (0, i * CELL_SIZE), (WINDOW_SIZE, i * CELL_SIZE))
        pygame.draw.line(screen, BLACK, (i * CELL_SIZE, 0), (i * CELL_SIZE, WINDOW_SIZE))

    # Draw chickens (green circles)
    for chicken in chickens:
        pygame.draw.circle(screen, GREEN, 
                          (chicken[1] * CELL_SIZE + CELL_SIZE // 2, 
                           chicken[0] * CELL_SIZE + CELL_SIZE // 2), 
                          CELL_SIZE // 3)

    # Draw crosshair (red X)
    x, y = crosshair[1] * CELL_SIZE, crosshair[0] * CELL_SIZE
    pygame.draw.line(screen, RED, (x + 10, y + 10), (x + CELL_SIZE - 10, y + CELL_SIZE - 10), 3)
    pygame.draw.line(screen, RED, (x + CELL_SIZE - 10, y + 10), (x + 10, y + CELL_SIZE - 10), 3)

    # Draw score
    score_text = font.render(f"Score: {score}", True, BLACK)
    screen.blit(score_text, (10, 10))

    # Update display
    pygame.display.flip()

# Game over
if len(chickens) == 0:
    game_over_text = font.render(f"You won! Score: {score}", True, BLACK)
    screen.blit(game_over_text, (WINDOW_SIZE // 4, WINDOW_SIZE // 2))
    pygame.display.flip()
    pygame.time.wait(2000)  # Show "You won!" for 2 seconds

pygame.quit()