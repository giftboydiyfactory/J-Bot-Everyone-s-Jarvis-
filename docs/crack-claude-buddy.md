# Crack Claude Code Buddy

Get any buddy you want (legendary shiny dragon, etc.) by brute-forcing a UUID that hashes to your desired traits.

**Tested on:** Claude Code 2.1.89 (April 2026)
**Requires:** [Bun](https://bun.sh) runtime (for native wyhash)
**Time:** < 1 second for most combinations

## How It Works

Claude Code's buddy system is deterministic:

```
oauthAccount.accountUuid + "friend-2026-401"
    -> Bun.hash (wyhash, truncated to uint32)
    -> SplitMix32 PRNG
    -> rarity, species, eye, hat, shiny, stats
```

Key discovery: the algorithm reads `oauthAccount.accountUuid` first (not `userID`). The buddy is a pure function of this UUID — same UUID always produces the same buddy.

### Trait odds

| Rarity | Weight | Approx Odds |
|--------|--------|-------------|
| Common | 60 | 60% |
| Uncommon | 25 | 25% |
| Rare | 10 | 10% |
| Epic | 4 | 4% |
| Legendary | 1 | 1% |

**Shiny**: 1% independent of rarity. **Legendary + Shiny**: ~1/18,000. **Legendary + Shiny + specific species**: ~1/180,000.

### Available traits

- **Species**: duck, goose, blob, cat, dragon, octopus, owl, penguin, turtle, snail, ghost, axolotl, capybara, cactus, robot, rabbit, mushroom, chonk
- **Eyes**: `·` `✦` `×` `◉` `@` `°`
- **Hats** (non-common only): crown, tophat, propeller, halo, wizard, beanie, tinyduck
- **Stats**: DEBUGGING, PATIENCE, CHAOS, WISDOM, SNARK (budget scales with rarity)

---

## Step 1: Install Bun

```bash
curl -fsSL https://bun.sh/install | bash
export BUN_INSTALL="$HOME/.bun"
export PATH="$BUN_INSTALL/bin:$PATH"
```

## Step 2: Create the crack script

Save as `crack_buddy.js`:

```javascript
// Claude Code Buddy Cracker
// Algorithm extracted from Claude Code 2.1.89 binary
//
// Usage: bun run crack_buddy.js
// Edit TARGET below to customize what you want.

// ── What do you want? ──────────────────────────────────────────
const TARGET = {
  rarity: "legendary",   // common | uncommon | rare | epic | legendary
  species: "dragon",     // duck | goose | blob | cat | dragon | octopus | owl |
                         // penguin | turtle | snail | ghost | axolotl | capybara |
                         // cactus | robot | rabbit | mushroom | chonk
  shiny: true,           // true | false | null (null = don't care)
};
const MAX_RESULTS = 3;
// ────────────────────────────────────────────────────────────────

const RARITY_WEIGHTS = { common: 60, uncommon: 25, rare: 10, epic: 4, legendary: 1 };
const RARITIES = ["common", "uncommon", "rare", "epic", "legendary"];
const SPECIES = [
  "duck","goose","blob","cat","dragon","octopus","owl","penguin",
  "turtle","snail","ghost","axolotl","capybara","cactus","robot",
  "rabbit","mushroom","chonk",
];
const EYES = ["·","✦","×","◉","@","°"];
const HATS = ["none","crown","tophat","propeller","halo","wizard","beanie","tinyduck"];
const STATS = ["DEBUGGING","PATIENCE","CHAOS","WISDOM","SNARK"];
const STAT_BUDGET = { common: 5, uncommon: 15, rare: 25, epic: 35, legendary: 50 };
const SALT = "friend-2026-401";

function splitmix32(seed) {
  let s = seed >>> 0;
  return function () {
    s |= 0;
    s = (s + 1831565813) | 0;
    let t = Math.imul(s ^ (s >>> 15), 1 | s);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function pick(rng, arr) {
  return arr[Math.floor(rng() * arr.length)];
}

function getRarity(rng) {
  const total = Object.values(RARITY_WEIGHTS).reduce((a, b) => a + b, 0);
  let r = rng() * total;
  for (const k of RARITIES) {
    r -= RARITY_WEIGHTS[k];
    if (r < 0) return k;
  }
  return "common";
}

function getStats(rng, rarity) {
  const budget = STAT_BUDGET[rarity];
  const primary = pick(rng, STATS);
  let secondary = pick(rng, STATS);
  while (secondary === primary) secondary = pick(rng, STATS);
  const result = {};
  for (const s of STATS) {
    if (s === primary) result[s] = Math.min(100, budget + 50 + Math.floor(rng() * 30));
    else if (s === secondary) result[s] = Math.max(1, budget - 10 + Math.floor(rng() * 15));
    else result[s] = budget + Math.floor(rng() * 40);
  }
  return result;
}

function hatch(input) {
  const key = input + SALT;
  const hash = Number(BigInt(Bun.hash(key)) & 0xffffffffn);
  const rng = splitmix32(hash);
  const rarity = getRarity(rng);
  const species = pick(rng, SPECIES);
  const eye = pick(rng, EYES);
  const hat = rarity === "common" ? "none" : pick(rng, HATS);
  const shiny = rng() < 0.01;
  const stats = getStats(rng, rarity);
  return { rarity, species, eye, hat, shiny, stats };
}

function randomUUID() {
  const h = "0123456789abcdef";
  let s = "";
  for (let i = 0; i < 36; i++) {
    if (i === 8 || i === 13 || i === 18 || i === 23) s += "-";
    else if (i === 14) s += "4";
    else s += h[Math.floor(Math.random() * 16)];
  }
  return s;
}

function matches(result) {
  if (TARGET.rarity && result.rarity !== TARGET.rarity) return false;
  if (TARGET.species && result.species !== TARGET.species) return false;
  if (TARGET.shiny !== null && TARGET.shiny !== undefined && result.shiny !== TARGET.shiny) return false;
  return true;
}

function formatStats(stats) {
  return STATS.map((s) => {
    const v = stats[s];
    const bar = "█".repeat(Math.round(v / 10)) + "░".repeat(10 - Math.round(v / 10));
    return `  ${s.padEnd(11)} ${bar} ${v}`;
  }).join("\n");
}

function printResult(uuid, result, index, attempts) {
  const stars = { common: "★", uncommon: "★★", rare: "★★★", epic: "★★★★", legendary: "★★★★★" };
  console.log(`\n━━━ Result #${index} (found in ${attempts.toLocaleString()} attempts) ━━━`);
  console.log(`  ${stars[result.rarity]} ${result.rarity.toUpperCase()}  ${result.species.toUpperCase()}`);
  console.log(`  Eye: ${result.eye}  Hat: ${result.hat}${result.shiny ? "  ✨ SHINY ✨" : ""}`);
  console.log(formatStats(result.stats));
  console.log(`\n  accountUuid: ${uuid}`);
}

