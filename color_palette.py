from colori import *
import json

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

    def find_closest_match(self, color: Colori, match_mode: ColorMatchMode) -> (Colori, str):
        dist = self.color_pairs[0][0].dist_to(color)
        best_pair = self.color_pairs[0]

        # yes the first element being done multiple times but I dont care
        for color_pair in self.color_pairs:
            new_dist = color_pair[0].dist_to(color, match_mode)

            if new_dist < dist:
                dist = new_dist
                best_pair = color_pair

        return best_pair


    color_pairs = []
