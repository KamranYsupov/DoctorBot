import asyncio

import aiohttp
import aiofiles
#sfrom core import config 


async def get_qr_code(url: str):
    async with aiohttp.ClientSession() as session:
        qr_code_url = 'https://api.qrserver.com/v1/create-qr-code/'#config.QR_CODE_API_GENERATOR_URL
        async with session.get(
            qr_code_url, 
            params={
                'size': '150x150', 
                'data': url
            }
        ) as response:
            if response.status == 200:
                image_data = await response.read()
                async with aiofiles.open('downloaded_image.jpg', 'wb') as file:
                    await file.write(image_data)

            
            
   
asyncio.run(get_qr_code('https://docs.aiohttp.org/en/stable/client_quickstart.html'))