"""
GitHub Filler - Fake Commit Generator for GitHub

Copyright (C) 2024-2024 Liam Arguedas

This file is part of GitHub Filler, a free CLI tool based on the original Commitify 
designed to generate fake commits for GitHub repositories.

GitHub Filler is distributed under the terms of the GNU General Public License (GPL),
either version 3 of the License, or any later version.

GitHub Filler is provided "as is", without warranty of any kind, express or implied,
including but not limited to the warranties of merchantability, fitness for a
particular purpose, and noninfringement. See the GNU General Public License for
more details.

You should have received a copy of the GNU General Public License along with
GitHub Filler. If not, see <https://www.gnu.org/licenses/>.
"""

from pathlib import Path
import random
import os
import json

WORDS = "random_words.txt"
FILE_TXT = "file_txt.txt"
CONFIG = "config.json"


class FileBuilder:

    def __init__(self):
        self.filepath = Path(__file__).parents[0]
        self.txt_path = self.filepath / "txt"
        self.words_file = self.txt_path / WORDS
        self.file_txt = self.txt_path / FILE_TXT
        self.words = self.read_text(self.words_file)
        self.file_text = self.read_text(self.file_txt)
        self.filename = None
        self.filetype = self.read_filetype()

    @staticmethod
    def path_exists(dirname):
        """todo"""
        return os.path.exists(dirname)

    @staticmethod
    def generate_extra_file(file, dirname):
        """todo"""
        _splited_file = file.split(".")
        same_name_files = [
            directory_file
            for directory_file in os.listdir(dirname)
            if _splited_file[0] in directory_file
        ]
        return f"{_splited_file[0]}{len(same_name_files) + 1}.{_splited_file[1]}"

    def write_new_file(self, filename):
        """todo"""
        with open(filename, "w", encoding="utf-8") as file:
            file.write(self.generate_realistic_content(filename))

    def read_filetype(self):
        """todo"""
        with open(self.filepath / "cfg" / CONFIG, "r", encoding="utf-8") as file:
            file_type = json.load(file)["file"]
            return file_type

    def generate_realistic_content(self, filename):
        """Create a more realistic data-science file based on the target extension."""
        suffix = Path(filename).suffix.lower()
        stem = Path(filename).stem

        if suffix == ".ipynb":
            return json.dumps(
                {
                    "cells": [
                        {
                            "cell_type": "markdown",
                            "metadata": {},
                            "source": [
                                "# Exploratory Data Analysis\n",
                                "This notebook profiles the dataset and summarizes key patterns.\n",
                            ],
                        },
                        {
                            "cell_type": "code",
                            "execution_count": None,
                            "metadata": {},
                            "outputs": [],
                            "source": [
                                "import pandas as pd\n",
                                "import seaborn as sns\n",
                                "import matplotlib.pyplot as plt\n",
                                "df = pd.read_csv('data/raw.csv')\n",
                                "display(df.head())\n",
                            ],
                        },
                    ],
                    "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
                    "nbformat": 4,
                    "nbformat_minor": 5,
                },
                indent=1,
            )

        if stem.lower().startswith("train") or "model" in stem.lower():
            return """import pandas as pd\nimport numpy as np\nfrom sklearn.model_selection import train_test_split\nfrom sklearn.pipeline import Pipeline\nfrom sklearn.compose import ColumnTransformer\nfrom sklearn.impute import SimpleImputer\nfrom sklearn.preprocessing import StandardScaler\nfrom sklearn.linear_model import LogisticRegression\n\n\ndef train_model(df: pd.DataFrame):\n    X = df.drop(columns=['target'])\n    y = df['target']\n    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)\n\n    numeric_features = X.select_dtypes(include=['number']).columns\n    numeric_transformer = Pipeline(steps=[\n        ('imputer', SimpleImputer(strategy='median')),\n        ('scaler', StandardScaler())\n    ])\n\n    preprocessor = ColumnTransformer(transformers=[\n        ('num', numeric_transformer, numeric_features)\n    ])\n\n    model = Pipeline(steps=[\n        ('preprocessor', preprocessor),\n        ('classifier', LogisticRegression(max_iter=1000))\n    ])\n    model.fit(X_train, y_train)\n    return model\n"""

        return """import pandas as pd\nimport numpy as np\nfrom pathlib import Path\n\n\ndef load_dataset(path: str) -> pd.DataFrame:\n    return pd.read_csv(path)\n\n\ndef clean_data(df: pd.DataFrame) -> pd.DataFrame:\n    cleaned = df.copy()\n    cleaned = cleaned.fillna(cleaned.median(numeric_only=True))\n    return cleaned\n\n\ndef summarize(df: pd.DataFrame) -> dict:\n    return {\n        \"rows\": int(df.shape[0]),\n        \"columns\": int(df.shape[1]),\n        \"missing_values\": int(df.isna().sum().sum()),\n    }\n\n\nif __name__ == \"__main__\":\n    data_path = Path(\"data/raw.csv\")\n    df = load_dataset(data_path)\n    cleaned_df = clean_data(df)\n    print(summarize(cleaned_df))\n"""

    def file_in_path(self, dirname):
        """todo"""
        return os.path.exists(f"{dirname}/{self.filename}")

    def generate_name(self):
        """todo"""
        templates = [
            "eda",
            "train",
            "model",
            "preprocess",
            "feature_engineering",
            "analysis",
            "pipeline",
            "explore",
        ]
        stem = random.choice(templates)
        suffix = self.filetype.lower()

        if suffix == "ipynb":
            self.filename = f"{stem}.ipynb"
        elif suffix == "py":
            self.filename = f"{stem}_{random.choice(self.words)}.py"
        else:
            self.filename = f"{stem}_{random.choice(self.words)}.{suffix}"
        return self.filename

    def read_text(self, file):
        """todo"""
        if self.path_exists(file):
            with open(file, "r", encoding="utf-8") as loaded_file:
                return [line.rstrip("\n") for line in loaded_file.readlines()]
        return ["file"]

    def create_file(self, dirname):
        """todo"""
        if self.path_exists(dirname):
            file = self.generate_name()
            if self.file_in_path(dirname):
                file = self.generate_extra_file(file, dirname)
            self.write_new_file(dirname / file)
