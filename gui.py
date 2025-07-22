import pygame
import sys
import math
from constellations import CONSTELLATIONS
from config import Config
from utils.logger import setup_logger
from celestial_objects import PLANETS, CONSTELLATIONS, STARS
from datetime import datetime
from astro_logic import calculate_star_positions
from skyfield.api import Topos
import textwrap
import json
from utils.logger import setup_logger
import random

logger = setup_logger()
config = Config()

WIDTH, HEIGHT = 800, 600
BACKGROUND_COLOR = (0, 0, 20)

# --- NEW COLORS AND ICONS ---
MENU_BG_COLOR = (220, 235, 255)  # Light blue
MENU_BTN_COLOR = (120, 180, 255)  # Blue
MENU_BTN_HOVER = (180, 220, 255)  # Lighter blue
MENU_TEXT_COLOR = (20, 40, 80)    # Navy
MENU_DESC_COLOR = (60, 120, 180)  # Blue
MENU_AUTHOR_COLOR = (255, 200, 60) # Gold

# --- NEW: Draw gradient background and animated stars ---
def draw_gradient_background(screen, top_color, bottom_color):
    """Draw a vertical gradient background on the screen."""
    height = screen.get_height()
    for y in range(height):
        ratio = y / height
        r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
        g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
        b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
        pygame.draw.line(screen, (r, g, b), (0, y), (screen.get_width(), y))

class AnimatedBackgroundStars:
    """Animated twinkling stars for background."""
    def __init__(self, width, height, num_stars=60):
        self.width = width
        self.height = height
        self.num_stars = num_stars
        self.stars = [self._random_star() for _ in range(num_stars)]

    def _random_star(self):
        return {
            'x': random.randint(0, self.width),
            'y': random.randint(0, self.height),
            'radius': random.randint(1, 2),
            'alpha': random.randint(120, 255),
            'speed': random.uniform(0.5, 1.5),
            'twinkle': random.choice([-1, 1])
        }

    def update(self):
        for star in self.stars:
            star['alpha'] += star['twinkle'] * star['speed']
            if star['alpha'] > 255:
                star['alpha'] = 255
                star['twinkle'] *= -1
            elif star['alpha'] < 120:
                star['alpha'] = 120
                star['twinkle'] *= -1

    def draw(self, screen):
        for star in self.stars:
            s = pygame.Surface((star['radius']*2, star['radius']*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 255, 255, int(star['alpha'])), (star['radius'], star['radius']), star['radius'])
            screen.blit(s, (star['x'], star['y']))

