"""
Example usage of the new ProgramManager system.

This demonstrates how to use the ProgramManager class for program generation,
saving, validation, and execution.
"""

from ARCKG.task import TASK
from program import ProgramManager
from basics.ARCLOADER import load_task

def main():
    # Load a task (replace with actual task loading)
    # task = load_task("some_task_id")
    
    # For demonstration, we'll create a mock task
    # In real usage, you would load an actual task
    print("ProgramManager Example Usage")
    print("=" * 50)
    
    # Example of how to use ProgramManager:
    print("""
    # Initialize ProgramManager
    program_manager = ProgramManager(task)
    
    # Generate a program for a specific pair
    program = program_manager.generate_program(pair, pair_index)
    
    # Save the program
    program_manager.save_program(program, pair_index, "GRID")
    
    # Execute a saved program
    result = program_manager.execute_saved_program(pair_index, "GRID")
    
    # Validate all programs in a level
    validation_results = program_manager.validate_program("GRID")
    
    # Check if a program exists
    exists = program_manager.program_exists(pair_index, "GRID")
    
    # Load a program
    program_code = program_manager.load_program(pair_index, "GRID")
    """)
    
    print("ProgramManager provides the following main methods:")
    print("- generate_program(pair, pair_index)")
    print("- generate_program_with_rules(pair, pair_index, rules)")
    print("- generate_and_save_program(pair, pair_index, rules, level)")
    print("- save_program(program, pair_index, level)")
    print("- save_code_and_ast(output_dir, base_filename, code)")
    print("- execute_program(program_path, input_grid)")
    print("- execute_saved_program(pair_index, level)")
    print("- validate_program(level)")
    print("- program_exists(pair_index, level)")
    print("- load_program(pair_index, level)")
    print("- get_program_file_path(pair_index, level)")
    print("- ast_to_dict(node)")

if __name__ == "__main__":
    main()
