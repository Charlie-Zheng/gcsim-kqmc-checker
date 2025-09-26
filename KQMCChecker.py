
import glob
import re
import sys
import argparse
import os
import traceback
from typing import List
from itertools import product
from dataclasses import dataclass, field

from Stats import Stat, main_values, avg_sub_values, flower_stats, feather_stats, sands_stats, hat_stats, goblet_stats

DEBUG = False

comment_regex = re.compile(r"#.*$", re.MULTILINE)
add_stats_regex = re.compile(r"([a-zA-Z]+) +add +stats +")
stat_regex = re.compile(r"([a-zA-Z%]+) *= *(\d*\.?\d*)")
set_regex = re.compile(
    r'([a-zA-Z]+) +add +set *= *"([a-zA-Z]*)" +count *= *(\d+)')

PRINT_ONLY_FAILS = False
ALLOCATED_SUBS_PER_STAT = 2
DISTRIBUTED_STATS_PER_NON_STAT_MAIN = 2
MAX_SUBS_TOTAL = 40


@dataclass
class ArtifactSet:
    name: str
    count: int


@dataclass
class ArtifactStats:
    stats: list[int] = field(default_factory=lambda: [0 for _ in Stat])
    sets: list[ArtifactSet] = field(default_factory=lambda: [])


def preprocess_file(file_content: str):
    file_content, _ = re.subn(comment_regex, "", file_content)
    file_content.replace(";", ";\n")
    lines = [x.strip() for x in file_content.splitlines()]
    return lines


def parse_json(jason: dict) -> dict[str, ArtifactStats]:
    char_stats: dict[str, ArtifactStats] = dict()
    for char_det in jason["character_details"]:
        char_name = char_det["name"]
        char_stats[char_name] = ArtifactStats()
        if "stats" in char_det.keys():
            for i in range(len(char_det["stats"])):
                char_stats[char_name].stats[i] = char_det["stats"][i]
        if "sets" in char_det.keys():
            for set_name, set_num in char_det["sets"].items():
                set_num = set_num // 2 * 2
                char_stats[char_name].sets.append(
                    ArtifactSet(set_name, set_num))
    return char_stats


def parse_lines(lines: List[str]):
    char_stats: dict[str, ArtifactStats] = dict()
    for line in lines:
        add_stats_match = re.match(add_stats_regex, line)
        if add_stats_match:
            char_name = add_stats_match.groups()[0]
            if char_name not in char_stats.keys():
                char_stats[char_name] = ArtifactStats()
            stats_data = line.split("stats")[-1]
            for stats_match in re.finditer(stat_regex, stats_data):
                stat = Stat.parse_stat(stats_match.groups()[0])
                value = float(stats_match.groups()[1])
                char_stats[char_name].stats[stat] += value
                add_stats_match = re.match(add_stats_regex, line)

        set_match = re.match(set_regex, line)
        if set_match:
            char_name = set_match.groups()[0]
            if char_name not in char_stats.keys():
                char_stats[char_name] = ArtifactStats()
            set_name = set_match.groups()[1].lower()
            set_num = int(set_match.groups()[2]) // 2 * 2
            if set_num != 0:
                char_stats[char_name].sets.append(
                    ArtifactSet(set_name, set_num))

    return char_stats


four_star_arti_sets = {"instructor", "scholar", "theexile", "exile"}
MAX_STAT_ERROR = 0.005


def check_main_stats_possible(equip_stats: tuple[Stat, Stat, Stat, Stat, Stat], possible_main_stats: List[int]) -> bool:
    used = [0 for _ in Stat]
    for stat in equip_stats:
        used[stat] += 1
        if possible_main_stats[stat] - used[stat] < 0:
            return False
    return True


def guess_main_stats(char_stats: ArtifactStats) -> list[tuple[Stat, Stat, Stat, Stat, Stat]]:
    for set in char_stats.sets:
        if set.name in four_star_arti_sets:
            debug(f"The 4* set {set.name} is not implemented for checking")
            raise NotImplementedError
    possible_main_stats = [0 for _ in Stat]
    for stat in Stat:
        if main_values[stat] is not None and char_stats.stats[stat] * (1+MAX_STAT_ERROR) >= main_values[stat]:
            possible_main_stats[stat] = int(
                char_stats.stats[stat] * (1+MAX_STAT_ERROR) / main_values[stat])
    valid_guesses = []

    perms = product(
        flower_stats,
        feather_stats,
        sands_stats,
        hat_stats,
        goblet_stats
    )

    for equip_stats in perms:
        if not check_main_stats_possible(equip_stats, possible_main_stats):
            continue
        valid_guesses.append(equip_stats)

    return valid_guesses


