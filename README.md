# wildflowers

An animated wildflower bouquet that grows and blooms in your terminal, with a message that types itself out underneath. One file, no dependencies.

## Run it

```bash
python3 wildflowers.py --to "Sam" --message "you are my favourite"
```

Press `Ctrl+C` to quit.

## Options

| Flag | What it does |
| --- | --- |
| `--to NAME` | Name added to the end of the message |
| `--message TEXT` | Message under the bouquet |
| `--flowers N` | Number of flowers (default 15) |
| `--fps N` | Frames per second (default 24) |
| `--seed N` | Same bouquet every run |
| `--snapshot SECONDS` | Print a single frame at that time and exit |
| `--no-color` | Plain text |

Needs Python 3.8+ and a terminal with 256-colour support. A window of at least 80x30 looks best. Resize it and the bouquet redraws to fit.
