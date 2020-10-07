import json

import cvxpy as cp
import numpy as np


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', '-i', type=str, required=True,
        help="Path to input JSON file.")
    parser.add_argument('--gamma', type=float, default=0.2,
        help="Penalties inside the interval are multiplied by gamma.")
    parser.add_argument('--t-min', type=float, default=0.2,
        help="Minimum expected target, used to compute the maximum weight. "
             "Defaults to 0.5")
    parser.add_argument('-absolute', action='store_true',
        help="If set, the objective will use absolute differences, instead of "
             "proportionally weighted differences.")
    args = parser.parse_args()

    max_weight = 1. / args.t_min
    print("Gamma: {}".format(args.gamma))

    # Open and parse requirements file
    with open(args.input, "r") as f:
        data = json.load(f)
        requirements = data['requirements']
        total = data['total']
        price = data.get('price', 0.0)
        ratio = price / total

    n_portions = len(requirements)

    print('Requirements:')
    name_pad = max([len(r['name']) for r in requirements])
    interval_pad = max([len(str(r['interval'])) for r in requirements])
    for req in requirements:
        print("{:<{name_pad}s}: interval = {:<{interval_pad}s} | target = {}".format(req['name'], str(req['interval']), req['target'],name_pad=name_pad, interval_pad=interval_pad))

    # Parse requirements
    names = []
    lower, upper, target = [], [], []
    for req in requirements:
        names.append(req['name'])
        lower.append(req['interval'][0])
        upper.append(req['interval'][1])
        if req['target'] == "lower":
            target.append(lower[-1])
        elif req['target'] == "upper":
            target.append(upper[-1])
        elif req['target'] == "center":
            target.append((lower[-1] + upper[-1]) / 2)
        else:
            target.append(float(req['target']))
    lower, upper, target = np.array(lower), np.array(upper), np.array(target)

    # Define problem
    x = cp.Variable(shape=(n_portions,))

    print("\nAdding constraints...")
    constraints = [cp.sum(x) == total]
    if np.sum(upper) >= total:
        print("Can reach total, adding upper bound constraints...")
        constraints.append(x <= upper)
    if np.sum(lower) <= total:
        print("Can stay below total, adding lower bound constraints...")
        constraints.append(x >= lower)

    def get_weights(arr, absolute):
        if absolute:
            return np.ones_like(arr)
        return np.where((1. / arr) > max_weight, max_weight, (1. / arr))

    lower_weights = get_weights(lower, args.absolute)
    upper_weights = get_weights(upper, args.absolute)
    target_weights = get_weights(target, args.absolute)
    objective = (
        cp.sum(lower_weights @ cp.square(cp.pos(lower - x))) +
        cp.sum(upper_weights @ cp.square(cp.pos(x - upper))) +
        args.gamma * cp.sum(target_weights @ cp.square(x - target))
    )

    # Solve problem
    prob = cp.Problem(cp.Minimize(objective), constraints)
    prob.solve()

    # Print result
    print("\nThe optimal value is", prob.value)
    print("A solution is:")
    sol = x.value
    for i, name in enumerate(names):
        if price > 0:
            sol_price = (1. + int(100 * ratio * sol[i])) / 100
            print("{:<{pad}s}: {:2.2f} units | $ {:3.2f}".format(name, sol[i], sol_price, pad=name_pad))
        else:
            print("{:<{pad}s}: {:2.2f} units".format(name, sol[i], pad=name_pad))
