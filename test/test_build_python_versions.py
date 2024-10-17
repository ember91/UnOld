import asyncio
from pathlib import Path

import pytest

SUPPORTED_PYTHON_VERSIONS = ('3.9', '3.10', '3.11', '3.12', '3.13')
CONTAINER_MANAGER = 'podman'
OS_BASE_NAME = 'alpine'


@pytest.mark.asyncio
async def test_python_versions() -> None:
    file_paths = list(Path('src/').glob('*.py'))
    mounts = []
    for file_path in file_paths:
        mounts += ['--mount', f'type=bind,source={file_path},destination=/{file_path},readonly']

    process_coroutines = []
    for version in SUPPORTED_PYTHON_VERSIONS:
        image_full_name = f'python:{version}-{OS_BASE_NAME}'
        process_coroutines.append(
            asyncio.create_subprocess_exec(
                CONTAINER_MANAGER,
                'run',
                *mounts,
                image_full_name,
                'python3',
                '-m',
                'py_compile',
                *file_paths,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        )
    processes = await asyncio.gather(*process_coroutines)
    outputs = await asyncio.gather(*[process.communicate() for process in processes])
    stderrs = [output[1].decode() for output in outputs]
    return_codes = [process.returncode for process in processes]

    for python_version, return_code, stderr in zip(SUPPORTED_PYTHON_VERSIONS, return_codes, stderrs, strict=True):
        assert return_code == 0, f'Python{python_version}: Return code {return_code}: {stderr}'
