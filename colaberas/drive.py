"""
Install following packages:

    !pip install tqdm

Usage:
    >>> from google.colab import auth
    >>> auth.authenticate_user()
    >>> from colaberas import download_file
    >>> download_file('https://drive.google.com/open?id=0B0BtCVXdKsWnd5LWcREol0l9mLT', 'photo.jpg')
"""
import io
import pathlib
import urllib.parse

from tqdm import tqdm
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload


def target_file_id(uri):
    """
    Parses shareable Google Drive link to file in google drive.
    :param uri: shareable link fro Google Drive
    :return: file id part of the uri
    """
    uri = urllib.parse.urlparse(uri)
    return urllib.parse.parse_qs(uri.query)['id'][0]


def file_id_from_path(path):
    parent_id = 'root'
    last_parent_id = None
    for path_part in path.parts:
        # expects that all the dirs exist
        last_parent_id = parent_id
        parent_id = find_id(path_part, parent_id)
        if parent_id is None:
            break

    return parent_id, last_parent_id


def find_id(filename, parent_folder_id=None):
    """
    Looks for ID of the file in GDrive. If there are multiple files with that name and parent_folder_id wasn't
    provider, ValueError exeption will be raised.

    :param filename: filename to search for
    :param parent_folder_id: optional id of the parent folder
    :exception ValueError: when multiple files were found
    :return: id of the file found

    Examples

        Search for id of the file 'text.txt' anywhere in the GDrive. Warning: if multiple file with that name exist,
        ValueError exception will be raised.

        >>> find_id('test.txt')

        Search for id of the file 'text.txt' in root directory (a.k.a. My Drive)

        >>> find_id('test.txt', 'root')

        Search for id of the file 'text.txt' in 'subdir' sub directory

        >>> find_id('test.txt', find_id('subdir'))
    """
    page_token = None

    query = "name='{}' and not trashed".format(filename)
    if parent_folder_id is not None:
        query += " and '{}' in parents".format(parent_folder_id)

    drive_service = build('drive', 'v3')
    response = drive_service.files().list(q=query,
                                          spaces='drive',
                                          fields='nextPageToken, files(id, name, parents)',
                                          pageToken=page_token).execute()

    files_found = response.get('files', [])
    if len(files_found) == 0:
        return None
    elif len(files_found) > 1:
        raise ValueError('Multiple \'{}\' files found!'.format(filename))
    else:
        return files_found[0].get('id')


def download_file(remote_path, local_dir, chunksize=1024 ** 2):
    """
    Downloads file from Google Drive
    :param remote_path: shareable link from Google Drive
    :param local_dir: name of the file it will be downloaded to
    :param chunksize: size of the download buffer, 1MB by default
    :return: None
    """
    local = pathlib.Path(local_dir)
    remote = pathlib.Path(remote_path)

    drive_service = build('drive', 'v3')
    fid, _ = file_id_from_path(remote)
    request = drive_service.files().get_media(fileId=fid)

    # https://google.github.io/google-api-python-client/docs/epy/googleapiclient.http.MediaIoBaseDownload-class.html
    if not local.exists() or not local.is_dir():
        local.mkdir(parents=True)

    fh = io.FileIO(str(local / remote.name), mode='wb')
    downloader = MediaIoBaseDownload(fh, request, chunksize=chunksize)

    with tqdm(total=100, ncols=100) as progress_bar:
        last_update = 0
        done = False
        while done is False:
            # _ is a placeholder for a progress object that we ignore.
            # (Our file is small, so we skip reporting progress.)
            status, done = downloader.next_chunk()

            if status:
                new_update = int(status.progress() * 100)
                progress_bar.update(new_update - last_update)
                last_update = new_update


def upload_file(local_path, remote_dir, mimetype='application/octet-stream'):
    local = pathlib.Path(local_path)
    remote = pathlib.Path(remote_dir)

    file_metadata = {
        'name': local.name,
        'mimeType': mimetype,
    }
    media = MediaFileUpload(str(local),
                            mimetype=mimetype,
                            resumable=True)

    drive_service = build('drive', 'v3')

    file_id, parent_id = file_id_from_path(remote / local.name)

    if file_id is not None:
        created = drive_service.files().update(fileId=file_id,
                                               body=file_metadata,
                                               media_body=media,
                                               fields='id').execute()
    else:
        file_metadata['parents'] = [parent_id]
        created = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id').execute()
