# tiny-chess-01 entry: capture greedy + piece-square tables, under 4096 bytes
import json, os, sys, urllib.request, urllib.error

ENV_URL = os.environ.get("MAKEFUN_ENV_URL") or sys.exit("MAKEFUN_ENV_URL not set")

VALUE = {"p": 1, "n": 3, "b": 3, "r": 5, "q": 9, "k": 0}
PSQ = {"p": [0, 1, 2, 3, 4, 5, 6, 7], "n": [-1, -1, -1, 0, 0, 1, 1, 1]}
CENTER = {"d4", "d5", "e4", "e5"}


def post(path, body):
    req = urllib.request.Request(
        ENV_URL + path,
        data=json.dumps(body).encode(),
        headers={"content-type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as res:
            return json.load(res)
    except urllib.error.HTTPError as e:
        sys.exit(f"{path}: HTTP {e.code} {e.read().decode(errors='replace')}")


def board_of(fen):
    board = {}
    for i, row in enumerate(fen.split()[0].split("/")):
        file = 0
        for c in row:
            if c.isdigit():
                file += int(c)
            else:
                board["abcdefgh"[file] + str(8 - i)] = c
                file += 1
    return board


def rank(move, board):
    mover = board[move[:2]].lower()
    victim = board.get(move[2:4])
    if victim is None and mover == "p" and move[0] != move[2]:
        victim = "p"
    taken = VALUE.get(victim.lower(), 0) if victim else 0
    promo = VALUE.get(move[4], 0) if len(move) == 5 else 0
    psq = PSQ.get(mover, [0] * 8)[int(move[3]) - 1] if mover in PSQ else 0
    center = 1 if move[2:4] in CENTER else 0
    return (-taken, -promo, VALUE[mover], -psq, -center, move)


def choose(fen, legal):
    board = board_of(fen)
    return min(legal, key=lambda m: rank(m, board))


while True:
    g = post("/game", {})
    if g["status"] == "done":
        break
    while g["status"] == "your_move":
        g = post("/move", {"game": g["game"], "move": choose(g["fen"], g["legal_moves"])})
    print(f"game {g['game']}: {g['outcome']} by {g['reason']}", file=sys.stderr)
print(f"done: {g.get('wins')} won, {g.get('draws')} drawn, {g.get('losses')} lost", file=sys.stderr)
