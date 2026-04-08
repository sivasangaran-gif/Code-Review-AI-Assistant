import subprocess
import sys
import tempfile
import os

def test_run():
    code = 'print("hello world")'
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode='w', encoding='utf-8') as tmp:
        tmp.write(code)
        tmp_path = tmp.name
    
    try:
        print("Running", sys.executable, tmp_path)
        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=2
        )
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
    except Exception as e:
        print("Error:", e)
    finally:
        os.remove(tmp_path)

if __name__ == "__main__":
    test_run()
