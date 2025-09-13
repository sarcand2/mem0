import asyncio
import os
from memory_client import AsyncMemoryClient


async def main():
    client = AsyncMemoryClient(host="http://localhost:8100", token=os.getenv("DAGIO_API_KEY"))
    res = await client.add(messages=[{"role": "user", "content": "Hello async"}], user_id="example-user")
    print("Add =>", res)
    allm = await client.get_all(user_id="example-user")
    print("Get all =>", allm)


if __name__ == "__main__":
    asyncio.run(main())
