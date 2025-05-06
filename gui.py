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

logger = setup_logger()
config = Config()

WIDTH, HEIGHT = 800, 600
BACKGROUND_COLOR = (0, 0, 20)

def init_pygame():
    """Initialize pygame and fonts system."""
    try:
        pygame.init()
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Virtual Planetarium")
        
        # Ensure font module is initialized
        if not pygame.font.get_init():
            pygame.font.init()
        return screen
    except pygame.error as e:
        print(f"Failed to initialize pygame: {e}")
        sys.exit(1)

class Menu:
    def __init__(self, font):
        self.font = font
        self.active = False
        self.categories = ['Settings', 'Stars', 'About']  # Updated categories
        self.current_category = None
        self.objects = {
            'Stars': list(STARS.keys()),
            'Settings': ['Set Date & Location', 'Export View'],
            'About': ['Program Info']  # New category
        }
        self.selected_object = None
        self.menu_width = 200
        self.colors = config.config['colors']
        
        # Position menu on right side
        self.menu_x = WIDTH - self.menu_width
        self.back_button = pygame.Rect(WIDTH - 70, HEIGHT - 40, 60, 30)
        self.close_button = pygame.Rect(WIDTH - 30, 10, 20, 20)
        
        # Input fields for date and location
        self.input_fields = {
            'date': {'value': datetime.now().strftime('%Y-%m-%d'), 
                    'label': 'Date (YYYY-MM-DD):', 
                    'rect': pygame.Rect(WIDTH - 190, 100, 180, 30)},
            'latitude': {'value': '52.0', 
                        'label': 'Latitude:', 
                        'rect': pygame.Rect(WIDTH - 190, 160, 180, 30)},
            'longitude': {'value': '21.0', 
                        'label': 'Longitude:', 
                        'rect': pygame.Rect(WIDTH - 190, 220, 180, 30)}
        }
        self.active_field = None
        self.settings_saved = False

    def draw(self, screen):
        if not self.active:
            # Draw menu button on right side
            pygame.draw.rect(screen, self.colors['highlight'], 
                           (WIDTH - 110, 10, 100, 30))
            text = self.font.render("Menu", True, self.colors['text'])
            screen.blit(text, (WIDTH - 85, 15))
            return

        # Draw menu background on right side
        pygame.draw.rect(screen, (0, 0, 50), 
                        (self.menu_x, 0, self.menu_width, HEIGHT))
        
        # Draw close button
        pygame.draw.rect(screen, self.colors['text'], self.close_button)
        close_text = self.font.render('×', True, (0, 0, 0))
        screen.blit(close_text, (self.close_button.x + 5, self.close_button.y))

        if self.current_category == 'Settings':
            self._draw_settings(screen)
        elif self.current_category == 'About':
            self._draw_about(screen)
        else:
            self._draw_categories_and_objects(screen)

    def _draw_settings(self, screen):
        # Draw input fields
        for field in self.input_fields.values():
            pygame.draw.rect(screen, self.colors['text'], field['rect'], 2)
            label = self.font.render(field['label'], True, self.colors['text'])
            value = self.font.render(field['value'], True, self.colors['text'])
            screen.blit(label, (field['rect'].x, field['rect'].y - 20))
            screen.blit(value, (field['rect'].x + 5, field['rect'].y + 5))

        # Draw save button
        save_button = pygame.Rect(WIDTH - 190, 280, 180, 30)
        pygame.draw.rect(screen, self.colors['highlight'], save_button)
        save_text = self.font.render('Save Settings', True, self.colors['text'])
        screen.blit(save_text, (save_button.x + 40, save_button.y + 5))

    def _draw_about(self, screen):
        """Draw about section with program information."""
        # Draw back button
        pygame.draw.rect(screen, self.colors['highlight'], self.back_button)
        back_text = self.font.render('Back', True, self.colors['text'])
        screen.blit(back_text, (self.back_button.x + 5, self.back_button.y + 5))

        y_pos = 80
        info_lines = [
            "Virtual Planetarium",
            "Explore the Night Sky",
            "",
            "Author: Adrian Lesniak",
            "",
            "Controls:",
            "- Mouse wheel to zoom",
            "- Left click + drag to pan",
            "- Hover over stars for info",
            "- Menu for settings and",
            "  star selection",
            "",
            "Version: 1.0",
            "© 2024 All rights reserved"
        ]
        
        for line in info_lines:
            text = self.font.render(line, True, self.colors['text'])
            screen.blit(text, (self.menu_x + 10, y_pos))
            y_pos += 25

    def _draw_categories_and_objects(self, screen):
        """Draw categories or objects depending on current selection."""
        y_pos = 60
        
        # Draw back button if in category
        if self.current_category:
            pygame.draw.rect(screen, self.colors['highlight'], self.back_button)
            back_text = self.font.render('Back', True, self.colors['text'])
            screen.blit(back_text, (self.back_button.x + 5, self.back_button.y + 5))
            
            # Draw objects in current category
            for obj in self.objects[self.current_category]:
                color = self.colors['highlight'] if obj == self.selected_object else self.colors['text']
                text = self.font.render(obj, True, color)
                screen.blit(text, (self.menu_x + 20, y_pos))
                y_pos += 30
        else:
            # Draw main categories
            for category in self.categories:
                color = self.colors['highlight'] if category == self.current_category else self.colors['text']
                text = self.font.render(category, True, color)
                screen.blit(text, (self.menu_x + 20, y_pos))
                y_pos += 30

    def handle_click(self, pos):
        if not self.active:
            if WIDTH - 110 <= pos[0] <= WIDTH - 10 and pos[1] < 40:
                self.active = True
            return None, None

        # Check close button
        if self.close_button.collidepoint(pos):
            self.active = False
            self.current_category = None
            self.selected_object = None
            return None, None

        # Check back button when in category
        if (self.current_category == 'About' or self.current_category) and self.back_button.collidepoint(pos):
            self.current_category = None
            self.selected_object = None
            return None, None

        # Settings handling
        if self.current_category == 'Settings':
            for field_name, field in self.input_fields.items():
                if field['rect'].collidepoint(pos):
                    self.active_field = field_name
                    return None, None
            save_button = pygame.Rect(WIDTH - 190, 280, 180, 30)
            if save_button.collidepoint(pos):
                return 'Settings', 'Save Settings'

        # Category selection
        y_pos = 60
        if not self.current_category:
            for category in self.categories:
                if self.menu_x <= pos[0] <= WIDTH and y_pos <= pos[1] <= y_pos + 25:
                    self.current_category = category
                    return None, None
                y_pos += 30
        else:
            # Object selection
            for obj in self.objects[self.current_category]:
                if self.menu_x <= pos[0] <= WIDTH and y_pos <= pos[1] <= y_pos + 25:
                    return (self.current_category, obj)
                y_pos += 30

        return None, None

    def handle_keydown(self, event):
        if self.active_field:
            if event.key == pygame.K_RETURN:
                self.active_field = None
            elif event.key == pygame.K_BACKSPACE:
                self.input_fields[self.active_field]['value'] = self.input_fields[self.active_field]['value'][:-1]
            else:
                self.input_fields[self.active_field]['value'] += event.unicode

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
        
        self.menu = Menu(self.font)
        self.current_view = None
        self.catalog = None
        self.ts = None
        self.observer = None
        self.current_time = None
        self.dragging = False
        self.last_mouse_pos = None
        self.view_offset = [0, 0]  # [x, y] offset for panning
        self.star_info_popup = StarInfoPopup(self.font)
    
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

    def handle_menu_selection(self, selection):
        """Handle menu selections and update display accordingly."""
        if not selection:
            return
            
        category, item = selection
        
        if category == 'Settings' and item == 'Save Settings':
            try:
                date_str = self.menu.input_fields['date']['value']
                lat = float(self.menu.input_fields['latitude']['value'])
                lon = float(self.menu.input_fields['longitude']['value'])
                
                # Create observer
                self.observer = Topos(latitude_degrees=lat, longitude_degrees=lon)
                
                # Parse date and create time object
                date = datetime.strptime(date_str, "%Y-%m-%d")
                self.current_time = self.ts.from_datetime(date)
                
                # Update star positions
                success = self.update_star_positions()
                if success:
                    logger.info("Settings saved and star positions updated successfully")
                else:
                    logger.error("Failed to update star positions after settings change")
                
            except (ValueError, TypeError) as e:
                logger.error(f"Error in settings: {e}")
                return
        
        elif category == 'Constellations':
            # Highlight selected constellation
            self.current_view = selection
            
        elif category == 'Stars':
            # Focus on selected star
            self.current_view = selection
            # Find the star and adjust zoom/position
            for star in self.star_positions:
                if star['name'] == item:
                    self.zoom_factor = 2.0  # Zoom in on selected star
                    break

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                if not self.menu.active or event.pos[0] < self.menu.menu_x:
                    self.dragging = True
                    self.last_mouse_pos = event.pos
                selection = self.menu.handle_click(event.pos)
                self.handle_menu_selection(selection)
            if event.button == 4:  # scroll up
                self.zoom_factor *= 1.1
            elif event.button == 5:  # scroll down
                self.zoom_factor /= 1.1
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
            self.menu.handle_keydown(event)

    def draw(self, screen, mouse_pos):
        """Draw the sky map with all elements."""
        screen.fill(self.colors['background'])
        
        # Calculate available space for star map
        map_area = pygame.Rect(
            0,
            0,
            WIDTH - (self.menu.menu_width if self.menu.active else 0),
            HEIGHT
        )
        
        # Draw within the available space
        self._draw_stars(screen, map_area)
        self._draw_constellations(screen, map_area)
        self._draw_description(screen)
        self._display_info(screen, mouse_pos)
        self.menu.draw(screen)
        
        if self.current_view:
            text = f"Current view: {self.current_view[0]} - {self.current_view[1]}"
            text_surface = self.font.render(text, True, self.colors['text'])
            screen.blit(text_surface, (10, HEIGHT - 30))

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
