import time
import sys
import random

def type_text(text, base_delay=0.08, variation=0.04):
    """Simulate realistic typing with slight variations in speed"""
    for char in text:
        # Add realistic pauses for punctuation and thinking
        if char in '.,!?':
            delay = base_delay + random.uniform(0.2, 0.5)
        elif char in ':;':
            delay = base_delay + random.uniform(0.1, 0.3)
        elif char == '\n':
            delay = base_delay + random.uniform(0.3, 0.7)
        elif char == ' ':
            delay = base_delay + random.uniform(0, 0.1)
        elif char in '()[]{}':
            delay = base_delay + random.uniform(0.05, 0.15)
        else:
            delay = base_delay + random.uniform(-variation, variation)
        
        # Ensure delay is never negative
        delay = max(0.02, delay)
        
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)

def simulate_thinking_pause(duration=2.0):
    """Simulate a natural pause while thinking"""
    time.sleep(duration)

# Start typing immediately
requirements_text = """I want to create a multiple choice Exam Bot to take a multiple choice exam for me. This is not cheating - this is just a test to see if I can do it. The exams are just for fun and don't count towards anything.

The exams are accessed through here https://example.com/app/courses/ and then it will have a long connection string at the end of the URL for each exam.

Here is how I think the Bot should approach taking the exam:

1. The number of questions will vary per exam.
2. The Bot should select A for each question to start
3. It will then click "Grade My Exam!" at the end
4. A score will be presented.
5. The Bot will then click B for the first question only and then continue selecting A for the rest of the questions.
   a. If the grade goes down then A was the correct question for the first question
   b. If the grade stays the same then Both A and B were incorrect for the first question and the Bot should then select C to see if that is the correct answer
   c. If the grade goes Up then B is the correct answer for question A
6. The Bot should continue this process focusing on the first question, with all other questions set to "A" until the grade goes up.
7. When the grade goes up the Bot should continue to question B and repeat the process.

So, to summarize the bot will:
1. Click A for all answers
2. Click Grade My Exam!
3. Review the results
4. The passing grade is 70%
5. Change the answer for A to B with the rest being A.
6. Use the logic explained above to determine what to choose for question A
7. Continue with the logic until the Bot achieves a passing grade of 70%
8. When the exam is passed the Bot should wait for the next exam to be loaded"""

# Type the requirements
type_text(requirements_text, base_delay=0.07, variation=0.03)

# Add a thinking pause
simulate_thinking_pause(3)

# Continue with next part
next_part = """

Now let me think about the implementation approach...

I'll need to use:
- Selenium WebDriver for browser automation
- Python for the logic
- Some way to track the scores and determine the correct answers

Let me start coding this step by step."""

type_text(next_part, base_delay=0.06, variation=0.02)
