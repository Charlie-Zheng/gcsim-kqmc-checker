import json
def get_stats(data:dict):

    char_final_stats=[[] for i in range(4)]
    for debug in json.loads(data["debug"]):
        if "final stats" in debug["msg"]:
            char_index = debug["char_index"]
            for stat, amount in debug["logs"].items():
                if stat in ["er", "cr", "cd"] or "%" in stat:
                    char_final_stats[char_index].append(f"\t{stat}:\t{float(amount)*100:.1f}%")
                else:
                    char_final_stats[char_index].append(f"\t{stat}:\t{float(amount):.1f}")


    output = []

    char_index = 0
    for char in data["char_details"]:
        # print(char)
        output.append(f"\tname: {char['name']}")
        output.append("\tstar: **FILL THIS IN YOURSELF**")
        output.append(f"\tconstellation: {char['cons']}")
        weapon = char["weapon"]
        output.append(f"\tweapon:")
        output.append(f"\t\tname: {weapon['name']}")
        output.append(f"\t\trefinement: {weapon['refine']}")
        output.append(f"\tartifacts:")
        for set, pc in char["sets"].items():
            output.append(f"\t\t{pc}pc {set}")
        output.extend(char_final_stats[char_index])
        output.append(f"\tdps: {data['damage_by_char_by_targets'][char_index]['1']['mean']:.0f}")
        output.append("----------------------------")
        output.append("")

        char_index+= 1
    
    output_str = '\n'.join(output)
    return output_str

if __name__ == "__main__":
    # get_stats(json.loads(input()))
    print(get_stats(json.loads(input())))