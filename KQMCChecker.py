from enum import IntEnum
import glob
import re
import sys
import argparse
import os
import traceback
from typing import List

DEBUG = False

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
    physical = 18
    dendro = 19
    atkspd = 20
    dmg = 21

    def __str__(self):
        return self.name.replace("_pcnt", "%")

    def __repr__(self):
        return self.name.replace("_pcnt", "%")

s = Stat


flower_stats = {s.hp}
feather_stats = {s.atk}
sands_stats = {s.er, s.em, s.atk_pcnt, s.defd_pcnt, s.hp_pcnt}
hat_stats = {s.cr, s.cd, s.heal, s.em, s.atk_pcnt, s.defd_pcnt, s.hp_pcnt}
goblet_stats = {s.pyro, s.cryo, s.hydro, s.electro, s.geo,
                s.anemo, s.physical, s.dendro, s.em, s.atk_pcnt, s.defd_pcnt, s.hp_pcnt}


max_sub_values = [None for _ in Stat]
max_sub_values[s.hp] = 298.75
max_sub_values[s.hp_pcnt] = 0.0583
max_sub_values[s.defd] = 23.15
max_sub_values[s.defd_pcnt] = 0.0729
max_sub_values[s.atk] = 19.45
max_sub_values[s.atk_pcnt] = 0.0583
max_sub_values[s.em] = 23.31
max_sub_values[s.cr] = 0.0389
max_sub_values[s.cd] = 0.0777
max_sub_values[s.er] = 0.0648

avg_sub_multiplier = (1+0.9+0.8+0.7)/4
avg_sub_values = [
    sub*avg_sub_multiplier if sub is not None else None for sub in max_sub_values]
avg_sub_values_4 = [
    sub*0.8 if sub is not None else None for sub in avg_sub_values]

main_values = [None for _ in Stat]
main_values[s.hp] = 4780
main_values[s.atk] = 311
main_values[s.hp_pcnt] = 0.466
main_values[s.atk_pcnt] = 0.466
main_values[s.defd_pcnt] = 0.583
main_values[s.em] = 186.5
main_values[s.er] = 0.518
main_values[s.pyro] = 0.466
main_values[s.hydro] = 0.466
main_values[s.cryo] = 0.466
main_values[s.electro] = 0.466
main_values[s.anemo] = 0.466
main_values[s.geo] = 0.466
main_values[s.dendro] = 0.466
main_values[s.physical] = 0.583
main_values[s.cr] = 0.311
main_values[s.cd] = 0.622
main_values[s.heal] = 0.359

text_to_stat = {
    "def%": s.defd_pcnt,
    "def": s.defd,
    "hp": s.hp,
    "hp%": s.hp_pcnt,
    "atk": s.atk,
    "atk%": s.atk_pcnt,
    "er": s.er,
    "em": s.em,
    "cr": s.cr,
    "cd": s.cd,
    "heal": s.heal,
    "pyro%": s.pyro,
    "hydro%": s.hydro,
    "cryo%": s.cryo,
    "electro%": s.electro,
    "anemo%": s.anemo,
    "geo%": s.geo,
    "dendro%": s.dendro,
    "phys%": s.physical,
}

comment_regex = re.compile("#.*$", re.MULTILINE)
add_stats_regex = re.compile("([a-zA-Z]+) +add +stats +")
stat_regex = re.compile("([a-zA-Z%]+) *= *(\d*\.?\d*)")
set_regex = re.compile(
    '([a-zA-Z]+) +add +set *= *"([a-zA-Z]*)" +count *= *(\d+)')

PRINT_ONLY_FAILS = False

def preprocess_file(file_content: str):
    file_content, _ = re.subn(comment_regex, "", file_content)
    file_content.replace(";", ";\n")
    lines = [x.strip() for x in file_content.splitlines()]
    return lines


