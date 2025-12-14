#!/usr/bin/env python3
"""Test helper to run analyze_image_with_gemini on the server.

Usage:
  python tools/test_analyze.py /full/path/to/test.jpg

What it does:
- prints environment info (Python executable, GEMINI_API_KEY presence)
- prints installed package versions for google-generativeai, Pillow, python-dotenv
- attempts to import and call analyze_image_with_gemini from food_detection_impl
- prints result or exception traceback

Run this in the same virtualenv used by your WSGI process.
"""
import sys
import os
import traceback
from importlib import import_module

# Ensure project root is on sys.path so imports work when script is run from any cwd
proj_root = os.path.dirname(os.path.dirname(__file__))
if proj_root and proj_root not in sys.path:
    sys.path.insert(0, proj_root)


def print_env():
    print('Python executable:', sys.executable)
    print('Python version:', sys.version.replace('\n', ' '))
    print('CWD:', os.getcwd())
    print('GEMINI_API_KEY set:', bool(os.environ.get('GEMINI_API_KEY')))


def pkg_info(name):
    try:
        import pkg_resources
        dist = pkg_resources.get_distribution(name)
        return f'{dist.project_name}=={dist.version}'
    except Exception:
        return f'{name}: not installed'


def main():
    if len(sys.argv) < 2:
        print('Usage: python tools/test_analyze.py /full/path/to/test.jpg')
        sys.exit(2)

    img = sys.argv[1]
    print_env()
    print('Package status:')
    for p in ('google-generativeai', 'Pillow', 'python-dotenv'):
        print(' -', pkg_info(p))

    # Try import and run
    try:
        # Prefer direct module import
        mod = import_module('food_detection_impl')
    except Exception as e:
        print('Failed to import food_detection_impl via package import:', e)
        # try alternative module name (some deployments use 'food_detection')
        try:
            mod = import_module('food_detection')
            print('Imported analysis module from package name "food_detection"')
        except Exception:
            # Fallback: try loading module directly from project file if it exists
            try:
                from importlib import util
                module_path = os.path.join(proj_root, 'food_detection_impl.py')
                if os.path.exists(module_path):
                    print(f'Trying to load module from file: {module_path}')
                    spec = util.spec_from_file_location('food_detection_impl', module_path)
                    if spec and spec.loader:
                        mod = util.module_from_spec(spec)
                        spec.loader.exec_module(mod)
                        print('Loaded food_detection_impl from file')
                    else:
                        raise ImportError('Cannot load spec for food_detection_impl')
                else:
                    # try loading food_detection.py file
                    module_path2 = os.path.join(proj_root, 'food_detection.py')
                    if os.path.exists(module_path2):
                        print(f'Trying to load module from file: {module_path2}')
                        spec = util.spec_from_file_location('food_detection', module_path2)
                        if spec and spec.loader:
                            mod = util.module_from_spec(spec)
                            spec.loader.exec_module(mod)
                            print('Loaded food_detection from file')
                        else:
                            raise ImportError('Cannot load spec for food_detection')
                    else:
                        raise ImportError('No food_detection_impl.py or food_detection.py found')
            except Exception:
                print('Failed to import food detection module:')
                traceback.print_exc()
                sys.exit(1)

    if not hasattr(mod, 'analyze_image_with_gemini'):
        print('Module does not expose analyze_image_with_gemini')
        sys.exit(1)

    if not os.path.exists(img):
        print('Provided image does not exist:', img)
        sys.exit(2)

    try:
        print('\nCalling analyze_image_with_gemini(...)')
        res = mod.analyze_image_with_gemini(img)
        print('Result:', res)
    except Exception as e:
        print('analyze_image_with_gemini raised an exception:')
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
