import json
import ast
from core.llm_service import generate_completion
from core.audio_io import speak_text, record_audio, transcribe_audio
from core.feedback_generator import generate_feedback_and_scores
from prompts.question_prompts import get_question_generation_prompt

class InterviewAgent:
    def __init__(self, resume_text: str):
        self.resume_text = resume_text
        self.interview_history = [] #
        self.current_round_info = None
        self.feedback = None

    def _generate_questions(self, round_name: str, num_questions: int) -> list[str]:
        """Generates questions for the specified round using LLM."""
        print(f"\nGenerating {num_questions} questions for the {round_name} round based on your resume...")
        prompt = get_question_generation_prompt(self.resume_text, round_name, num_questions)
        raw_response = generate_completion(prompt, max_tokens=300 * num_questions, temperature=0.6) # Allow more tokens

        # Try to parse the response as a Python list
        try:
            # Clean potential markdown/fences
            raw_response = raw_response.strip().strip('```python').strip('```').strip()
            questions = ast.literal_eval(raw_response) # Safer than eval
            if isinstance(questions, list) and all(isinstance(q, str) for q in questions):
                 # Ensure we have the correct number, truncate or pad if necessary (though LLM should follow instructions)
                if len(questions) > num_questions:
                    print(f"Warning: LLM generated {len(questions)} questions, expected {num_questions}. Using the first {num_questions}.")
                    questions = questions[:num_questions]
                elif len(questions) < num_questions:
                     print(f"Warning: LLM generated only {len(questions)} questions, expected {num_questions}.")
                     # Could try generating more, or just proceed
                
                print("Questions generated successfully.")
                return questions
            else:
                raise ValueError("Parsed result is not a list of strings.")
        except (SyntaxError, ValueError, TypeError) as e:
            print(f"Error parsing questions from LLM response: {e}")
            print(f"Raw response was: {raw_response}")
            # Fallback: Try splitting by newline if list parsing fails and response looks like lines of questions
            lines = [line.strip() for line in raw_response.split('\n') if line.strip()]
            if lines and len(lines) >= num_questions // 2: # Heuristic: if we got at least half the questions as lines
                print("Falling back to line splitting for questions.")
                return lines[:num_questions]
            else:
                print("Could not generate questions properly. Using generic questions.")
                # Generic fallback questions
                return [
                    f"Tell me about your experience relevant to the {round_name} role based on your resume.",
                    "What is your biggest strength related to this area?",
                    "Can you describe a challenge you faced and how you overcame it?",
                    "Where do you see yourself in 5 years?",
                    "Do you have any questions for me?" # Always good to include
                ][:num_questions]


    def conduct_round(self, round_info: dict):
        """Conducts a single round of the interview."""
        self.current_round_info = round_info
        round_name = round_info['name']
        num_questions = round_info['num_questions']
        self.interview_history = [] # Reset history for the new round

        print(f"\n--- Starting {round_name} Round ---")
        speak_text(f"Welcome to the {round_name} round. I will ask you {num_questions} questions based on your resume. Please answer clearly after I finish speaking.")

        questions = self._generate_questions(round_name, num_questions)

        for i, question in enumerate(questions):
            print(f"\nQuestion {i+1}/{len(questions)}:")
            speak_text(question)

            # Record user's response
            # Adjust duration based on question length? Or use a longer default?
            record_duration = 30 # Let's give 30 seconds per answer initially
            audio_file = record_audio(duration=record_duration)

            answer = None
            if audio_file:
                answer = transcribe_audio(audio_file)

            if not answer:
                speak_text("I didn't catch that. Let's move to the next question.")
                answer = "[No response recorded]" # Mark as no response

            self.interview_history.append({"question": question, "answer": answer})

        print(f"\n--- {round_name} Round Complete ---")
        speak_text("Thank you. That concludes the questions for this round.")

        # Generate feedback for the completed round
        self.feedback = generate_feedback_and_scores(
            self.resume_text, round_name, self.interview_history
        )

    def display_feedback(self):
        """Prints the generated feedback and scores."""
        if not self.feedback:
            print("\nNo feedback available.")
            return

        print("\n--- Interview Feedback ---")
        print(f"\nRound: {self.current_round_info['name']}")

        print("\n[ Overall Feedback ]")
        print(self.feedback.get("overall_feedback", "N/A"))

        print("\n[ Suggestions for Improvement ]")
        print(self.feedback.get("suggestions", "N/A"))

        print("\n[ Scores per Question ]")
        scores = self.feedback.get("scores_per_question", [])
        if scores and len(scores) == len(self.interview_history):
            for i, score in enumerate(scores):
                print(f"  Q{i+1}: {score}/10")
        elif scores:
             print(f"  (Raw scores: {scores} - Mismatch in count, check 'raw_output')") # Show if count mismatch
        else:
             print("  Scores not available or parsing failed.")


        print(f"\n[ Total Score for Round ]")
        print(f"  {self.feedback.get('total_score', 'N/A')} / {len(self.interview_history) * 10 if self.interview_history else 'N/A'}")

        # Optionally print raw output for debugging
        # print("\n[ Raw LLM Feedback Output (for debugging) ]")
        # print(self.feedback.get("raw_output", "N/A"))

    def get_total_score(self) -> int | None:
        """Returns the total score for the last completed round."""
        if self.feedback:
            return self.feedback.get("total_score")
        return None