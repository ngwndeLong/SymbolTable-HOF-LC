from StaticError import *
from Symbol import *
from functools import *

def simulate(list_of_commands):
    """
    Executes a list of commands and processes them sequentially.

    Args:
        list_of_commands (list[str]): A list of commands to be executed.

    Returns:
        list[str]: A list of return messages corresponding to each command.
    """
    def find(name, scopes):
        return next(((i, scope[name]) for i, scope in reversed(list(enumerate(scopes))) if name in scope), None)

    def valid_id(name):
        return (len(name) > 0 and name[0].islower() and all(i.isalnum() or i == '_' for i in name))
    
    def parse(cmd):
        if cmd.strip() != cmd: raise InvalidInstruction(cmd)
        if any(i == '' for i in cmd.split(' ')): raise InvalidInstruction(cmd)
        return cmd.split(' ')
    
    def insert(cmd, parts, scopes):
        if not valid_id(parts[1]) or parts[2] not in {"number", "string"}: raise InvalidInstruction(cmd)
        if parts[1] in scopes[-1]: raise Redeclared(cmd)
        return scopes[:-1] + [{**scopes[-1], parts[1]: parts[2]}], "success"
    
    def assign(cmd, parts, scopes):
        if not valid_id(parts[1]): raise InvalidInstruction(cmd)
        lhs = find(parts[1], scopes)
        if not lhs: raise Undeclared(cmd)
        rhs = parts[2]   
        if rhs.isdigit():
            if lhs[1] != "number": raise TypeMismatch(cmd)
        elif len(rhs) >= 2 and rhs[0] == "'" and rhs[-1] == "'" and all(i.isalnum() for i in rhs[1:-1]):
            if lhs[1] != "string": raise TypeMismatch(cmd)
        elif valid_id(rhs):
            rhs_found = find(rhs, scopes)
            if not rhs_found: raise Undeclared(cmd)
            if lhs[1] != rhs_found[1]: raise TypeMismatch(cmd)
        else: raise InvalidInstruction(cmd)
        return scopes[:-1] + [{**scopes[-1], parts[1]: rhs}], "success"
    
    def begin(scopes):
        return scopes + [{}], None
    
    def end(scopes):
        if len(scopes) == 1: raise UnknownBlock()
        return scopes[:-1], None
    
    def lookup(cmd, parts, scopes):
        if not valid_id(parts[1]): raise InvalidInstruction(cmd)
        found = find(parts[1], scopes)
        if not found: raise Undeclared(cmd)
        return scopes, str(found[0])

    def p_print(scopes):
        sorted_vars = sorted(reduce(lambda acc, curr: acc if any(curr[0] == x[0] for x in acc) else acc + [curr], list((name, level) for level, scope in list(reversed(list(enumerate(scopes)))) for name in scope), []), key = lambda x: (x[1], list((name, level) for level, scope in list(reversed(list(enumerate(scopes)))) for name in scope).index(x)))
        return scopes, " ".join(f"{name}//{level}" for name, level in sorted_vars)
    
    def r_print(scopes):
        return scopes, " ".join(f"{name}//{level}" for name, level in reduce(lambda acc, curr: acc if any(curr[0] == x[0] for x in acc) else acc + [curr], list((name, level) for level, scope in list(reversed(list(enumerate(scopes)))) for name in reversed(scope)), []))
    
    def dispatch(cmd, parts, scopes):
        if parts[0] == "INSERT":
            if len(parts) != 3: raise InvalidInstruction(cmd)
            return insert(cmd, parts, scopes)
        elif parts[0] == "ASSIGN":
            if len(parts) != 3: raise InvalidInstruction(cmd)
            return assign(cmd, parts, scopes)
        elif parts[0] == "BEGIN":
            if len(parts) != 1: raise InvalidInstruction(cmd)
            return begin(scopes)
        elif parts[0] == "END": 
            if len(parts) != 1: raise InvalidInstruction(cmd)
            return end(scopes)
        elif parts[0] == "LOOKUP": 
            if len(parts) != 2: raise InvalidInstruction(cmd)
            return lookup(cmd, parts, scopes)
        elif parts[0] == "PRINT": 
            if len(parts) != 1: raise InvalidInstruction(cmd)
            return p_print(scopes)
        elif parts[0] == "RPRINT":
            if len(parts) != 1: raise InvalidInstruction(cmd)
            return r_print(scopes)
        else: raise InvalidInstruction(cmd)
        
    def step(acc, cmd):
        current_output, current_scopes = acc
        try:
            parts = parse(cmd)
            new_scopes, output = dispatch(cmd, parts, current_scopes)
            return (current_output + [output], new_scopes)
        except StaticError as e: raise e

    final_output, final_scopes = reduce(step, list_of_commands, ([], [{}]))
    if len(final_scopes) > 1: raise UnclosedBlock(len(final_scopes) - 1)
    return list(filter(lambda x: x is not None, final_output))