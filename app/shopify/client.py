from app.config import settings
import httpx, time, asyncio


class ShopifyApi:
    def __init__(self) -> None:
        self.base = f"https://{settings.shopify_shop}"
        self._token: str | None = None
        self._token_expires_at = 0.0
        self._httpx = httpx.AsyncClient(timeout=30)

    async def get_token(self) -> str:
        if self._token and time.time() < self._token_expires_at - 60:
            return self._token

        resp = await self._httpx.post(
            f"{self.base}/admin/oauth/access_token",
            data={
                "grant_type": "client_credentials",
                "client_id": settings.shopify_client_id,
                "client_secret": settings.shopify_client_secret,
            },
        )
        resp.raise_for_status()
        body = resp.json()
        self._token = body["access_token"]
        self._token_expires_at = time.time() + body["expires_in"]
        return self._token

    async def graphql(self, query: str, variables: dict | None = None) -> dict:
        for attempt in range(5):
            url = f"https://{settings.shopify_shop}/admin/api/{settings.shopify_api_version}/graphql.json"
            resp = await self._httpx.post(
                url,
                json={"query": query, "variables": variables or {}},
                headers={
                    "Content-Type": "application/json",
                    "X-Shopify-Access-Token": await self.get_token(),
                },
            )
            if resp.status_code == 429:
                await asyncio.sleep(2**attempt)
                continue
            resp.raise_for_status()
            body = resp.json()
            errors = body.get("errors") or []
            if any(e.get("extensions", {}).get("code") == "THROTTLED" for e in errors):
                await asyncio.sleep(2**attempt)
                continue
            if errors:
                raise RuntimeError(f"Shopify graphql errors: {errors}")
            return body["data"]
        raise RuntimeError("Shopify kept rate limitting us, giving up...")

    async def close(self) -> None:
        await self._httpx.aclose()


async def main() -> dict:
    shopify = ShopifyApi()
    query = "{ shop { name } }"
    data = await shopify.graphql(query)
    print(data)
    await shopify.close()


if __name__ == "__main__":
    asyncio.run(main())
