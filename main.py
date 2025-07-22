from astro_logic import load_star_catalog, calculate_star_positions
import pygame
from gui import main_loop, SkyMap, MainMenu
from skyfield.api import load, Topos
from datetime import datetime
import os
import sys
from utils.logger import setup_logger

# --- NEW: Set window size ---
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 900


def main():
    logger = setup_logger()
    try:
        logger.info('Program started')
        # Get base directory
        base_dir = os.path.dirname(os.path.abspath(__file__))
        catalog_path = os.path.join(base_dir, 'data', 'star_catalog.csv')

        # Initialize Pygame and GUI
        pygame.init()
        screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Virtual Planetarium")
        font = pygame.font.SysFont('arial', 24)
        # --- Pass new window size to GUI classes if needed ---
        import gui
        gui.WIDTH = WINDOW_WIDTH
        gui.HEIGHT = WINDOW_HEIGHT
        menu = MainMenu(font)
        sky_map = SkyMap()

        # Load star catalog and initialize
        try:
            catalog = load_star_catalog(catalog_path)
            if catalog.empty:
                logger.error('Star catalog is empty')
                raise ValueError("Star catalog is empty")
            sky_map.catalog = catalog
            logger.info(f"Loaded {len(catalog)} stars")
        except Exception as e:
            logger.error(f"Error loading star catalog: {e}")
            print(f"Error loading star catalog: {e}")
            sys.exit(1)

        # Set default time and location
        ts = load.timescale()
        sky_map.ts = ts
        sky_map.observer = Topos(latitude_degrees=52.0, longitude_degrees=21.0)
        sky_map.current_time = ts.now()

        # Calculate initial positions
        if sky_map.update_star_positions():
            logger.info(f"Calculated positions for {len(sky_map.star_positions)} stars")
        else:
            logger.warning("Failed to calculate star positions")

        running = True
        while running:
            menu_action = None
            while menu_action is None:
                screen.fill((220, 235, 255))
                menu.draw(screen)
                pygame.display.flip()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        logger.info('User closed the program from menu')
                        running = False
                        break
                    menu_action = menu.handle_event(event)
            if not running:
                break
            logger.info(f"User selected menu option: {menu_action}")
            if menu_action == 'start':
                main_loop(screen, sky_map)
                logger.info('User ran sky map view')
                _wait_for_key(screen, font, msg="Press any key to return to menu...")
            elif menu_action == 'load':
                view_name = _input_view_name(screen, font, load=True, sky_map=sky_map)
                if view_name:
                    logger.info(f"User attempts to load view: {view_name}")
                    success, msg = sky_map.load_user_view(view_name)
                    logger.info(msg)
                    _show_message(screen, font, msg)
            elif menu_action == 'save':
                view_name = _input_view_name(screen, font, load=False, sky_map=sky_map)
                if view_name:
                    logger.info(f"User attempts to save view: {view_name}")
                    success, msg = sky_map.save_user_view(view_name)
                    logger.info(msg)
                    _show_message(screen, font, msg)
            elif menu_action == 'quit':
                logger.info('User selected quit')
                running = False
        logger.info('Program exited normally')
        pygame.quit()
        sys.exit()
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        print(f"An error occurred: {e}")
        print(f"Type of error: {type(e)}")
        sys.exit(1)

def main_loop(screen, sky_map):
    clock = pygame.time.Clock()
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            sky_map.handle_event(event)
        # --- POWRÓT DO MENU ---
        if hasattr(sky_map, 'exit_to_main_menu') and sky_map.exit_to_main_menu:
            break
        sky_map.draw(screen, mouse_pos)
        pygame.display.flip()
        clock.tick(30)
    # Nie zamykaj pygame.quit() tutaj, wróć do menu

def _wait_for_key(screen, font, msg="Press any key to continue..."):
    screen.fill((220, 235, 255))
    text = font.render(msg, True, (20, 40, 80))
    screen.blit(text, (40, 300))
    pygame.display.flip()
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                waiting = False

def _show_message(screen, font, msg):
    screen.fill((220, 235, 255))
    lines = msg.split('\n')
    for i, line in enumerate(lines):
        text = font.render(line, True, (20, 40, 80))
        screen.blit(text, (40, 300 + i*40))
    pygame.display.flip()
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                waiting = False

def _input_view_name(screen, font, load, sky_map):
    import json
    input_text = ''
    clock = pygame.time.Clock()
    views = []
    if load:
        # List available views
        try:
            with open(sky_map.saved_views_file, 'r') as f:
                all_views = json.load(f)
                views = list(all_views.keys())
        except Exception:
            views = []
    while True:
        screen.fill((220, 235, 255))
        if load:
            prompt = 'Enter view name to LOAD:'
            info = 'Available views: ' + (', '.join(views) if views else 'None')
        else:
            prompt = 'Enter view name to SAVE:'
            info = ''
        prompt_surf = font.render(prompt, True, (20, 40, 80))
        screen.blit(prompt_surf, (40, 220))
        input_surf = font.render(input_text, True, (60, 120, 180))
        screen.blit(input_surf, (40, 270))
        if info:
            info_surf = font.render(info, True, (20, 40, 80))
            screen.blit(info_surf, (40, 320))
        instr = 'Type name and press ENTER. ESC to cancel.'
        instr_surf = font.render(instr, True, (120, 180, 255))
        screen.blit(instr_surf, (40, 370))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return input_text.strip() if input_text.strip() else None
                elif event.key == pygame.K_ESCAPE:
                    return None
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                else:
                    if len(input_text) < 32 and event.unicode.isprintable():
                        input_text += event.unicode
        clock.tick(30)

if __name__ == '__main__':
    main()
