import os
import httpx
from dotenv import load_dotenv

load_dotenv()


async def login_with_credentials(email: str, password: str) -> str:
    base_url = os.environ["MERCHANT_API_URL"].rstrip("/")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{base_url}/auth/login",
            json={
                "email": email,
                "password": password,
            },
        )

        response.raise_for_status()

        data = response.json()
        return data["access_token"]
