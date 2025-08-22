def get_feedback_prompt(resume_text: str, round_name: str, qa_pairs: list[dict], scoring_criteria: str = None) -> str:
    """Creates a prompt to generate feedback and scores."""

    if not scoring_criteria:
        scoring_criteria = """
        Score each answer out of 10 based on the following criteria:
        1. Relevance: How well does the answer address the question? (0-3 points)
        2. Clarity: How clear and concise is the answer? (0-2 points)
        3. Detail/Examples: Does the answer provide sufficient detail or examples (like STAR method where applicable)? (0-3 points)
        4. Resume Alignment: How well does the answer align with the candidate's resume? (0-2 points)
        """

    formatted_qa = "\n".join([f"Q: {item['question']}\nA: {item['answer']}" for item in qa_pairs])

    prompt = f"""
    You are an expert interviewer providing feedback on a mock interview.
    The interview was for the '{round_name}' round.
    The candidate's resume is provided below for context.
    Analyze the following question and answer pairs from the interview.

    Resume Context:
    ---
    {resume_text}
    ---

    Interview Questions and Answers:
    ---
    {formatted_qa}
    ---

    Instructions:
    1. Provide overall constructive feedback for the candidate's performance in this round. Focus on strengths and areas for improvement.
    2. Give specific suggestions for improvement based on their answers.
    3. Score each answer individually based on the provided criteria.
    4. Calculate a total score for the round (sum of individual scores).
    5. Format the output clearly, starting with Overall Feedback, then Suggestions, then a list of scores per question, and finally the Total Score.

    Scoring Criteria (per question, max 10 points):
    {scoring_criteria}

    Generate the feedback and scores now:
    """
    return prompt