def parse_lines(lines: List[str]):
    char_stats = dict()
    for line in lines:
        add_stats_match = re.match(add_stats_regex, line)
        if add_stats_match:
            char_name = add_stats_match.groups()[0]
            if char_name not in char_stats.keys():
                char_stats[char_name] = [0 for _ in Stat]
                char_stats[char_name].append([])
            stats_data = line.split("stats")[-1]
            for stats_match in re.finditer(stat_regex, stats_data):
                stat = text_to_stat[stats_match.groups()[0]]
                value = float(stats_match.groups()[1])
                char_stats[char_name][stat] += value
                add_stats_match = re.match(add_stats_regex, line)

        set_match = re.match(set_regex, line)
        if set_match:
            char_name = set_match.groups()[0]
            if char_name not in char_stats.keys():
                char_stats[char_name] = [0 for _ in Stat]
                char_stats[char_name].append([])
            set_name = set_match.groups()[1].lower()
            set_num = int(set_match.groups()[2]) // 2 * 2
            if set_num != 0:
                char_stats[char_name][-1].append((set_name, set_num))

    return char_stats


four_star_arti_sets = {"instructor", "scholar", "theexile", "exile"}
MAX_STAT_ERROR = 0.005


def guess_main_stats(char_stats: list):

    for set_name, _ in char_stats[-1]:
        if set_name in four_star_arti_sets:
            debug(f"The 4* set {set_name} is not implemented for checking")
            raise NotImplementedError

    possible_main_stats = dict()
    for stat in Stat:
        if main_values[stat] is not None and char_stats[stat] * (1+MAX_STAT_ERROR) >= main_values[stat]:
            possible_main_stats[stat] = int(
                char_stats[stat] * (1+MAX_STAT_ERROR) / main_values[stat])
    valid_guesses = []
    guess = [s.nothing for _ in range(5)]
    used = [0 for _ in Stat]
    for i in flower_stats:
        if i in possible_main_stats and possible_main_stats[i]-used[i] > 0:
            guess[0] = i
            used[i] += 1
            for ii in feather_stats:
                if ii in possible_main_stats and possible_main_stats[ii]-used[ii] > 0:
                    guess[1] = ii
                    used[ii] += 1
                    for iii in sands_stats:
                        if iii in possible_main_stats and possible_main_stats[iii]-used[iii] > 0:
                            guess[2] = iii
                            used[iii] += 1
                            for iv in hat_stats:
                                if iv in possible_main_stats and possible_main_stats[iv]-used[iv] > 0:
                                    guess[3] = iv
                                    used[iv] += 1
                                    for v in goblet_stats:
                                        if v in possible_main_stats and possible_main_stats[v]-used[v] > 0:
                                            guess[4] = v
                                            used[v] += 1
                                            valid_guesses.append(guess.copy())
                                            used[v] -= 1
                                    used[iv] -= 1
                            used[iii] -= 1
                    used[ii] -= 1
            used[i] -= 1

    return valid_guesses


def get_subs_from_guess(char_stats: List, guess: List):
    char_stats_copy = char_stats.copy()
    mains = [0 for _ in Stat]
    for stat in guess:
        char_stats_copy[stat] -= main_values[stat]
        mains[stat] += 1
        if (-main_values[stat]*MAX_STAT_ERROR < char_stats_copy[stat] < main_values[stat]*MAX_STAT_ERROR):
            char_stats_copy[stat] = 0

    subs = [0 for _ in Stat]
    for stat in Stat:
        if char_stats_copy[stat] != 0 and avg_sub_values[stat] == None:
            raise ValueError(
                "'{stat}' has leftover stats that cannot be filled by sub stats")
        if avg_sub_values[stat] != None:
            sub_count = round(char_stats_copy[stat]/avg_sub_values[stat])
            calculated_stat_total = sub_count * \
                avg_sub_values[stat] + ((mains[stat] * main_values[stat])
                                        if (mains[stat] != 0) else 0)
            msg = f"Cannot find integer subs. "
            err = False
            if not (calculated_stat_total * (1-MAX_STAT_ERROR) <= char_stats[stat] <= calculated_stat_total * (1+MAX_STAT_ERROR)):
                msg += f"'{stat}' has {char_stats_copy[stat]/avg_sub_values[stat]:.3f} subs"
                err = True
            if err:
                raise ValueError(msg)
            subs[stat] = sub_count
    return subs


ALLOCATED_SUBS_PER_STAT = 2
DISTRIBUTED_STATS_PER_NON_STAT_MAIN = 2
MAX_SUBS_TOTAL = 40

