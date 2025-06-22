#!/usr/bin/env python3
"""
Pulse Activity Tracker - Main Entry Point
Intelligent work-life balance automation system

Usage: 
  python main.py monitor --duration 60
  python main.py dashboard --period week
  python main.py todo list
  python main.py todo generate
  python main.py report daily --format json
  python main.py settings show
  python main.py backup create
  python main.py status
"""

import sys
import os
from pathlib import Path

# Add the pulse package to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from pulse.cli import PulseCLI


def main():
    """Main entry point for Pulse Activity Tracker"""
    # Show banner for direct invocation
    if len(sys.argv) <= 1:
        print("🚀 Pulse Activity Tracker")
        print("Intelligent Work-Life Balance Automation")
        print("=" * 45)
        print()
        print("Available commands:")
        print("  monitor     - Start activity monitoring")
        print("  dashboard   - Show productivity dashboard") 
        print("  todo        - Manage todos and generate suggestions")
        print("  report      - Generate productivity reports")
        print("  settings    - Manage configuration")
        print("  backup      - Backup and restore data")
        print("  status      - Show system status")
        print()
        print("For detailed help: python main.py <command> --help")
        print("Quick start: python main.py monitor --duration 5")
        return
    
    # Initialize and run CLI
    cli = PulseCLI()
    cli.run(sys.argv[1:])


if __name__ == "__main__":
    main()