class MainMenu:
    """Main menu with buttons, info bar, and extra icons."""
    def __init__(self, font):
        self.font = font
        self.buttons = [
            {"label": "Start", "icon": "star", "key": pygame.K_s},
            {"label": "Load", "icon": "load", "key": pygame.K_l},
            {"label": "Save", "icon": "save", "key": pygame.K_v},
            {"label": "Quit", "icon": "quit", "key": pygame.K_q},
        ]
        self.selected = 0
        self.active = True
        self.menu_rects = []
        self.hovered = -1
        self.extra_icons = ["moon", "telescope"]

    def draw(self, screen):
        # Draw gradient background
        draw_gradient_background(screen, (220, 235, 255), (180, 210, 255))
        # Draw animated background stars
        if not hasattr(self, 'bg_stars'):
            self.bg_stars = AnimatedBackgroundStars(WIDTH, HEIGHT, 60)
        self.bg_stars.update()
        self.bg_stars.draw(screen)
        # Draw info bar at the top
        pygame.draw.rect(screen, MENU_BG_COLOR, (0, 0, WIDTH, 70), border_radius=0)
        desc = "Virtual Planetarium – Explore the Night Sky"
        desc_surf = self.font.render(desc, True, MENU_DESC_COLOR)
        screen.blit(desc_surf, (20, 10))
        menu_opts = "[S] Start   [L] Load   [V] Save   [Q] Quit"
        opts_surf = self.font.render(menu_opts, True, MENU_TEXT_COLOR)
        screen.blit(opts_surf, (20, 35))
        author = "Author: Adrian Lesniak"
        author_surf = self.font.render(author, True, MENU_AUTHOR_COLOR)
        screen.blit(author_surf, (WIDTH - 260, 10))
        short_desc = "This program lets you explore the night sky, view stars, constellations, and save your favorite views."
        short_surf = self.font.render(short_desc, True, MENU_TEXT_COLOR)
        screen.blit(short_surf, (20, 60))
        # Draw extra icons (moon, telescope)
        self._draw_icon(screen, "moon", WIDTH-60, 60)
        self._draw_icon(screen, "telescope", WIDTH-100, 60)
        # Draw menu buttons with border
        self.menu_rects = []
        btn_w, btn_h = 200, 60
        gap = 30
        start_y = 120
        mouse_pos = pygame.mouse.get_pos()
        for i, btn in enumerate(self.buttons):
            x = WIDTH//2 - btn_w//2
            y = start_y + i*(btn_h+gap)
            rect = pygame.Rect(x, y, btn_w, btn_h)
            self.menu_rects.append(rect)
            # Highlight on hover or selection
            hovered = rect.collidepoint(mouse_pos)
            color = MENU_BTN_HOVER if (i == self.selected or hovered) else MENU_BTN_COLOR
            pygame.draw.rect(screen, color, rect, border_radius=15)
            pygame.draw.rect(screen, (120,180,255), rect, 3, border_radius=15)  # Border
            # Draw icon
            self._draw_icon(screen, btn["icon"], x+20, y+btn_h//2)
            # Draw label
            label_surf = self.font.render(btn["label"], True, MENU_TEXT_COLOR)
            screen.blit(label_surf, (x+70, y+btn_h//2-15))

    def _draw_icon(self, screen, icon, x, y):
        # Draw simple icons (star, load, save, quit, moon, telescope)
        if icon == "star":
            pygame.draw.polygon(screen, (255, 215, 0), [
                (x, y-15), (x+7, y-5), (x+18, y-5), (x+9, y+2),
                (x+12, y+14), (x, y+7), (x-12, y+14), (x-9, y+2),
                (x-18, y-5), (x-7, y-5)
            ])
        elif icon == "load":
            pygame.draw.rect(screen, (60, 120, 180), (x-10, y-10, 20, 20), border_radius=4)
            pygame.draw.polygon(screen, (0, 180, 0), [(x, y+10), (x-8, y), (x+8, y)])
        elif icon == "save":
            pygame.draw.rect(screen, (255, 255, 255), (x-10, y-10, 20, 20), border_radius=4)
            pygame.draw.rect(screen, (120, 180, 255), (x-10, y, 20, 10))
            pygame.draw.rect(screen, (200, 200, 200), (x-5, y-7, 10, 7))
        elif icon == "quit":
            pygame.draw.circle(screen, (255, 100, 100), (x, y), 12)
            pygame.draw.line(screen, (255,255,255), (x-6, y-6), (x+6, y+6), 3)
            pygame.draw.line(screen, (255,255,255), (x-6, y+6), (x+6, y-6), 3)
        elif icon == "moon":
            pygame.draw.circle(screen, (240, 240, 200), (x, y), 14)
            pygame.draw.circle(screen, (220, 220, 180), (x+5, y-5), 7)
        elif icon == "telescope":
            pygame.draw.rect(screen, (120, 120, 120), (x-10, y-4, 20, 8), border_radius=3)
            pygame.draw.circle(screen, (80, 80, 80), (x+12, y), 6)
            pygame.draw.line(screen, (60, 60, 60), (x-10, y+4), (x-18, y+14), 4)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % len(self.buttons)
            elif event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % len(self.buttons)
            elif event.key in [btn["key"] for btn in self.buttons]:
                idx = [btn["key"] for btn in self.buttons].index(event.key)
                self.selected = idx
                return self.buttons[self.selected]["label"].lower()
            elif event.key == pygame.K_RETURN:
                return self.buttons[self.selected]["label"].lower()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            for i, rect in enumerate(self.menu_rects):
                if rect.collidepoint(event.pos):
                    self.selected = i
                    return self.buttons[i]["label"].lower()
        return None

class StarInfoPopup:
    def __init__(self, font):
        self.font = font
        self.min_width = 250  # Increased minimum width
        self.max_width = 400  # Maximum width
        self.padding = 15
        self.line_spacing = 25
        self.visible = False
        self.star_data = None
        self.position = (0, 0)
        self.background_color = (0, 0, 50, 230)
        self.border_color = (255, 223, 0)
        self.text_wrap_length = 35  # Characters per line for description

    def _calculate_size(self, info_lines):
        """Calculate required popup size based on content"""
        max_line_width = 0
        total_height = self.padding * 2

        # Calculate maximum width and total height needed
        for line in info_lines:
            if isinstance(line, list):  # Wrapped text
                total_height += len(line) * self.line_spacing
                for wrapped_line in line:
                    text_surface = self.font.render(wrapped_line, True, (255, 255, 255))
                    max_line_width = max(max_line_width, text_surface.get_width())
            else:
                text_surface = self.font.render(line, True, (255, 255, 255))
                max_line_width = max(max_line_width, text_surface.get_width())
                total_height += self.line_spacing

        width = min(max(max_line_width + self.padding * 2, self.min_width), self.max_width)
        return width, total_height

    def show(self, star_data, position):
        self.star_data = star_data
        
        # Prepare information lines
        info_lines = [
            f"Star: {self.star_data['name']}",
            f"Magnitude: {self.star_data['mag']:.2f}",
            f"Azimuth: {self.star_data['az']:.1f}°",
            f"Altitude: {self.star_data['alt']:.1f}°"
        ]

        # Add additional info if available
        if self.star_data['name'] in STARS:
            star_info = STARS[self.star_data['name']]
            info_lines.append(f"Distance: {star_info['distance']} ly")
            # Wrap description text
            wrapped_desc = textwrap.wrap(star_info['description'], 
                                       width=self.text_wrap_length)
            info_lines.append(wrapped_desc)

        # Calculate required size
        width, height = self._calculate_size(info_lines)
        self.width = width
        self.height = height

        # Position the popup to avoid going off screen
        x = min(position[0], WIDTH - self.width - 10)
        y = min(position[1], HEIGHT - self.height - 10)
        x = max(10, x)  # Ensure minimum distance from left edge
        y = max(10, y)  # Ensure minimum distance from top edge
        self.position = (x, y)
        self.visible = True
        self.info_lines = info_lines

    def draw(self, screen):
        if not self.visible or not self.star_data:
            return

        # Create surface with transparency
        popup_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # Draw background and border
        pygame.draw.rect(popup_surface, self.background_color, 
                        (0, 0, self.width, self.height))
        pygame.draw.rect(popup_surface, self.border_color, 
                        (0, 0, self.width, self.height), 2)

        # Draw information
        y_offset = self.padding
        for line in self.info_lines:
            if isinstance(line, list):  # Wrapped description
                for wrapped_line in line:
                    text_surface = self.font.render(wrapped_line, True, (255, 255, 255))
                    popup_surface.blit(text_surface, (self.padding, y_offset))
                    y_offset += self.line_spacing
            else:
                text_surface = self.font.render(line, True, (255, 255, 255))
                popup_surface.blit(text_surface, (self.padding, y_offset))
                y_offset += self.line_spacing

        screen.blit(popup_surface, self.position)

    def hide(self):
        """Hide the popup window."""
        self.visible = False
        self.star_data = None
        self.info_lines = []

class SkyMap:
    def __init__(self):
        """Initialize the sky map with default settings and configuration."""
        self.zoom_factor = 1.0
        self.star_positions = []
        self.font = None
        self._init_font()
        self.colors = config.config['colors']
        
        # Remove description from main screen
        self.description = []  # Empty list instead of program info
        
        self.exit_to_main_menu = False  # Flaga do powrotu do menu głównego
        self.current_view = None
        self.catalog = None
        self.ts = None
        self.observer = None
        self.current_time = None
        self.dragging = False
        self.last_mouse_pos = None
        self.view_offset = [0, 0]  # [x, y] offset for panning
        self.star_info_popup = StarInfoPopup(self.font)
        self.saved_views_file = 'user_views.json'  # File for saving user views
        self.logger = setup_logger()
        self.day_mode = False
        self.flash_effect = None  # (x, y, time)
        self.last_click_time = 0
        self.side_menu_width = 90
        self.side_menu_buttons = [
            {"icon": "back", "tooltip": "Back to Main Menu", "action": "back"},
            {"icon": "save", "tooltip": "Save View", "action": "save"},
            {"icon": "load", "tooltip": "Load View", "action": "load"},
            {"icon": "daynight", "tooltip": "Toggle Day/Night (D)", "action": "daynight"},
            {"icon": "export", "tooltip": "Export View as PNG", "action": "export"},
        ]
        self.side_menu_rects = []
        self.side_menu_tooltip = None
        self.last_action_message = None
        self.last_action_time = 0
    
    def _init_font(self):
        """Initialize fonts with error handling."""
        try:
            if not pygame.font.get_init():
                pygame.font.init()
            self.font = pygame.font.SysFont(
                config.config['font']['name'], 
                config.config['font']['size']
            )
        except pygame.error as e:
            logger.error(f"Font initialization failed: {e}")
            self.font = pygame.font.Font(None, config.config['font']['size'])

    def update_star_positions(self):
        """Update star positions based on current settings."""
        try:
            if self.catalog is None or self.ts is None or self.observer is None or self.current_time is None:
                logger.warning("Missing required data for star position calculation")
                return False

            self.star_positions = calculate_star_positions(
                self.catalog, 
                self.observer, 
                self.current_time
            )
            logger.info(f"Calculated positions for {len(self.star_positions)} stars")
            return True
        except Exception as e:
            logger.error(f"Error calculating star positions: {e}")
            self.star_positions = []
            return False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                # Sprawdź, czy kliknięto w boczne menu
                for i, rect in enumerate(self.side_menu_rects):
                    if rect.collidepoint(event.pos):
                        action = self.side_menu_buttons[i]["action"]
                        self._handle_side_menu_action(action)
                        return  # Nie wykonuj dalej, jeśli kliknięto menu
                    self.dragging = True
                    self.last_mouse_pos = event.pos
                # --- NEW: Flash effect on star click ---
                star_clicked = self._star_at_pos(event.pos)
                if star_clicked:
                    self.flash_effect = (event.pos[0], event.pos[1], pygame.time.get_ticks())
                    self.last_click_time = pygame.time.get_ticks()
            # --- Nowy zoom względem kursora ---
            elif event.button == 4:  # scroll up (zoom in)
                mx, my = pygame.mouse.get_pos()
                old_zoom = self.zoom_factor
                self.zoom_factor *= 1.1
                self.view_offset[0] = int((self.view_offset[0] - mx) * (self.zoom_factor/old_zoom) + mx)
                self.view_offset[1] = int((self.view_offset[1] - my) * (self.zoom_factor/old_zoom) + my)
            elif event.button == 5:  # scroll down (zoom out)
                mx, my = pygame.mouse.get_pos()
                old_zoom = self.zoom_factor
                self.zoom_factor /= 1.1
                self.view_offset[0] = int((self.view_offset[0] - mx) * (self.zoom_factor/old_zoom) + mx)
                self.view_offset[1] = int((self.view_offset[1] - my) * (self.zoom_factor/old_zoom) + my)
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:  # Left click release
                self.dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging and self.last_mouse_pos:
                dx = event.pos[0] - self.last_mouse_pos[0]
                dy = event.pos[1] - self.last_mouse_pos[1]
                self.view_offset[0] += dx
                self.view_offset[1] += dy
                self.last_mouse_pos = event.pos
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_d:
                self.day_mode = not self.day_mode
            if event.key == pygame.K_ESCAPE:
                self._handle_side_menu_action("back")
        self.side_menu_tooltip = None
        for i, rect in enumerate(self.side_menu_rects):
            if rect.collidepoint(pygame.mouse.get_pos()):
                self.side_menu_tooltip = self.side_menu_buttons[i]["tooltip"]

    def _handle_side_menu_action(self, action):
        if action == "back":
            self.exit_to_main_menu = True
            self.last_action_message = "Returning to main menu..."
            self.last_action_time = pygame.time.get_ticks()
        elif action == "save":
            from main import _input_view_name
            screen = pygame.display.get_surface()
            font = self.font
            view_name = _input_view_name(screen, font, load=False, sky_map=self)
            if view_name:
                success, msg = self.save_user_view(view_name)
                self.last_action_message = msg
                self.last_action_time = pygame.time.get_ticks()
        elif action == "load":
            from main import _input_view_name
            screen = pygame.display.get_surface()
            font = self.font
            view_name = _input_view_name(screen, font, load=True, sky_map=self)
            if view_name:
                success, msg = self.load_user_view(view_name)
                self.last_action_message = msg
                self.last_action_time = pygame.time.get_ticks()
        elif action == "daynight":
            self.day_mode = not self.day_mode
            self.last_action_message = "Day/Night mode toggled."
            self.last_action_time = pygame.time.get_ticks()
        elif action == "export":
            filename = f"exported_view_{pygame.time.get_ticks()//1000}.png"
            success = self.export_view(filename)
            if success:
                self.last_action_message = f"View exported as {filename}"
            else:
                self.last_action_message = "Export failed."
            self.last_action_time = pygame.time.get_ticks()

    def _star_at_pos(self, pos):
        # Helper: return star dict if mouse is near a star
        if not self.star_positions:
            return None
        map_area = pygame.Rect(0, 0, WIDTH - self.side_menu_width, HEIGHT)
        center_x = map_area.x + map_area.width // 2 + self.view_offset[0]
        center_y = map_area.height // 2 + self.view_offset[1]
        scale_factor = min(map_area.width, map_area.height) / 3
        for star in self.star_positions:
            x = int(center_x + math.cos(math.radians(star['az'])) * scale_factor * self.zoom_factor)
            y = int(center_y - math.sin(math.radians(star['alt'])) * scale_factor * self.zoom_factor)
            radius = max(3, 10 - float(star['mag']))
            if (pos[0] - x)**2 + (pos[1] - y)**2 < (radius+8)**2:
                return star
        return None

    def draw(self, screen, mouse_pos):
        # --- NEW: Smooth background color transition for day/night ---
        t = pygame.time.get_ticks() / 1000.0
        if self.day_mode:
            top_color = (255, 255, 230)
            bottom_color = (200, 220, 255)
        else:
            # Subtle color cycling at night
            c = 220 + int(20 * (0.5 + 0.5 * math.sin(t/4)))
            top_color = (c, 235, 255)
            bottom_color = (180, 210, 255)
        draw_gradient_background(screen, top_color, bottom_color)
        if not hasattr(self, 'bg_stars'):
            self.bg_stars = AnimatedBackgroundStars(WIDTH, HEIGHT, 60)
        if not self.day_mode:
            self.bg_stars.update()
            self.bg_stars.draw(screen)
        # --- Decorative: pastel overlay for sky map area ---
        map_area = pygame.Rect(0, 0, WIDTH - self.side_menu_width, HEIGHT)
        pastel_overlay = pygame.Surface((map_area.width, map_area.height), pygame.SRCALPHA)
        if self.day_mode:
            pygame.draw.rect(pastel_overlay, (255, 255, 240, 60), pastel_overlay.get_rect())
        else:
            pygame.draw.rect(pastel_overlay, (200, 220, 255, 40), pastel_overlay.get_rect())
        screen.blit(pastel_overlay, (0, 0))
        # --- Draw stars with dynamic radius to avoid overlap ---
        if not self.star_positions:
            return
        center_x = map_area.x + map_area.width // 2 + self.view_offset[0]
        center_y = map_area.height // 2 + self.view_offset[1]
        scale_factor = min(map_area.width, map_area.height) / 3
        star_screen_positions = []
        for star in self.star_positions:
            try:
                x = int(center_x + math.cos(math.radians(star['az'])) * scale_factor * self.zoom_factor)
                y = int(center_y - math.sin(math.radians(star['alt'])) * scale_factor * self.zoom_factor)
                magnitude = float(star['mag'])
                # --- Zmniejszony promień gwiazd ---
                base_radius = max(2, 6 - magnitude)
                # --- Dynamic radius: check for overlap ---
                min_dist = min([((x-x2)**2 + (y-y2)**2)**0.5 for (x2, y2, r2) in star_screen_positions] + [9999])
                radius = min(base_radius, max(1.5, min_dist/2.2))
                star_screen_positions.append((x, y, radius))
                # Draw glow for brightest stars
                if magnitude < 1.0:
                    glow = pygame.Surface((int(radius*8), int(radius*8)), pygame.SRCALPHA)
                    pygame.draw.circle(glow, (255,255,180,60), (int(radius*4), int(radius*4)), int(radius*4))
                    screen.blit(glow, (x-int(radius*4), y-int(radius*4)), special_flags=pygame.BLEND_RGBA_ADD)
                # Draw halo if selected
                if self.current_view and self.current_view[1] == star['name']:
                    halo = pygame.Surface((int(radius*10), int(radius*10)), pygame.SRCALPHA)
                    pygame.draw.circle(halo, (120,200,255,90), (int(radius*5), int(radius*5)), int(radius*5))
                    screen.blit(halo, (x-int(radius*5), y-int(radius*5)), special_flags=pygame.BLEND_RGBA_ADD)
                # Draw the star
                pygame.draw.circle(screen, (255, 255, 255), (x, y), int(radius))
                if self.zoom_factor > 1.5:
                    self.draw_star_name(screen, star['name'], x, y)
            except (ValueError, TypeError):
                continue
        # --- Draw animated constellation lines (pulsing effect) ---
        pulse = 120 + int(60 * (0.5 + 0.5 * math.sin(t*2)))
        for const_name, const_data in CONSTELLATIONS.items():
            stars = const_data['stars']
            for i in range(len(stars) - 1):
                star1 = next((s for s in self.star_positions if s['name'] == stars[i]), None)
                star2 = next((s for s in self.star_positions if s['name'] == stars[i+1]), None)
                if star1 and star2:
                    x1 = int(center_x + math.cos(math.radians(star1['az'])) * scale_factor * self.zoom_factor)
                    y1 = int(center_y - math.sin(math.radians(star1['alt'])) * scale_factor * self.zoom_factor)
                    x2 = int(center_x + math.cos(math.radians(star2['az'])) * scale_factor * self.zoom_factor)
                    y2 = int(center_y - math.sin(math.radians(star2['alt'])) * scale_factor * self.zoom_factor)
                    pygame.draw.line(screen, (pulse, pulse, 255), (x1, y1), (x2, y2), 3)
        # --- NEW: Flash effect on click ---
        if self.flash_effect:
            fx, fy, start_time = self.flash_effect
            elapsed = pygame.time.get_ticks() - start_time
            if elapsed < 400:
                alpha = 180 - int(180 * (elapsed/400))
                flash = pygame.Surface((80, 80), pygame.SRCALPHA)
                pygame.draw.circle(flash, (255,255,200,alpha), (40,40), 40)
                screen.blit(flash, (fx-40, fy-40), special_flags=pygame.BLEND_RGBA_ADD)
            else:
                self.flash_effect = None
        # --- Draw description, info, menu ---
        self._draw_description(screen)
        self._display_info(screen, mouse_pos)
        # self.menu.draw(screen) # USUWAMY stare menu
        if self.current_view:
            text = f"Current view: {self.current_view[0]} - {self.current_view[1]}"
            text_surface = self.font.render(text, True, self.colors['text'])
            screen.blit(text_surface, (10, HEIGHT - 30))
        # --- Draw vertical side menu ---
        self._draw_side_menu(screen, mouse_pos)
        # --- Draw last action message if any ---
        if self.last_action_message and pygame.time.get_ticks() - self.last_action_time < 2000:
            msg_surf = self.font.render(self.last_action_message, True, (20, 40, 80))
            screen.blit(msg_surf, (self.side_menu_width + 30, 30))

    def _draw_description(self, screen):
        """Draw program description at the top of the screen."""
        y_offset = 10
        for line in self.description:
            text_surface = self.font.render(line, True, self.colors['text'])
            screen.blit(text_surface, (10, y_offset))
            y_offset += 25

    def _draw_stars(self, screen, map_area):
        """Updated to use map_area for positioning"""
        if not self.star_positions:
            print("No star positions available")  # Debug print
            return
            
        center_x = map_area.x + map_area.width // 2 + self.view_offset[0]
        center_y = map_area.height // 2 + self.view_offset[1]
        scale_factor = min(map_area.width, map_area.height) / 3
        
        for star in self.star_positions:
            try:
                # Convert coordinates to screen position
                x = int(center_x + math.cos(math.radians(star['az'])) * scale_factor * self.zoom_factor)
                y = int(center_y - math.sin(math.radians(star['alt'])) * scale_factor * self.zoom_factor)
                
                # Make stars more visible and scale size by magnitude
                magnitude = float(star['mag'])
                radius = max(3, 10 - magnitude)  # Larger base size
                
                # Draw the star
                pygame.draw.circle(screen, (255, 255, 255), (x, y), radius)
                
                # Draw star name if zoomed in enough
                if self.zoom_factor > 1.5:
                    name_surface = self.font.render(star['name'], True, (255, 255, 0))
                    screen.blit(name_surface, (x + 10, y - 10))
                
            except (ValueError, TypeError) as e:
                print(f"Error drawing star {star.get('name', 'unknown')}: {e}")
                continue

    def _draw_constellations(self, screen, map_area):
        """Draw constellation lines between stars"""
        if not self.star_positions:
            return
            
        center_x = map_area.x + map_area.width // 2 + self.view_offset[0]
        center_y = map_area.height // 2 + self.view_offset[1]
        scale_factor = min(map_area.width, map_area.height) / 3
        
        # Create a dictionary of star positions by name
        star_positions = {star['name']: (
            int(center_x + math.cos(math.radians(star['az'])) * scale_factor * self.zoom_factor),
            int(center_y - math.sin(math.radians(star['alt'])) * scale_factor * self.zoom_factor)
        ) for star in self.star_positions}
        
        # Draw lines for each constellation
        for const_name, const_data in CONSTELLATIONS.items():
            stars = const_data['stars']
            for i in range(len(stars) - 1):
                if stars[i] in star_positions and stars[i + 1] in star_positions:
                    start_pos = star_positions[stars[i]]
                    end_pos = star_positions[stars[i + 1]]
                    pygame.draw.line(screen, (100, 100, 255), start_pos, end_pos, 1)

    def _display_info(self, screen, mouse_pos):
        """Display constellation and star information."""
        if self.font is None:
            print("Error: Font not initialized. Cannot display star info.")
            return
            
        for star in self.star_positions:
            x = int(WIDTH/2 + math.cos(math.radians(star['az'])) * 200 * self.zoom_factor)
            y = int(HEIGHT/2 - math.sin(math.radians(star['alt'])) * 200 * self.zoom_factor)
            
            # Check if mouse is near star
            if math.hypot(mouse_pos[0] - x, mouse_pos[1] - y) < 10:
                # Show popup instead of simple text
                self.star_info_popup.show(star, (x + 20, y - 20))
                break
        else:
            self.star_info_popup.hide()

        # Draw the popup if visible
        self.star_info_popup.draw(screen)

    def export_view(self, filename):
        """Export current view as PNG image."""
        try:
            pygame.image.save(pygame.display.get_surface(), filename)
            logger.info(f"View exported to {filename}")
            return True
        except pygame.error as e:
            logger.error(f"Failed to export view: {e}")
            return False

    def save_user_view(self, view_name):
        """Save current view (date, location, zoom, offset) under a given name."""
        try:
            # Zapisz datę jako string ISO, nie Time Skyfielda
            if self.current_time:
                dt = self.current_time.utc_datetime()
                date_str = dt.isoformat()
            else:
                date_str = None
            data = {
                'date': date_str,
                'latitude': float(self.observer.latitude.degrees) if self.observer else None,
                'longitude': float(self.observer.longitude.degrees) if self.observer else None,
                'zoom_factor': self.zoom_factor,
                'view_offset': self.view_offset,
            }
            try:
                with open(self.saved_views_file, 'r') as f:
                    all_views = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                all_views = {}
            all_views[view_name] = data
            with open(self.saved_views_file, 'w') as f:
                json.dump(all_views, f, indent=2)
            self.logger.info(f"Saved user view: {view_name}")
            return True, f"View '{view_name}' saved."
        except Exception as e:
            self.logger.error(f"Error saving view '{view_name}': {e}")
            return False, f"Error saving view: {e}"

    def load_user_view(self, view_name):
        """Load a saved view by name and update sky map state."""
        try:
            with open(self.saved_views_file, 'r') as f:
                all_views = json.load(f)
            if view_name not in all_views:
                self.logger.warning(f"View '{view_name}' not found.")
                return False, f"View '{view_name}' not found."
            data = all_views[view_name]
            from skyfield.api import Topos, load
            ts = self.ts or load.timescale()
            # Odczytaj datę jako datetime, nie Time Skyfielda
            if data['date']:
                dt = datetime.fromisoformat(data['date'])
                self.current_time = ts.from_datetime(dt)
            else:
                self.current_time = ts.now()
            self.observer = Topos(latitude_degrees=data['latitude'], longitude_degrees=data['longitude'])
            self.zoom_factor = data.get('zoom_factor', 1.0)
            self.view_offset = data.get('view_offset', [0, 0])
            self.update_star_positions()
            self.logger.info(f"Loaded user view: {view_name}")
            return True, f"View '{view_name}' loaded."
        except Exception as e:
            self.logger.error(f"Error loading view '{view_name}': {e}")
            return False, f"Error loading view: {e}"

    def _draw_side_menu(self, screen, mouse_pos):
        menu_x = 0
        menu_y = 0
        btn_size = 60
        gap = 30
        self.side_menu_rects = []
        for i, btn in enumerate(self.side_menu_buttons):
            y = menu_y + 40 + i * (btn_size + gap)
            rect = pygame.Rect(menu_x + 15, y, btn_size, btn_size)
            self.side_menu_rects.append(rect)
            color = (180, 220, 255) if rect.collidepoint(mouse_pos) else (120, 180, 255)
            pygame.draw.rect(screen, color, rect, border_radius=15)
            pygame.draw.rect(screen, (120,180,255), rect, 3, border_radius=15)
            self._draw_side_icon(screen, btn["icon"], rect.centerx, rect.centery)
        # Draw tooltip if any
        if self.side_menu_tooltip:
            tooltip_surf = self.font.render(self.side_menu_tooltip, True, (20, 40, 80))
            screen.blit(tooltip_surf, (self.side_menu_width + 30, 100))

    def _draw_side_icon(self, screen, icon, x, y):
        if icon == "back":
            pygame.draw.polygon(screen, (60, 120, 180), [(x+10, y-15), (x-10, y), (x+10, y+15)])
        elif icon == "save":
            pygame.draw.rect(screen, (255, 255, 255), (x-12, y-12, 24, 24), border_radius=4)
            pygame.draw.rect(screen, (120, 180, 255), (x-12, y, 24, 12))
            pygame.draw.rect(screen, (200, 200, 200), (x-6, y-8, 12, 8))
        elif icon == "load":
            pygame.draw.rect(screen, (60, 120, 180), (x-12, y-12, 24, 24), border_radius=4)
            pygame.draw.polygon(screen, (0, 180, 0), [(x, y+10), (x-8, y), (x+8, y)])
        elif icon == "daynight":
            pygame.draw.circle(screen, (255, 255, 200), (x, y), 14)
            pygame.draw.circle(screen, (220, 220, 180), (x+5, y-5), 7)
            pygame.draw.arc(screen, (120, 180, 255), (x-10, y-10, 20, 20), 3.14, 6.28, 3)
        elif icon == "export":
            pygame.draw.rect(screen, (120, 180, 255), (x-14, y-10, 28, 20), border_radius=4)
            pygame.draw.rect(screen, (255, 255, 255), (x-8, y-6, 16, 12))
            pygame.draw.line(screen, (60, 120, 180), (x-8, y+6), (x+8, y+6), 2)

    def draw_star_name(self, screen, name, x, y):
        # Draw star name in dark navy color for readability
        name_surface = self.font.render(name, True, (20, 40, 80))
        screen.blit(name_surface, (x + 10, y - 10))

def main_loop(screen, sky_map):
    clock = pygame.time.Clock()
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            sky_map.handle_event(event)
        
        sky_map.draw(screen, mouse_pos)
        pygame.display.flip()
        clock.tick(30)
    
    pygame.quit()
    sys.exit()
