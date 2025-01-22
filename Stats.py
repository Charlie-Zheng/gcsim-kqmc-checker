from enum import IntEnum


class Stat(IntEnum):
    nothing = 0
    defd_pcnt = 1
    defd = 2
    hp = 3
    hp_pcnt = 4
    atk = 5
    atk_pcnt = 6
    er = 7
    em = 8
    cr = 9
    cd = 10
    heal = 11
    pyro = 12
    hydro = 13
    cryo = 14
    electro = 15
    anemo = 16
    geo = 17
    dendro = 18
    physical = 19
    atkspd = 20
    dmg = 21
    delim_base_stat = 22
    baseHP = 23
    baseATK = 24
    baseDef = 25

    def __str__(self):
        return self.name.replace("_pcnt", "%")

    def __repr__(self):
        return self.name.replace("_pcnt", "%")

    def parse_stat(text: str):
        if text in text_to_stat.keys():
            return text_to_stat[text]
        return Stat.nothing


flower_stats = {Stat.hp}
feather_stats = {Stat.atk}
sands_stats = {Stat.er, Stat.em, Stat.atk_pcnt, Stat.defd_pcnt, Stat.hp_pcnt}
hat_stats = {Stat.cr, Stat.cd, Stat.heal, Stat.em,
             Stat.atk_pcnt, Stat.defd_pcnt, Stat.hp_pcnt}
goblet_stats = {Stat.pyro, Stat.cryo, Stat.hydro, Stat.electro, Stat.geo,
                Stat.anemo, Stat.physical, Stat.dendro, Stat.em, Stat.atk_pcnt, Stat.defd_pcnt, Stat.hp_pcnt}


max_sub_values = [None for _ in Stat]
max_sub_values[Stat.hp] = 298.75
max_sub_values[Stat.hp_pcnt] = 0.0583
max_sub_values[Stat.defd] = 23.15
max_sub_values[Stat.defd_pcnt] = 0.0729
max_sub_values[Stat.atk] = 19.45
max_sub_values[Stat.atk_pcnt] = 0.0583
max_sub_values[Stat.em] = 23.31
max_sub_values[Stat.cr] = 0.0389
max_sub_values[Stat.cd] = 0.0777
max_sub_values[Stat.er] = 0.0648

avg_sub_multiplier = 0.85
avg_sub_values = [
    sub*avg_sub_multiplier if sub is not None else None for sub in max_sub_values]
avg_sub_values_4 = [
    sub*0.8 if sub is not None else None for sub in avg_sub_values]

main_values = [None for _ in Stat]
main_values[Stat.hp] = 4780
main_values[Stat.atk] = 311
main_values[Stat.hp_pcnt] = 0.466
main_values[Stat.atk_pcnt] = 0.466
main_values[Stat.defd_pcnt] = 0.583
main_values[Stat.em] = 186.5
main_values[Stat.er] = 0.518
main_values[Stat.pyro] = 0.466
main_values[Stat.hydro] = 0.466
main_values[Stat.cryo] = 0.466
main_values[Stat.electro] = 0.466
main_values[Stat.anemo] = 0.466
main_values[Stat.geo] = 0.466
main_values[Stat.dendro] = 0.466
main_values[Stat.physical] = 0.583
main_values[Stat.cr] = 0.311
main_values[Stat.cd] = 0.622
main_values[Stat.heal] = 0.359

text_to_stat = {
    "def%": Stat.defd_pcnt,
    "def": Stat.defd,
    "hp": Stat.hp,
    "hp%": Stat.hp_pcnt,
    "atk": Stat.atk,
    "atk%": Stat.atk_pcnt,
    "er": Stat.er,
    "em": Stat.em,
    "cr": Stat.cr,
    "cd": Stat.cd,
    "heal": Stat.heal,
    "pyro%": Stat.pyro,
    "hydro%": Stat.hydro,
    "cryo%": Stat.cryo,
    "electro%": Stat.electro,
    "anemo%": Stat.anemo,
    "geo%": Stat.geo,
    "dendro%": Stat.dendro,
    "phys%": Stat.physical,
}
