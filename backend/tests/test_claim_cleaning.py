import pytest
from llm_client import clean_claim_text


def test_clean_claim_text_removes_generated_claim_prefix():
    raw = 'The generated claim is: "College food eliminates the need for dishwashing and kitchen cleanup, making it a more convenient option for students."'
    cleaned = clean_claim_text(raw)
    assert cleaned == "College food eliminates the need for dishwashing and kitchen cleanup, making it a more convenient option for students."


def test_clean_claim_text_removes_final_answer_prefix():
    raw = 'The final answer is:\n\n"Students who cook at home develop essential life skills, such as meal planning, cooking techniques, and time management."'
    cleaned = clean_claim_text(raw)
    assert cleaned == "Students who cook at home develop essential life skills, such as meal planning, cooking techniques, and time management."


def test_clean_claim_text_removes_here_is_the_claim_prefix():
    raw = "Here is the claim: Dayscholars commuting from home enjoy a supportive family environment."
    cleaned = clean_claim_text(raw)
    assert cleaned == "Dayscholars commuting from home enjoy a supportive family environment."


def test_clean_claim_text_removes_agent_prefix_and_quotes():
    raw = '"Agent A: Living in a hostel fosters self-reliance."'
    cleaned = clean_claim_text(raw)
    assert cleaned == "Living in a hostel fosters self-reliance."


def test_clean_claim_text_preserves_clean_claim():
    raw = "Home-cooked food provides superior nutritional balance and hygiene compared to large-scale mess catering."
    cleaned = clean_claim_text(raw)
    assert cleaned == raw
