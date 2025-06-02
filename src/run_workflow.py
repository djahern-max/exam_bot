#!/usr/bin/env python3
"""
Exam Bot Workflow Helper
Guides you through the complete exam bot process
"""

import os
import sys
import subprocess
import glob
from datetime import datetime


def show_banner():
    print("🎯 EXAM BOT WORKFLOW HELPER")
    print("=" * 40)
    print("This script guides you through the complete process:")
    print("1. Data Collection (A, B, C, D option testing)")
    print("2. Analysis (Build answer key)")
    print("3. Final Submission")
    print()


def check_files():
    """Check if required files exist"""
    required_files = [
        "persistent_exam_bot.py",
        "exam_analyzer.py",
        "exam_automation_updated.py",
    ]

    missing = []
    for file in required_files:
        if not os.path.exists(file):
            missing.append(file)

    if missing:
        print(f"❌ Missing required files: {', '.join(missing)}")
        return False

    print("✅ All required files found")
    return True


def check_results_status():
    """Check what option tests have been completed"""
    if not os.path.exists("exam_results"):
        print("📁 No exam_results directory found")
        return {"completed": [], "missing": ["A", "B", "C", "D"]}

    options = ["A", "B", "C", "D"]
    completed = []

    for option in options:
        files = glob.glob(f"exam_results/option_{option}_*.json")
        if files:
            completed.append(option)

    missing = [opt for opt in options if opt not in completed]

    print(f"📊 Completed tests: {', '.join(completed) if completed else 'None'}")
    print(f"📋 Missing tests: {', '.join(missing) if missing else 'None'}")

    return {"completed": completed, "missing": missing}


def run_option_test(option_index):
    """Run option test"""
    option_name = ["A", "B", "C", "D"][option_index]
    print(f"\n🧪 Starting Option {option_name} Test")
    print("=" * 30)

    try:
        # Run the persistent exam bot with proper input handling
        process = subprocess.Popen(
            [sys.executable, "persistent_exam_bot.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )

        # Send the option index
        process.stdin.write(f"{option_index}\n")
        process.stdin.flush()

        # Read output in real-time
        while True:
            output = process.stdout.readline()
            if output == "" and process.poll() is not None:
                break
            if output:
                print(output.strip())

        # Wait for process to complete
        return_code = process.wait()

        if return_code == 0:
            print(f"✅ Option {option_name} test completed successfully")
            return True
        else:
            print(f"❌ Option {option_name} test failed")
            return False

    except Exception as e:
        print(f"❌ Error running option {option_name} test: {e}")
        return False


def run_analysis():
    """Run the analysis"""
    print(f"\n🔍 Starting Analysis")
    print("=" * 20)

    try:
        result = subprocess.run(
            [sys.executable, "exam_analyzer.py"],
            input="\n",
            text=True,
            capture_output=False,
        )

        if result.returncode == 0:
            print(f"✅ Analysis completed successfully")
            return True
        else:
            print(f"❌ Analysis failed")
            return False

    except Exception as e:
        print(f"❌ Error running analysis: {e}")
        return False


def show_menu():
    """Show main menu"""
    print("\n📋 MAIN MENU")
    print("=" * 15)
    print("1. Run Option A Test")
    print("2. Run Option B Test")
    print("3. Run Option C Test")
    print("4. Run Option D Test")
    print("5. Run Analysis (after all options)")
    print("6. Check Status")
    print("7. Quick Start (run next missing test)")
    print("0. Exit")
    print()


def quick_start(status):
    """Run the next missing test automatically"""
    missing = status["missing"]

    if not missing:
        print("🎉 All option tests completed! Running analysis...")
        return run_analysis()

    next_option = missing[0]
    option_index = ["A", "B", "C", "D"].index(next_option)

    print(f"🚀 Quick Start: Running next missing test (Option {next_option})")
    confirm = input(f"Continue with Option {next_option}? (y/N): ").lower()

    if confirm == "y":
        return run_option_test(option_index)
    else:
        print("❌ Cancelled")
        return False


def main():
    """Main workflow"""
    show_banner()

    if not check_files():
        return

    while True:
        status = check_results_status()
        show_menu()

        try:
            choice = input("Enter your choice (0-7): ").strip()

            if choice == "0":
                print("👋 Goodbye!")
                break
            elif choice == "1":
                run_option_test(0)  # A
            elif choice == "2":
                run_option_test(1)  # B
            elif choice == "3":
                run_option_test(2)  # C
            elif choice == "4":
                run_option_test(3)  # D
            elif choice == "5":
                if len(status["completed"]) < 4:
                    print(f"⚠️ Only {len(status['completed'])}/4 option tests completed")
                    print("Complete all option tests before running analysis")
                else:
                    run_analysis()
            elif choice == "6":
                # Status already shown above
                pass
            elif choice == "7":
                quick_start(status)
            else:
                print("❌ Invalid choice")

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
