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
import urllib.parse

from tqdm import tqdm
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload


def target_file_id(uri):
    """
    Parses shareable Google Drive link to file in google drive.
    :param uri: shareable link fro Google Drive
    :return: file id part of the uri
    """
    uri = urllib.parse.urlparse(uri)
    return urllib.parse.parse_qs(uri.query)['id'][0]


def download_file(file_uri, local_name, chunksize=1024 ** 2):
    """
    Downloads file from Google Drive
    :param file_uri: shareable link from Google Drive
    :param local_name: name of the file it will be downloaded to
    :param chunksize: size of the download buffer, 1MB by default
    :return: None
    """
    drive_service = build('drive', 'v3')
    file_id = target_file_id(file_uri)
    request = drive_service.files().get_media(fileId=file_id)

    # https://google.github.io/google-api-python-client/docs/epy/googleapiclient.http.MediaIoBaseDownload-class.html
    fh = io.FileIO(local_name, mode='wb')
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
