import httk.atomistic.pathfinderutils as pfutils
import httk.atomistic.data.bilbaoDatasetAPI as bilbaoAPI
import datetime
import os
import json
from httk.atomistic.simplestructure import SimpleStructure
from httk.atomistic.symmetrystructure import SymmetryStructure
import httk.atomistic.symmetrystructureutils as symutils
from httk.atomistic.symmetrypath import SymmetryPath

def create_subgroup_structs(start_struct, start_subgroups, end_struct, end_subgroups):
    start_space_groups = [start_struct._space_number]
    start_intermediate_structs = []
    end_space_groups = [end_struct._space_number]
    end_intermediate_structs = None
    i = 1
    while i < len(start_subgroups)-1:
        start_intermediate_structs.append(symutils.create_lower_symmetry_copy(start_struct, start_subgroups[i][0]["int_number"], transformation_id=start_subgroups[i][0]["id"]))
        i += 1
    if len(start_subgroups) > 1:
        start_common_struct = symutils.create_lower_symmetry_copy(start_struct, start_subgroups[-1][0]["int_number"], transformation_id=start_subgroups[-1][0]["id"])
    else:
        start_common_struct = start_struct
    i = 1
    while i < len(end_subgroups)-1:
        end_intermediate_structs.append(symutils.create_lower_symmetry_copy(end_struct, end_subgroups[i][0]["int_number"], transformation_id=end_subgroups[i][0]["id"]))
        i += 1
    if len(start_subgroups) > 1:
        end_common_struct = symutils.create_lower_symmetry_copy(end_struct, end_subgroups[-1][0]["int_number"], transformation_id=end_subgroups[-1][0]["id"])
    else:
        end_common_struct = end_struct
    if symutils.compare_wyckoffs(start_common_struct, end_common_struct):
        return SymmetryPath(common_subgroup_number=start_subgroups[-1][0]["int_number"],
                            start_space_groups=start_space_groups,
                            start_orig=None,
                            start_sym=start_struct,
                            start_common_struct=start_common_struct,
                            start_intermediate_structs=start_intermediate_structs,
                            end_space_groups=end_space_groups,
                            end_orig=None,
                            end_sym=end_struct,
                            end_common_struct=end_common_struct,
                            end_intermediate_structs=end_intermediate_structs)
    return None

def search_for_paths(start_struct, start_path, end_struct, end_path, max_size, sub_type, max_depth, max_results, subgroup_choices, search_within_spacegroup=False):
    complete_matches = []
    continue_search = True
    curr_depth = 0
    start_path_prev_len = 0
    end_path_prev_len = 1
    start_path_init_len = len(start_path[0])
    end_path_init_len = len(end_path[0])
    if len(start_path) > 1 or len(end_path) > 1:
        print("Incorrectly provided lengths of starting paths")
    subgroup_restriction = []
    if search_within_spacegroup:
        subgroup_restriction.append(start_path[0][-1][0]["int_number"])
    while continue_search:
        i = start_path_prev_len
        while i < len(start_path):
            if start_path[i][-1][0]["int_number"] in subgroup_choices:
                j = 0
                while j < len(end_path):
                    if end_path[j][-1][0]["int_number"] in subgroup_choices:
                        if end_path[j][-1][0]["int_number"] == start_path[i][-1][0]["int_number"]:
                            if end_path[j][-1][1] == start_path[i][-1][1]:
                                sym_path = create_subgroup_structs(start_struct, start_path[i], end_struct, end_path[j])
                                if sym_path:
                                    subgroup_choices.remove(start_path[i][-1][0]["int_number"])
                                    complete_matches.append(sym_path)
                                    if len(complete_matches) == max_results:
                                        return complete_matches
                            elif not search_within_spacegroup:
                                new_matches = search_for_paths(start_struct, [start_path[i]], end_struct, [end_path[j]], max_size, sub_type, 4, 1, [start_path[i][-1][0]["int_number"]], True)
                                subgroup_choices.remove(start_path[i][-1][0]["int_number"])
                                if len(new_matches) > 0:
                                    complete_matches += new_matches
                                    if len(complete_matches) == max_results:
                                        return complete_matches
                    j += 1
            i += 1
        i = 0
        while i < start_path_prev_len:
            if start_path[i][-1][0]["int_number"] in subgroup_choices:
                j = end_path_prev_len
                while j < len(end_path):
                    if end_path[j][-1][0]["int_number"] in subgroup_choices:
                        if end_path[j][-1][0]["int_number"] == start_path[i][-1][0]["int_number"]:
                            if end_path[j][-1][1] == start_path[i][-1][1]:
                                sym_path = create_subgroup_structs(start_struct, start_path[i], end_struct, end_path[j])
                                if sym_path:
                                    subgroup_choices.remove(start_path[i][-1][0]["int_number"])
                                    complete_matches.append(sym_path)
                                    if len(complete_matches) == max_results:
                                        return complete_matches
                            elif not search_within_spacegroup:
                                new_matches = search_for_paths(start_struct, [start_path[i]], end_struct, [end_path[j]], max_size, sub_type, 4, 1, [start_path[i][-1][0]["int_number"]], True)
                                subgroup_choices.remove(start_path[i][-1][0]["int_number"])
                                if len(new_matches) > 0:
                                    complete_matches += new_matches
                                    if len(complete_matches) == max_results:
                                        return complete_matches
                    j += 1
            i += 1
        curr_depth += 1
        all_new_empty = True
        if curr_depth < max_depth:
            k = 0
            start_path_prev_len = len(start_path)
            while k < start_path_prev_len:
                if len(start_path[k]) == curr_depth - 1 + start_path_init_len:
                    new_subgroups = bilbaoAPI.get_max_subgroups(start_path[k][-1][0]["int_number"], sub_type, start_path[k][-1][1], max_size, subgroup_restriction, search_within_spacegroup)
                    for subgroup in new_subgroups:
                        all_new_empty = False
                        start_path.append(start_path[k] + [(subgroup, start_path[k][-1][1] * subgroup["size_increase"])])
                k += 1
            m = 0
            end_path_prev_len = len(end_path)
            while m < end_path_prev_len:
                if len(end_path[m]) == curr_depth - 1 + end_path_init_len:
                    new_subgroups = bilbaoAPI.get_max_subgroups(end_path[m][-1][0]["int_number"], sub_type, end_path[m][-1][1], max_size, subgroup_restriction, search_within_spacegroup)
                    for subgroup in new_subgroups:
                        all_new_empty = False
                        end_path.append(end_path[m] + [(subgroup, end_path[m][-1][1] * subgroup["size_increase"])])
                m += 1
        else:
            continue_search = False
        if all_new_empty:
            continue_search = False
    return complete_matches

