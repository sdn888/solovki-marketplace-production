import os


def list_files(startpath):
    for root, dirs, files in os.walk(startpath):
        # Исключаем ненужные папки
        if 'venv' in dirs:
            dirs.remove('venv')
        if '__pycache__' in dirs:
            dirs.remove('__pycache__')

        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            if not file.endswith('.pyc'):
                print(f"{subindent}{file}")


list_files('.')