#!/usr/bin/env python3
"""
Persistent Exam Bot - Saves results after each option test
Tests one option at a time and saves results to JSON files
"""

import sys
import os
import time
import json
import re
from datetime import datetime
from typing import Dict, Optional
from selenium.webdriver.common.by import By

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from exam_automation_updated import ExamAutomation


def show_progress(current, total, message="Working"):
    """Show a clean progress indicator"""
    percent = int((current / total) * 100) if total > 0 else 0
    bar_length = 30
    filled_length = int(bar_length * current // total) if total > 0 else 0
    bar = "█" * filled_length + "░" * (bar_length - filled_length)
    print(f"\r{message}: [{bar}] {percent}% ({current}/{total})", end="", flush=True)


class PersistentExamBot:
    def __init__(self):
        self.automation = None
        self.total_questions = 0
        self.options = ["A", "B", "C", "D"]
        self.results_dir = "exam_results"
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Create results directory
        os.makedirs(self.results_dir, exist_ok=True)

    def start(self):
        """Initialize the automation"""
        print("🎯 Persistent Exam Bot - Option by Option Testing")
        print("=" * 55)
        print(f"📁 Results will be saved to: {self.results_dir}/")
        print(f"🆔 Session ID: {self.session_id}")

        try:
            self.automation = ExamAutomation(headless=False)

            if not self.automation.start_browser():
                print("❌ Failed to start browser")
                return False

            return True
        except Exception as e:
            print(f"❌ Error starting: {e}")
            return False

    def login_and_navigate(self):
        """Handle login and navigation to exam"""
        print("\n🔗 Going to MasterCPE...")
        self.automation.navigate_to_exam("https://mastercpe.com")

        print("👤 Please log in and navigate to your exam")
        try:
            input("Press Enter when you're on the exam page...")
        except EOFError:
            print("⚠️ Running in automated mode - assuming you're ready")
            time.sleep(2)  # Give a moment for manual navigation

        current_url = self.automation.driver.current_url
        print(f"📄 Using current page: {current_url}")

        # Save session info
        session_info = {
            "session_id": self.session_id,
            "exam_url": current_url,
            "start_time": datetime.now().isoformat(),
            "total_questions": None,  # Will be filled later
        }

        with open(f"{self.results_dir}/session_{self.session_id}.json", "w") as f:
            json.dump(session_info, f, indent=2)

        return True

    def find_and_analyze_questions(self):
        """Find questions and set up tracking"""
        print("\n🔍 Finding questions...")
        questions = self.automation.find_questions()

        if not questions:
            print("❌ No questions found")
            return False

        self.total_questions = len(questions)
        print(f"📝 Found {self.total_questions} questions")

        # Update session info with question count
        session_file = f"{self.results_dir}/session_{self.session_id}.json"
        with open(session_file, "r") as f:
            session_info = json.load(f)

        session_info["total_questions"] = self.total_questions

        with open(session_file, "w") as f:
            json.dump(session_info, f, indent=2)

        return True

    def test_single_option(self, option_index: int) -> bool:
        """
        Test a single option (A=0, B=1, C=2, D=3) for ALL questions
        Save results to JSON file
        """
        option_name = self.options[option_index]
        print(f"\n🧪 TESTING OPTION {option_name} FOR ALL QUESTIONS")
        print("=" * 50)

        # Select the same option for all questions
        print(f"📝 Selecting {option_name} for all {self.total_questions} questions...")
        start_time = time.time()

        for q_num in range(1, self.total_questions + 1):
            show_progress(q_num, self.total_questions, f"Selecting {option_name}")
            self.automation.select_answer(q_num, option_index)
            time.sleep(0.02)

        print(f"\n✅ All {option_name} answers selected!")
        print(f"📤 Submitting exam...")

        # Submit the exam
        success = self.automation.submit_exam()
        if not success:
            print("❌ Failed to submit exam")
            return False

        print("⏳ Waiting for results...")
        time.sleep(5)

        # Get score
        score = self.automation.get_score()
        if score is not None:
            print(f"🎯 Score with all {option_name}'s: {score}%")

        # Parse detailed results
        results = self.parse_detailed_results()

        if not results:
            print(f"❌ Failed to parse results for option {option_name}")
            return False

        # Save results to file
        result_data = {
            "session_id": self.session_id,
            "option": option_name,
            "option_index": option_index,
            "score": score,
            "total_questions": self.total_questions,
            "timestamp": datetime.now().isoformat(),
            "results": results,  # {question_number: is_correct}
            "test_duration_seconds": time.time() - start_time,
        }

        filename = f"{self.results_dir}/option_{option_name}_{self.session_id}.json"
        with open(filename, "w") as f:
            json.dump(result_data, f, indent=2)

        # Show summary
        correct_count = sum(1 for is_correct in results.values() if is_correct)
        print(
            f"📊 Option {option_name}: {correct_count}/{len(results)} questions correct"
        )
        print(f"💾 Results saved to: {filename}")

        elapsed = time.time() - start_time
        print(f"⏱️ {option_name} test completed in {elapsed:.1f} seconds")

        return True

    def parse_detailed_results(self) -> Dict[int, bool]:
        """
        Fast result parsing by looking for Correct/Incorrect labels and green/red indicators
        """
        print("⚡ Fast result parsing using visual indicators...")
        start_time = time.time()

        try:
            results = {}

            # Method 1: Direct search for "Correct" and "Incorrect" text elements
            print("🔍 Method 1: Searching for Correct/Incorrect text...")

            from selenium.webdriver.common.by import By

            # Find all elements containing "Correct"
            correct_elements = self.automation.driver.find_elements(
                By.XPATH, "//*[contains(text(), 'Correct')]"
            )

            # Find all elements containing "Incorrect"
            incorrect_elements = self.automation.driver.find_elements(
                By.XPATH, "//*[contains(text(), 'Incorrect')]"
            )

            print(f"🔍 Found {len(correct_elements)} 'Correct' elements")
            print(f"🔍 Found {len(incorrect_elements)} 'Incorrect' elements")

            # Process correct elements
            for element in correct_elements:
                q_num = self.find_question_number_near_element(element)
                if q_num and 1 <= q_num <= self.total_questions:
                    results[q_num] = True
                    print(f"✅ Q{q_num}: Correct")

            # Process incorrect elements
            for element in incorrect_elements:
                q_num = self.find_question_number_near_element(element)
                if (
                    q_num
                    and 1 <= q_num <= self.total_questions
                    and q_num not in results
                ):
                    results[q_num] = False
                    print(f"❌ Q{q_num}: Incorrect")

            # Method 2: If we didn't find enough, look for green/red colored elements
            if len(results) < self.total_questions * 0.8:
                print(
                    f"🔍 Method 2: Only found {len(results)}/{self.total_questions}, trying color-based search..."
                )

                # Look for green elements (likely correct answers)
                green_selectors = [
                    "*[style*='color: green']",
                    "*[style*='color:#008000']",
                    "*[style*='color: #008000']",
                    "*[style*='background-color: green']",
                    ".correct",
                    ".success",
                    "*[class*='correct']",
                    "*[class*='success']",
                ]

                for selector in green_selectors:
                    try:
                        elements = self.automation.driver.find_elements(
                            By.CSS_SELECTOR, selector
                        )
                        for element in elements:
                            q_num = self.find_question_number_near_element(element)
                            if (
                                q_num
                                and 1 <= q_num <= self.total_questions
                                and q_num not in results
                            ):
                                results[q_num] = True
                                print(f"✅ Q{q_num}: Correct (green indicator)")
                    except:
                        continue

                # Look for red elements (likely incorrect answers)
                red_selectors = [
                    "*[style*='color: red']",
                    "*[style*='color:#ff0000']",
                    "*[style*='color: #ff0000']",
                    "*[style*='background-color: red']",
                    ".incorrect",
                    ".error",
                    "*[class*='incorrect']",
                    "*[class*='error']",
                ]

                for selector in red_selectors:
                    try:
                        elements = self.automation.driver.find_elements(
                            By.CSS_SELECTOR, selector
                        )
                        for element in elements:
                            q_num = self.find_question_number_near_element(element)
                            if (
                                q_num
                                and 1 <= q_num <= self.total_questions
                                and q_num not in results
                            ):
                                results[q_num] = False
                                print(f"❌ Q{q_num}: Incorrect (red indicator)")
                    except:
                        continue

            # Method 3: Fallback to page source analysis
            if len(results) < self.total_questions * 0.5:
                print(
                    f"🔍 Method 3: Only found {len(results)}/{self.total_questions}, trying page source..."
                )

                page_source = self.automation.driver.page_source

                # Look for question patterns in page source
                for q_num in range(1, self.total_questions + 1):
                    if q_num in results:
                        continue

                    # Look for "Question X" followed by "Correct" or "Incorrect"
                    pattern = rf"Question\s+{q_num}[^0-9]*?(Correct|Incorrect)"
                    match = re.search(pattern, page_source, re.IGNORECASE | re.DOTALL)

                    if match:
                        is_correct = match.group(1).lower() == "correct"
                        results[q_num] = is_correct
                        status = "Correct" if is_correct else "Incorrect"
                        print(
                            f"{'✅' if is_correct else '❌'} Q{q_num}: {status} (page source)"
                        )

            # Fill any remaining missing results
            missing_count = 0
            for q_num in range(1, self.total_questions + 1):
                if q_num not in results:
                    results[q_num] = False
                    missing_count += 1

            if missing_count > 0:
                print(
                    f"❓ {missing_count} questions had no results found, assumed incorrect"
                )

            elapsed = time.time() - start_time
            correct_count = sum(1 for is_correct in results.values() if is_correct)
            print(
                f"⚡ Parsing completed in {elapsed:.2f}s - {correct_count}/{self.total_questions} correct"
            )

            return results

        except Exception as e:
            print(f"❌ Fast parsing failed: {e}")
            return {q_num: False for q_num in range(1, self.total_questions + 1)}

    def find_question_number_near_element(self, element) -> Optional[int]:
        """
        Find question number near a given element by looking at surrounding text
        """
        try:
            # Check the element itself
            text = element.text
            if text:
                q_match = re.search(r"Question\s+(\d+)", text, re.IGNORECASE)
                if q_match:
                    q_num = int(q_match.group(1))
                    if 1 <= q_num <= self.total_questions:
                        return q_num

            # Check parent elements (go up the DOM tree)
            current = element
            for _ in range(5):  # Check up to 5 levels up
                try:
                    current = current.find_element(By.XPATH, "..")
                    parent_text = current.text
                    if parent_text:
                        # Look for "Question X" pattern
                        q_match = re.search(
                            r"Question\s+(\d+)", parent_text, re.IGNORECASE
                        )
                        if q_match:
                            q_num = int(q_match.group(1))
                            if 1 <= q_num <= self.total_questions:
                                return q_num
                except:
                    break

            # Check nearby elements
            try:
                # Check previous siblings
                for i in range(1, 4):
                    try:
                        sibling = element.find_element(
                            By.XPATH, f"preceding-sibling::*[{i}]"
                        )
                        sibling_text = sibling.text
                        if sibling_text:
                            q_match = re.search(
                                r"Question\s+(\d+)", sibling_text, re.IGNORECASE
                            )
                            if q_match:
                                q_num = int(q_match.group(1))
                                if 1 <= q_num <= self.total_questions:
                                    return q_num
                    except:
                        continue
            except:
                pass

            return None

        except Exception:
            return None

    def extract_question_number_from_element(self, element) -> Optional[int]:
        """Extract question number from an element's context"""
        try:
            # Get text from element and nearby elements
            texts_to_check = []

            # Current element
            if element.text:
                texts_to_check.append(element.text)

            # Parent elements
            current = element
            for _ in range(3):
                try:
                    current = current.find_element(By.XPATH, "..")
                    if current.text:
                        texts_to_check.append(current.text)
                except:
                    break

            # Previous and next siblings
            try:
                prev_sibling = element.find_element(By.XPATH, "preceding-sibling::*[1]")
                if prev_sibling.text:
                    texts_to_check.append(prev_sibling.text)
            except:
                pass

            try:
                next_sibling = element.find_element(By.XPATH, "following-sibling::*[1]")
                if next_sibling.text:
                    texts_to_check.append(next_sibling.text)
            except:
                pass

            # Look for question numbers in all collected text
            for text in texts_to_check:
                patterns = [
                    r"Question\s*(\d+)",
                    r"Q\s*(\d+)",
                    r"^(\d+)\.",
                    r"(\d+)\s*(?:Correct|Incorrect)",
                ]

                for pattern in patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        q_num = int(match.group(1))
                        if 1 <= q_num <= self.total_questions:
                            return q_num

            return None

        except Exception:
            return None

    def click_retake(self) -> bool:
        """Click the retake button"""
        print("\n🔄 Looking for retake button...")

        try:
            retake_selectors = [
                "//button[contains(text(), 'Retake Exam')]",
                "//button[contains(text(), 'Retake')]",
                "//a[contains(text(), 'Retake Exam')]",
                "//input[@value='Retake Exam']",
            ]

            for selector in retake_selectors:
                try:
                    button = self.automation.driver.find_element(By.XPATH, selector)

                    if button.is_displayed() and button.is_enabled():
                        self.automation.driver.execute_script(
                            "arguments[0].scrollIntoView(true);", button
                        )
                        time.sleep(1)
                        self.automation.driver.execute_script(
                            "arguments[0].click();", button
                        )
                        time.sleep(5)
                        print("✅ Clicked retake button")
                        return True

                except Exception:
                    continue

            print("❌ No retake button found")
            return False

        except Exception as e:
            print(f"❌ Error clicking retake: {e}")
            return False

    def run_option_test(self, option_index: int):
        """Run test for a specific option"""
        try:
            if not self.start():
                return False

            if not self.login_and_navigate():
                return False

            if not self.find_and_analyze_questions():
                return False

            option_name = self.options[option_index]
            print(
                f"\n🎯 Ready to test option {option_name} for all {self.total_questions} questions"
            )

            try:
                confirm = (
                    input(f"Type 'GO' to test option {option_name}: ").strip().upper()
                )
                if confirm != "GO":
                    print("❌ Cancelled")
                    return False
            except EOFError:
                print(
                    f"⚠️ Running in automated mode - proceeding with option {option_name}"
                )
                confirm = "GO"

            success = self.test_single_option(option_index)

            if success:
                print(f"\n🎉 Option {option_name} test completed successfully!")
                print(f"📁 Results saved in {self.results_dir}/")

                # Check if we should continue to next option
                if option_index < 3:  # Not the last option
                    print(
                        f"\n🔄 Ready for next option ({self.options[option_index + 1]})?"
                    )
                    print("The retake button should be visible on the results page.")
                    try:
                        input(
                            "Press Enter to continue to retake (or Ctrl+C to stop)..."
                        )
                    except EOFError:
                        print("⚠️ Automated mode - proceeding to retake")
                        time.sleep(2)

                    if self.click_retake():
                        print(
                            f"✅ Ready for option {self.options[option_index + 1]} test"
                        )
                        print("You can now run this script again with the next option")
                    else:
                        print(
                            "❌ Could not click retake - you'll need to manually navigate back"
                        )
                else:
                    print(
                        f"\n🏁 All options tested! Use the analyzer script to build final answer key."
                    )
            else:
                print(f"❌ Option {option_name} test failed")

        except KeyboardInterrupt:
            print("\n⏹️ Stopped by user")
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            try:
                input("Press Enter to close browser...")
            except EOFError:
                print("⚠️ Automated mode - closing browser automatically")
                time.sleep(1)
            if self.automation:
                self.automation.close()


def main():
    """Main entry point"""
    print("🎯 Persistent Exam Bot")
    print("=" * 30)
    print("This bot tests one option at a time and saves results.")
    print("Run it 4 times to test A, B, C, and D options.")
    print()

    print("Which option would you like to test?")
    print("0 = A")
    print("1 = B")
    print("2 = C")
    print("3 = D")

    try:
        option_index = int(input("Enter option index (0-3): ").strip())
        if not 0 <= option_index <= 3:
            print("❌ Invalid option index")
            return

        bot = PersistentExamBot()
        bot.run_option_test(option_index)

    except ValueError:
        print("❌ Please enter a valid number")
    except KeyboardInterrupt:
        print("\n⏹️ Cancelled")


if __name__ == "__main__":
    main()
