import asyncio
import os.path
import logging
import os
import sys
from functools import partial

from aiohttp import web
import aiofiles
import configargparse


async def archivate(request, base_file_storage_path, enable_response_delay):
    archive_hash = request.match_info['archive_hash']

    archive_info_message = f'Archive {archive_hash}'

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
                f'{archive_info_message}: Sending chunk #{chunk_number} '
                f'with size {len(archive_chunk)} bytes ...'
            )
            await response.write(archive_chunk)

            chunk_number += 1

    except asyncio.CancelledError:
        logging.info(f'{archive_info_message}: Cancelled error')
        archiving_process.terminate()
        raise

    finally:
        logging.info(f'{archive_info_message}: Force closing')
        response.force_close()

    logging.info(f'{archive_info_message}: Transfer finished')

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
        choices=[0, 1],
        default=0,
    )
    parser.add_argument(
        '-d',
        '--delay',
        help='delay for sending response on/off (0: off, 1: on). Default: 0',
        env_var='ENABLE_RESPONSE_DELAY',
        type=int,
        choices=[0, 1],
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


def main():
    command_line_arguments = get_command_line_arguments()

    if not os.path.exists(command_line_arguments.path):
        logging.critical(
            f'Given base file storage path does not exists: '
            f'{command_line_arguments.path}',
        )
        sys.exit(1)

    if command_line_arguments.logging:
        logging.basicConfig(level=logging.INFO)

    app = web.Application()
    app.add_routes([
        web.get(
            path='/',
            handler=handle_index_page,
        ),
        web.get(
            path='/archive/{archive_hash}/',
            handler=partial(
                archivate,
                base_file_storage_path=command_line_arguments.path,
                enable_response_delay=command_line_arguments.delay,
            ),
        ),
    ])
    web.run_app(app)


if __name__ == '__main__':
    main()
