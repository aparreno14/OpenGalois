import ast
from pathlib import Path

import pytest

# --- ROBUST PATH CONFIGURATION ---

def get_project_root() -> Path:
    """Find the root directory of the project by locating the 'pyproject.toml' file.

    Returns:
        Path: The root directory of the project.
    """
    current_path = Path(__file__).resolve().parent
    for parent in [current_path] + list(current_path.parents):
        if (parent / "pyproject.toml").exists():
            return parent
    return current_path.parent

PROJECT_ROOT = get_project_root()
SRC_DIR = PROJECT_ROOT / "src" / "opengalois"

# Verify that the paths exist before starting
if not SRC_DIR.exists():
    raise FileNotFoundError(
        f"Source directory not found at: {SRC_DIR}\n"
        f"Detected root: {PROJECT_ROOT}"
    )

# --- WHITELIST ---
# Files where importing sympy is ALLOWED
ALLOWED_FILES = {
    "core/polys.py",
}

# --- TEST LOGIC ---

class SympyImportVisitor(ast.NodeVisitor):
    """Analyze code to find sympy imports."""

    def __init__(self) -> None:
        """Initialize the SympyImportVisitor.

        Attributes:
            found_sympy (bool): Indicates if 'sympy' imports were found.
            lines (list[int]): Line numbers where 'sympy' imports were detected.
        """
        self.found_sympy: bool = False
        self.lines: list[int] = []

    def visit_Import(self, node: ast.Import) -> None:
        """Visit and analyze 'import' statements to detect 'sympy' imports.

        Args:
            node (ast.Import): The AST node representing an import statement.
        """
        for alias in node.names:
            if alias.name == "sympy" or alias.name.startswith("sympy."):
                self.found_sympy = True
                self.lines.append(node.lineno)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visit and analyze 'from ... import ...' statements to detect 'sympy' imports.

        Args:
            node (ast.ImportFrom): The AST node representing a 'from ... import ...' statement.
        """
        if node.module and (node.module == "sympy" or node.module.startswith("sympy.")):
            self.found_sympy = True
            self.lines.append(node.lineno)
        self.generic_visit(node)

def get_python_files(src_dir: Path) -> list[Path]:
    """Recursively find all Python files in the given directory.

    Args:
        src_dir (Path): The source directory to search for Python files.

    Returns:
        list[Path]: A list of paths to Python files.
    """
    return list(src_dir.rglob("*.py"))

def test_sympy_is_isolated_in_backend():
    """Verify that 'sympy' is only imported in allowed backend files.

    This test ensures that the 'sympy' library is only used in files explicitly
    listed in the whitelist (ALLOWED_FILES). This helps maintain a clean
    architecture by isolating heavy dependencies.

    Raises:
        pytest.fail: If 'sympy' is imported in files outside the allowed list.
    """
    python_files = get_python_files(SRC_DIR)
    violations = []

    print(f"\n[DEBUG] Analyzing {len(python_files)} files in {SRC_DIR}...")

    for file_path in python_files:
        # Calculate relative path (e.g., 'api.py' or 'core/polys.py')
        # .as_posix() ensures it uses / slashes even on Windows for string comparison
        rel_path = file_path.relative_to(SRC_DIR).as_posix()

        if rel_path in ALLOWED_FILES:
            continue

        try:
            with open(file_path, encoding="utf-8") as f:
                source = f.read()
                tree = ast.parse(source, filename=str(file_path))
        except (SyntaxError, UnicodeDecodeError):
            continue

        visitor = SympyImportVisitor()
        visitor.visit(tree)

        if visitor.found_sympy:
            violations.append(f"{rel_path} (lines: {visitor.lines})")

    if violations:
        pytest.fail(
            f"Architecture Violation: 'sympy' found outside the backend.\n"
            f"Only allowed in: {ALLOWED_FILES}\n"
            f"Violating files:\n" + "\n".join(f" - {v}" for v in violations)
        )