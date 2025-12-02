#!/usr/bin/env python3
import argparse
import os
import re
import gzip
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Iterator, Tuple, Pattern

# Configure logging for error and debug messages
logging.basicConfig(level=logging.ERROR, format='[%(levelname)s] %(message)s')

class EventFilter:
    """
    Represents a single event filter as defined in the events configuration file.
    Supports filtering by event type, log level, and message pattern, and can count matches.
    """
    def __init__(self, event_type: str, count: bool = False, level: Optional[str] = None, pattern: Optional[str] = None):
        self.event_type: str = event_type
        self.count: bool = count
        self.level: Optional[str] = level
        self.pattern_str: Optional[str] = pattern
        self.pattern: Optional[Pattern] = re.compile(pattern) if pattern else None

    def matches(self, log: Dict[str, Any]) -> bool:
        """
        Check if a log entry matches this filter.
        """
        if log['event_type'] != self.event_type:
            return False
        if self.level and log['level'] != self.level:
            return False
        if self.pattern and not self.pattern.match(log['message']):
            return False
        return True

    def description(self) -> str:
        """
        Return a human-readable description of this filter for output.
        """
        desc = f"Event: {self.event_type}"
        if self.pattern_str:
            desc += f" pattern [{self.pattern_str}]"
        if self.level:
            desc += f" level [{self.level}]"
        if self.count:
            desc += " count"
        return desc

