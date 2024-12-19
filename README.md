# ARX ARVENTINUS

<div style="text-align: center;">
    <img src="aventine/static/media/logo.svg" width="200px">
    <p style="font-size: 22px; font-family: serif;">
        THE AVENTINE SOFTWARE
    </p>
</div>

## Installation

First ensure that you have an isolated Python environment set up (we encourage using [mamba](https://mamba.readthedocs.io/en/latest/) to manage environments). Aventine has been tested to work with Python 3.11.11.

1. First run the following to clone and install Aventine:
    ```bash
    git clone https://PerceptronV/aventine
    cd aventine
    pip install -e .
    ```

2. Run the onboarding script to use pre-indexed data provided by the authors of Aventine. It is IMPORTANT that you run this command in the root directory of the repository; i.e. where you installed Aventine from.
    ```bash
    aventine-download
    ```

3. Extract the [relevant binaries](./aventine/tools/dist/) of Whitaker's Words for your operating system into [`aventine/tools/bin`](./aventine/tools/bin/).

## Deployment

Run the following to initialise the Aventine database:
```
flask --app aventine init-db
```

Then run the following to spin up a debug server:
```
flask --app flaskr run --debug
```

For production, set a private key.

# License

All of my code are licensed under the GNU General Public License 3.0, except for tool binaries in ([tools](./aventine/tools/)). See the [README](./aventine/tools/README.md) in that directory for attribution.

```
Aventine: Vector search for classical Latin texts.
Copyright (C) 2024  Yiding Song

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
```
