Google Colab deep learning helpers
===============================

version number: 0.0.1
author: Michal Kosinski

Overview
--------

Google Colab boilerplate to help train deep learning models with Keras

Installation
------------

To install use pip:

```bash
!pip install git+https://github.com/mkos/colaberas
```

Usage
-----

```python
from google.colab import auth
auth.authenticate_user()
from colaberas.drive import download_file
download_file('https://drive.google.com/open?id=0B0BtCVXdKsWnd5LWcREol0l9mLT', 'photo.jpg')
```