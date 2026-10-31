from src.services.query_engine import answer_question

questions = [
    "Which customers have outstanding payments?",
    "Which equipment generates the most rental value?",
    "How many active rentals do we have?",
    "Which invoices are overdue?",
    "Show pending quotations",
    "How many equipment assets do we have?",
    "How much money have we collected?"
]

for question in questions:
    result = answer_question(question)

    print("\nQUESTION:", question)
    print("ANSWER:", result["answer"])
    print("SOURCES:", len(result["sources"]))
    print("-" * 60)