def get_paths(start_struct, end_struct, max_depth, symprec, sub_type, max_path, max_orig, max_results, steps, subgroups, collision_threshold, collision_level):
    # Function for getting start and end structures, generating paths and generating the structures along the paths.
    if isinstance(start_struct, SimpleStructure):
        start_struct_sym = symutils.create_from_simple_struct(start_struct, symprec)
    else:
        start_struct_sym = start_struct
    if isinstance(end_struct, SimpleStructure):
        end_struct_sym = symutils.create_from_simple_struct(end_struct, symprec)
    else:
        end_struct_sym = end_struct
    prefix_str = symutils.check_path_compatibility(start_struct_sym, end_struct_sym, max_orig)
    if subgroups[0].lower() == "any":
        subgroup_choice = [x for x in range(1, 231)]
    else:
        subgroup_choice = [int(x) for x in subgroups]
    paths_1 = [[({"int_number": start_struct_sym._space_number}, start_struct_sym._num_of_atoms)]]
    paths_2 = [[({"int_number": end_struct_sym._space_number}, end_struct_sym._num_of_atoms)]]
    found_paths = search_for_paths(start_struct_sym, paths_1, end_struct_sym, paths_2, max_path, sub_type, max_depth, max_results, subgroup_choice)
    if len(found_paths) == 0:
        print("No found paths")
        return None, None, None, None, "no_path"
        #sys.exit(0)
    i = 0
    while i < len(found_paths):
        symutils.generate_interpolation(found_paths[i], steps, collision_threshold, collision_level)
        i += 1
    return prefix_str, start_struct, end_struct, found_paths

