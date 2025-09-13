import os
from memory_client import MemoryClient


def main():
    client = MemoryClient(host="http://localhost:8100", token=os.getenv("DAGIO_API_KEY"))
    res = client.add(messages=[{"role": "user", "content": "Hello from example"}], user_id="example-user")
    print("Add =>", res)
    allm = client.get_all(user_id="example-user")
    print("Get all =>", allm)


if __name__ == "__main__":
    main()
