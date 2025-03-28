import unittest
from unittest.mock import patch, mock_open, MagicMock
import sys
import os

# Assume cli.py is at root and we import main function
import cli

class TestCLIModule(unittest.TestCase):

    @patch("cli.load_config")
    @patch("cli.setup_logger")
    @patch("cli.validate_and_clean")
    @patch("cli.run_descriptive_analysis")
    @patch("cli.run_bootstrap_test")
    @patch("cli.save_results")
    @patch("cli.show_progress")
    @patch("builtins.print")
    def test_main_successful_flow(
            self, mock_print, mock_progress, mock_save, mock_bootstrap,
            mock_analysis, mock_clean, mock_logger, mock_config
    ):
        mock_args = ["cli.py", "input1.csv", "input2.csv", "output.txt"]
        with patch.object(sys, 'argv', mock_args):

            mock_config_obj = MagicMock()
            mock_config_obj.getboolean.return_value = False
            mock_config.return_value = mock_config_obj

            mock_clean.side_effect = lambda f, c, l: f.replace('.csv', '_cleaned.csv')
            mock_bootstrap.return_value = {'p95_1': 1000, 'p95_2': 1200}

            cli.main()

            mock_clean.assert_any_call("input1.csv", mock_config_obj, None)
            mock_clean.assert_any_call("input2.csv", mock_config_obj, None)
            #mock_analysis.assert_any_call("input1_cleaned.csv", mock_config_obj, None)
            #mock_analysis.assert_any_call("input2_cleaned.csv", mock_config_obj, None)
            #mock_save.assert_called_once()
            #mock_progress.assert_any_call("Running Hypothesis Test...", 50)
            #mock_progress.assert_any_call("Complete", 100)

    @patch("cli.load_config")
    @patch("builtins.print")
    def test_main_raises_exception(self, mock_print, mock_config):
        mock_args = ["cli.py", "badfile.csv", "input2.csv"]
        with patch.object(sys, 'argv', mock_args):
            mock_config.side_effect = Exception("Config error")

            with self.assertRaises(SystemExit) as cm:
                cli.main()

            mock_print.assert_any_call("[Error] Config error")
            self.assertEqual(cm.exception.code, 1)

if __name__ == '__main__':
    unittest.main()
