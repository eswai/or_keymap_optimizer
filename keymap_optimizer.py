import sys
from itertools import combinations, permutations

from ortools.sat.python import cp_model


def optimize_keymap(penalty2, letters, input_text):
    """
    キーマップを最適化する関数。
    この関数は、与えられた文字のリストと入力テキストに基づいて、キーの割り当てを最適化します。
    最適化は、連接頻度とペナルティ行列に基づいて行われます。
    Args:
        penalty2 (list of list of int): キー間のペナルティを表す行列。
        letters (list of str): 割り当てる文字のリスト。
        input_text (str): 連接頻度を計算するための入力テキスト。
    Returns:
        list of str: 最適化されたキー割り当てを表すリスト。キーの位置に対応する文字が格納されます。
        None: 最適化が失敗した場合。
    """

    # ソルバーの作成
    model = cp_model.CpModel()
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 900  # 時間制限 sec
    solver.parameters.log_search_progress = True

    # キーの割り当て keyの位置にletterを割り当てる
    variables = {}
    for letter in letters:
        for key, _ in enumerate(letters):
            variables[(letter, key)] = model.NewBoolVar(f'{letter}_{key}')

    # 文字l1, l2をキーk1, k2に割り当てる
    for l1, l2 in permutations(letters, 2):
        for k1, k2 in combinations(range(len(letters)), 2):
            variables[(l1, l2, k1, k2)] = model.NewBoolVar(f'{l1}_{l2}_{k1}_{k2}')

    # 制約条件1: 各文字は1つのキーにのみ割り当て可能
    for letter in letters:
        model.Add(cp_model.LinearExpr.Sum([variables[(letter, key)] for key, _ in enumerate(letters)]) == 1)

    # 制約条件2: 各キーには1つの文字のみ割り当て可能
    for key, _ in enumerate(letters):
        model.Add(cp_model.LinearExpr.Sum([variables[(letter, key)] for letter in letters]) <= 1)

    # 制約条件3: variables[(l1, l2, k1, k2)]とvariables[(l1, k1)]とvariables[(l2, k2)]の関係
    for l1, l2 in permutations(letters, 2):
        for k1, k2 in combinations(range(len(letters)), 2):
            model.AddBoolAnd([variables[(l1, k1)], variables[(l2, k2)]]).OnlyEnforceIf(variables[(l1, l2, k1, k2)])
            model.AddBoolOr([variables[(l1, k1)].Not(), variables[(l2, k2)].Not()]).OnlyEnforceIf(variables[(l1, l2, k1, k2)].Not())

    # 目的関数 = Sum(連接頻度 x ペナルティ)
    expr = []
    coef = []
    for l1, l2 in permutations(letters, 2):
        freq = input_text.count(l1 + l2)
        # print(f"{l1}{l2}: {freq}")
        for k1, k2 in combinations(range(len(letters)), 2):
            expr.append(variables[(l1, l2, k1, k2)])
            coef.append(freq * penalty2[k1][k2])
    model.Minimize(cp_model.LinearExpr.WeightedSum(expr, coef))

    # 最適化の実行
    status = solver.solve(model)

    # 結果の表示
    print(f"Status = {solver.StatusName(status)}")
    print(f"Objective = {solver.ObjectiveValue()}")

    # result[key] = letterを作る
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        result = [None] * len(letters)
        for letter in letters:
            for key in range(len(letters)):
                # print(f"{letter}: {key} = {solver.Value(variables[(letter, key)])}")
                if solver.Value(variables[(letter, key)]) > 0.5:
                    result[key] = letter
        return result
    else:
        return None


# 最適化したい文字
letters_ = ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P',
            'A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', ';',
            'Z', 'X', 'C', 'V', 'B', 'N', 'M', ',', '.', '/']

# penalty = [4, 3, 3, 4, 5, 5, 4, 3, 3, 4,
#            4, 2, 1, 1, 4, 4, 1, 1, 2, 4,
#            5, 6, 6, 3, 4, 4, 3, 6, 6, 5]