def get_subs_from_guess(char_stat: ArtifactStats, guess: tuple[Stat, Stat, Stat, Stat, Stat]):
    stats = char_stat.stats.copy()
    mains = [0 for _ in Stat]
    for stat in guess:
        stats[stat] -= main_values[stat]
        mains[stat] += 1
        if (-main_values[stat]*MAX_STAT_ERROR < stats[stat] < main_values[stat]*MAX_STAT_ERROR):
            stats[stat] = 0

    subs = [0 for _ in Stat]
    for stat in Stat:
        if stats[stat] != 0 and avg_sub_values[stat] == None:
            raise ValueError(
                f"'{stat}' has leftover stats that cannot be filled by sub stats")
        if avg_sub_values[stat] != None:
            sub_count = round(stats[stat]/avg_sub_values[stat])
            calculated_stat_total = sub_count * \
                avg_sub_values[stat] + ((mains[stat] * main_values[stat])
                                        if (mains[stat] != 0) else 0)
            msg = f"Cannot find integer subs. "
            err = False
            if not (calculated_stat_total * (1-MAX_STAT_ERROR) <= char_stat.stats[stat] <= calculated_stat_total * (1+MAX_STAT_ERROR)):
                msg += f"'{stat}' has {stats[stat]/avg_sub_values[stat]:.3f} subs"
                err = True
            if err:
                raise ValueError(msg)
            subs[stat] = sub_count
    return subs


def check_json(jason: str, name="Unknown name"):
    char_stats = parse_json(jason)
    all_valid = True
    msg = ""
    for char in char_stats.keys():
        possible_mains = []
        try:
            possible_mains = guess_main_stats(char_stats[char])
        except NotImplementedError:
            debug(
                f"{char} has 4* set. Skipping this character. Please confirm manually")
            msg += f"\t{char} has 4* set. Skipping this character. Please confirm manually\n\n"
            continue
        if len(possible_mains) == 0:
            debug(f"{char} does not have 5 possible main stats")
            msg += f"\t{char} does not have 5 possible main stats\n\n"
            all_valid = False
            continue
        debug(f"For character {char} found possible main stats combinations: ")
        err_m = []
        char_is_valid = False
        for guess in possible_mains:
            debug(f"\t{guess}")
            err_m.append(f"\t\t{guess}\n")
            if char_is_valid:
                debug(
                    "\t\tSkipping because a valid KQMC main/substat distribution has been found already")
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
                debug(
                    f"\t\tThis main stat guess was invalid due to failing KQMC substat check: {kqmc_msg}")
                err_m = [err_m[-1] + f"\t\t\t{kqmc_msg}"]
                break
        if not char_is_valid:
            debug(f"{char} isn't valid KQMC mains/substats")
            msg += f"\t{char} isn't valid KQMC mains/substats\n"
            if not DEBUG:
                msg += '\n'.join(err_m) + "\n\n"
        all_valid = all_valid and char_is_valid

    if all_valid:
        if not PRINT_ONLY_FAILS:
            msg = f"'{name}' is KQMC valid\n" + msg
        else:
            msg = ""
    else:
        msg = f"'{name}' is not KQMC valid\n" + msg

    return msg


def checkKQMC(mains, subs):
    if sum(subs) != MAX_SUBS_TOTAL:
        return False, f"Total sub count is {sum(subs)} but expected {MAX_SUBS_TOTAL}"
    for stat in Stat:
        if avg_sub_values[stat] != None:
            min_subs = ALLOCATED_SUBS_PER_STAT
            max_subs = ALLOCATED_SUBS_PER_STAT + DISTRIBUTED_STATS_PER_NON_STAT_MAIN * 5
            for main in mains:
                if stat == main:
                    max_subs -= DISTRIBUTED_STATS_PER_NON_STAT_MAIN

            if not (min_subs <= subs[stat] <= max_subs):
                return False, f"'{stat}' has {subs[stat]} substats but expected {min_subs} to {max_subs} subs"
    return True, ""


def debug(*args):
    if DEBUG:
        print(*args)


parser = argparse.ArgumentParser()
parser.add_argument('filename', nargs='*', metavar='filename', type=str,
                    default=[], help='the filename of the config to check')
parser.add_argument('--glob', action='store', metavar='glob', type=str,
                    default="", help='Directories of files')
parser.add_argument('--debug', action='store_true',
                    default=False, help='Print debug info')
parser.add_argument('--print-only-failures', action='store_true',
                    default=False, help='Prints results only on failures')
parser.add_argument('--kurt', action='store_true', default=False,
                    help='also check cons and weapon (not implemented yet)')


def check_config(config: str, name="Unknown name"):
    lines = preprocess_file(config)
    char_stats = parse_lines(lines)
    all_valid = True
    msg = ""
    for char in char_stats.keys():
        possible_mains = 0
        try:
            possible_mains = guess_main_stats(char_stats[char])
        except NotImplementedError:
            debug(
                f"{char} has 4* set. Skipping this character. Please confirm manually")
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
                debug(
                    "\t\tSkipping because a valid KQMC main/substat distribution has been found already")
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
                debug(
                    f"\t\tThis main stat guess was invalid due to failing KQMC substat check: {kqmc_msg}")
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
    DEBUG = args.debug
    files = args.filename
    PRINT_ONLY_FAILS = args.print_only_failures

    glob_str = args.glob
    if glob_str != "":
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