def parse_events_file(events_file: str) -> List[EventFilter]:
    """
    Parse the events configuration file and return a list of EventFilter objects.
    Ignores comments and blank lines. Handles parsing errors gracefully.
    """
    filters: List[EventFilter] = []
    with open(events_file, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue  # Skip comments and blank lines
            tokens = line.split()
            if not tokens:
                continue
            event_type = tokens[0]
            count = False
            level = None
            pattern = None
            i = 1
            while i < len(tokens):
                if tokens[i] == '--count':
                    count = True
                    i += 1
                elif tokens[i] == '--level':
                    if i + 1 >= len(tokens):
                        logging.warning(f"Missing level after --level in events file at line {line_num}")
                        break
                    level = tokens[i+1]
                    i += 2
                elif tokens[i] == '--pattern':
                    if i + 1 >= len(tokens):
                        logging.warning(f"Missing pattern after --pattern in events file at line {line_num}")
                        break
                    pattern = tokens[i+1]
                    i += 2
                else:
                    logging.warning(f"Unknown token '{tokens[i]}' in events file at line {line_num}")
                    i += 1
            try:
                filters.append(EventFilter(event_type, count, level, pattern))
            except re.error as e:
                logging.error(f"Invalid regex pattern in events file at line {line_num}: {e}")
    return filters

def parse_log_line(line: str) -> Optional[Dict[str, Any]]:
    """
    Parse a single log line into its components.
    Returns a dict with timestamp, level, event_type, message, and raw line.
    Returns None if the line does not match the expected format.
    """
    LOG_LINE_REGEX: Pattern = re.compile(r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\s+(\w+)\s+(\w+)\s+(.*)$')
    m = LOG_LINE_REGEX.match(line)
    if not m:
        logging.debug(f"Skipping malformed log line: {line.strip()}")
        return None
    timestamp, level, event_type, message = m.groups()
    return {
        'timestamp': timestamp,
        'level': level,
        'event_type': event_type,
        'message': message,
        'raw': line.strip()
    }

def log_files_in_dir(log_dir: str) -> Iterator[str]:
    """
    Yield all .log and .log.gz files in the given directory, but only if they are files (not directories).
    """
    for entry in os.listdir(log_dir):
        full_path = os.path.join(log_dir, entry)
        if (entry.endswith('.log') or entry.endswith('.log.gz')) and os.path.isfile(full_path):
            yield full_path

def log_lines_from_file(filepath: str) -> Iterator[str]:
    """
    Yield lines from a log file, supporting both plain text and gzip-compressed files.
    """
    if filepath.endswith('.gz'):
        # Open gzip-compressed log file
        with gzip.open(filepath, 'rt', encoding='utf-8') as f:
            for line in f:
                yield line
    else:
        # Open plain text log file
        with open(filepath, 'rt', encoding='utf-8') as f:
            for line in f:
                yield line

def filter_logs(log_dir: str, from_ts: Optional[str], to_ts: Optional[str]) -> Iterator[Dict[str, Any]]:
    """
    Yield parsed log entries from all log files in the directory, filtered by timestamp range if provided.
    This is a generator and does not load all logs into memory.
    """
    TIMESTAMP_FORMAT: str = '%Y-%m-%dT%H:%M:%S'
    from_dt: Optional[datetime] = datetime.strptime(from_ts, TIMESTAMP_FORMAT) if from_ts else None
    to_dt: Optional[datetime] = datetime.strptime(to_ts, TIMESTAMP_FORMAT) if to_ts else None
    for filepath in log_files_in_dir(log_dir):
        for line in log_lines_from_file(filepath):
            log = parse_log_line(line)
            if not log:
                continue  # Skip lines that don't match the log format
            try:
                log_dt = datetime.strptime(log['timestamp'], TIMESTAMP_FORMAT)
            except ValueError:
                logging.warning(f"Invalid timestamp in log: {log['timestamp']}")
                continue
            if from_dt and log_dt < from_dt:
                continue
            if to_dt and log_dt > to_dt:
                continue
            yield log

def analyze_logs(log_dir: str, event_filters: List[EventFilter], from_ts: Optional[str], to_ts: Optional[str]) -> List[Tuple[EventFilter, List[Dict[str, Any]]]]:
    """
    For each event filter, collect all matching log entries from the log files.
    Returns a list of (EventFilter, [matching logs]) tuples.
    This version processes logs in a streaming fashion for memory efficiency.
    """
    # Prepare a list to hold matches for each filter
    matches_per_filter: List[List[Dict[str, Any]]] = [[] for _ in event_filters]
    # Process logs one by one, checking each filter
    for log in filter_logs(log_dir, from_ts, to_ts):
        for idx, f in enumerate(event_filters):
            if f.matches(log):
                matches_per_filter[idx].append(log)
    # Pair each filter with its matches
    return list(zip(event_filters, matches_per_filter))

def format_results(results: List[Tuple[EventFilter, List[Dict[str, Any]]]]) -> str:
    """
    Format the results for each event filter in the required output format.
    Returns a string suitable for printing or writing to a file.
    """
    output_lines: List[str] = []
    for i, (f, matches) in enumerate(results):
        if i > 0:
            output_lines.append('--------------------')
        desc = f.description()
        if f.count:
            output_lines.append(f"{desc} — matches: {len(matches)} entries")
        else:
            output_lines.append(f"{desc} — matching log lines:")
            for log in matches:
                output_lines.append(log['raw'])
    return '\n'.join(output_lines)

def main() -> None:
    """
    Main entry point: parse arguments, run analysis, and print results.
    Handles errors and provides user-friendly messages.
    """
    parser = argparse.ArgumentParser(description='Log Analyzer: Extract and report structured event data from logs.')
    parser.add_argument('--log-dir', required=True, help='Path to folder containing log files (.log, .log.gz)')
    parser.add_argument('--events-file', required=True, help='Path to events configuration file')
    parser.add_argument('--from', dest='from_ts', help='Filter logs from this timestamp (inclusive), format: YYYY-MM-DDTHH:MM:SS')
    parser.add_argument('--to', dest='to_ts', help='Filter logs up to this timestamp (inclusive), format: YYYY-MM-DDTHH:MM:SS')
    args = parser.parse_args()

    # Validate input paths
    if not os.path.isdir(args.log_dir):
        parser.error(f"Log directory does not exist: {args.log_dir}")
    if not os.path.isfile(args.events_file):
        parser.error(f"Events file does not exist: {args.events_file}")
    try:
        event_filters = parse_events_file(args.events_file)
    except Exception as e:
        logging.error(f"Failed to parse events file: {e}")
        parser.error(f"Failed to parse events file: {e}")
    try:
        results = analyze_logs(args.log_dir, event_filters, args.from_ts, args.to_ts)
    except Exception as e:
        logging.error(f"Failed to analyze logs: {e}")
        parser.error(f"Failed to analyze logs: {e}")
    print(format_results(results))

# Only run the CLI if this script is executed directly
if __name__ == '__main__':
    main()