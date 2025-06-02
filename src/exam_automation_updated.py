#!/usr/bin/env python3
"""
Updated Exam Automation Module for MasterCPE Format
Handles web browser interactions using Selenium for the specific exam layout
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from pathlib import Path
import time
import re
from typing import List, Dict, Optional, Tuple


class ExamAutomation:
    def __init__(self, headless: bool = True):
        """Initialize the web automation"""
        self.driver = None
        self.headless = headless
        self.questions = []
        self.current_answers = {}

    def __enter__(self):
        """Context manager entry"""
        self.start_browser()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

    def start_browser(self):
        """Start the browser session"""
        try:
            # Get the fixed ChromeDriver path
            chromedriver_path = self.get_chromedriver_path()
            if not chromedriver_path:
                print("❌ ChromeDriver not found. Run fix_chromedriver.py first")
                return False

            # Configure Chrome options
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1280,720")
            chrome_options.add_argument(
                "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )

            # Create service with fixed ChromeDriver
            service = Service(chromedriver_path)

            # Create the driver
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.implicitly_wait(10)  # 10 seconds implicit wait

            print("✅ Browser started successfully")
            return True

        except Exception as e:
            print(f"❌ Error starting browser: {e}")
            return False

    def get_chromedriver_path(self):
        """Get the path to our manually installed ChromeDriver"""
        download_dir = Path.home() / ".exam_bot_chromedriver"

        # Look for chromedriver executable
        chromedriver_files = list(download_dir.glob("**/chromedriver*"))

        for path in chromedriver_files:
            if path.is_file() and (
                path.name == "chromedriver" or path.name == "chromedriver.exe"
            ):
                return str(path)

        return None

    def navigate_to_exam(self, url: str) -> bool:
        """Navigate to the exam URL"""
        try:
            if not self.driver:
                self.start_browser()

            print(f"🌐 Navigating to: {url}")
            self.driver.get(url)

            # Wait a bit for any dynamic content to load
            time.sleep(5)

            # Check if we successfully loaded an exam page
            page_title = self.driver.title
            print(f"📄 Page title: {page_title}")

            return True

        except Exception as e:
            print(f"❌ Error navigating to exam: {e}")
            return False

    def find_questions(self) -> List[Dict]:
        """Find all questions on the MasterCPE exam page"""
        try:
            self.questions = []

            # Look for all radio buttons first
            radio_inputs = self.driver.find_elements(
                By.CSS_SELECTOR, 'input[type="radio"]'
            )

            if not radio_inputs:
                print("❌ No radio buttons found")
                return []

            print(f"🔍 Found {len(radio_inputs)} radio buttons")

            # Group radio buttons by name attribute (each question should have unique name)
            question_groups = {}
            for radio in radio_inputs:
                name = radio.get_attribute("name")
                if name and name not in question_groups:
                    question_groups[name] = []

                if name:
                    question_groups[name].append(
                        {
                            "element": radio,
                            "value": radio.get_attribute("value"),
                            "label": self.get_radio_label(radio),
                        }
                    )

            # Convert to our questions format - only keep groups with multiple options
            question_number = 1
            for name, options in question_groups.items():
                if (
                    len(options) >= 2
                ):  # Only include if it has multiple options (real question)
                    self.questions.append(
                        {
                            "number": question_number,
                            "name": name,
                            "options": options,
                            "selected": None,
                        }
                    )
                    question_number += 1

            print(f"📝 Found {len(self.questions)} actual questions")

            # Debug: Print first few questions found
            for i, q in enumerate(self.questions[:3]):
                print(f"   Q{i+1}: {q['name']} - {len(q['options'])} options")

            return self.questions

        except Exception as e:
            print(f"❌ Error finding questions: {e}")
            return []

    def get_radio_label(self, radio_element) -> str:
        """Get the label text for a radio button"""
        try:
            # Try to find associated label by 'for' attribute
            radio_id = radio_element.get_attribute("id")
            if radio_id:
                try:
                    label = self.driver.find_element(
                        By.CSS_SELECTOR, f'label[for="{radio_id}"]'
                    )
                    return label.text.strip()
                except:
                    pass

            # Try to find parent label
            try:
                parent = radio_element.find_element(By.XPATH, "..")
                text = parent.text.strip()
                if text and len(text) < 200:  # Reasonable label length
                    return text
            except:
                pass

            # Try to find nearby text
            try:
                # Look for text in next sibling
                next_sibling = radio_element.find_element(
                    By.XPATH, "following-sibling::*[1]"
                )
                text = next_sibling.text.strip()
                if text:
                    return text
            except:
                pass

            # Fallback to value
            value = radio_element.get_attribute("value")
            return value if value else "Unknown"

        except Exception:
            return "Unknown"

    def select_answer(self, question_number: int, option_index: int) -> bool:
        """Select an answer for a specific question"""
        try:
            if question_number > len(self.questions):
                print(f"❌ Question {question_number} not found")
                return False

            question = self.questions[question_number - 1]

            if option_index >= len(question["options"]):
                print(
                    f"❌ Option {option_index} not found for question {question_number}"
                )
                return False

            # Scroll to the question first
            option = question["options"][option_index]
            self.driver.execute_script(
                "arguments[0].scrollIntoView(true);", option["element"]
            )
            time.sleep(0.2)

            # Click the radio button using JavaScript for reliability
            self.driver.execute_script("arguments[0].click();", option["element"])

            # Update our tracking
            question["selected"] = option_index
            self.current_answers[question["name"]] = option["value"]

            # Small delay to ensure the click registers
            time.sleep(0.1)

            return True

        except Exception as e:
            print(f"❌ Error selecting answer for Q{question_number}: {e}")
            return False

    def select_all_answers(self, answers: List[int]) -> bool:
        """Select answers for all questions"""
        try:
            success = True
            for i, answer_index in enumerate(answers):
                if i < len(self.questions):  # Safety check
                    if not self.select_answer(i + 1, answer_index):
                        success = False
                    time.sleep(0.1)  # Small delay between selections
            return success
        except Exception as e:
            print(f"❌ Error selecting all answers: {e}")
            return False

    def submit_exam(self) -> bool:
        """Submit the exam for grading - specifically for MasterCPE format"""
        try:
            # Look specifically for "Grade My Exam!" button
            grade_button_selectors = [
                '//button[contains(text(), "Grade My Exam")]',
                '//input[@value="Grade My Exam!"]',
                '//button[contains(text(), "Grade")]',
                '//input[contains(@value, "Grade")]',
                "#grade-button",
                ".grade-button",
                'button[onclick*="grade"]',
            ]

            submit_button = None

            # Try each selector
            for selector in grade_button_selectors:
                try:
                    if selector.startswith("//"):
                        # XPath selector
                        submit_button = self.driver.find_element(By.XPATH, selector)
                    else:
                        # CSS selector
                        submit_button = self.driver.find_element(
                            By.CSS_SELECTOR, selector
                        )

                    if (
                        submit_button
                        and submit_button.is_displayed()
                        and submit_button.is_enabled()
                    ):
                        print(f"🎯 Found grade button")
                        break
                    else:
                        submit_button = None
                except:
                    continue

            # If not found, look for any button containing "grade" (case insensitive)
            if not submit_button:
                try:
                    all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                    all_inputs = self.driver.find_elements(
                        By.CSS_SELECTOR, 'input[type="submit"], input[type="button"]'
                    )

                    for element in all_buttons + all_inputs:
                        text = element.text.lower() if element.text else ""
                        value = element.get_attribute("value")
                        if value:
                            text += " " + value.lower()

                        if (
                            "grade" in text
                            and element.is_displayed()
                            and element.is_enabled()
                        ):
                            submit_button = element
                            print(f"🎯 Found grade button by text search")
                            break
                except:
                    pass

            if not submit_button:
                print("❌ No 'Grade My Exam!' button found")
                return False

            # Scroll to button and click
            self.driver.execute_script(
                "arguments[0].scrollIntoView(true);", submit_button
            )
            time.sleep(1)

            # Click using JavaScript for reliability
            self.driver.execute_script("arguments[0].click();", submit_button)

            # Wait for the page to process the submission
            time.sleep(5)

            print("✅ Exam submitted successfully")
            return True

        except Exception as e:
            print(f"❌ Error submitting exam: {e}")
            return False

    def get_score(self) -> Optional[float]:
        """Extract the score from the results page"""
        try:
            # Wait a moment for results to load
            time.sleep(3)

            # Look for specific score text like "You got a score of 52"
            page_source = self.driver.page_source

            # Try to find "You got a score of X" pattern first
            score_pattern = r"You got a score of (\d+(?:\.\d+)?)"
            match = re.search(score_pattern, page_source, re.IGNORECASE)
            if match:
                score = float(match.group(1))
                print(f"📊 Found score: {score}%")
                return score

            # Fallback to general percentage patterns
            percentage_patterns = [
                r"(\d+(?:\.\d+)?)\s*%",
                r"Score[:\s]+(\d+(?:\.\d+)?)",
                r"Grade[:\s]+(\d+(?:\.\d+)?)",
                r"(\d+(?:\.\d+)?)\s*/\s*100",
            ]

            for pattern in percentage_patterns:
                matches = re.findall(pattern, page_source, re.IGNORECASE)
                if matches:
                    for match in matches:
                        try:
                            score = float(match)
                            if 0 <= score <= 100:  # Valid percentage range
                                # Skip common false positives like "100%" in other contexts
                                if (
                                    score != 100
                                    or "You got a score of 100" in page_source
                                ):
                                    print(f"📊 Found score: {score}%")
                                    return score
                        except ValueError:
                            continue

            print("❌ No score found on page")
            return None

        except Exception as e:
            print(f"❌ Error getting score: {e}")
            return None

    def should_retry(self) -> bool:
        """Check if page shows 'You did not pass'"""
        try:
            page_text = self.driver.page_source.lower()
            return "you did not pass" in page_text
        except:
            return False

    def click_retake(self) -> bool:
        """Click Retake Exam button"""
        try:
            button = self.driver.find_element(
                By.XPATH, "//button[contains(text(), 'Retake Exam')]"
            )
            self.driver.execute_script("arguments[0].click();", button)
            time.sleep(5)
            return True
        except Exception as e:
            print(f"❌ Retake error: {e}")
            return False

    def retry_with_option_b(self):
        """Try option B for first 25 questions"""
        try:
            print("🔄 Starting retry with option B...")
            questions = self.find_questions()
            print(f"📝 Found {len(questions)} questions for retry")

            for i in range(len(questions)):
                if i < 25:  # First 25 questions - try B
                    self.select_answer(i + 1, 1)
                else:  # Rest - keep A
                    self.select_answer(i + 1, 0)

            print(f"📤 Submitting retry...")
            self.submit_exam()

            time.sleep(5)
            retry_score = self.get_score()
            if retry_score:
                print(f"🎯 Retry score: {retry_score}%")

        except Exception as e:
            print(f"❌ Retry error: {e}")

    def close(self):
        """Close the browser and cleanup"""
        try:
            if self.driver:
                self.driver.quit()
                print("✅ Browser closed")
        except Exception as e:
            print(f"❌ Error closing browser: {e}")

    def get_page_info(self) -> Dict:
        """Get information about the current page"""
        try:
            return {
                "title": self.driver.title,
                "url": self.driver.current_url,
                "questions_found": len(self.questions),
            }
        except Exception:
            return {"title": "Unknown", "url": "Unknown", "questions_found": 0}
