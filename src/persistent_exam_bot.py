#!/usr/bin/env python3
"""
Fully Automated Exam Bot
Automatically tests all options (A, B, C, D) and builds final answer key
No user input required except initial login
"""

import sys
import os
import time
import json
import re
from datetime import datetime
from typing import Dict, Optional, List
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


class AutomatedExamBot:
    def __init__(self):
        self.automation = None
        self.total_questions = 0
        self.options = ["A", "B", "C", "D"]
        self.results_dir = "exam_results"
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.test_results = {}  # Store all option results
        self.target_score = 70.0

        # Create results directory
        os.makedirs(self.results_dir, exist_ok=True)

    def start(self):
        """Initialize the automation"""
        print("🎯 Fully Automated Exam Bot")
        print("=" * 35)
        print(f"📁 Results will be saved to: {self.results_dir}/")
        print(f"🆔 Session ID: {self.session_id}")
        print("🤖 Will automatically test all options A, B, C, D")

        try:
            self.automation = ExamAutomation(headless=False)

            if not self.automation.start_browser():
                print("❌ Failed to start browser")
                return False

            return True  # ✅ Now correctly inside the try block

        except Exception as e:
            print(f"❌ Error starting: {e}")
            return False

    def click_retake(self) -> bool:
        """Click the retake button with better error handling"""
        print("🔄 Looking for retake button...")

        try:
            # Wait a moment for page to fully load
            time.sleep(3)

            # Check if browser is still responsive
            try:
                current_url = self.automation.driver.current_url
                print(f"📍 On results page: {current_url}")
            except Exception as e:
                print(f"❌ Browser not responsive: {e}")
                return False

            retake_selectors = [
                "//button[contains(text(), 'Retake Exam')]",
                "//button[contains(text(), 'Retake')]",
                "//a[contains(text(), 'Retake Exam')]",
                "//input[@value='Retake Exam']",
                "//button[contains(@class, 'retake')]",
                "//*[contains(@onclick, 'retake')]",
            ]

            retake_button = None

            for selector in retake_selectors:
                try:
                    button = self.automation.driver.find_element(By.XPATH, selector)

                    if button.is_displayed() and button.is_enabled():
                        retake_button = button
                        print(f"✅ Found retake button: {selector}")
                        break

                except Exception:
                    continue

            if not retake_button:
                print("❌ No retake button found")
                # Try to find any button with "retake" in text (case insensitive)
                try:
                    all_buttons = self.automation.driver.find_elements(
                        By.TAG_NAME, "button"
                    )
                    for button in all_buttons:
                        if button.text and "retake" in button.text.lower():
                            retake_button = button
                            print(f"✅ Found retake button by text: '{button.text}'")
                            break
                except:
                    pass

            if retake_button:
                try:
                    # Scroll to button
                    self.automation.driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center'});", retake_button
                    )
                    time.sleep(1)

                    # Try clicking with JavaScript first (more reliable)
                    self.automation.driver.execute_script(
                        "arguments[0].click();", retake_button
                    )

                    # Wait for page to load
                    print("⏳ Waiting for retake page to load...")
                    time.sleep(5)

                    # Verify we're back on the exam page
                    try:
                        questions = self.automation.find_questions()
                        if questions:
                            print(
                                f"✅ Successfully retook exam - found {len(questions)} questions"
                            )
                            return True
                        else:
                            print("⚠️ Retake may have failed - no questions found")
                            return False
                    except:
                        print("⚠️ Could not verify retake success")
                        return True  # Assume it worked

                except Exception as e:
                    print(f"❌ Error clicking retake button: {e}")
                    return False
            else:
                print("❌ Could not find any retake button")
                return False

        except Exception as e:
            print(f"❌ Error in retake process: {e}")
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
        print("⏱️ You have 60 seconds to login and get to the exam page...")

        # Wait for user to login and navigate
        for i in range(60, 0, -1):
            print(
                f"\r⏰ Starting automated testing in {i} seconds... (Press Ctrl+C to cancel)",
                end="",
                flush=True,
            )
            time.sleep(1)

        print(f"\n🚀 Starting automated testing!")

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

    def test_single_option(self, option_index: int) -> Dict[int, bool]:
        """
        Test a single option (A=0, B=1, C=2, D=3) for ALL questions
        """
        option_name = self.options[option_index]
        print(f"\n🧪 TESTING OPTION {option_name} FOR ALL QUESTIONS")
        print("=" * 50)

        # Verify we can still interact with the page
        try:
            # Check if browser is still responsive
            current_url = self.automation.driver.current_url
            print(f"📍 Current URL: {current_url}")
        except Exception as e:
            print(f"❌ Browser connection lost: {e}")
            return {}

        # Re-find questions to ensure we have fresh elements
        print(f"🔍 Re-finding questions for option {option_name}...")
        questions = self.automation.find_questions()

        if not questions:
            print(f"❌ Could not find questions for option {option_name}")
            return {}

        if len(questions) != self.total_questions:
            print(
                f"⚠️ Question count changed: expected {self.total_questions}, found {len(questions)}"
            )

        # Select the same option for all questions with verification
        print(f"📝 Selecting {option_name} for all {self.total_questions} questions...")
        start_time = time.time()

        successful_selections = 0

        for q_num in range(1, self.total_questions + 1):
            show_progress(q_num, self.total_questions, f"Selecting {option_name}")

            try:
                success = self.automation.select_answer(q_num, option_index)
                if success:
                    successful_selections += 1

                    # Extra verification: check if the selection actually "stuck"
                    if q_num <= 5:  # Only verify first 5 to avoid slowing down too much
                        time.sleep(0.1)
                        # Try to verify the selection was applied
                        try:
                            question = self.automation.questions[q_num - 1]
                            selected_option = question.get("selected")
                            if selected_option == option_index:
                                print(
                                    f"\n✅ Q{q_num} verification: {option_name} selected"
                                )
                            else:
                                print(
                                    f"\n⚠️ Q{q_num} verification failed: expected {option_name}, got index {selected_option}"
                                )
                        except:
                            pass  # Skip verification if it fails
                else:
                    print(f"\n⚠️ Failed to select {option_name} for Q{q_num}")

                # Add a small delay and check browser health every 10 questions
                if q_num % 10 == 0:
                    time.sleep(0.1)
                    try:
                        # Quick browser health check
                        self.automation.driver.current_url
                    except Exception as e:
                        print(f"\n❌ Browser health check failed at Q{q_num}: {e}")
                        return {}
                else:
                    time.sleep(0.02)

            except Exception as e:
                print(f"\n❌ Error selecting Q{q_num}: {e}")
                # Try to continue with next question
                continue

        print(
            f"\n✅ Successfully selected {option_name} for {successful_selections}/{self.total_questions} questions"
        )

        if successful_selections < self.total_questions * 0.8:  # Less than 80% success
            print(
                f"⚠️ Only {successful_selections}/{self.total_questions} selections successful"
            )
            print("🔄 This may affect results accuracy")

        # Wait a moment for selections to register
        print("⏱️ Waiting for selections to register...")
        time.sleep(2)

        # Debug: Check a few selections to verify they're actually applied
        print("🔍 Verifying selections were applied...")
        verification_count = 0
        for q_num in [1, 2, 3, 4, 5]:  # Check first 5 questions
            try:
                if q_num <= len(self.automation.questions):
                    question = self.automation.questions[q_num - 1]
                    if question.get("selected") == option_index:
                        verification_count += 1
            except:
                pass

        print(f"🔍 Verified {verification_count}/5 sample selections are correct")

        if verification_count < 3:  # Less than 3 out of 5 verified
            print("⚠️ Warning: Many selections may not have been applied properly")
            print("🔄 This could explain score mismatch")

        print(f"📤 Submitting exam...")

        # Submit the exam
        success = self.automation.submit_exam()
        if not success:
            print("❌ Failed to submit exam")
            return {}

        print("⏳ Waiting for results...")
        time.sleep(5)

        # Get score
        score = self.automation.get_score()
        if score is not None:
            print(f"🎯 Score with all {option_name}'s: {score}%")
        else:
            print(f"⚠️ Could not detect score for option {option_name}")

        # Parse detailed results
        results = self.parse_detailed_results()

        if not results:
            print(f"❌ Failed to parse results for option {option_name}")
            return {}

        # Verify results make sense
        correct_count = sum(1 for is_correct in results.values() if is_correct)
        if correct_count == 0 and score != 0:
            print(f"⚠️ Mismatch: parsed 0 correct but score is {score}%")
        elif score == 0 and correct_count > 0:
            print(f"⚠️ Mismatch: score is 0% but parsed {correct_count} correct")

        # Save results to file
        result_data = {
            "session_id": self.session_id,
            "option": option_name,
            "option_index": option_index,
            "score": score,
            "total_questions": self.total_questions,
            "successful_selections": successful_selections,
            "timestamp": datetime.now().isoformat(),
            "results": results,  # {question_number: is_correct}
            "test_duration_seconds": time.time() - start_time,
        }

        filename = f"{self.results_dir}/option_{option_name}_{self.session_id}.json"
        with open(filename, "w") as f:
            json.dump(result_data, f, indent=2)

        # Store in memory for analysis
        self.test_results[option_index] = results

        # Show summary
        print(
            f"📊 Option {option_name}: {correct_count}/{len(results)} questions correct"
        )
        print(f"💾 Results saved to: {filename}")

        elapsed = time.time() - start_time
        print(f"⏱️ {option_name} test completed in {elapsed:.1f} seconds")

        return results

    def parse_detailed_results(self) -> Dict[int, bool]:
        """Fast result parsing using visual indicators"""
        print("⚡ Fast result parsing using visual indicators...")
        start_time = time.time()

        try:
            results = {}

            # Find all elements containing "Correct" and "Incorrect"
            correct_elements = self.automation.driver.find_elements(
                By.XPATH, "//*[contains(text(), 'Correct')]"
            )
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

            # Process incorrect elements
            for element in incorrect_elements:
                q_num = self.find_question_number_near_element(element)
                if (
                    q_num
                    and 1 <= q_num <= self.total_questions
                    and q_num not in results
                ):
                    results[q_num] = False

            # Fill any remaining missing results
            for q_num in range(1, self.total_questions + 1):
                if q_num not in results:
                    results[q_num] = False

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
        """Find question number near a given element"""
        try:
            # Check parent elements (go up the DOM tree)
            current = element
            for _ in range(5):
                try:
                    current = current.find_element(By.XPATH, "..")
                    parent_text = current.text
                    if parent_text:
                        q_match = re.search(
                            r"Question\s+(\d+)", parent_text, re.IGNORECASE
                        )
                        if q_match:
                            q_num = int(q_match.group(1))
                            if 1 <= q_num <= self.total_questions:
                                return q_num
                except:
                    break
            return None
        except Exception:
            return None

    def check_browser_health(self) -> bool:
        """Check if browser is still responsive"""
        try:
            # Simple health check
            self.automation.driver.current_url
            self.automation.driver.title
            return True
        except Exception:
            return False

    def restart_browser_if_needed(self) -> bool:
        """Restart browser if it's not responsive"""
        if self.check_browser_health():
            return True

        print("🔄 Browser not responsive, attempting restart...")

        try:
            # Close existing browser
            if self.automation:
                try:
                    self.automation.close()
                except:
                    pass

            # Start new browser
            self.automation = ExamAutomation(headless=False)
            if not self.automation.start_browser():
                print("❌ Failed to restart browser")
                return False

            print("✅ Browser restarted successfully")

            # Navigate back to exam (user will need to login again)
            print("👤 Please log back in and navigate to the exam page...")
            print("⏱️ You have 30 seconds...")

            for i in range(30, 0, -1):
                print(f"\r⏰ Continuing in {i} seconds...", end="", flush=True)
                time.sleep(1)

            print(f"\n🚀 Continuing automated testing...")
            return True

        except Exception as e:
            print(f"❌ Failed to restart browser: {e}")
            return False

    def click_retake(self) -> bool:
        """Click the retake button with better error handling"""
        print("🔄 Looking for retake button...")

        try:
            # Wait a moment for page to fully load
            time.sleep(3)

            # Check if browser is still responsive
            try:
                current_url = self.automation.driver.current_url
                print(f"📍 On results page: {current_url}")
            except Exception as e:
                print(f"❌ Browser not responsive: {e}")
                return False

            retake_selectors = [
                "//button[contains(text(), 'Retake Exam')]",
                "//button[contains(text(), 'Retake')]",
                "//a[contains(text(), 'Retake Exam')]",
                "//input[@value='Retake Exam']",
                "//button[contains(@class, 'retake')]",
                "//*[contains(@onclick, 'retake')]",
            ]

            retake_button = None

            for selector in retake_selectors:
                try:
                    button = self.automation.driver.find_element(By.XPATH, selector)

                    if button.is_displayed() and button.is_enabled():
                        retake_button = button
                        print(f"✅ Found retake button: {selector}")
                        break

                except Exception:
                    continue

            if not retake_button:
                print("❌ No retake button found")
                # Try to find any button with "retake" in text (case insensitive)
                try:
                    all_buttons = self.automation.driver.find_elements(
                        By.TAG_NAME, "button"
                    )
                    for button in all_buttons:
                        if button.text and "retake" in button.text.lower():
                            retake_button = button
                            print(f"✅ Found retake button by text: '{button.text}'")
                            break
                except:
                    pass

            if retake_button:
                try:
                    # Scroll to button
                    self.automation.driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center'});", retake_button
                    )
                    time.sleep(1)

                    # Try clicking with JavaScript first (more reliable)
                    self.automation.driver.execute_script(
                        "arguments[0].click();", retake_button
                    )

                    # Wait for page to load
                    print("⏳ Waiting for retake page to load...")
                    time.sleep(5)

                    # Verify we're back on the exam page
                    try:
                        questions = self.automation.find_questions()
                        if questions:
                            print(
                                f"✅ Successfully retook exam - found {len(questions)} questions"
                            )
                            return True
                        else:
                            print("⚠️ Retake may have failed - no questions found")
                            return False
                    except:
                        print("⚠️ Could not verify retake success")
                        return True  # Assume it worked

                except Exception as e:
                    print(f"❌ Error clicking retake button: {e}")
                    return False
            else:
                print("❌ Could not find any retake button")
                return False

        except Exception as e:
            print(f"❌ Error in retake process: {e}")
            return False

    def analyze_and_build_answer_key(self) -> Dict[int, int]:
        """Analyze all test results and build optimal answer key"""
        print("\n🔑 Building optimal answer key from all test results...")

        answer_key = {}

        for q_num in range(1, self.total_questions + 1):
            # Find which option(s) were correct for this question
            correct_options = []

            for option_idx in range(4):
                if option_idx in self.test_results:
                    if q_num in self.test_results[option_idx]:
                        if self.test_results[option_idx][q_num]:
                            correct_options.append(option_idx)

            if correct_options:
                # Use the first correct option found
                answer_key[q_num] = correct_options[0]
                option_name = self.options[correct_options[0]]
                print(f"✅ Q{q_num}: {option_name}")

                if len(correct_options) > 1:
                    other_options = [self.options[i] for i in correct_options[1:]]
                    print(f"   ⚠️ Multiple correct: {', '.join(other_options)}")
            else:
                # No correct option found - default to A
                answer_key[q_num] = 0
                print(f"❓ Q{q_num}: No correct option found, defaulting to A")

        return answer_key

    def submit_final_exam(self, answer_key: Dict[int, int]) -> float:
        """Submit the exam with the optimal answer key"""
        print("\n🎯 SUBMITTING FINAL EXAM WITH OPTIMAL ANSWER KEY")
        print("=" * 55)

        # Apply the answer key
        for q_num in range(1, self.total_questions + 1):
            option_idx = answer_key.get(q_num, 0)  # Default to A if not found
            show_progress(q_num, self.total_questions, "Applying answers")
            self.automation.select_answer(q_num, option_idx)
            time.sleep(0.02)

        print(f"\n✅ All answers applied!")
        print(f"📤 Submitting final exam...")

        # Submit
        success = self.automation.submit_exam()
        if not success:
            print("❌ Failed to submit final exam")
            return 0.0

        print("⏳ Waiting for final results...")
        time.sleep(5)

        score = self.automation.get_score()
        if score is not None:
            print(f"\n🎯 FINAL SCORE: {score}%")
            if score >= self.target_score:
                print(f"🎉 SUCCESS! Achieved target of {self.target_score}%")
            else:
                print(f"❌ Did not reach target of {self.target_score}%")
        else:
            print("⚠️ Could not detect final score")
            score = 0.0

        return score

    def run_fully_automated(self):
        """Main automated workflow"""
        try:
            total_start_time = time.time()

            # Initial setup
            if not self.start():
                return False

            if not self.login_and_navigate():
                return False

            if not self.find_and_analyze_questions():
                return False

            print(f"\n🤖 Starting fully automated testing...")
            print(f"📝 Will test A, B, C, D for all {self.total_questions} questions")

            # Test each option (A, B, C, D) automatically
            for option_idx in range(4):
                option_name = self.options[option_idx]

                print(f"\n{'='*60}")
                print(f"🧪 AUTOMATED PHASE {option_idx + 1}/4: OPTION {option_name}")
                print(f"{'='*60}")

                # Check browser health before each test
                if not self.check_browser_health():
                    print("⚠️ Browser not responsive, attempting restart...")
                    if not self.restart_browser_if_needed():
                        print("❌ Could not restart browser, aborting")
                        break

                # Test this option for all questions
                results = self.test_single_option(option_idx)

                if not results:
                    print(f"❌ Failed to get results for option {option_name}")

                    # Try to restart browser and continue
                    if not self.restart_browser_if_needed():
                        print("❌ Could not recover, stopping")
                        break
                    else:
                        print(
                            "🔄 Browser restarted, skipping this option and continuing..."
                        )
                        continue

                # Automatically click retake (unless this is the last option)
                if option_idx < 3:  # Not the last option
                    print(f"🔄 Automatically proceeding to next option...")

                    retake_attempts = 0
                    max_retake_attempts = 3

                    while retake_attempts < max_retake_attempts:
                        if self.click_retake():
                            break
                        else:
                            retake_attempts += 1
                            print(
                                f"⚠️ Retake attempt {retake_attempts}/{max_retake_attempts} failed"
                            )

                            if retake_attempts < max_retake_attempts:
                                print("🔄 Trying browser restart...")
                                if self.restart_browser_if_needed():
                                    # After restart, we need to manually navigate back to results
                                    print(
                                        "👤 Please navigate back to the exam results page..."
                                    )
                                    print("⏱️ You have 20 seconds...")
                                    for i in range(20, 0, -1):
                                        print(
                                            f"\r⏰ Waiting {i} seconds...",
                                            end="",
                                            flush=True,
                                        )
                                        time.sleep(1)
                                    print()
                                else:
                                    break

                    if retake_attempts >= max_retake_attempts:
                        print(
                            "❌ Could not retake for next option after multiple attempts"
                        )
                        break

                    time.sleep(2)  # Brief pause between tests

            # Build the optimal answer key
            if not self.test_results:
                print("❌ No test results available")
                return False

            answer_key = self.analyze_and_build_answer_key()

            # Automatically submit final exam
            if self.click_retake():
                final_score = self.submit_final_exam(answer_key)
            else:
                print("❌ Could not retake for final submission")
                final_score = 0.0

            total_time = time.time() - total_start_time
            print(f"\n🏁 FULLY AUTOMATED EXAM COMPLETION")
            print(f"⏱️ Total time: {total_time/60:.1f} minutes")
            print(f"🎯 Final score: {final_score}%")

            if final_score >= self.target_score:
                print("🎉🎉🎉 EXAM PASSED! 🎉🎉🎉")
            else:
                print("❌ Exam not passed, but all data collected for analysis")

        except KeyboardInterrupt:
            print("\n⏹️ Stopped by user")
        except Exception as e:
            print(f"❌ Error in automated testing: {e}")
        finally:
            print("\n⏱️ Keeping browser open for 30 seconds to review results...")
            time.sleep(30)
            if self.automation:
                self.automation.close()


if __name__ == "__main__":
    print("🤖 Fully Automated Exam Bot")
    print("=" * 30)
    print("This bot will automatically:")
    print("1. Test all options A, B, C, D")
    print("2. Build optimal answer key")
    print("3. Submit final exam")
    print("4. No user input required after login!")
    print()

    confirm = input("Ready to start automated exam solving? (y/N): ").lower()
    if confirm == "y":
        bot = AutomatedExamBot()
        bot.run_fully_automated()
    else:
        print("❌ Cancelled")
