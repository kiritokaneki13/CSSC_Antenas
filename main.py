import asyncio
from antena_processor import process_antenna, aggregate_and_upload_antennas
from config import db

async def main():
    while True:
        registered_antennas_ref = db.reference('antenas_registradas')
        antennas_snapshot = await asyncio.get_event_loop().run_in_executor(None, lambda: registered_antennas_ref.get())
        if antennas_snapshot:
            antennas_data = []
            for antenna_id, antenna_data in antennas_snapshot.items():
                if antenna_data.get('activa', False):
                    antenna_info = await process_antenna(antenna_id, antenna_data)
                    antennas_data.append(antenna_info)
            await aggregate_and_upload_antennas(antennas_data)
        await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(main())