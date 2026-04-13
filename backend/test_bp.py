import asyncio
import json
from services.gemini_service import generate_blueprint

async def main():
    try:
        res = await generate_blueprint('web_app', {})
        print("RESULT:::")
        print(json.dumps(res, indent=2))
    except Exception as e:
        print("ERROR:::", e)

if __name__ == "__main__":
    asyncio.run(main())
