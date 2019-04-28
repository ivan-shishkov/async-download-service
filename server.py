import asyncio
import os.path
import logging
import os
import argparse

from aiohttp import web
import aiofiles

enable_logging = False
enable_response_delay = False
storage_base_path = 'test_photos'


async def archivate(request):
    archive_hash = request.match_info['archive_hash']

    archive_content_path = os.path.join(storage_base_path, archive_hash)

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

            if enable_response_delay:
                await asyncio.sleep(1)

            logging.info(
                f'Sending archive chunk #{chunk_number} '
                f'with size {len(archive_chunk)} bytes ...'
            )
            await response.write(archive_chunk)

            chunk_number += 1

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


def get_command_line_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-l',
        '--logging',
        help='Enables logging',
        action='store_true',
    )
    parser.add_argument(
        '-d',
        '--delay',
        help='Enables delay for send response',
        action='store_true',
    )
    parser.add_argument(
        '-p',
        '--path',
        help='Base path for store',
        type=str,
    )
    return parser.parse_args()


if __name__ == '__main__':
    command_line_arguments = get_command_line_arguments()

    enable_logging = bool(
        command_line_arguments.logging or
        os.getenv('ENABLE_LOGGING') or
        enable_logging
    )
    enable_response_delay = bool(
        command_line_arguments.delay or
        os.getenv('ENABLE_RESPONSE_DELAY') or
        enable_response_delay
    )
    storage_base_path = (
            command_line_arguments.path or
            os.getenv('STORE_BASE_PATH') or
            storage_base_path
    )

    if enable_logging:
        logging.basicConfig(level=logging.INFO)

    app = web.Application()
    app.add_routes([
        web.get('/', handle_index_page),
        web.get('/archive/{archive_hash}/', archivate),
    ])
    web.run_app(app)
