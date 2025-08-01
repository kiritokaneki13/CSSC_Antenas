import asyncio
import asyncssh

async def get_antenna_data(ip, username, password, command):
    try:
        async with asyncssh.connect(
            ip,
            username=username,
            password=password,
            known_hosts=None  
        ) as conn:
            result = await conn.run(command, check=True)
            return result.stdout
    except Exception as e:
        return None