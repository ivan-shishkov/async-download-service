import asyncio
import os.path
import logging
import os
import sys

from aiohttp import web
import aiofiles
import configargparse


async def archivate(request):
    archive_hash = request.match_info['archive_hash']

    archive_content_path = os.path.join(base_file_storage_path, archive_hash)

    if not os.path.exists(archive_content_path):
        raise web.HTTPNotFound(text='Archive does not exists or was removed')

    response = web.StreamResponse()
    response.headers['Content-Disposition'] = (
        'attachment; filename="archive.zip"'
    )
    await response.prepare(request)

    archiving_process = await asyncio.create_subprocess_shell(
        f'zip - {archive_content_path} -jr',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    chunk_number = 1

    try:
        while True:
            archive_chunk = await archiving_process.stdout.readline()

            if not archive_chunk:
                break

            if enable_response_delay:
                await asyncio.sleep(1)

            logging.info(
                f'Archive {archive_hash}: Sending chunk #{chunk_number} '
                f'with size {len(archive_chunk)} bytes ...'
            )
            await response.write(archive_chunk)

            chunk_number += 1

    except asyncio.CancelledError:
        logging.info(f'Archive {archive_hash}: Cancelled error')
        archiving_process.terminate()
        raise
    finally:
        logging.info(f'Archive {archive_hash}: Force closing')
        response.force_close()

    logging.info(f'Archive {archive_hash}: Transfer finished')

    return response


async def handle_index_page(request):
    async with aiofiles.open('index.html', mode='r') as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type='text/html')


def get_command_line_arguments():
    parser = configargparse.ArgumentParser()

    parser.add_argument(
        '-l',
        '--logging',
        help='logging on/off (0: off, 1: on). Default: 0',
        env_var='ENABLE_LOGGING',
        type=int,
        default=0,
    )
    parser.add_argument(
        '-d',
        '--delay',
        help='delay for sending response on/off (0: off, 1: on). Default: 0',
        env_var='ENABLE_RESPONSE_DELAY',
        type=int,
        default=0,
    )
    parser.add_argument(
        '-p',
        '--path',
        help='a base file storage path. Default: photos',
        env_var='BASE_FILE_STORAGE_PATH',
        type=str,
        default='photos',
    )
    return parser.parse_args()


def run_server():
    app = web.Application()
    app.add_routes([
        web.get('/', handle_index_page),
        web.get('/archive/{archive_hash}/', archivate),
    ])
    web.run_app(app)


if __name__ == '__main__':
    command_line_arguments = get_command_line_arguments()

    enable_logging = bool(command_line_arguments.logging)
    enable_response_delay = bool(command_line_arguments.delay)
    base_file_storage_path = command_line_arguments.path

    if not os.path.exists(base_file_storage_path):
        logging.critical(
            f'Given base file storage path does not exists: '
            f'{base_file_storage_path}',
        )
        sys.exit(1)

    if enable_logging:
        logging.basicConfig(level=logging.INFO)

    run_server()
