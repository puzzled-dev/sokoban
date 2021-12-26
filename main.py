import csv
import os
import sys

import pygame

SIZE = WIDTH, HEIGHT = 1200, 1000
BLOCK_SIDE = 50
PLAYER_HEIGHT = int(450 / 350 * BLOCK_SIDE)
N, M = WIDTH // BLOCK_SIDE, HEIGHT // BLOCK_SIDE
PLAYER_IMAGES = {"front": ["1.jpg", "2.jpg", "3.jpg", "4.jpg"],
                 "back": ["1.jpg", "2.jpg", "3.jpg", "4.jpg"],
                 "left": ["1.jpg", "2.jpg", "3.jpg", "4.jpg"],
                 "right": ["1.jpg", "2.jpg", "3.jpg", "4.jpg"]}
start_pos = None
boxes = None
positions = None
positions_radius = list(range(80, 171, 2)) + list(range(171, 80, -2))
buttons = None


def load_image(name, colorkey=None, width=BLOCK_SIDE):
    fullname = os.path.join('img', name)
    if not os.path.isfile(fullname):
        print(f"Файл с изображением \"{fullname}\" не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    n, m = image.get_size()
    image = pygame.transform.scale(image, (width, m / n * width))
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


def rect_intersect(rect1, rect2):
    points1 = set()
    for x in range(rect1[0][0] + 3, rect1[1][0] - 3):
        for y in range(rect1[0][1] + 3, rect1[1][1] - 3):
            points1.add((x, y))
    points2 = set()
    for x in range(rect2[0][0], rect2[1][0]):
        for y in range(rect2[0][1], rect2[1][1]):
            points2.add((x, y))
    return points1.intersection(points2)


def get_level(level_number, obj_id):
    with open(f"data/level{level_number}.csv", mode="r", encoding="utf-8") as csv_file:
        level = list(csv.reader(csv_file, delimiter=",", quotechar="\""))
    with open("data/start_pos.csv", mode="r", encoding="utf-8") as csv_file:
        reader = list(csv.reader(csv_file, delimiter=",", quotechar="\""))
        reader = {int(elem[0]): (int(elem[1]) * BLOCK_SIDE,
                                 int(elem[2]) * BLOCK_SIDE + BLOCK_SIDE - PLAYER_HEIGHT)
                  for elem in reader[1:]}
        start_pos = reader[level_number]
    with open(f"data/boxes{level_number}.csv", mode="r", encoding="utf-8") as csv_file:
        reader = list(csv.reader(csv_file, delimiter=",", quotechar="\""))
        boxes = [Box(obj_id, int(elem[1]) * BLOCK_SIDE, int(elem[0]) * BLOCK_SIDE)
                 for elem in reader[1:]]
    with open(f"data/positions{level_number}.csv", mode="r", encoding="utf-8") as csv_file:
        reader = list(csv.reader(csv_file, delimiter=",", quotechar="\""))
        positions = [(int(elem[0]) * BLOCK_SIDE + BLOCK_SIDE // 2,
                      int(elem[1]) * BLOCK_SIDE + BLOCK_SIDE // 2)
                     for elem in reader[1:]]
    return start_pos, level, boxes, positions


def get_buttons():
    global buttons
    with open("data/buttons.csv", mode="r", encoding="utf-8") as csv_file:
        reader = list(csv.reader(csv_file, delimiter=",", quotechar="\""))
        buttons = {elem[0]: (int(elem[1]), int(elem[2])) for elem in reader[1:]}


class BlockObj:
    def __init__(self, obj_type, obj_id, x, y):
        global start_pos
        self.obj_type = obj_type
        self.obj_id = obj_id
        self.x, self.y = x, y
        self.sprites = pygame.sprite.Group()
        self.sprite = pygame.sprite.Sprite(self.sprites)
        self.sprite.image = load_image(f"{obj_type}{obj_id}.jpg")
        self.sprite.rect = self.sprite.image.get_rect()
        self.sprite.rect.x, self.sprite.rect.y = x, y

    def render(self, screen):
        self.sprites.draw(screen)

    def __repr__(self):
        return f"BlockObj({self.obj_type}, {self.obj_id}, {self.x}, {self.y})"


class Brick(BlockObj):
    def __init__(self, brick_id, x, y):
        super().__init__("brick", brick_id, x, y)


class Box(BlockObj):
    def __init__(self, box_id, x, y):
        super().__init__("box", box_id, x, y)

    @property
    def rect(self):
        return ((self.sprite.rect.x,
                 self.sprite.rect.y),
                (self.sprite.rect.x + BLOCK_SIDE,
                 self.sprite.rect.y + BLOCK_SIDE))

    @property
    def other_boxes(self):
        global boxes
        other_boxes = boxes.copy()
        index = []
        for i in range(len(boxes)):
            if boxes[i] is self:
                index = i
        other_boxes.pop(index)
        return other_boxes

    @property
    def cell(self):
        return self.sprite.rect.x // BLOCK_SIDE, self.sprite.rect.y // BLOCK_SIDE

    def __bool__(self):
        rect_points = set()
        for x in range(self.rect[0][0] + 3, self.rect[1][0] - 3):
            for y in range(self.rect[0][1] + 3, self.rect[1][1] - 3):
                rect_points.add((x, y))
        for position in positions:
            if position in rect_points:
                return True
        return False

    def wall_rect(self, x, y):
        return ((x * BLOCK_SIDE, y * BLOCK_SIDE),
                ((x + 1) * BLOCK_SIDE, (y + 1) * BLOCK_SIDE))

    def walls(self, board):
        x, y = self.rect[0][0] + BLOCK_SIDE // 2, \
               self.rect[0][1] + PLAYER_HEIGHT // 4
        bx, by = x // BLOCK_SIDE, \
                 y // BLOCK_SIDE
        dxl, dyl = [-1, 0, 1], [-1, 0, 1]
        walls_neighbours = []
        for dx in dxl:
            for dy in dyl:
                if dx * dy != 0 or not (0 <= bx + dx < N and 0 <= by + dy < M):
                    continue
                if isinstance(board[int(by + dy)][int(bx + dx)], Brick):
                    walls_neighbours.append(self.wall_rect(bx + dx, by + dy))
        for wall in walls_neighbours:
            if rect_intersect(self.rect, wall):
                return True

    def move(self, dx1, dy1, board):
        self.sprite.rect.x += dx1
        self.sprite.rect.y += dy1
        if self.walls(board):
            self.move(-dx1, -dy1, board)
            return False
        for box in self.other_boxes:
            if rect_intersect(self.rect, box.rect):
                box_moved1 = box.move(dx1, dy1, board)
                if not box_moved1:
                    return False
            if box.walls(board):
                box.move(-dx1, -dy1, board)
                return False
        return True


class Floor(BlockObj):
    def __init__(self, floor_id, x, y):
        super().__init__("floor", floor_id, x, y)


class Board:
    def __init__(self, level_number, obj_id):
        global start_pos, boxes, positions
        start_pos, self.board, boxes, positions = get_level(level_number, obj_id)
        self.board = [[LEVELS_DECODE[self.board[i][j]](obj_id, j * BLOCK_SIDE, i * BLOCK_SIDE)
                       for j in range(len(self.board[i]))]
                      for i in range(len(self.board))]

    def render(self, screen):
        for i in range(N):
            for j in range(M):
                self.board[j][i].render(screen)

    def __getitem__(self, item):
        return self.board[item]


class Player:
    def __init__(self, board):
        self.board = board
        self.sprites = pygame.sprite.Group()
        self.sprite = pygame.sprite.Sprite(self.sprites)
        self.sprite.image = load_image("players/front/1.png")
        self.sprite.rect = self.sprite.image.get_rect()
        self.sprite.rect.x, self.sprite.rect.y = start_pos
        self.prev_x, self.prev_y = None, None
        self.image_number = 1
        self.prev_right, self.prev_left, self.prev_down, self.prev_up = 0, 0, 0, 0

    @property
    def rect(self):
        return ((self.sprite.rect.x,
                 self.sprite.rect.y + PLAYER_HEIGHT // 2),

                (self.sprite.rect.x + BLOCK_SIDE,
                 self.sprite.rect.y + PLAYER_HEIGHT))

    def wall_rect(self, x, y):
        return ((x * BLOCK_SIDE, y * BLOCK_SIDE),
                ((x + 1) * BLOCK_SIDE, (y + 1) * BLOCK_SIDE))

    def wall_border(self):
        x, y = self.rect[0][0] + BLOCK_SIDE // 2, \
               self.rect[0][1] + PLAYER_HEIGHT // 4
        bx, by = x // BLOCK_SIDE, \
                 y // BLOCK_SIDE
        dxl, dyl = [-1, 0, 1], [-1, 0, 1]
        walls_neighbours = []
        for dx in dxl:
            for dy in dyl:
                if dx * dy != 0 or not (0 <= bx + dx < N and 0 <= by + dy < M):
                    continue
                if isinstance(self.board[int(by + dy)][int(bx + dx)], Brick):
                    walls_neighbours.append(self.wall_rect(bx + dx, by + dy))
        for wall in walls_neighbours:
            if rect_intersect(self.rect, wall):
                return True
        return False

    def move(self, x, y, up, right, down, left):
        if right == 0 and self.prev_right != 0:
            self.image_number = 1
            self.sprite.image = load_image("players/right/1.png")
            self.prev_right = 0
        elif left == 0 and self.prev_left != 0:
            self.image_number = 1
            self.sprite.image = load_image("players/left/1.png")
            self.prev_left = 0
        elif up == 0 and self.prev_up != 0:
            self.image_number = 1
            self.sprite.image = load_image("players/back/1.png")
            self.prev_up = 0
        elif down == 0 and self.prev_down != 0:
            self.image_number = 1
            self.sprite.image = load_image("players/front/1.png")
            self.prev_down = 0
        if x - self.sprite.rect.x > 0:
            if right > 19:
                self.image_number = self.image_number % 4 + 1
            self.sprite.image = load_image(f"players/right/{self.image_number}.png")
            self.prev_right = right
        if x - self.sprite.rect.x < 0:
            if left > 19:
                self.image_number = self.image_number % 4 + 1
            self.sprite.image = load_image(f"players/left/{self.image_number}.png")
            self.prev_left = left
        if y - self.sprite.rect.y < 0:
            if up > 19:
                self.image_number = self.image_number % 4 + 1
            self.sprite.image = load_image(f"players/back/{self.image_number}.png")
            self.prev_up = up
        if y - self.sprite.rect.y > 0:
            if down > 19:
                self.image_number = self.image_number % 4 + 1
            self.sprite.image = load_image(f"players/front/{self.image_number}.png")
            self.prev_down = down
        if abs(x - self.sprite.rect.x) > 1 or abs(y - self.sprite.rect.y) > 1:
            return self.sprite.rect.x, self.sprite.rect.y
        self.sprite.rect.x, self.sprite.rect.y = x, y
        box_moved = self.move_boxes(up, right, down, left)
        if self.wall_border():
            self.sprite.rect.x, self.sprite.rect.y = self.prev_x, self.prev_y
            return None, None
        if not box_moved:
            if right:
                self.sprite.rect.x -= 1
            elif left:
                self.sprite.rect.x += 1
            elif up:
                self.sprite.rect.y += 1
            elif down:
                self.sprite.rect.y -= 1
        self.prev_x, self.prev_y = self.sprite.rect.x, self.sprite.rect.y
        return None, None

    def move_boxes(self, up, right, down, left):
        box_moved = True
        for box in boxes:
            if rect_intersect(box.rect, self.rect):
                if up:
                    box_moved = box.move(0, -2, self.board)
                elif right:
                    box_moved = box.move(2, 0, self.board)
                elif down:
                    box_moved = box.move(0, 2, self.board)
                elif left:
                    box_moved = box.move(-2, 0, self.board)
        return box_moved

    def render(self, screen):
        self.sprites.draw(screen)


class Button:
    def __init__(self, width, btn_type=""):
        self.btn_type = btn_type
        self.sprites = pygame.sprite.Group()
        self.sprite = pygame.sprite.Sprite(self.sprites)
        self.sprite.image = load_image(f"buttons/{btn_type}.png", width=width)
        self.sprite.rect = self.sprite.image.get_rect()
        self.sprite.rect.x, self.sprite.rect.y = buttons[btn_type]

    def render(self, screen):
        self.sprites.draw(screen)


class Menu:
    def __init__(self, obj_id, menu_buttons):
        self.background = [[Brick(obj_id, j * BLOCK_SIDE, i * BLOCK_SIDE) for j in range(N)]
                           for i in range(M)]
        self.buttons = buttons

    def render(self, screen):
        for i in range(N):
            for j in range(M):
                self.background[j][i].render(screen)
        for btn in self.buttons:
            btn.render(screen)


LEVELS_DECODE = {"0": Brick, "1": Floor}


def main():
    pygame.init()
    get_buttons()
    screen = pygame.display.set_mode(SIZE)
    icon_surface = pygame.image.load("img/icon.png")
    pygame.display.set_caption("Sokoban")
    pygame.display.set_icon(icon_surface)
    clock = pygame.time.Clock()
    fps = 100
    running = True
    obj_id = 1
    level_number = 1
    board = Board(level_number, obj_id)
    player = Player(board)
    start_button = Button(width=300, btn_type="start")
    menu_buttons = [start_button]
    exit_button = Button(width=150, btn_type="exit")
    menu = Menu(obj_id, menu_buttons)
    x, y = player.sprite.rect.x, player.sprite.rect.y
    directions = {"right": False, "up": False, "down": False, "left": False}
    up, right, down, left = 0, 0, 0, 0
    radius_index = 0
    game_on = True
    display_font = False
    menu_opened = False
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if game_on:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RIGHT:
                        directions["right"] = True
                    elif event.key == pygame.K_LEFT:
                        directions["left"] = True
                    elif event.key == pygame.K_UP:
                        directions["up"] = True
                    elif event.key == pygame.K_DOWN:
                        directions["down"] = True
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_RIGHT:
                        directions["right"] = False
                        right = 0
                    elif event.key == pygame.K_LEFT:
                        directions["left"] = False
                        left = 0
                    elif event.key == pygame.K_UP:
                        directions["up"] = False
                        up = 0
                    elif event.key == pygame.K_DOWN:
                        directions["down"] = False
                        down = 0
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    if 1065 <= mx <= 1065 + 33 / 13 * BLOCK_SIDE and 15 <= my <= BLOCK_SIDE:
                        game_on = False
                    # todo: Доделать
            if not game_on:
                if not menu_opened:
                    display_font = True
                if display_font:
                    screen.fill(pygame.Color("black"))
                    font = pygame.font.Font("fonts/pixeboy.ttf", 100)
                    text = font.render("YOU WIN", True, pygame.Color("white"))
                    text_x = WIDTH // 2 - text.get_width() // 2
                    text_y = HEIGHT // 2 - text.get_height() // 2
                    screen.blit(text, (text_x, text_y))
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    for button in menu_buttons:
                        bx, by = buttons[button.btn_type]
                        # if bx <= mx <= bx +
                    # todo: Доделать
                if event.type == pygame.MOUSEBUTTONDOWN and display_font:
                    menu_opened = True
                    display_font = False
                    menu.render(screen)
        if game_on:
            if directions["right"]:
                right = (right + 1) % 20 + 1
                x += 1
            elif directions["left"]:
                left = (left + 1) % 20 + 1
                x -= 1
            elif directions["up"]:
                up = (up + 1) % 20 + 1
                y -= 1
            elif directions["down"]:
                down = (down + 1) % 20 + 1
                y += 1
            board.render(screen)
            exit_button.render(screen)
            for position in positions:
                pygame.draw.circle(screen, pygame.Color("red"), position,
                                   positions_radius[radius_index] // 20)
            for i in range(len(boxes)):
                boxes[i].render(screen)
            x1, y1 = player.move(x, y, up, right, down, left)
            if any([x1, y1]):
                x, y = x1, y1
            radius_index = (radius_index + 1) % len(positions_radius)
            player.render(screen)
            game_on = not all(boxes)
        clock.tick(fps)
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()
