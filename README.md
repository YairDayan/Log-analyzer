# Log Analyzer Home Assignment

## Overview

A command-line tool to analyze log files and extract/report structured event data, as specified in the assignment.

## Features

- Supports `.log` and `.log.gz` files in any user-specified directory
- Filters logs by optional timestamp range (`--from`, `--to`)
- Event configuration file supports multiple independent filters per event type, with `--count`, `--level`, and `--pattern` options
- Each filter is applied independently and output is separated for clarity
- Outputs either counts or matching log lines, as specified per filter
- Good CLI UX: `--help`, clear error messages, and input validation
- Modular, readable, and maintainable code (no global state, clear function boundaries)
- Performance: processes files line by line using generators, uses compiled regexes
- Extensible: easy to add new filter types or output formats
- Robust error handling for malformed input and files

## Usage

```bash
python3 log_analyzer.py --log-dir <log_folder> --events-file <events.txt> [--from <timestamp>] [--to <timestamp>]
```

**Example:**

```bash

python3 log_analyzer.py --log-dir logs --events-file events_sample.txt --from 2025-06-01T14:00:00 --to 2025-06-01T15:00:00
```

- `<log_folder>`: Path to the directory containing your `.log` and/or `.log.gz` files (can be any directory).
- `<events.txt>`: Path to the events configuration file.

## Input Formats

### Log File  

Each line:  
`<TIMESTAMP> <LEVEL> <EVENT_TYPE> <MESSAGE>`

Example:  
2025-06-01T14:03:05 INFO TELEMETRY Iteration time: 1793.845 sec

### Events File

Each line: `EVENT_TYPE [--count] [--level LEVEL] [--pattern REGEX]`

Example:

```bash
DEVICE --level WARNING --count
GNMI --level ERROR
TELEMETRY --count --pattern ^Iteration time:\s\d+\.\d+\ssec$
```

## Output

- For each filter, prints either a count or matching log lines, as specified in the events file.
- Each filter's output is separated by a line of dashes (`--------------------`) for readability.

**Example Output:**

```markdown
--------------------
Event: TELEMETRY pattern [^Iteration time:\s\d+\.\d+\ssec$] count — matches: 1 entries
--------------------
Event: DEVICE level [WARNING] count — matches: 1 entries
--------------------
Event: GNMI level [ERROR] — matching log lines:
2025-06-01T14:10:00 ERROR GNMI unresponsive telemetry at endpoint http://SWX1:9001/ low_freq_debug

## Design Considerations

- **Modularity:** Code is split into functions/classes for parsing, filtering, and output.
- **Performance:** Uses generators and compiled regexes, processes files line by line.
- **Extensibility:** Easy to add new filter types or output formats.
- **Error Handling:** CLI provides clear error messages for missing/invalid input.

## Test Inputs

- `sample.log` and `events_sample.txt` are provided for testing.

## Requirements

- Python 3.7+

## Install dependencies

No external dependencies required (uses only Python standard library).

## Run tests

```bash
python3 -m unittest discover tests
