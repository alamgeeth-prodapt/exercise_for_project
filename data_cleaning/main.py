from telecom_preprocessor import TelecomChurnPreprocessor


if __name__ == "__main__":
    processor = TelecomChurnPreprocessor()
    processor.run(show_plot=True)