from typing import Any, Tuple, Optional

from stimpl.expression import *
from stimpl.types import *
from stimpl.errors import *

"""
Interpreter State
"""


class State(object):
    def __init__(self, variable_name: str, variable_value: Expr, variable_type: Type, next_state: 'State') -> None:
        self.variable_name = variable_name
        self.value = (variable_value, variable_type)
        self.next_state = next_state

    def copy(self) -> 'State':
        variable_value, variable_type = self.value
        return State(self.variable_name, variable_value, variable_type, self.next_state)

    def set_value(self, variable_name, variable_value, variable_type):
        return State(variable_name, variable_value, variable_type, self)

    def get_value(self, variable_name) -> Any:
        currState = self
        while not isinstance(currState, EmptyState):
            if currState.variable_name == variable_name:
                return currState.value
            else:
                currState = currState.next_state

        return None

    def __repr__(self) -> str:
        return f"{self.variable_name}: {self.value}, " + repr(self.next_state)


class EmptyState(State):
    def __init__(self):
        pass

    def copy(self) -> 'EmptyState':
        return EmptyState()

    def get_value(self, variable_name) -> None:
        return None

    def __repr__(self) -> str:
        return ""


"""
Main evaluation logic!
"""


def evaluate(expression: Expr, state: State) -> Tuple[Optional[Any], Type, State]:
    match expression:
        case Ren():
            return (None, Unit(), state)

        case IntLiteral(literal=l):
            return (l, Integer(), state)

        case FloatingPointLiteral(literal=l):
            return (l, FloatingPoint(), state)

        case StringLiteral(literal=l):
            return (l, String(), state)

        case BooleanLiteral(literal=l):
            return (l, Boolean(), state)

        case Print(to_print=to_print):
            printable_value, printable_type, new_state = evaluate(
                to_print, state)

            match printable_type:
                case Unit():
                    print("Unit")
                case _:
                    print(f"{printable_value}")

            return (printable_value, printable_type, new_state)

        case Sequence(exprs=exprs) | Program(exprs=exprs):
            # Setting up default return
            currState = state
            result = None
            resultType = Unit()

            for expr in exprs:
                result, resultType, currState = evaluate(expr, currState)

            return (result, resultType, currState)

        case Variable(variable_name=variable_name):
            value = state.get_value(variable_name)
            if value == None:
                raise InterpSyntaxError(
                    f"Cannot read from {variable_name} before assignment.")
            variable_value, variable_type = value
            return (variable_value, variable_type, state)

        case Assign(variable=variable, value=value):

            value_result, value_type, new_state = evaluate(value, state)

            variable_from_state = new_state.get_value(variable.variable_name)
            _, variable_type = variable_from_state if variable_from_state else (
                None, None)

            if value_type != variable_type and variable_type != None:
                raise InterpTypeError(f"""Mismatched types for Assignment:
            Cannot assign {value_type} to {variable_type}""")

            new_state = new_state.set_value(
                variable.variable_name, value_result, value_type)
            return (value_result, value_type, new_state)

        case Add(left=left, right=right):
            result = 0
            left_result, left_type, new_state = evaluate(left, state)
            right_result, right_type, new_state = evaluate(right, new_state)

            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for Add:
            Cannot add {left_type} to {right_type}""")

            match left_type:
                case Integer() | String() | FloatingPoint():
                    result = left_result + right_result
                case _:
                    raise InterpTypeError(f"""Cannot add {left_type}s""")

            return (result, left_type, new_state)

        case Subtract(left=left, right=right):
            result = 0
            leftResult, leftType, newState = evaluate(left, state)
            rightResult, rightType, newState = evaluate(right, newState)

            if leftType != rightType:
                raise InterpTypeError(f"""Mismatched types for Subtract:
                                      Cannot subtract {leftType} from {rightType}""")

            match leftType:
                case Integer() | FloatingPoint():
                    result = leftResult - rightResult
                case _:
                    raise InterpTypeError(f"""Cannot Subtract {leftType}s""")

            return (result, leftType, newState)

        case Multiply(left=left, right=right):
            result = 0
            leftResult, leftType, newState = evaluate(left, state)
            rightResult, rightType, newState = evaluate(right, newState)

            if leftType != rightType:
                raise InterpTypeError(f"""Mismatched types for Multiply:
                                      Cannot multiply {leftType}s and {rightType}s""")

            match leftType:
                case Integer() | FloatingPoint():
                    result = leftResult * rightResult
                case _:
                    raise InterpTypeError(f"""Cannot Multiply {leftType}s""")

            return (result, leftType, newState)

        case Divide(left=left, right=right):
            result = 0
            leftResult, leftType, newState = evaluate(left, state)
            rightResult, rightType, newState = evaluate(right, newState)

            if leftType != rightType:
                raise InterpTypeError(f"""Mismatched types for Divide:
                                      Cannot multiply {leftType}s and {rightType}s""")

            if rightResult == 0:
                raise InterpMathError(f"""Cannot Divide by Zero""")

            match leftType:
                case Integer() | FloatingPoint():
                    result = leftResult / rightResult
                case _:
                    raise InterpTypeError(f"Cannot Divide {leftType}s")

            return (result, leftType, newState)

        case And(left=left, right=right):
            left_value, left_type, new_state = evaluate(left, state)
            right_value, right_type, new_state = evaluate(right, new_state)

            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for And:
            Cannot evaluate {left_type} and {right_type}""")
            match left_type:
                case Boolean():
                    result = left_value and right_value
                case _:
                    raise InterpTypeError(
                        "Cannot perform logical and on non-boolean operands.")

            return (result, left_type, new_state)

        case Or(left=left, right=right):
            leftResult, leftType, newState = evaluate(left, state)
            rightResult, rightType, newState = evaluate(right, newState)

            if leftType != rightType:
                raise InterpTypeError(f"""Mismatched types for Or:
            Cannot evaluate {leftType} and {rightType}""")
            match leftType:
                case Boolean():
                    result = leftResult or rightResult
                case _:
                    raise InterpTypeError("Cannot perform logical or on non-boolean operands.")

            return (result, leftType, newState)

        case Not(expr=expr):
            exprResult, exprType, newState = evaluate(expr, state)

            match exprType:
                case Boolean():
                   result = not(exprResult)
                case _:
                   raise InterpTypeError("Cannot perform logical not on non-boolean operand.")

            return (result, exprType, newState)

        case If(condition=condition, true=true, false=false):
            condResult, condType, newState = evaluate(condition, state)

            match condType:
                case Boolean():
                    tempRes = (condResult == True)
                    if tempRes:
                        result, resultType, newState = evaluate(true, newState)
                    else:
                        result, resultType, newState = evaluate(false, newState)
                case _:
                    raise InterpTypeError("Cannot perform If conditional on non-boolean condition")

            return (result, resultType, newState)

        case Lt(left=left, right=right):
            left_value, left_type, new_state = evaluate(left, state)
            right_value, right_type, new_state = evaluate(right, new_state)

            result = None

            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for Lt:
            Cannot compare {left_type} and {right_type}""")

            match left_type:
                case Integer() | Boolean() | String() | FloatingPoint():
                    result = left_value < right_value
                case Unit():
                    result = False
                case _:
                    raise InterpTypeError(
                        f"Cannot perform < on {left_type} type.")

            return (result, Boolean(), new_state)

        case Lte(left=left, right=right):
            leftVal, leftType, newState = evaluate(left, state)
            rightVal, rightType, newState = evaluate(right, newState)

            result = None

            if leftType != rightType:
                raise InterpTypeError(f"""Mismatched types for Lte:
                Cannot compare {leftType} and {rightType}""")

            match leftType:
                case Integer() | Boolean() | String() | FloatingPoint():
                    result = leftVal <= rightVal
                case Unit():
                    result = False  # Handle units properly!!!
                case _:
                    raise InterpTypeError(f"Cannot compare {leftType}s")

            return (result, Boolean(), newState)

        case Gt(left=left, right=right):
            leftVal, leftType, newState = evaluate(left, state)
            rightVal, rightType, newState = evaluate(right, newState)

            result = None

            if leftType != rightType:
                raise InterpTypeError(f"""Mismatched types for Gt:
                Cannot compare {leftType} and {rightType}""")

            match leftType:
                case Integer() | Boolean() | String() | FloatingPoint():
                    result = leftVal > rightVal
                case Unit():
                    result = False
                case _:
                    raise InterpTypeError(f"Cannot compare {leftType}s")

            return (result, Boolean(), newState)


        case Gte(left=left, right=right):
            leftVal, leftType, newState = evaluate(left, state)
            rightVal, rightType, newState = evaluate(right, newState)

            result = None

            if leftType != rightType:
                raise InterpTypeError(f"""Mismatched types for Gte:
                Cannot compare {leftType} and {rightType}""")

            match leftType:
                case Integer() | Boolean() | String() | FloatingPoint():
                    result = leftVal >= rightVal
                case Unit():
                    result = False
                case _:
                    raise InterpTypeError(f"Cannot compare {leftType}s")

            return (result, Boolean(), newState)

        case Eq(left=left, right=right):
            leftVal, leftType, newState = evaluate(left, state)
            rightVal, rightType, newState = evaluate(right, newState)

            result = None

            if leftType != rightType:
                raise InterpTypeError(f"""Mismatched types for Eq:
                Cannot compare {leftType} and {rightType}""")

            match leftType:
                case Integer() | Boolean() | String() | FloatingPoint():
                    result = (leftVal == rightVal)
                case Unit():
                    result = False
                case _:
                    raise InterpTypeError(f"Cannot compare {leftType}s")

            return (result, Boolean(), newState)

        case Ne(left=left, right=right):
            leftVal, leftType, newState = evaluate(left, state)
            rightVal, rightType, newState = evaluate(right, newState)

            result = None

            if leftType != rightType:
                raise InterpTypeError(f"""Mismatched types for Ne:
                Cannot compare {leftType} and {rightType}""")

            match leftType:
                case Integer() | Boolean() | String() | FloatingPoint():
                    result = not (leftVal == rightVal)
                case Unit():
                    result = False
                case _:
                    raise InterpTypeError(f"Cannot compare {leftType}s")

            return (result, Boolean(), newState)

        case While(condition=condition, body=body):
            currState = state

            while True:
                condResult, condType, newState = evaluate(condition, state)

                match condType:
                    case Boolean():
                        if condResult:
                            _, _, newState = evaluate(body, state)
                        else:
                            return None, Unit(), newState
                    case _:
                        raise InterpTypeError(f"Cannot evaluate while loops for {condType}s")

        case _:
            raise InterpSyntaxError("Unhandled!")
    pass


def run_stimpl(program, debug=False):
    state = EmptyState()
    program_value, program_type, program_state = evaluate(program, state)

    if debug:
        print(f"program: {program}")
        print(f"final_value: ({program_value}, {program_type})")
        print(f"final_state: {program_state}")

    return program_value, program_type, program_state
