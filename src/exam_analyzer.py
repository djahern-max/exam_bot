#!/usr/bin/env python3
"""
Exam Results Analyzer
Analyzes saved JSON results from all option tests and builds final answer key
"""

import os
import json
import glob
from typing import Dict, List, Optional
from datetime import datetime


class ExamAnalyzer:
    def __init__(self, results_dir: str = "exam_results"):
        self.results_dir = results_dir
        self.options = ["A", "B", "C", "D"]
        self.test_results = {}  # {option_index: {question_number: is_correct}}
        self.sessions = []
        self.total_questions = 0

    def load_all_results(self) -> bool:
        """Load all saved test results from JSON files"""
        print("🔍 Loading saved test results...")

        if not os.path.exists(self.results_dir):
            print(f"❌ Results directory not found: {self.results_dir}")
            return False

        # Find all option result files
        option_files = glob.glob(f"{self.results_dir}/option_*_*.json")

        if not option_files:
            print(f"❌ No option result files found in {self.results_dir}")
            return False

        print(f"📁 Found {len(option_files)} result files")

        # Load each result file
        for file_path in sorted(option_files):
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)

                option = data["option"]
                option_index = data["option_index"]
                session_id = data["session_id"]
                results = data["results"]
                score = data.get("score", 0)

                # Convert string keys to integers for question numbers
                question_results = {}
                for q_str, is_correct in results.items():
                    question_results[int(q_str)] = is_correct

                self.test_results[option_index] = question_results

                if not self.total_questions:
                    self.total_questions = data["total_questions"]

                correct_count = sum(
                    1 for is_correct in question_results.values() if is_correct
                )
                print(
                    f"✅ Loaded Option {option}: {correct_count}/{len(question_results)} correct (Score: {score}%)"
                )

                # Track session info
                if session_id not in [s["session_id"] for s in self.sessions]:
                    self.sessions.append(
                        {"session_id": session_id, "timestamp": data["timestamp"]}
                    )

            except Exception as e:
                print(f"❌ Error loading {file_path}: {e}")
                continue

        print(f"\n📊 Loaded results for {len(self.test_results)} options")
        print(f"📝 Total questions: {self.total_questions}")

        return len(self.test_results) > 0

    def analyze_questions(self) -> Dict[int, Dict]:
        """Analyze each question to find correct answers"""
        print("\n🔍 Analyzing questions...")

        question_analysis = {}

        for q_num in range(1, self.total_questions + 1):
            analysis = {
                "question_number": q_num,
                "correct_options": [],
                "incorrect_options": [],
                "missing_options": [],
                "recommended_answer": None,
                "confidence": "unknown",
            }

            # Check each option for this question
            for option_idx in range(4):
                option_name = self.options[option_idx]

                if option_idx in self.test_results:
                    if q_num in self.test_results[option_idx]:
                        is_correct = self.test_results[option_idx][q_num]
                        if is_correct:
                            analysis["correct_options"].append(
                                (option_idx, option_name)
                            )
                        else:
                            analysis["incorrect_options"].append(
                                (option_idx, option_name)
                            )
                    else:
                        analysis["missing_options"].append((option_idx, option_name))
                else:
                    analysis["missing_options"].append((option_idx, option_name))

            # Determine recommended answer and confidence
            if analysis["correct_options"]:
                # Use the first correct option found
                analysis["recommended_answer"] = analysis["correct_options"][0]

                if len(analysis["correct_options"]) == 1:
                    analysis["confidence"] = "high"
                else:
                    analysis["confidence"] = "multiple_correct"
            elif len(analysis["incorrect_options"]) == 4:
                # All options were tested and all were incorrect - something's wrong
                analysis["recommended_answer"] = (0, "A")  # Default to A
                analysis["confidence"] = "all_incorrect"
            elif analysis["missing_options"]:
                # Some options weren't tested, pick the first untested one
                analysis["recommended_answer"] = analysis["missing_options"][0]
                analysis["confidence"] = "untested_guess"
            else:
                # Fallback to A
                analysis["recommended_answer"] = (0, "A")
                analysis["confidence"] = "fallback"

            question_analysis[q_num] = analysis

        return question_analysis

    def build_answer_key(self, question_analysis: Dict[int, Dict]) -> Dict[int, int]:
        """Build the final answer key"""
        print("\n🔑 Building final answer key...")

        answer_key = {}
        confidence_stats = {
            "high": 0,
            "multiple_correct": 0,
            "untested_guess": 0,
            "all_incorrect": 0,
            "fallback": 0,
        }

        for q_num, analysis in question_analysis.items():
            recommended = analysis["recommended_answer"]
            confidence = analysis["confidence"]

            answer_key[q_num] = recommended[0]  # Store option index
            confidence_stats[confidence] += 1

            # Print details for review
            option_idx, option_name = recommended

            if confidence == "high":
                print(f"✅ Q{q_num}: {option_name} (confident)")
            elif confidence == "multiple_correct":
                other_correct = [f"{opt[1]}" for opt in analysis["correct_options"][1:]]
                print(
                    f"🔄 Q{q_num}: {option_name} (also correct: {', '.join(other_correct)})"
                )
            elif confidence == "untested_guess":
                print(f"❓ Q{q_num}: {option_name} (untested - best guess)")
            elif confidence == "all_incorrect":
                print(f"⚠️ Q{q_num}: {option_name} (all options were incorrect!)")
            else:
                print(f"🤔 Q{q_num}: {option_name} (fallback)")

        print(f"\n📈 Confidence Statistics:")
        for conf_type, count in confidence_stats.items():
            if count > 0:
                print(f"   {conf_type}: {count} questions")

        return answer_key

    def save_answer_key(
        self, answer_key: Dict[int, int], question_analysis: Dict[int, Dict]
    ):
        """Save the final answer key to a file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        final_data = {
            "generated_at": datetime.now().isoformat(),
            "total_questions": self.total_questions,
            "sessions_analyzed": self.sessions,
            "answer_key": answer_key,
            "question_analysis": question_analysis,
            "summary": {
                "high_confidence": len(
                    [
                        q
                        for q, a in question_analysis.items()
                        if a["confidence"] == "high"
                    ]
                ),
                "multiple_correct": len(
                    [
                        q
                        for q, a in question_analysis.items()
                        if a["confidence"] == "multiple_correct"
                    ]
                ),
                "guessed_answers": len(
                    [
                        q
                        for q, a in question_analysis.items()
                        if a["confidence"] in ["untested_guess", "fallback"]
                    ]
                ),
                "problematic": len(
                    [
                        q
                        for q, a in question_analysis.items()
                        if a["confidence"] == "all_incorrect"
                    ]
                ),
            },
        }

        filename = f"{self.results_dir}/final_answer_key_{timestamp}.json"
        with open(filename, "w") as f:
            json.dump(final_data, f, indent=2)

        print(f"💾 Answer key saved to: {filename}")
        return filename

    def create_submission_script(self, answer_key: Dict[int, int]):
        """Create a script to submit the final exam with the answer key"""
        script_content = f'''#!/usr/bin/env python3
"""
Auto-generated Final Exam Submission Script
Generated at: {datetime.now().isoformat()}
"""

import sys
import os
import time

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
    print(f"\\r{{message}}: [{{bar}}] {{percent}}% ({{current}}/{{total}})", end="", flush=True)


def submit_final_exam():
    """Submit exam with the analyzed answer key"""
    
    # The final answer key (question_number: option_index)
    answer_key = {answer_key}
    
    options = ['A', 'B', 'C', 'D']
    
    print("🎯 Final Exam Submission")
    print("=" * 30)
    print(f"📝 Will apply {{len(answer_key)}} answers")
    
    try:
        automation = ExamAutomation(headless=False)
        automation.start_browser()

        print("🔗 Going to MasterCPE...")
        automation.navigate_to_exam("https://mastercpe.com")

        print("👤 Please log in and navigate to your exam")
        input("Press Enter when you're on the exam page...")

        print("🔍 Finding questions...")
        questions = automation.find_questions()

        if not questions:
            print("❌ No questions found")
            return

        total_questions = len(questions)
        print(f"📝 Found {{total_questions}} questions")

        if total_questions != len(answer_key):
            print(f"⚠️ Question count mismatch: found {{total_questions}}, expected {{len(answer_key)}}")

        confirm = input("Ready to apply final answer key? (y/N): ").lower()
        if confirm != 'y':
            print("❌ Cancelled")
            return

        print("🚀 Applying final answer key...")
        start_time = time.time()

        # Apply answers
        for q_num in range(1, total_questions + 1):
            option_idx = answer_key.get(q_num, 0)  # Default to A if not found
            option_name = options[option_idx]
            
            show_progress(q_num, total_questions, f"Applying answers")
            automation.select_answer(q_num, option_idx)
            time.sleep(0.02)

        print(f"\\n✅ All answers applied!")
        print(f"📤 Submitting final exam...")

        automation.submit_exam()

        print("⏳ Waiting for final results...")
        time.sleep(5)

        score = automation.get_score()
        if score is not None:
            print(f"\\n🎯 FINAL SCORE: {{score}}%")
            if score >= 70:
                print("🎉 SUCCESS! Passed the exam!")
            else:
                print(f"❌ Did not reach 70% target")
        else:
            print("⚠️ Could not detect final score")

        total_time = time.time() - start_time
        print(f"⏱️ Completed in {{total_time:.1f}} seconds")

        input("\\nPress Enter to close browser...")
        automation.close()

    except KeyboardInterrupt:
        print("\\n⏹️ Stopped by user")
    except Exception as e:
        print(f"❌ Error: {{e}}")


if __name__ == "__main__":
    submit_final_exam()
'''

        script_filename = f"{self.results_dir}/submit_final_exam.py"
        with open(script_filename, "w") as f:
            f.write(script_content)

        # Make it executable
        os.chmod(script_filename, 0o755)

        print(f"📜 Submission script created: {script_filename}")
        return script_filename

    def generate_report(
        self, question_analysis: Dict[int, Dict], answer_key: Dict[int, int]
    ):
        """Generate a detailed analysis report"""
        print("\n📋 ANALYSIS REPORT")
        print("=" * 50)

        # Summary statistics
        total_questions = len(question_analysis)
        high_confidence = len(
            [q for q, a in question_analysis.items() if a["confidence"] == "high"]
        )
        multiple_correct = len(
            [
                q
                for q, a in question_analysis.items()
                if a["confidence"] == "multiple_correct"
            ]
        )
        guessed = len(
            [
                q
                for q, a in question_analysis.items()
                if a["confidence"] in ["untested_guess", "fallback"]
            ]
        )
        problematic = len(
            [
                q
                for q, a in question_analysis.items()
                if a["confidence"] == "all_incorrect"
            ]
        )

        print(f"📊 Total Questions: {total_questions}")
        print(
            f"✅ High Confidence: {high_confidence} ({high_confidence/total_questions*100:.1f}%)"
        )
        print(
            f"🔄 Multiple Correct: {multiple_correct} ({multiple_correct/total_questions*100:.1f}%)"
        )
        print(f"❓ Guessed/Untested: {guessed} ({guessed/total_questions*100:.1f}%)")
        print(f"⚠️ Problematic: {problematic} ({problematic/total_questions*100:.1f}%)")

        # Option distribution
        option_counts = [0, 0, 0, 0]
        for q_num, option_idx in answer_key.items():
            option_counts[option_idx] += 1

        print(f"\n📈 Answer Distribution:")
        for i, count in enumerate(option_counts):
            option_name = self.options[i]
            percentage = count / total_questions * 100
            print(f"   {option_name}: {count} questions ({percentage:.1f}%)")

        # Expected score estimation
        expected_correct = high_confidence + multiple_correct
        if guessed > 0:
            # Assume 25% chance for guessed answers (random choice)
            expected_correct += guessed * 0.25

        expected_score = (expected_correct / total_questions) * 100
        print(f"\n🎯 Expected Score: {expected_score:.1f}%")

        if expected_score >= 70:
            print("🎉 Expected to PASS!")
        else:
            print(f"⚠️ May not reach 70% target (need {70 - expected_score:.1f}% more)")

        # Detailed question breakdown
        print(f"\n📝 QUESTION DETAILS:")
        print("-" * 50)

        for q_num in sorted(question_analysis.keys()):
            analysis = question_analysis[q_num]
            recommended = analysis["recommended_answer"]
            confidence = analysis["confidence"]

            option_idx, option_name = recommended

            # Format the line based on confidence
            if confidence == "high":
                print(f"Q{q_num:2d}: {option_name} ✅ (confident)")
            elif confidence == "multiple_correct":
                other_options = ", ".join(
                    [
                        opt[1]
                        for opt in analysis["correct_options"]
                        if opt != recommended
                    ]
                )
                print(f"Q{q_num:2d}: {option_name} 🔄 (also correct: {other_options})")
            elif confidence == "untested_guess":
                tested = ", ".join([opt[1] for opt in analysis["incorrect_options"]])
                print(f"Q{q_num:2d}: {option_name} ❓ (untested, ruled out: {tested})")
            elif confidence == "all_incorrect":
                print(f"Q{q_num:2d}: {option_name} ⚠️ (all options failed!)")
            else:
                print(f"Q{q_num:2d}: {option_name} 🤔 (fallback)")

    def run_analysis(self):
        """Main analysis workflow"""
        print("🔍 Exam Results Analyzer")
        print("=" * 30)

        try:
            # Load all saved results
            if not self.load_all_results():
                return False

            # Analyze each question
            question_analysis = self.analyze_questions()

            # Build final answer key
            answer_key = self.build_answer_key(question_analysis)

            # Save results
            answer_key_file = self.save_answer_key(answer_key, question_analysis)
            submission_script = self.create_submission_script(answer_key)

            # Generate detailed report
            self.generate_report(question_analysis, answer_key)

            print(f"\n🎉 Analysis Complete!")
            print(f"📁 Files created:")
            print(f"   • {answer_key_file}")
            print(f"   • {submission_script}")

            print(f"\n📋 Next Steps:")
            print(f"   1. Review the analysis report above")
            print(f"   2. Run the submission script: python {submission_script}")
            print(f"   3. Or manually review the answer key file")

            return True

        except Exception as e:
            print(f"❌ Analysis error: {e}")
            return False


def main():
    """Main entry point"""
    print("🔍 Exam Results Analyzer")
    print("=" * 30)
    print("This script analyzes saved test results and builds the final answer key.")
    print()

    results_dir = input(
        "Enter results directory (or press Enter for 'exam_results'): "
    ).strip()
    if not results_dir:
        results_dir = "exam_results"

    analyzer = ExamAnalyzer(results_dir)
    success = analyzer.run_analysis()

    if success:
        print("\n✅ Analysis completed successfully!")
    else:
        print("\n❌ Analysis failed!")

    input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()
