import pygame
import os

# Inicialización de Pygame
pygame.init()

# Configuración de la pantalla
screen_width = 720
screen_height = 1280
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Selección de Personaje")

# Colores
white = (255, 255, 255)
black = (0, 0, 0)
blue = (0, 0, 255)

# Cargar imágenes de personajes
character_images = [
    pygame.image.load(os.path.join("img", "img1.png")),
    pygame.image.load(os.path.join("img", "img2.png")),
    pygame.image.load(os.path.join("img", "img3.png"))
]

# Ajustar tamaño de imágenes
character_images = [pygame.transform.scale(img, (300, 300)) for img in character_images]

# Variables del juego
selected_character = 0
character_selected = False
font = pygame.font.Font(None, 72)
clock = pygame.time.Clock()
running = True

# Posiciones de botones
button_width = 100
button_height = 100
button_left_pos = (screen_width // 4 - button_width // 2, screen_height // 1.5)
button_right_pos = (3 * screen_width // 4 - button_width // 2, screen_height // 1.5)
button_select_pos = (screen_width // 2 - 100, screen_height // 1.2)

# Bucle principal del juego
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos
            if not character_selected:
                if button_left_pos[0] <= mouse_x <= button_left_pos[0] + button_width and button_left_pos[
                    1] <= mouse_y <= button_left_pos[1] + button_height:
                    selected_character = (selected_character - 1) % len(character_images)
                elif button_right_pos[0] <= mouse_x <= button_right_pos[0] + button_width and button_right_pos[
                    1] <= mouse_y <= button_right_pos[1] + button_height:
                    selected_character = (selected_character + 1) % len(character_images)
                elif button_select_pos[0] <= mouse_x <= button_select_pos[0] + 200 and button_select_pos[
                    1] <= mouse_y <= button_select_pos[1] + 50:
                    character_selected = True

    screen.fill(white)

    if not character_selected:
        # Dibujar imagen del personaje seleccionado
        screen.blit(character_images[selected_character], (screen_width // 2 - 150, screen_height // 2 - 300))

        # Dibujar botones
        pygame.draw.rect(screen, blue, (*button_left_pos, button_width, button_height))
        pygame.draw.rect(screen, blue, (*button_right_pos, button_width, button_height))
        pygame.draw.rect(screen, blue, (*button_select_pos, 200, 50))

        # Dibujar flechas en los botones
        pygame.draw.polygon(screen, black, [(button_left_pos[0] + 75, button_left_pos[1] + 50),
                                            (button_left_pos[0] + 25, button_left_pos[1] + 25),
                                            (button_left_pos[0] + 25, button_left_pos[1] + 75)])
        pygame.draw.polygon(screen, black, [(button_right_pos[0] + 25, button_right_pos[1] + 50),
                                            (button_right_pos[0] + 75, button_right_pos[1] + 25),
                                            (button_right_pos[0] + 75, button_right_pos[1] + 75)])

        # Dibujar texto del botón "Seleccionar Personaje"
        select_text = font.render("Seleccionar", True, white)
        screen.blit(select_text, (button_select_pos[0] + 20, button_select_pos[1] + 10))

        # Mostrar el personaje seleccionado
        selected_text = font.render(f"Personaje {selected_character + 1} seleccionado", True, black)
        screen.blit(selected_text, (screen_width // 2 - selected_text.get_width() // 2, 100))
    else:
        # Dibujar la arena y el personaje seleccionado
        arena_text = font.render("Arena del bruto", True, black)
        screen.blit(arena_text, (screen_width // 2 - arena_text.get_width() // 2, 100))
        screen.blit(character_images[selected_character], (screen_width // 2 - 150, screen_height // 2 - 150))

    pygame.display.flip()
    clock.tick(30)

pygame.quit()
