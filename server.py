import asyncio
import os.path
import logging

from aiohttp import web
import aiofiles


async def archivate(request):
    store_base_path = 'test_photos'

    archive_hash = request.match_info['archive_hash']

    archive_content_path = os.path.join(store_base_path, archive_hash)

    if not os.path.exists(archive_content_path):
        raise web.HTTPNotFound(text='Archive does not exists or was removed')

    response = web.StreamResponse()
    response.headers['Content-Disposition'] = (
        'attachment; filename="archive.zip"'
    )
    await response.prepare(request)

    archivating_process = await asyncio.create_subprocess_shell(
        f'zip - {archive_content_path} -jr',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    chunk_number = 1

    try:
        while True:
            archive_chunk = await archivating_process.stdout.readline()

            if not archive_chunk:
                break

            logging.info(
                f'Sending archive chunk #{chunk_number} '
                f'with size {len(archive_chunk)} bytes ...'
            )
            await response.write(archive_chunk)

            chunk_number += 1

            await asyncio.sleep(1)

    except asyncio.CancelledError:
        logging.info('Cancelled error')
        archivating_process.terminate()
        raise
    finally:
        logging.info('Force closing')
        response.force_close()

    logging.info('Transfer finished')

    return response


async def handle_index_page(request):
    async with aiofiles.open('index.html', mode='r') as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type='text/html')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    app = web.Application()
    app.add_routes([
        web.get('/', handle_index_page),
        web.get('/archive/{archive_hash}/', archivate),
    ])
    web.run_app(app)
