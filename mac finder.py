import asyncio
from bleak import BleakScanner

async def find_device():
    name = input().strip().lower()
    devices = await BleakScanner.discover()

    for d in devices:
        if d.name and name in d.name.lower():
            print(d.address)
            return

    print("Not found")

asyncio.run(find_device())