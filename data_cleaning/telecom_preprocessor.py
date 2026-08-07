from pathlib import Path

import matplotlib.pyplot as plt


from base_preprocessor import BasePreprocessor
from validators import validate_pincode, convert_boolean



class TelecomChurnPreprocessor(BasePreprocessor):

    def __init__(
        self,
        input_path=None,
        output_path=None
    ):
        base = Path(__file__).resolve().parent

        super().__init__(
            input_path or base / "telecom_churn.csv",
            output_path or "../data/telecom_churn_clean.csv"
        )

        self.invalid_pincodes = None

    def validate_pincodes(self):
        self.invalid_pincodes = validate_pincode(self.df)

    def convert_churn(self):
        convert_boolean(self.df, "churn")

    def plot_data_usage(self, show=False):

        self.df["data_used"].hist(bins=30)

        if show:
            plt.show()

    def telecom_summary(self):

        print(self.invalid_pincodes)

        print(
            (self.df["data_used"] == 0).sum()
        )

    def run(self, show_plot=False):

        self.load_data()

        self.clean_numeric_columns([
            "data_used",
            "calls_made",
            "sms_sent"
        ])

        self.normalize_dates([
            "date_of_registration"
        ])

        self.validate_pincodes()

        self.convert_churn()

        self.summarize()

        self.telecom_summary()

        self.plot_data_usage(show_plot)

        self.save_data()

        return self.df