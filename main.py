from kivy.app import App
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, Mesh, Rectangle
from kivy.core.window import Window
from kivy.core.image import Image as CoreImage


import math
import random


# ------------------------------
# Hex helper
# ------------------------------
def hex_corners(cx, cy, size):
    corners = []
    for i in range(6):
        angle = math.radians(60 * i - 30)
        corners.append((cx + size * math.cos(angle), cy + size * math.sin(angle)))
    return corners


# ------------------------------
# Board widget
# ------------------------------
class HexBoard(Widget):

    def __init__(
        self,
        hex_size=40,
        rows_pattern=None,
        colours=None,
        start_visible_tile=0,
        developer=False,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.hex_size = hex_size
        self.rows_patterns = rows_pattern
        self.colours = colours or []

        self.logos = {
            0: CoreImage("logos/ship.png").texture,
            10: CoreImage("logos/cave.png").texture,
            8: CoreImage("logos/castle-tower.png").texture,
            13: CoreImage("logos/mountain.png").texture,
            14: CoreImage("logos/village.png").texture,
            9: CoreImage("logos/desert.png").texture,
        }

        self.tile_centers = []
        self.token_tile = None  # Current token position
        self.revealed = set()  # Tiles that are visible

        self.developer_mode = developer

        # Set starting visible tile
        self.start_visible_tile = start_visible_tile
        self.revealed.add(self.start_visible_tile)

        self.bind(size=self.redraw, pos=self.redraw)

    # --------------------------
    # Check if a point is inside a hex
    # --------------------------
    def point_in_hex(self, px, py, hx, hy, size):
        dx = abs(px - hx)
        dy = abs(py - hy)
        if dy > size:
            return False
        max_dx = math.sqrt(3) * (size - dy)
        return dx <= max_dx

    # --------------------------
    # Get neighbors using distance
    # --------------------------
    def get_neighbors(self, tile_idx):
        neighbors = []
        x0, y0 = self.tile_centers[tile_idx]

        for idx, (x1, y1) in enumerate(self.tile_centers):
            if idx == tile_idx:
                continue
            dx = x1 - x0
            dy = y1 - y0
            dist = math.hypot(dx, dy)
            # Edge-sharing distance for flat-top hexes
            horiz = self.hex_size * math.sqrt(3)
            vert = self.hex_size * 1.5
            tolerance = 2  # small tolerance for floating point errors
            if abs(dist - horiz) < tolerance or abs(dist - vert) < tolerance:
                neighbors.append(idx)
        return neighbors

    # --------------------------
    # Handle clicks
    # --------------------------
    def on_touch_down(self, touch):
        for idx, (hx, hy) in enumerate(self.tile_centers):
            if self.point_in_hex(touch.x, touch.y, hx, hy, self.hex_size):
                # Only allow clicks on revealed tiles
                if idx in self.revealed:
                    self.token_tile = idx
                    # Reveal neighbors
                    for n in self.get_neighbors(idx):
                        self.revealed.add(n)
                    self.redraw()
                    return True
        return super().on_touch_down(touch)

    # --------------------------
    # Draw the red token
    # --------------------------
    def draw_player_token(self, tile_index, color=(1, 0, 0), radius=14):
        if tile_index >= len(self.tile_centers):
            return
        x, y = self.tile_centers[tile_index]
        with self.canvas.after:
            Color(*color)
            Line(circle=(x, y, radius), width=3)

    # --------------------------
    # Redraw the board
    # --------------------------
    def redraw(self, *args):
        self.canvas.clear()
        self.canvas.after.clear()  # Clear token layer
        self.tile_centers = []

        w_spacing = self.hex_size * math.sqrt(3)
        h_spacing = self.hex_size * 1.5

        cx = self.x + self.width / 2
        cy = self.y + self.height / 2

        total_height = (len(self.rows_patterns) - 1) * h_spacing
        start_y = cy + total_height / 2

        hex_index = 0

        with self.canvas:
            for row_idx, count in enumerate(self.rows_patterns):
                row_width = (count - 1) * w_spacing
                row_offset_x = -row_width / 2
                y = start_y - row_idx * h_spacing

                for col in range(count):
                    x = cx + row_offset_x + col * w_spacing
                    self.tile_centers.append((x, y))

                    corners = hex_corners(x, y, self.hex_size)

                    if hex_index < len(self.colours):
                        r, g, b = (c / 255 for c in self.colours[hex_index])
                    else:
                        r, g, b = (random.random(), random.random(), random.random())

                    # Draw black if not revealed
                    if not self.developer_mode and hex_index not in self.revealed:
                        r, g, b = 0, 0, 0

                    Color(r, g, b)

                    # Fill hex
                    vertices, indices = [], []
                    for px, py in corners:
                        vertices.extend([px, py, 0, 0])
                    vertices.extend([x, y, 0, 0])
                    for i in range(6):
                        indices.extend([i, (i + 1) % 6, 6])
                    Mesh(vertices=vertices, indices=indices, mode="triangles")

                    # Outline (black)
                    Color(0, 0, 0)
                    pts = []
                    for px, py in corners:
                        pts.extend([px, py])
                    Line(points=pts + pts[:2], width=1.5)

                    # Logo
                    if hex_index in self.logos and (
                        hex_index in self.revealed or self.developer_mode
                    ):
                        texture = self.logos[hex_index]
                        size = self.hex_size * 1.5
                        Rectangle(
                            texture=texture, pos=(x - size / 2, y - size / 2), size=(size, size)
                        )

                    hex_index += 1
        # Draw token on top if exists
        if self.token_tile is not None:
            self.draw_player_token(self.token_tile)


# ------------------------------
# Color keys
# ------------------------------
keys = {
    "Desert": (212, 163, 115),
    "Sand": (250, 237, 205),
    "Grass": (204, 213, 174),
    "Mountain": (94, 87, 77),
    "Sea": (122, 156, 198),
}


# ------------------------------
# App
# ------------------------------
class HexApp(App):
    def build(self):
        Window.size = (700, 700)
        colours = [
            # fmt: off
            keys['Sea'], keys['Sea'], keys['Sea'],
            keys['Sea'], keys['Sand'], keys['Sand'], keys['Sea'],
            keys['Sea'], keys['Sand'], keys['Desert'], keys['Sand'], keys['Sea'],
            keys['Sea'], keys['Mountain'], keys['Grass'] , keys['Sea'],
            keys['Sea'], keys['Sea'] , keys['Sea'],
            # fmt: on
        ]
        # Specify which tile starts visible, e.g., first tile of third row
        start_visible_tile = sum([3, 4])  # index 7
        board = HexBoard(
            hex_size=45,
            rows_pattern=[3, 4, 5, 4, 3],
            colours=colours,
            start_visible_tile=start_visible_tile,
            developer=True,
        )
        # Set starting token on visible tile
        board.token_tile = start_visible_tile
        return board


# ------------------------------
# Run
# ------------------------------
if __name__ == "__main__":
    HexApp().run()
