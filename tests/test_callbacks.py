from unittest import mock
from unittest.mock import patch
from colaberas.callbacks import ModelCheckpointDriveUpload
from keras.callbacks import ModelCheckpoint

@patch('colaberas.drive.upload_file')
def test_ModelCheckpointDriveUpload_on_epoch_end(upload_file):
    patcher = mock.patch.object(ModelCheckpointDriveUpload, '__bases__', (ModelCheckpoint,))
    with patcher:
        patcher.is_local = True
        obj = ModelCheckpointDriveUpload('test_path_a', 'test_path_b', save_weights_only=True)
        obj.on_epoch_end(123, {'test_key': 'test_value'})
        assert upload_file.called