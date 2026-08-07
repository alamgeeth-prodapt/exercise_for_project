from pathlib import Path
import pandas as pd


class BasePreprocessor:
    """Base class containing generic CSV preprocessing operations."""

    def __init__(self, input_path: str | Path, output_path: str | Path):
        self.input_path = Path(input_path)
        self.output_path = Path(output_path)
        self.df = pd.DataFrame()

    def load_data(self):
        self.df = pd.read_csv(self.input_path)
        return self.df

    def save_data(self):
        self.df.to_csv(self.output_path, index=False)

    def normalize_dates(self, columns: list[str]):
        for column in columns:
            self.df[column] = pd.to_datetime(
                self.df[column],
                errors="coerce"
            )

    def clean_numeric_columns(self, columns: list[str]):
        self.df[columns] = self.df[columns].clip(lower=0)

    def summarize(self):
        print(self.df.info())
        print(self.df.describe(include="all"))