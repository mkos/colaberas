from unittest import mock
from unittest.mock import call
from colaberas.drive import file_id_from_path, upload_file, download_file
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


def media_five_upload_side_effect(path, *args, **kwargs):
    if path != 'local/something/file.txt':
        raise FileNotFoundError()


@mock.patch('colaberas.drive.find_id', side_effect=patch_find_id)
def test_file_id_from_path(find_id):
    file_id, parent_id = file_id_from_path(pathlib.Path('test/path/file.txt'))

    find_id.assert_has_calls([call('test', 'root'), call('path', 123), call('file.txt', 345)])
    assert file_id == 567
    assert parent_id == 345


@mock.patch('colaberas.drive.find_id', side_effect=patch_find_id)
def test_file_id_from_path_bad_path(find_id):
    file_id, parent_id = file_id_from_path(pathlib.Path('test/bad_path/path/file.txt'))

    find_id.assert_has_calls([call('test', 'root'), call('bad_path', 123)])
    assert file_id is None
    assert parent_id is None


@mock.patch('colaberas.drive.find_id', side_effect=patch_find_id)
def test_file_id_from_path_file_does_not_exit(find_id):
    file_id, parent_id = file_id_from_path(pathlib.Path('test/path/other_file.txt'))

    find_id.assert_has_calls([call('test', 'root'), call('path', 123), call('other_file.txt', 345)])
    assert file_id is None
    assert parent_id == 345


@mock.patch('colaberas.drive.find_id', side_effect=patch_find_id)
def test_file_id_from_path_file_does_not_exit_short_path(find_id):
    file_id, parent_id = file_id_from_path(pathlib.Path('test/other_file.txt'))

    find_id.assert_has_calls([call('test', 'root'), call('other_file.txt', 123)])
    assert file_id is None
    assert parent_id == 123


@mock.patch('colaberas.drive.find_id', side_effect=patch_find_id)
def test_file_id_from_path_file_does_not_exit_short_path(find_id):
    file_id, parent_id = file_id_from_path(pathlib.Path('test/bad_path/file.txt'))

    find_id.assert_has_calls([call('test', 'root'), call('bad_path', 123)])
    assert file_id is None
    assert parent_id is None


@mock.patch('colaberas.drive.file_id_from_path')
@mock.patch('colaberas.drive.MediaFileUpload', side_effect=media_five_upload_side_effect)
@mock.patch('colaberas.drive.build')
@pytest.mark.parametrize('local_path,gdrive_path,fifp_retval,result', [
    ('local/something/file.txt', 'test/path/', (567, 345), 'update'),
    ('local/something/file.txt', 'test/path', (567, 345), 'update'),
    ('local/something/file.txt', 'test/path/othername.txt', (567, 345), 'update'),
    ('local/something/file.txt', 'test/new_path/', (None, 345), 'create'),
    ('local/something/file.txt', 'test/new_path/another_new/', (None, None), None),
    ('local/bad_local/file.txt', 'test/new_path/another_new/', (None, None), None)
])
def test_upload_file(build_mock, media_file_upload_mock, file_id_from_path_mock, local_path, gdrive_path, fifp_retval, result):
    file_id_from_path_mock.return_value = fifp_retval
    gdrive_file = pathlib.Path(gdrive_path) / 'file.txt'

    if result is None:
        with pytest.raises(ValueError):
            upload_file(local_path, gdrive_path, mimetype='application/octet-stream')
    else:
        upload_file(local_path, gdrive_path, mimetype='application/octet-stream')

        build_mock.return_value.files.assert_called_once()
        media_file_upload_mock.assert_called_with(local_path, mimetype='application/octet-stream', resumable=True)
        file_id_from_path_mock.assert_called_with(gdrive_file)
        build_mock.assert_called_with('drive', 'v3')

    if result == 'create':
        file_metadata = {
            'name': 'file.txt',
            'mimeType': mock.ANY,
            'parents': [345]
        }

        (build_mock.return_value
         .files.return_value
         .create
         .assert_called_once_with(body=file_metadata,
                                  media_body=mock.ANY,
                                  fields=mock.ANY)
         )
        build_mock.return_value.files.return_value.update.assert_not_called()

    elif result == 'update':
        file_metadata = {
            'name': 'file.txt',
            'mimeType': mock.ANY,
        }
        build_mock.return_value.files.return_value.create.assert_not_called()
        (build_mock.return_value
         .files.return_value
         .update
         .assert_called_once_with(fileId=567,
                                  body=file_metadata,
                                  media_body=mock.ANY,
                                  fields=mock.ANY)
         )

    else:
        build_mock.return_value.files.return_value.create.assert_not_called()
        build_mock.return_value.files.return_value.update.assert_not_called()


@mock.patch('colaberas.drive.tqdm')
@mock.patch('colaberas.drive.MediaIoBaseDownload')
@mock.patch('colaberas.drive.file_id_from_path')
@mock.patch('colaberas.drive.build')
@pytest.mark.parametrize('gdrive_path,local_path,result', [
    ('test/path/file.txt', 'local/something/', None),
])
def test_download_file(build_mock, file_id_from_path_mock, media_id_file_dl_mock, tqdm_mock, gdrive_path, local_path, result):
    file_id_from_path_mock.return_value = (567, None)
    download_file(gdrive_path, local_path)
    build_mock.assert_called_with('drive', 'v3')
    build_mock.return_value.files.return_value.get_media.assert_called_once_with(fileId=567)