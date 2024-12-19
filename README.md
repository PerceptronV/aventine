# ARX ARVENTINUS

<div style="text-align: center;">
    <img src="aventine/static/media/logo.svg" width="200px">
    <p style="font-size: 22px; font-family: serif;">
        THE AVENTINE SOFTWARE
    </p>
</div>

## Installation

## Deployment

Run the following to initialise the Aventine database:
```
flask --app aventine init-db
```

Then run the following to spin up a debug server:
```
flask --app flaskr run --debug
```

For production,

# License

All of my code are licensed under the GNU General Public License 3.0, except for tool binaries in ([tools](aventine/tools/)). See the [README](aventine/tools/README.md) in that directory for attribution.

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
