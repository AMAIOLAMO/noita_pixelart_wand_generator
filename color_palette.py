from colori import *
import json

class ColorMatch:
    def __init__(self, color: Colori, action_str: str, dist: float):
        self.color = color
        self.action_str = action_str
        self.dist = dist

    def get_action(self) -> str:
        return self.action_str

    def get_color(self) -> Colori:
        return self.color

    def get_dist(self) -> float:
        return self.dist

class Palette:
    @staticmethod
    def from_file(file_path: str) -> Palette:
        new_palette = Palette()

        with open(file_path, 'r') as plt_file:
            deserialized_palette_raw = json.load(plt_file)

            for pair in deserialized_palette_raw:
                color_arr = pair[0]
                spell_id = pair[1]

                new_palette.color_pairs.append(
                    (Colori(color_arr[0], color_arr[1], color_arr[2]), spell_id)
                )

        return new_palette

    def find_closest_match(self, color: Colori, match_mode: ColorMatchMode, dist_tolerance: float = 0.5) -> ColorMatch:
        best_dist = self.color_pairs[0][0].dist_to(color)
        best_pair = self.color_pairs[0]

        # yes the first element being done two times but it doesnt matter :)
        for color_pair in self.color_pairs:

            # speed up using tolerance
            if best_dist < dist_tolerance:
                break

            # TODO: can be sped up utilizing a faster LAB calculation
            # approx_dist = color_pair[0].dist_to(color, ColorMatchMode.PERCEPTUAL_LINEAR)
            #
            # if approx_dist > best_dist:
            #     continue

            new_dist = color_pair[0].dist_to(color, match_mode)

            if new_dist < best_dist:
                best_dist = new_dist
                best_pair = color_pair

        return ColorMatch(
            best_pair[0], best_pair[1], best_dist
        )


    color_pairs = []
