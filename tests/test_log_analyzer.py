import unittest
import subprocess

class TestLogAnalyzer(unittest.TestCase):
    def test_sample_log_and_events(self):
        result = subprocess.run([
            'python3', 'log_analyzer.py',
            '--log-dir', 'logs',
            '--events-file', 'events_sample.txt',
            '--from', '2025-06-01T14:00:00',
            '--to',   '2025-06-01T15:00:00'
        ], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        out = result.stdout

        # TELEMETRY
        self.assertIn('Event: TELEMETRY pattern [^Iteration] count', out)
        self.assertIn('Event: TELEMETRY pattern [^Iteration] level [INFO] — matching log lines:', out)

        # DEVICE - counts and patterns
        self.assertIn('Event: DEVICE level [WARNING] count', out)
        self.assertIn('Event: DEVICE pattern [^detected] level [WARNING] — matching log lines:', out)
        self.assertIn('2025-06-01T14:05:22 WARNING DEVICE detected high temperature of device', out)
        self.assertIn('Event: DEVICE pattern [^disk] level [WARNING] — matching log lines:', out)
        self.assertIn('2025-06-01T14:50:28 WARNING DEVICE disk space low: 92% full', out)
        self.assertIn('Event: DEVICE pattern [^low] level [WARNING] — matching log lines:', out)
        self.assertIn('2025-06-01T14:20:45 WARNING DEVICE low memory warning: 85% usage', out)

        # DEVICE patterns that should NOT appear (no matching logs)
        self.assertIn('Event: DEVICE pattern [^network] level [WARNING] — matching log lines:', out)
        self.assertIn('Event: DEVICE pattern [^CPU] level [WARNING] — matching log lines:', out)
        self.assertIn('Event: DEVICE pattern [^fan] level [WARNING] — matching log lines:', out)
        self.assertIn('Event: DEVICE pattern [^power] level [WARNING] — matching log lines:', out)
        self.assertIn('Event: DEVICE pattern [^temperature] level [WARNING] — matching log lines:', out)
        self.assertIn('Event: DEVICE pattern [^backup] level [WARNING] — matching log lines:', out)

        # GNMI - level and multiple patterns
        self.assertIn('Event: GNMI level [ERROR] — matching log lines:', out)
        self.assertIn('2025-06-01T14:10:00 ERROR GNMI unresponsive telemetry at endpoint', out)
        self.assertIn('Event: GNMI pattern [^unresponsive] level [ERROR] — matching log lines:', out)
        self.assertIn('Event: GNMI pattern [^connection] level [ERROR] — matching log lines:', out)
        self.assertIn('2025-06-01T14:25:10 ERROR GNMI connection timeout at endpoint', out)
        self.assertIn('Event: GNMI pattern [^authentication] level [ERROR] — matching log lines:', out)
        self.assertIn('2025-06-01T14:55:45 ERROR GNMI authentication failed for endpoint', out)
        self.assertIn('Event: GNMI pattern [^retry] level [WARNING] — matching log lines:', out)
        self.assertIn('2025-06-01T14:40:30 WARNING GNMI retry attempt 3/5 for endpoint detection', out)

        # GNMI patterns that should NOT appear
        self.assertIn('Event: GNMI pattern [^data] level [ERROR] — matching log lines:', out)
        self.assertIn('Event: GNMI pattern [^endpoint] level [ERROR] — matching log lines:', out)
        self.assertIn('Event: GNMI pattern [^SSL] level [ERROR] — matching log lines:', out)
        self.assertIn('Event: GNMI pattern [^malformed] level [ERROR] — matching log lines:', out)
        self.assertIn('Event: GNMI pattern [^network] level [ERROR] — matching log lines:', out)
        self.assertIn('Event: GNMI pattern [^rate] level [ERROR] — matching log lines:', out)

if __name__ == '__main__':
    unittest.main()