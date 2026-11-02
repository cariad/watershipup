# WatershipUp

`watershipup` is a Python package and command line tool for uploading static websites to [bunny.net] storage zones.

## Requirements

- Python 3.14 or later
- Your own [bunny.net] account

## Installing

```bash
pip install watershipup
```

## Publishing

`watershipup` needs three values:

- The path of the directory to upload.
- The name of the storage zone to upload to.
- The read-write password for that zone.

The directory and zone are passed on the command line, and the password must be set as the `WATERSHIPUP_PASSWORD` environment variable.

```bash
export WATERSHIPUP_PASSWORD="..."
watershipup --zone example-zone site-dir
```

## Exit codes

| Code | Meaning                                          |
| -    | -                                                |
| 0    | The publish succeeded.                           |
| 1    | The publish failed.                              |
| 2    | An argument or the password is missing or wrong. |

[bunny.net]: https://bunny.net
