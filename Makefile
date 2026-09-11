PY  ?= python3
SB3  = dist/ClubRoyale.sb3
FAST = build/ClubRoyale_fast.sb3

.PHONY: all deps tables build fast test verify mocks clean

all: build test

## one-time setup
deps:
	$(PY) -m pip install -r requirements.txt
	npm install

## solve the payout tables (cached in build/)
tables:
	cd src && $(PY) tables.py && $(PY) tables2.py && $(PY) tables3.py \
	             && $(PY) tables4.py && $(PY) tables5.py \
	             && $(PY) tables6.py

## real-timing build -> dist/ClubRoyale.sb3   (this is the shippable file)
build:
	cd src && $(PY) build.py

## fast-timing build -> build/ClubRoyale_fast.sb3  (same logic, short waits)
fast:
	cd src && FAST=1 $(PY) build.py

## quick gate: structure + VM load + click-blocking. ~1 minute.
check: build
	$(PY) tests/validate.py $(SB3)
	node tests/load.js $(SB3)
	node tests/overlap.js $(SB3)

## full suite on the fast build. ~10 minutes. Run before every commit.
test: fast
	$(PY) tests/validate.py $(FAST)
	node tests/load.js $(FAST)
	node tests/overlap.js $(FAST)
	node tests/play_blackjack.js $(FAST) 110
	node tests/play_games.js $(FAST) 70
	node tests/play_core.js $(FAST) 50 8 8
	node tests/play_duck.js $(FAST) 60
	node tests/play_crash.js $(FAST) 30
	node tests/play_avia.js $(FAST) 60
	node tests/play_coin.js $(FAST) 40
	node tests/play_dice.js $(FAST) 60
	node tests/boot_race.js $(FAST)

## full suite on the shipped file at real speed. 30+ minutes. Run before release.
verify: build
	$(PY) tests/validate.py $(SB3)
	node tests/load.js $(SB3)
	node tests/overlap.js $(SB3)
	node tests/play_blackjack.js $(SB3) 110
	node tests/play_games.js $(SB3) 50
	node tests/play_core.js $(SB3) 40 6 8
	node tests/play_duck.js $(SB3) 40
	node tests/play_crash.js $(SB3) 20
	node tests/play_avia.js $(SB3) 30
	node tests/play_coin.js $(SB3) 24
	node tests/play_dice.js $(SB3) 40
	node tests/boot_race.js $(SB3)

## render every screen at exact sprite coordinates -> mocks/
mocks: build
	$(PY) tools/mock.py

clean:
	rm -rf build mocks
