from random import randint, random

import numpy

from variables import *


def normalize_coords(*args):
    if len(args) == 1:
        args = args[0][0], args[0][1]
    x = args[0] % (window_width // 10)
    y = args[1]
    return x, y


class DeadCell(pygame.sprite.Sprite):
    def __init__(self, coords, game):
        super().__init__()
        self.game = game
        self.x = coords[1]
        self.y = coords[0]
        self.game.dead_cells_group.add(self)
        self.color = [150, 150, 150]
        self.border_color = (80, 80, 80)
        self.image = pygame.Surface((10, 10))
        self.rect = pygame.Rect(self.x, self.y, 10, 10)
        pygame.draw.rect(self.image, self.border_color, (0, 0, 10, 10))
        pygame.draw.rect(self.image, self.color, (1, 1, 8, 8))
        self.game.cells_field_image.add(self.image, self.x, self.y)

    def kill(self):
        self.game.cells_field[self.y][self.x] = None
        self.game.cells_field_image.delete(self.x, self.y)
        super().kill()


class Cell(pygame.sprite.Sprite):
    def __init__(self, coords, game, parent=None, color=[20, 150, 20]):
        super().__init__()
        game.cells_group.add(self)
        self.x = coords[1]
        self.y = coords[0]
        self.color = color
        self.border_color = (80, 80, 80)
        self.game = game
        self.energy = start_cell_energy
        self.max_energy = max_cell_energy
        self.genome_id: int = 0
        self.degree = randint(0, 7) * 45
        self.children_counter = 0
        self.rec_counter = 0

        self.actions_count = cells_number_of_available_actions
        self.image = pygame.Surface((10, 10))
        create_border(self.image, self.border_color)
        pygame.draw.rect(self.image, self.color, (1, 1, 8, 8))
        self.rect = pygame.Rect(self.x * 10, self.y * 10, 10, 10)

        self.game.cells_field_image.add(self.image, self.x, self.y)

        self.from_sun_energy_counter = 0
        self.from_cells_energy_counter = 0
        self.from_minerals_energy_counter = 0

        self.actions_dict = {
            21: self.get_self_energy,
            22: self.look_in_front,
            23: self.change_degree,
            24: self.get_energy_from_mineral,
            25: self.photosynthesize,
            26: self.move,
            27: self.bite
        }
        if not parent:
            self.genome = numpy.array([randint(24, 25) for i in range(64)], numpy.int8)
            # self.genome = numpy.array([randint(0, 64) for i in range(64)], numpy.int8)
        else:
            self.genome = parent.genome.copy()
            if random() < 0.25:
                self.genome[randint(0, 63)] = randint(1, 63)

    def change_color(self):
        maximum_color_id = 0
        colors = [self.from_cells_energy_counter,
                  self.from_sun_energy_counter,
                  self.from_minerals_energy_counter]
        if any(colors):
            for color_id in range(0, 3):
                if colors[color_id] > colors[maximum_color_id]:
                    maximum_color_id = color_id
            self.color[maximum_color_id] = 150
            for color_id in list({0, 1, 2} - {maximum_color_id}):
                self.color[color_id] = colors[color_id] / colors[maximum_color_id] * 150

    def bite(self, recursion_counter):
        in_front_coords = self.in_front_position()
        in_front_obj = self.get_object_from_coords(in_front_coords)
        if in_front_obj == 'Cell' or in_front_obj == 'DeadCell' or in_front_obj == 'FamilyCell':
            self.game.cells_field[in_front_coords[1]][in_front_coords[0]].kill()
            self.energy += energy_for_cell_eat

    def do_action(self, action_id, recursion_counter=0):
        if recursion_counter > 15:
            print('recdel')
            self.kill()
            return
        try:
            if action_id in self.actions_dict.keys():
                if self.actions_count - actions_costs[action_id] >= 0:
                    if action_id == 23:
                        self.actions_dict[action_id]((self.genome[(self.genome_id + 1) % 64] % 8)
                                                     * 45)
                    else:
                        self.actions_dict[action_id](recursion_counter)
                    self.actions_count -= actions_costs[action_id]
                    self.genome_id = (self.genome_id + 1) % 64
                    self.do_action(self.genome[self.genome_id], recursion_counter + 1)
                else:
                    self.energy -= cell_energy_to_live
                    self.actions_count = cells_number_of_available_actions
            else:
                self.genome_id = (self.genome_id + self.genome[(self.genome_id + 1) % 64]) % 64
                self.do_action(self.genome[self.genome_id], recursion_counter + 1)
        except RecursionError:
            print("recErr", recursion_counter)
            self.kill()

    def in_front_position(self):
        if self.degree == 0:
            coords = normalize_coords(self.x + 1, self.y)
        elif self.degree == 1 * 45:
            coords = normalize_coords(self.x + 1, self.y + 1)
        elif self.degree == 2 * 45:
            coords = normalize_coords(self.x, self.y + 1)
        elif self.degree == 3 * 45:
            coords = normalize_coords(self.x - 1, self.y + 1)
        elif self.degree == 4 * 45:
            coords = normalize_coords(self.x - 1, self.y)
        elif self.degree == 5 * 45:
            coords = normalize_coords(self.x - 1, self.y - 1)
        elif self.degree == 6 * 45:
            coords = normalize_coords(self.x, self.y - 1)
        elif self.degree == 7 * 45:
            coords = normalize_coords(self.x + 1, self.y - 1)
        return coords

    def change_degree(self, degree):
        self.degree = (self.degree + degree) % 360

    def get_self_energy(self, recursion_counter):
        if self.energy < self.genome[(self.genome_id + 1) % 64]:
            self.do_action(25, recursion_counter + 1)
        else:
            self.genome_id = (self.genome_id + 1) % 64
            self.do_action(self.genome_id, recursion_counter + 1)

    def look_in_front(self, recursion_counter):
        coords = self.in_front_position()
        in_front_obj = self.get_object_from_coords(*coords)
        if in_front_obj == 'Cell':
            coefficient = 1
        elif in_front_obj == 'DeadCell':
            coefficient = 2
        elif in_front_obj == 'FamilyCell':
            coefficient = 3
        elif in_front_obj == 'Wall':
            coefficient = 4
        elif not in_front_obj:
            coefficient = 5
        action_id = self.genome[(self.genome_id + coefficient) % 64]
        self.do_action(action_id, recursion_counter + 1)

    def move(self, recursion_counter):
        start_x, start_y = self.x, self.y
        self.change_degree((self.genome[(self.genome_id + 1) % 64] % 8) * 45)
        in_front_coords = self.in_front_position()
        if self.can_move(in_front_coords):
            self.x, self.y = in_front_coords
        if start_x != self.x or start_y != self.y:
            self.game.cells_field_image.move(start_x, start_y, self.x, self.y, self.image)
            self.rect.x, self.rect.y = self.x * 10, self.y * 10
            self.game.cells_field[start_y][start_x] = None
            self.game.cells_field[self.y][self.x] = self

    def can_move(self, *args):
        if len(args) == 1:
            x, y = args[0][0], args[0][1]
        else:
            x, y = args[0], args[1]

        if 0 <= y < window_height // 10 and \
            not self.get_object_from_coords(x % (window_width // 10), y):
            return True
        else:
            return False

    def get_object_from_coords(self, *args):
        if len(args) == 1:
            x, y = args[0][0], args[0][1]
        else:
            x, y = args[0], args[1]

        if y < 0 or y >= (window_height // 10):
            return 'Wall'
        if isinstance(self.game.cells_field[y][x], Cell):
            counter = 0
            for i in self.genome == self.game.cells_field[y][x]:
                if not i:
                    counter += 1
                    if counter > 1:
                        break
            if counter == 1:
                return 'FamilyCell'
            else:
                return 'Cell'
        elif isinstance(self.game.cells_field[y][x], DeadCell):
            return 'DeadCell'
        elif not self.game.cells_field[y][x]:
            return None

    def update(self, game):
        self.change_color()
        if self.energy >= self.max_energy:
            self.reproduce()
            pass
        elif self.energy <= 0:
            self.kill()
        # self.change_color()
        self.do_action(self.genome[self.genome_id])

    def reproduce(self):
        coords_list = []
        for i in range(0, 2):
            x = (self.x + (-1) ** i + window_width // 10) % (window_width // 10)
            y = self.y + (-1) ** i
            if self.can_move(x, self.y):
                coords_list.append((self.y, x))
            if self.can_move(self.x, y):
                coords_list.append((y, self.x))
        if len(coords_list):
            coords = coords_list[randint(0, len(coords_list) - 1)]
            self.game.cells_field[coords[0]][coords[1]] = \
                Cell([coords[0], coords[1]], self.game, self, self.color)
        else:
            self.game.cells_group.remove(self)
            # super().kill()
            self.game.cells_field[self.y][self.x] = DeadCell((self.y, self.x), self.game)
            return
        self.energy = start_cell_energy

        self.children_counter += 1
        if self.children_counter == 2:
            self.kill()

    def photosynthesize(self, recursion_counter):
        self.energy += self.game.energy_field[self.y][self.x]['sun']
        self.from_sun_energy_counter += 1

    def get_energy_from_mineral(self, recursion_counter):
        self.energy += self.game.energy_field[self.y][self.x]['minerals']
        self.from_minerals_energy_counter += 1

    def kill(self):
        self.game.cells_field[self.y][self.x] = None
        self.game.cells_field_image.delete(self.x, self.y)
        super().kill()