def checkKQMC(mains, subs):
    mains = mains.copy()
    if sum(subs) != MAX_SUBS_TOTAL:
        return False , f"Total sub count is {sum(subs)} but expected {MAX_SUBS_TOTAL}"
    for stat in Stat:
        if avg_sub_values[stat] != None:
            min_subs = ALLOCATED_SUBS_PER_STAT
            max_subs = ALLOCATED_SUBS_PER_STAT + DISTRIBUTED_STATS_PER_NON_STAT_MAIN * 5
            for main in mains:
                if stat == main:
                    max_subs -= DISTRIBUTED_STATS_PER_NON_STAT_MAIN

            if not (min_subs <= subs[stat] <= max_subs):
                return False , f"'{stat}' has {subs[stat]} substats but expected {min_subs} to {max_subs} subs"
    return True , ""


def debug(*args):
    if DEBUG:
        print(*args)

parser = argparse.ArgumentParser()
parser.add_argument('filename', nargs='*', metavar='filename', type=str,
                    default=[], help='the filename of the config to check')
parser.add_argument('--glob', action='store', metavar='glob', type=str,
                    default="", help='Directories of files')
parser.add_argument('--debug', action='store_true', default=False, help='Print debug info')
parser.add_argument('--print-only-failures', action='store_true', default=False, help='Prints results only on failures')
parser.add_argument('--kurt', action='store_true', default=False,
                    help='also check cons and weapon (not implemented yet)')
def check_config(config:str, name="Unknown name"):
    lines = preprocess_file(config)
    char_stats = parse_lines(lines)
    all_valid = True
    msg = ""
    for char in char_stats.keys():
        possible_mains = 0
        try:
            possible_mains = guess_main_stats(char_stats[char])
        except NotImplementedError:
            debug(f"{char} has 4* set. Skipping this character. Please confirm manually")
            msg += f"\t{char} has 4* set. Skipping this character. Please confirm manually\n\n"
            continue
        if len(possible_mains) == 0:
            debug(f"{char} does not have 5 possible main stats")
            msg += f"\t{char} does not have 5 possible main stats\n\n"
            all_valid = False
            continue
        debug(
            f"For character {char} found possible main stats combinations: ")
        err = ""
        err_m = []
        char_is_valid = False
        for guess in possible_mains:
            debug(f"\t{guess}")
            err_m.append(f"\t\t{guess}\n")
            if char_is_valid:
                debug("\t\tSkipping because a valid KQMC main/substat distribution has been found already")
                continue
            try:
                subs = get_subs_from_guess(char_stats[char], guess)
                debug(f"\t\t{subs=}")
            except ValueError as e:
                debug(
                    f"\t\tThis main stat guess was invalid:\n {e}")
                err_m[-1] += f"\t\t\t{e}"
                continue
            check, kqmc_msg = checkKQMC(guess, subs)
            char_is_valid = char_is_valid or check
            if not check:
                debug(f"\t\tThis main stat guess was invalid due to failing KQMC substat check: {kqmc_msg}")
                err_m = [err_m[-1] + f"\t\t\t{kqmc_msg}"]
                break
        if not char_is_valid:
            debug(f"{char} isn't valid KQMC mains/substats")
            msg += f"\t{char} isn't valid KQMC mains/substats\n"
            if not DEBUG:
                msg += err + '\n'.join(err_m) + "\n\n"
        all_valid = all_valid and char_is_valid

    if all_valid:
        if not PRINT_ONLY_FAILS:
            msg = f"'{name}' is KQMC valid\n" + msg
        else:
            msg = ""
    else:
        msg = f"'{name}' is not KQMC valid\n" + msg
    
    return msg

def main():
    global DEBUG, PRINT_ONLY_FAILS
    args = parser.parse_args()
    # print(args)
    DEBUG = args.debug
    files = args.filename
    PRINT_ONLY_FAILS = args.print_only_failures

    glob_str = args.glob
    if glob_str != "":
        print(glob_str)
        for file in glob.glob(glob_str, recursive=True):
            print(f"Globbing found {file}")
            files.append(file)

    for f in files:
        try:
            file = open(f, 'r', encoding='UTF-8')
            file_content = file.read()
            msg = check_config(file_content, os.path.basename(file.name))
            if msg:
                print(msg)
        except FileNotFoundError as e:
            print(e, file=sys.stderr)
        except Exception as e:
            print(f"exception occured while processing {f}", file=sys.stderr)
            print(e, file=sys.stderr)
            traceback.print_exc()
        finally:
            file.close()

main()
