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
    
    def insert(cmd, parts, scopes):
        if not valid_id(parts[1]) or parts[2] not in {"number", "string"}: raise InvalidInstruction(cmd)
        if parts[1] in scopes[-1]: raise Redeclared(cmd)
        return scopes[:-1] + [{**scopes[-1], parts[1]: parts[2]}], "success"
    
    def assign(cmd, parts, scopes):
        if not valid_id(parts[1]): raise InvalidInstruction(cmd)
        if not find(parts[1], scopes): raise Undeclared(cmd)
        if parts[2].isdigit():
            if find(parts[1], scopes)[1] != "number": raise TypeMismatch(cmd)
        elif len(parts[2]) >= 2 and parts[2][0] == "'" and parts[2][-1] == "'" and all(i.isalnum() for i in parts[2][1:-1]):
            if find(parts[1], scopes)[1] != "string": raise TypeMismatch(cmd)
        elif valid_id(parts[2]):
            if not find(parts[2], scopes): raise Undeclared(cmd)
            if find(parts[1], scopes)[1] != find(parts[2], scopes)[1]: raise TypeMismatch(cmd)
        else: raise InvalidInstruction(cmd)
        return scopes[:-1] + [{**scopes[-1], parts[1]: parts[2]}], "success"
    
    def begin(scopes):
        return scopes + [{}], None
    
    def end(scopes):
        if len(scopes) == 1: raise UnknownBlock()
        return scopes[:-1], None
    
    def lookup(cmd, parts, scopes):
        if not valid_id(parts[1]): raise InvalidInstruction(cmd)
        if not find(parts[1], scopes): raise Undeclared(cmd)
        return scopes, str(find(parts[1], scopes)[0])

    def p_print(scopes):
        return scopes, " ".join(f"{name}//{level}" for name, level in sorted(reduce(lambda acc, curr: acc if any(curr[0] == x[0] for x in acc) else acc + [curr], list((name, level) for level, scope in list(reversed(list(enumerate(scopes)))) for name in scope), []), key = lambda x: (x[1], list((name, level) for level, scope in list(reversed(list(enumerate(scopes)))) for name in scope).index(x))))
    
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
        else: raise InvalidInstruction("Invalid command")
        
    def step(acc, cmd):
        current_output, current_scopes = acc
        try:
            new_scopes, output = dispatch(cmd, cmd.split(' '), current_scopes)
            return (current_output + [output], new_scopes)
        except StaticError as e: raise e

    final_output, final_scopes = reduce(step, list_of_commands, ([], [{}]))
    if len(final_scopes) > 1: raise UnclosedBlock(len(final_scopes) - 1)
    return list(filter(lambda x: x is not None, final_output))