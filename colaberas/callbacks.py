from keras.callbacks import ModelCheckpoint, CSVLogger
from colaberas.drive import upload_file


class ModelCheckpointDriveUpload(ModelCheckpoint):
    """ Overrides Keras' ModelCheckpoint class to save weights Google Drive as well. """

    def __init__(self, filepath, drive_folder='', **kwargs):
        super().__init__(filepath, **kwargs)
        self.drive_folder = drive_folder
        self.filepath = filepath

    def on_epoch_end(self, epoch, logs=None):
        super().on_epoch_end(epoch, logs)
        upload_file(self.filepath, self.drive_folder)


class CSVLoggerDriveUpload(CSVLogger):
    """ Overrides Keras' CSVLogger class to save weights Google Drive as well. """

    def on_epoch_end(self, epoch, logs=None):
        super().on_epoch_end(epoch, logs)
        upload_file(self.filename)
