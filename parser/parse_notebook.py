import json
import ast

def extract_variables(code):
    """
    Given a code cell's source, return which variable names are
    assigned (created) and which are used (referenced).
    """
    assigned = set()
    used = set()

    try:
        tree = ast.parse(code)
    except SyntaxError:
        # Some cells have magic commands (%matplotlib inline) or
        # incomplete code that isn't valid Python on its own — skip these safely
        return {'assigned': [], 'used': [], 'parse_error': True}

    for node in ast.walk(tree):
        # Variable being assigned, e.g. df = ...
        if isinstance(node, ast.Name):
            if isinstance(node.ctx, ast.Store):
                assigned.add(node.id)
            elif isinstance(node.ctx, ast.Load):
                used.add(node.id)

    return {
        'assigned': sorted(assigned),
        'used': sorted(used),
        'parse_error': False
    }


def parse_notebook(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        notebook = json.load(f)

    cells = []
    for i, cell in enumerate(notebook['cells']):
        source = ''.join(cell['source'])
        cell_data = {
            'index': i,
            'type': cell['cell_type'],
            'source': source,
            'outputs': cell.get('outputs', [])
        }

        # Only run variable extraction on code cells
        if cell['cell_type'] == 'code':
            cell_data['variables'] = extract_variables(source)
        else:
            cell_data['variables'] = None

        cells.append(cell_data)

    return cells

def build_narrative_graph(cells):
    """
    Cross-references all cells to find variables that are created
    but never used again — a strong signal of orphaned/dead-end analysis.
    """
    variable_history = {}  # var_name -> {'created_at': int, 'used_at': [int, ...]}

    for cell in cells:
        if cell['type'] != 'code' or cell['variables'] is None:
            continue
        if cell['variables']['parse_error']:
            continue

        idx = cell['index']

        # Record where each variable was first created
        for var in cell['variables']['assigned']:
            if var not in variable_history:
                variable_history[var] = {'created_at': idx, 'used_at': []}

        # Record every place a variable was used
        for var in cell['variables']['used']:
            if var in variable_history:
                # only count uses AFTER creation
                if idx > variable_history[var]['created_at']:
                    variable_history[var]['used_at'].append(idx)

    # Flag variables that were created but never used again
    dead_ends = []
    for var, history in variable_history.items():
        if len(history['used_at']) == 0:
            dead_ends.append({
                'variable': var,
                'created_at': history['created_at']
            })

    return {
        'variable_history': variable_history,
        'dead_end_variables': dead_ends
    }

def get_notebook_analysis(file_path):
    cells = parse_notebook(file_path)
    graph = build_narrative_graph(cells)
    return {
        'cells': cells,
        'narrative_graph': graph
    }
if __name__ == '__main__':
    result = get_notebook_analysis(r'A:\PlotHole\test_notebooks\prediction-with-3-models.ipynb')
    
    for cell in result['cells']:
        print(f"Cell {cell['index']} ({cell['type']}): {cell['source'][:60]}...")
        if cell['variables']:
            print(f"   assigned: {cell['variables']['assigned']}")
            print(f"   used: {cell['variables']['used']}")

    print("\n--- Narrative Graph ---")
    print("Dead-end variables (created but never used again):")
    for d in result['narrative_graph']['dead_end_variables']:
        print(f"   '{d['variable']}' created in Cell {d['created_at']}, never used again")