def get_subgroup_struct(orig_struct, subgroup_num, symprec):
    # timing code
    # import time
    struct_info = symutils.read_file(orig_struct, symprec)
    reduced_formula = symutils.get_reduced_formula_info(struct_info["formula"])
    prefix_str = "".join([i + str(j) if j > 1 else i for i, j in reduced_formula.items()])
    subgroups = bilbaoAPI.get_max_subgroups(struct_info["space_number"])
    i = 0
    while i < len(subgroups):
        if subgroup_num[0] != "all":
            if subgroups[i]["int_number"] not in subgroup_num or subgroups[i]["int_number"] == struct_info["space_number"]:
                del subgroups[i]
                i -= 1
        elif subgroups[i]["int_number"] == struct_info["space_number"]:
            del subgroups[i]
            i -= 1
        i += 1
    if len(subgroups) == 0:
        print("Space group(s) " + str(subgroup_num) + " not in list of maximal subgroups of space group " + str(struct_info["space_number"]))
    subgroup_structs = []
    trans_info_list = []
    for subgroup_info in subgroups:
        # timing code
        # start_time = time.time()
        transformation_info = symutils.get_best_trans_matrix(bilbaoAPI.get_trans_matrices(struct_info["space_number"], subgroup_info["id"]))
        wp_splitting = transformation_info["wp_splitting"]
        transformation_matrix = transformation_info["trans_matrix"]
        next_wyckoffs = symutils.get_next_wyckoffs(subgroup_info["int_number"], struct_info["wyckoffs"], wp_splitting)
        trans_info_list.append({"matrix": transformation_matrix, "group": {"space_num": struct_info["space_number"], "wyckoff": struct_info["wyckoffs"]}, "subgroup": {"space_num": subgroup_info["int_number"], "wyckoff": next_wyckoffs}})
        new_positions = []
        new_numbers = []
        new_lattice = symutils.calc_new_lattice(struct_info["new_struct"][0], transformation_matrix)
        for wyckoff in next_wyckoffs:
            pos, num = symutils.get_pos_from_wyckoff(subgroup_info["int_number"], wyckoff)
            new_positions += list(pos)
            new_numbers += list(num)
        subgroup_structs.append((new_lattice, new_positions, new_numbers))
        # timing code
        # end_time = time.time()
        # elapsed_time = (end_time-start_time)
        # trans_info_list[-1]["time"] = elapsed_time
    return struct_info["space_number"], struct_info["new_struct"], subgroup_structs, trans_info_list, prefix_str

def output_paths(prefix_str, start_orig, end_orig, paths_short, paths_main, output_folder, formats, output_name, input_values):
    # Output results to files.
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    if output_name:
        work_folder = os.path.join(output_folder, output_name)
    else:
        work_folder = os.path.join(output_folder, timestamp)
    input_values["timestamp"] = timestamp
    os.makedirs(work_folder)
    main_dict = {"input_values": input_values, "paths": paths_short}
    with open(os.path.join(work_folder, prefix_str + "_out.json"), "w") as f:
        json.dump(main_dict, f, indent=4)
    for format_name in formats:
        symutils.write_struct_to_file(os.path.join(work_folder, prefix_str + "_start." + format_name.replace("poscar", "vasp")), start_orig, format_name)
        symutils.write_struct_to_file(os.path.join(work_folder, prefix_str + "_end." + format_name.replace("poscar", "vasp")), end_orig, format_name)
    for key_main, val_main in paths_main.items():
        for key, val in val_main.items():
            os.makedirs(os.path.join(work_folder, key_main, key))
            for struct_key, struct_val in val.items():
                if struct_key == "structs":
                    i = 0
                    while i < len(struct_val):
                        for format_name in formats:
                            symutils.write_struct_to_file(os.path.join(os.path.join(work_folder, key_main, key), prefix_str + "_path" + key_main + "_" + key + "_" + str(i) + "." + format_name.replace("poscar", "vasp")), struct_val[i], format_name)
                        i += 1
                elif struct_key == "desc":
                    symutils.write_interpolation_info(os.path.join(os.path.join(work_folder, key_main, key), prefix_str + "_path" + key_main + "_" + key + "_" + struct_key + ".txt"), struct_val)
                elif "-" in struct_key:
                    symutils.write_transition(os.path.join(os.path.join(work_folder, key_main, key), prefix_str + "_path" + key_main + "_" + key + "_" + struct_key + ".txt"), struct_val)
                else:
                    for format_name in formats:
                        symutils.write_struct_to_file(os.path.join(os.path.join(work_folder, key_main, key), prefix_str + "_path" + key_main + "_" + key + "_" + struct_key + "_" + str(paths_short[key_main][key][int(struct_key) - 1]) + "." + format_name.replace("poscar", "vasp")), struct_val, format_name)

def output_subgroup(file_prefix, start_num, std_struct, sub_structs, transition_info, output_folder, formats):
    work_folder = os.path.join(output_folder, datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
    os.makedirs(work_folder)
    for format_name in formats:
        symutils.write_struct_to_file(os.path.join(work_folder, file_prefix + "_" + str(start_num) + "_std." + format_name.replace("poscar", "vasp")), std_struct, format_name)
    i = 0
    while i < len(sub_structs):
        for format_name in formats:
            symutils.write_struct_to_file(os.path.join(work_folder, file_prefix + "_" + str(transition_info[i]["subgroup"]["space_num"]) + "_struct." + format_name.replace("poscar", "vasp")), sub_structs[i], format_name)
        symutils.write_transition(os.path.join(work_folder, file_prefix + "_" + str(transition_info[i]["subgroup"]["space_num"]) + "_wyckoff.txt"), transition_info[i])
        i += 1
