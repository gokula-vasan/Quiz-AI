import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.quizmaster
    
    print("--- ALL ATTEMPTS ---")
    async for att in db.attempts.find():
        print(f"Attempt: {att['_id']}")
        for eq in att.get('evaluated_questions', []):
            print(f"  Topic: '{eq.get('topic')}'")
            print(f"  QText: '{eq.get('question_text')}'")
            
    print("\n--- ALL QUIZZES ---")
    async for q in db.quizzes.find():
        print(f"Quiz: {q['_id']}")
        for question in q.get('questions', []):
            print(f"  Topic: '{question.get('topic')}'")
            print(f"  QText: '{question.get('question_text')}'")

if __name__ == "__main__":
    asyncio.run(main())