// ── Main ───────────────────────────────────────────────────────
const desc = [TARGET.rarity, TARGET.shiny ? "shiny" : null, TARGET.species].filter(Boolean).join(" ");
console.log(`Cracking: ${desc}`);
console.log("Searching...\n");

let found = 0;
const maxAttempts = 50_000_000;

for (let i = 0; i < maxAttempts; i++) {
  const uuid = randomUUID();
  const result = hatch(uuid);
  if (matches(result)) {
    found++;
    printResult(uuid, result, found, i + 1);
    if (found >= MAX_RESULTS) break;
  }
}

if (found === 0) {
  console.log(`Not found in ${maxAttempts.toLocaleString()} attempts. Try again or relax criteria.`);
} else {
  console.log("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
  console.log("Apply: see Step 3 below");
}
```

## Step 3: Run the cracker

```bash
bun run crack_buddy.js
```

Output example:
```
Cracking: legendary shiny dragon
Searching...

━━━ Result #1 (found in 107,885 attempts) ━━━
  ★★★★★ LEGENDARY  DRAGON
  Eye: ◉  Hat: crown  ✨ SHINY ✨
  DEBUGGING   ██████████ 100
  PATIENCE    ████░░░░░░  45
  CHAOS       █████░░░░░  52
  WISDOM      ██████░░░░  61
  SNARK       █████░░░░░  53

  accountUuid: 2b790e9b-ddcd-4d39-108d-c860e61d36ab
```

## Step 4: Apply the cracked UUID

Edit `~/.claude.json` (NOT `~/.claude/.claude.json`):

```bash
# Backup first
cp ~/.claude.json ~/.claude.json.bak

# Apply — replace UUID and delete companion
python3 -c "
import json, pathlib, shutil
p = pathlib.Path.home() / '.claude.json'
d = json.loads(p.read_text())
d['oauthAccount']['accountUuid'] = 'PASTE_YOUR_UUID_HERE'
d.pop('companion', None)
p.write_text(json.dumps(d, indent=2))
print('Done! Restart Claude Code and run /buddy')
"
```

Or manually:
1. Open `~/.claude.json`
2. Find `"oauthAccount"` -> `"accountUuid"` and replace the value
3. Delete the entire `"companion": { ... }` block
4. Save

## Step 5: Hatch your new buddy

1. **Restart Claude Code** (exit and reopen)
2. Run `/buddy`
3. Your new buddy appears with the cracked traits

> **Note:** The name and personality are generated by an LLM call during hatching, so they will be unique each time. Species, rarity, stats, shiny, hat, and eyes are deterministic from the UUID.

---

## Customizing the target

Edit the `TARGET` object in `crack_buddy.js`:

```javascript
// Legendary shiny capybara
const TARGET = { rarity: "legendary", species: "capybara", shiny: true };

// Any epic ghost (shiny or not)
const TARGET = { rarity: "epic", species: "ghost", shiny: null };

// Legendary anything (fast — ~1/100 odds)
const TARGET = { rarity: "legendary", species: null, shiny: null };
```

## Restoring your original buddy

```bash
cp ~/.claude.json.bak ~/.claude.json
```

Restart Claude Code and run `/buddy`.

---

## Appendix: Algorithm details

Extracted from Claude Code 2.1.89 binary at offset `109742322`:

```
vE8() = oauthAccount.accountUuid ?? userID ?? "anon"
key   = vE8() + "friend-2026-401"
hash  = uint32(Bun.hash(key))   // wyhash truncated to 32-bit
rng   = SplitMix32(hash)

rarity  = weightedPick(rng, {common:60, uncommon:25, rare:10, epic:4, legendary:1})
species = pick(rng, 18 species)
eye     = pick(rng, 6 eyes)
hat     = rarity=="common" ? "none" : pick(rng, 8 hats)
shiny   = rng() < 0.01
stats   = allocate(rng, budget[rarity])  // primary stat gets +50, secondary gets -10
```

The `userID` fallback in `~/.claude.json` is only used when `oauthAccount` is absent. For OAuth-authenticated users (most setups), you must change `oauthAccount.accountUuid`.
