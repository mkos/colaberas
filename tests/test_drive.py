from unittest import mock
from unittest.mock import call
from colaberas.drive import file_id_from_path, upload_file
import pathlib
import pytest


def patch_find_id(filename, *args, **kwargs):
    parent_id = args[0]
    if filename == 'test' and parent_id == 'root':
        return 123
    if filename == 'path' and parent_id == 123:
        return 345
    if filename == 'file.txt' and parent_id == 345:
        return 567
    return None


@mock.patch('colaberas.drive.find_id', side_effect=patch_find_id)
def test_file_id_from_path(find_id):
    file_id, parent_id = file_id_from_path(pathlib.Path('test/path/file.txt'))

    find_id.assert_has_calls([call('test', 'root'), call('path', 123), call('file.txt', 345)])
    assert file_id == 567
    assert parent_id == 345


@mock.patch('colaberas.drive.find_id', side_effect=patch_find_id)
def test_file_id_from_path_bad_path(find_id):
    file_id, parent_id = file_id_from_path(pathlib.Path('test/bad_path/file.txt'))

    find_id.assert_has_calls([call('test', 'root'), call('bad_path', 123)])
    assert file_id is None
    assert parent_id == 123


@mock.patch('colaberas.drive.file_id_from_path', return_value=(None, None))
@mock.patch('colaberas.drive.MediaFileUpload')
@mock.patch('colaberas.drive.build')
@pytest.mark.parametrize('local_path,gdrive_path, result', [
    ('local/file/path.txt', 'test/path/', None),
    # ('local/file/path.txt', 'test/path/file.txt', None)
])
def test_upload_file(build_mock, media_file_upload_mock, file_id_from_path_mock, local_path, gdrive_path, result):
    upload_file(local_path, gdrive_path, mimetype='application/octet-stream')

    media_file_upload_mock.assert_called_with(local_path, mimetype='application/octet-stream', resumable=True)
    file_id_from_path_mock.assert_called_with(pathlib.Path(gdrive_path) / 'path.txt')
    build_mock.assert_called_with('drive', 'v3')

    build_mock.return_value.files.assert_called_once()
    build_mock.return_value.files.return_value.create.assert_called_once()