# penalty_2gram[i][j] = 2文字をi, jの順に打鍵するときのペナルティ
# 大岡俊彦氏の研究に基づく http://oookaworks.seesaa.net/article/490739021.html
penalty_2gram = [
    #  Q      W      E      R      T      Y      U      I      O      P      A      S      D      F      G      H      J      K      L      ;      Z      X      C      V      B      N      M      ,      .      /
    [0.476, 0.581, 0.584, 0.556, 0.462, 0.137, 0.134, 0.129, 0.145, 0.148, 0.642, 0.621, 0.703, 0.527, 0.537, 0.202, 0.220, 0.245, 0.224, 0.242, 0.775, 0.675, 0.700, 0.545, 0.530, 0.205, 0.238, 0.238, 0.205, 0.227],  # Q
    [0.653, 0.429, 0.367, 0.361, 0.383, 0.075, 0.097, 0.090, 0.112, 0.123, 0.595, 0.653, 0.635, 0.429, 0.454, 0.191, 0.220, 0.256, 0.248, 0.259, 0.916, 0.746, 0.822, 0.487, 0.556, 0.205, 0.173, 0.194, 0.205, 0.216],  # W
    [0.527, 0.350, 0.367, 0.256, 0.512, 0.097, 0.101, 0.101, 0.097, 0.108, 0.497, 0.454, 0.437, 0.372, 0.411, 0.216, 0.191, 0.194, 0.188, 0.166, 0.523, 0.523, 0.548, 0.472, 0.462, 0.137, 0.140, 0.166, 0.173, 0.177],  # E
    [0.307, 0.256, 0.375, 0.375, 0.408, 0.086, 0.075, 0.083, 0.101, 0.097, 0.440, 0.440, 0.389, 0.411, 0.516, 0.169, 0.151, 0.177, 0.173, 0.199, 0.512, 0.556, 0.632, 0.559, 0.595, 0.129, 0.148, 0.159, 0.159, 0.155],  # R
    [0.383, 0.343, 0.350, 0.465, 0.383, 0.101, 0.155, 0.104, 0.115, 0.115, 0.353, 0.448, 0.472, 0.497, 0.469, 0.137, 0.177, 0.173, 0.166, 0.199, 0.469, 0.551, 0.595, 0.577, 0.502, 0.119, 0.104, 0.159, 0.180, 0.183],  # T
    [0.209, 0.245, 0.194, 0.227, 0.248, 0.220, 0.288, 0.080, 0.112, 0.188, 0.245, 0.253, 0.324, 0.389, 0.411, 0.321, 0.367, 0.224, 0.227, 0.180, 0.253, 0.213, 0.227, 0.238, 0.238, 0.422, 0.448, 0.487, 0.448, 0.270],  # Y
    [0.238, 0.253, 0.209, 0.220, 0.227, 0.288, 0.238, 0.036, 0.090, 0.123, 0.310, 0.346, 0.357, 0.303, 0.404, 0.335, 0.310, 0.224, 0.115, 0.159, 0.216, 0.216, 0.220, 0.220, 0.213, 0.397, 0.404, 0.429, 0.259, 0.188],  # U
    [0.205, 0.180, 0.267, 0.188, 0.242, 0.216, 0.238, 0.227, 0.264, 0.270, 0.199, 0.183, 0.267, 0.191, 0.231, 0.281, 0.465, 0.432, 0.491, 0.437, 0.177, 0.202, 0.357, 0.353, 0.324, 0.242, 0.256, 0.253, 0.216, 0.224],  # I
    [0.270, 0.303, 0.357, 0.307, 0.332, 0.155, 0.126, 0.183, 0.270, 0.324, 0.350, 0.389, 0.512, 0.429, 0.404, 0.134, 0.166, 0.389, 0.335, 0.332, 0.238, 0.242, 0.248, 0.267, 0.285, 0.259, 0.259, 0.497, 0.462, 0.700],  # O
    [0.324, 0.364, 0.383, 0.343, 0.321, 0.292, 0.177, 0.281, 0.386, 0.285, 0.285, 0.339, 0.367, 0.378, 0.350, 0.270, 0.183, 0.426, 0.378, 0.599, 0.238, 0.248, 0.264, 0.253, 0.299, 0.292, 0.224, 0.432, 0.454, 0.559],  # P
    [0.675, 0.761, 0.487, 0.458, 0.432, 0.220, 0.234, 0.238, 0.242, 0.224, 0.512, 1.000, 0.689, 0.367, 0.397, 0.199, 0.227, 0.209, 0.173, 0.216, 0.649, 0.735, 0.649, 0.465, 0.432, 0.123, 0.145, 0.151, 0.162, 0.166],  # A
    [0.627, 0.534, 0.383, 0.378, 0.462, 0.188, 0.173, 0.177, 0.183, 0.183, 0.508, 0.386, 0.372, 0.375, 0.432, 0.129, 0.140, 0.071, 0.173, 0.202, 0.624, 0.519, 0.692, 0.364, 0.451, 0.101, 0.112, 0.126, 0.137, 0.145],  # S
    [0.627, 0.534, 0.383, 0.378, 0.462, 0.134, 0.148, 0.155, 0.180, 0.191, 0.508, 0.386, 0.372, 0.375, 0.398, 0.123, 0.112, 0.145, 0.112, 0.123, 0.624, 0.519, 0.692, 0.364, 0.451, 0.083, 0.097, 0.101, 0.108, 0.115],  # D
    [0.335, 0.292, 0.253, 0.389, 0.443, 0.101, 0.104, 0.101, 0.115, 0.129, 0.231, 0.285, 0.194, 0.378, 0.389, 0.094, 0.140, 0.151, 0.169, 0.173, 0.307, 0.375, 0.440, 0.408, 0.451, 0.083, 0.094, 0.097, 0.112, 0.115],  # F
    [0.458, 0.332, 0.231, 0.462, 0.448, 0.119, 0.101, 0.115, 0.137, 0.119, 0.281, 0.361, 0.303, 0.426, 0.386, 0.104, 0.094, 0.126, 0.169, 0.199, 0.408, 0.480, 0.502, 0.469, 0.487, 0.069, 0.094, 0.104, 0.112, 0.151],  # G
    [0.299, 0.329, 0.339, 0.332, 0.343, 0.296, 0.303, 0.032, 0.069, 0.134, 0.238, 0.238, 0.278, 0.313, 0.432, 0.231, 0.248, 0.054, 0.101, 0.123, 0.278, 0.245, 0.270, 0.288, 0.383, 0.278, 0.310, 0.173, 0.140, 0.155],  # H
    [0.253, 0.224, 0.238, 0.174, 0.343, 0.346, 0.313, 0.010, 0.058, 0.086, 0.264, 0.288, 0.253, 0.274, 0.242, 0.303, 0.220, 0.000, 0.054, 0.101, 0.278, 0.321, 0.299, 0.292, 0.313, 0.307, 0.299, 0.083, 0.083, 0.159],  # J
    [0.224, 0.274, 0.231, 0.248, 0.285, 0.299, 0.213, 0.307, 0.188, 0.216, 0.259, 0.274, 0.274, 0.411, 0.101, 0.148, 0.104, 0.216, 0.108, 0.191, 0.367, 0.367, 0.285, 0.318, 0.364, 0.119, 0.123, 0.281, 0.183, 0.231],  # K
    [0.267, 0.299, 0.267, 0.285, 0.303, 0.177, 0.191, 0.220, 0.372, 0.397, 0.267, 0.299, 0.364, 0.318, 0.324, 0.162, 0.145, 0.259, 0.259, 0.307, 0.313, 0.361, 0.361, 0.364, 0.310, 0.162, 0.188, 0.270, 0.346, 0.256],  # L
    [0.248, 0.248, 0.248, 0.227, 0.267, 0.227, 0.281, 0.400, 0.472, 0.610, 0.288, 0.307, 0.310, 0.324, 0.307, 0.332, 0.318, 0.400, 0.339, 0.313, 0.339, 0.281, 0.264, 0.313, 0.324, 0.274, 0.264, 0.462, 0.581, 0.512],  # ;
    [0.670, 0.667, 0.508, 0.476, 0.534, 0.259, 0.245, 0.253, 0.281, 0.270, 0.581, 0.638, 0.559, 0.422, 0.383, 0.115, 0.134, 0.194, 0.199, 0.188, 0.451, 0.642, 0.567, 0.408, 0.367, 0.213, 0.242, 0.231, 0.231, 0.224],  # Z
    [0.653, 0.599, 0.472, 0.440, 0.556, 0.227, 0.191, 0.220, 0.231, 0.224, 0.472, 0.458, 0.329, 0.288, 0.469, 0.115, 0.137, 0.162, 0.159, 0.166, 0.437, 0.393, 0.397, 0.209, 0.386, 0.183, 0.209, 0.205, 0.177, 0.183],  # X
    [0.551, 0.632, 0.527, 0.527, 0.537, 0.256, 0.259, 0.270, 0.259, 0.264, 0.545, 0.476, 0.411, 0.364, 0.448, 0.097, 0.123, 0.123, 0.148, 0.140, 0.505, 0.372, 0.375, 0.162, 0.361, 0.194, 0.162, 0.159, 0.177, 0.194],  # C
    [0.335, 0.313, 0.274, 0.502, 0.516, 0.205, 0.209, 0.245, 0.245, 0.242, 0.216, 0.224, 0.119, 0.404, 0.437, 0.104, 0.123, 0.123, 0.126, 0.134, 0.288, 0.307, 0.343, 0.400, 0.422, 0.159, 0.083, 0.169, 0.191, 0.194],  # V
    [0.519, 0.429, 0.397, 0.581, 0.551, 0.202, 0.199, 0.183, 0.202, 0.188, 0.329, 0.404, 0.367, 0.516, 0.476, 0.108, 0.097, 0.134, 0.137, 0.140, 0.397, 0.408, 0.418, 0.408, 0.372, 0.151, 0.159, 0.173, 0.169, 0.159],  # B
    [0.296, 0.324, 0.364, 0.343, 0.361, 0.372, 0.353, 0.036, 0.064, 0.155, 0.253, 0.281, 0.324, 0.378, 0.332, 0.285, 0.307, 0.040, 0.090, 0.104, 0.288, 0.310, 0.339, 0.313, 0.404, 0.248, 0.245, 0.069, 0.090, 0.123],  # N
    [0.264, 0.339, 0.367, 0.335, 0.383, 0.367, 0.332, 0.043, 0.069, 0.086, 0.256, 0.303, 0.288, 0.321, 0.227, 0.278, 0.274, 0.010, 0.069, 0.094, 0.256, 0.270, 0.259, 0.310, 0.329, 0.303, 0.224, 0.029, 0.061, 0.108],  # M
    [0.307, 0.313, 0.329, 0.324, 0.353, 0.386, 0.383, 0.353, 0.281, 0.299, 0.259, 0.288, 0.285, 0.361, 0.367, 0.346, 0.194, 0.292, 0.432, 0.454, 0.307, 0.318, 0.313, 0.245, 0.259, 0.202, 0.162, 0.245, 0.155, 0.248],  # ,
    [0.329, 0.310, 0.324, 0.339, 0.339, 0.393, 0.303, 0.303, 0.422, 0.454, 0.288, 0.288, 0.292, 0.332, 0.321, 0.259, 0.173, 0.205, 0.292, 0.357, 0.248, 0.238, 0.281, 0.335, 0.318, 0.253, 0.155, 0.194, 0.227, 0.256],  # .
    [0.288, 0.339, 0.357, 0.343, 0.310, 0.329, 0.329, 0.386, 0.465, 0.562, 0.267, 0.267, 0.288, 0.299, 0.375, 0.264, 0.183, 0.375, 0.329, 0.437, 0.296, 0.238, 0.245, 0.270, 0.264, 0.202, 0.234, 0.346, 0.361, 0.307],  # /
]

if len(sys.argv) < 2:
    print("Usage: python keymap_optimizer.py <input_file>")
    sys.exit(1)

input_file = sys.argv[1]

with open(input_file, 'r', encoding='utf-8') as file:
    input_text_ = file.read()

result = optimize_keymap(penalty_2gram, letters_, input_text_.upper())

# 10列3行で表示
for i, l in enumerate(result):
    print(l, end=' ')
    if i % 10 == 9:
        print("")
