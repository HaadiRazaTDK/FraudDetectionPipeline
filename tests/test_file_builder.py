import tempfile
import unittest
from pathlib import Path

from src.file_builder import FileBuilder


class FileBuilderTests(unittest.TestCase):
    def test_create_file_writes_realistic_data_science_content(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            builder = FileBuilder()
            builder.filetype = "py"
            builder.create_file(Path(temp_dir))

            created_files = list(Path(temp_dir).iterdir())
            self.assertEqual(len(created_files), 1)

            content = created_files[0].read_text(encoding="utf-8")
            self.assertTrue("import pandas as pd" in content or "import numpy as np" in content)
            self.assertIn("def ", content)


if __name__ == "__main__":
    unittest.main()
