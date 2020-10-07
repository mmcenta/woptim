# woptim

Using optimization to solve allocation problems.

This program solves the problem of allocating T units of something to N different people, each one with a preferred target and acceptable intervals.

## Input Specification

This program accepts as input a JSON file containing the total number of units, the price paid for all the units, and each person's preferences. The file should an object with the following properties:

* **total**: the total amount of units of goods that will be divided;
* **price**: (Optional) price paid for the total amount of goods. If provided, the program outputs how much each person should pay;
* **requirements**: the preferences of each person;

The **requirements** property should be a list of objects with the following properties:

* **name**: the name of the person;
* **interval**: the interval of acceptable values for this person. It should be a list with two numbers [lower, upper];
* **target**: the ideal value for this person. It can be either a number or the strings *lower*, *center*, *upper*, which denote the lower bound, the center, and the upper bound of the interval.

For example:
```json
{
    "total": 70,
    "price": 10,
    "requirements": [
        {
            "name": "alice",
            "interval": [30, 40],
            "target": "upper",
        },
        {
            "name": "bob",
            "interval": [30, 40],
            "target": "lower",
        }
    ]
}
```

## Method

This program works with *convex optimization* to minimize a custom convex function that models each person's discontent with a convex function to be minimized.

First, suppose that the constraints are satisfiable: the total amount is between the sum of lower bounds and the sum of upper bounds. Let <img src="https://i.upmath.me/svg/l" alt="l" />, <img src="https://i.upmath.me/svg/u" alt="u" />, and <img src="https://i.upmath.me/svg/t" alt="t" /> be the vectors of lower bounds, upper bounds, and targets, respectively. A first reflex is to solve the following problem:

<img src="https://i.upmath.me/svg/x%5E*%20%3D%20%5Carg%5Cmin_x%20%5Csum_%7Bi%3D1%7D%5E%7BN%7D(x_i%20-%20t_i)%5E2" alt="x^* = \arg\min_x \sum_{i=1}^{N}(x_i - t_i)^2" />

<img src="https://i.upmath.me/svg/%5Ctext%7Bs.t.%20%7D%20l_i%20%5Cleq%20x_i%20%5Cleq%20u_i%2C%20%5C%20%5Cforall%20i%20%3D%20%5B1%20..%20N%5D." alt="\text{s.t. } l_i \leq x_i \leq u_i, \ \forall i = [1 .. N]." />

However, these errors are not all equal. Suppose two people have targets 10 and 100 and that a solution misses these targets by one unit. In proportion, one person achieved 0.9 of their goal and the other 0.99, but they both had equivalent discontent according to the formulation above. We weight the objective function above proportionally to the target magnitude, but lower than a maximum weight <img src="https://i.upmath.me/svg/W" alt="W" />:

<img src="https://i.upmath.me/svg/x%5E*%20%3D%20%5Carg%5Cmin_x%20%5Csum_%7Bi%3D1%7D%5E%7BN%7Dw%5El_i%20(x_i%20-%20t_i)%5E2" alt="x^* = \arg\min_x \sum_{i=1}^{N}w^l_i (x_i - t_i)^2" />

<img src="https://i.upmath.me/svg/%5Ctext%7Bs.t.%20%7D%20l_i%20%5Cleq%20x_i%20%5Cleq%20u_i%2C%20%5C%20%5Cforall%20i%20%3D%20%5B1%20..%20N%5D%2C" alt="\text{s.t. } l_i \leq x_i \leq u_i, \ \forall i = [1 .. N]," />

where <img src="https://i.upmath.me/svg/w%5El_i%20%3D%20%5Cmin(1%2Ft_i%2C%20W)" alt="w^l_i = \min(1/t_i, W)" />. The maximum weight should be chosen such that <img src="https://i.upmath.me/svg/W%20%3D%201%20%2F%20t_%7Bmin%7D" alt="W = 1 / t_{min}" />, where <img src="https://i.upmath.me/svg/t_%7Bmin%7D" alt="t_{min}" /> is a minimum target (for example, we can choose <img src="https://i.upmath.me/svg/t_%7Bmin%7D%20%3D%200.5" alt="t_{min} = 0.5" /> for pizza slices). This assures that the solutions are more proportinally fair. This feature can be disabled with the `-absolute` flag, which sets all weights to 1.

Now we consider cases where the conditions are not satisfiable. In that case, we add additional error terms that are positive only when a value is outside of the acceptable interval. The <img src="https://i.upmath.me/svg/%5Cgamma" alt="\gamma" /> parameter, which defaults to 0.2, controls the trade-off between the error in relation to the target and the errors due to a value being outside the acceptable interval. The objective function can be written as:

<img src="https://i.upmath.me/svg/E(x)%20%3D%20%5Cgamma%20%5Csum_%7Bi%3D1%7D%5E%7BN%7D(x_i%20-%20t_i)%5E2%20%2B%20%5Csum_%7Bi%3D1%7D%5E%7BN%7D(l_i%20-%20x_i)_%2B%5E2%20%2B%20%5Csum_%7Bi%3D1%7D%5E%7BN%7D(x_i%20-%20u_i)_%2B%5E2%2C" alt="E(x) = \gamma \sum_{i=1}^{N}(x_i - t_i)^2 + \sum_{i=1}^{N}(l_i - x_i)_+^2 + \sum_{i=1}^{N}(x_i - u_i)_+^2," />

where <img src="https://i.upmath.me/svg/(.)_%2B%20%3A%3D%20%5Cmax(0%2C%20.)" alt="(.)_+ := \max(0, .)" />. The proportional formulation is:

<img src="https://i.upmath.me/svg/E(x)%20%3D%20%5Cgamma%20%5Csum_%7Bi%3D1%7D%5E%7BN%7Dw_i%5Et(x_i%20-%20t_i)%5E2%20%2B%20%5Csum_%7Bi%3D1%7D%5E%7BN%7Dw_i%5El(l_i%20-%20x_i)_%2B%5E2%20%2B%20%5Csum_%7Bi%3D1%7D%5E%7BN%7Dw_i%5Eu(x_i%20-%20u_i)_%2B%5E2%2C" alt="E(x) = \gamma \sum_{i=1}^{N}w_i^t(x_i - t_i)^2 + \sum_{i=1}^{N}w_i^l(l_i - x_i)_+^2 + \sum_{i=1}^{N}w_i^u(x_i - u_i)_+^2," />

where the weights <img src="https://i.upmath.me/svg/w%5El" alt="w^l" /> and <img src="https://i.upmath.me/svg/w%5Eu" alt="w^u" /> are calculated similarly to <img src="https://i.upmath.me/svg/w%5Et" alt="w^t" />. By removing the unsatisfiable constraints and optimizing the objective functions above, we solve these cases.

## Usage

The problem information should be entirely contained in the input JSON file. The program accepts the following arguments:

* `--input`, `-i`: path to input JSON file. Required;
* `--gamma`: penalties inside the interval are multiplied by gamma. Defaults to 0.2;
* `--t-min`: minimum expected target, used to compute the maximum weight. Defaults to 0.5;
* `-absolute`: if set, the objective will use absolute differences, instead of proportionally weighted differences.

## Requirements

To run this code, you will need:

* Python 3;
* Numpy;
* Cvxpy;
