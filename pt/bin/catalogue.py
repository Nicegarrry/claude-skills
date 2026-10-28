"""Exercise catalogue: canonical name -> pattern, muscles, region, kind, swap factor.

Canonical names follow Strong's and Hevy's style ("Bench Press (Barbell)"). `factor` is the
load relative to the pattern's anchor (factor 1.0), used to carry load across a swap when the
user has no history on the new lift. Dumbbell factors are per hand. Add rows freely: unknown
names are still logged, they just don't count toward weekly sets or get swap suggestions.
"""

MUSCLES = ["chest", "back", "shoulders", "biceps", "triceps",
           "quads", "hamstrings", "glutes", "calves", "core"]
BIG_MUSCLES = ["chest", "back", "shoulders", "quads", "hamstrings", "glutes"]

# kind: weight | bodyweight | assisted | time | cardio | physio | warmup
# Lifts a user must avoid live in their profile.json ("avoid"), not here.
_ROWS = [
    # name, pattern, primary, secondary, region, kind, factor, extra aliases
    ("Bench Press (Barbell)", "horizontal_press", "chest", "triceps shoulders", "upper", "weight", 1.0, "bench, bb bench, barbell bench, flat bench, bench press"),
    ("Bench Press (Dumbbell)", "horizontal_press", "chest", "triceps shoulders", "upper", "weight", 0.38, "db bench, dumbbell bench, db press"),
    ("Chest Press (Machine)", "horizontal_press", "chest", "triceps shoulders", "upper", "weight", 1.0, "machine press, chest press"),
    ("Incline Bench Press (Barbell)", "horizontal_press", "chest", "shoulders triceps", "upper", "weight", 0.85, "incline bench, incline bb"),
    ("Incline Bench Press (Dumbbell)", "horizontal_press", "chest", "shoulders triceps", "upper", "weight", 0.33, "incline db, incline dumbbell"),
    ("Decline Bench Press (Barbell)", "horizontal_press", "chest", "triceps", "upper", "weight", 1.0, "decline bench"),
    ("Push Up", "horizontal_press", "chest", "triceps shoulders", "upper", "bodyweight", 0.0, "pushup, push-up, push ups"),
    ("Chest Dip (Assisted)", "dip", "chest", "triceps", "upper", "assisted", 1.0, "assisted dip, dip"),
    ("Triceps Dip (Assisted)", "dip", "triceps", "chest", "upper", "assisted", 1.0, "assisted tricep dip"),
    ("Bench Dip", "elbow_ext", "triceps", "chest", "upper", "bodyweight", 0.0, ""),
    ("Cable Crossover", "chest_fly", "chest", "", "upper", "weight", 1.0, "crossover, cable fly"),
    ("Chest Fly", "chest_fly", "chest", "", "upper", "weight", 1.0, "pec deck, fly"),
    ("Chest Fly (Dumbbell)", "chest_fly", "chest", "", "upper", "weight", 0.4, "db fly"),
    ("Incline Chest Fly (Dumbbell)", "chest_fly", "chest", "shoulders", "upper", "weight", 0.35, "incline fly"),
    ("Lat Pulldown (Cable)", "vertical_pull", "back", "biceps", "upper", "weight", 1.0, "pulldown, lat pulldown, lat pull, pull down"),
    ("Lat Pulldown - Underhand (Cable)", "vertical_pull", "back", "biceps", "upper", "weight", 1.0, "underhand pulldown, reverse grip pulldown"),
    ("Pull Up", "vertical_pull", "back", "biceps", "upper", "bodyweight", 0.0, "pullup, pull-up"),
    ("Chin Up", "vertical_pull", "back", "biceps", "upper", "bodyweight", 0.0, "chinup, chin-up, chins"),
    ("Pull Up (Assisted)", "vertical_pull", "back", "biceps", "upper", "assisted", 1.0, "assisted pullup, assisted pull up"),
    ("Straight Arm Pull-Down", "vertical_pull", "back", "", "upper", "weight", 0.5, "straight arm pulldown"),
    ("Seated Row (Cable)", "horizontal_pull", "back", "biceps", "upper", "weight", 1.0, "cable row, seated row, row"),
    ("Seated Row (Machine)", "horizontal_pull", "back", "biceps", "upper", "weight", 1.0, "machine row"),
    ("Iso-Lateral Row (Machine)", "horizontal_pull", "back", "biceps", "upper", "weight", 0.9, "iso row"),
    ("Chest Supported Row (Dumbbell)", "horizontal_pull", "back", "biceps", "upper", "weight", 0.4, "chest supported row, cs row, chest-supported row"),
    ("Single Arm Cable Row", "horizontal_pull", "back", "biceps", "upper", "weight", 0.5, "single arm row"),
    ("Bent Over One Arm Row (Dumbbell)", "horizontal_pull", "back", "biceps", "upper", "weight", 0.45, "one arm row, db row"),
    ("Bent Over Row (Barbell)", "horizontal_pull", "back", "biceps", "upper", "weight", 0.9, "barbell row, bb row"),
    ("Bent Over Row (Dumbbell)", "horizontal_pull", "back", "biceps", "upper", "weight", 0.4, ""),
    ("T Bar Row", "horizontal_pull", "back", "biceps", "upper", "weight", 0.8, "tbar row"),
    ("Inverted Row (Bodyweight)", "horizontal_pull", "back", "biceps", "upper", "bodyweight", 0.0, "inverted row"),
    ("Overhead Press (Barbell)", "vertical_press", "shoulders", "triceps", "upper", "weight", 1.0, "ohp, overhead press, military press"),
    ("Pike Push Up", "vertical_press", "shoulders", "triceps", "upper", "bodyweight", 0.0, "pike pushup, pike push-up"),
    ("Overhead Press (Dumbbell)", "vertical_press", "shoulders", "triceps", "upper", "weight", 0.4, "db ohp, db shoulder press"),
    ("Arnold Press (Dumbbell)", "vertical_press", "shoulders", "triceps", "upper", "weight", 0.35, "arnold"),
    ("Shoulder Press (Machine)", "vertical_press", "shoulders", "triceps", "upper", "weight", 1.0, "machine shoulder press"),
    ("Lateral Raise (Dumbbell)", "lateral_raise", "shoulders", "", "upper", "weight", 1.0, "lateral raise, lat raise, side raise"),
    ("Lateral Raise (Cable)", "lateral_raise", "shoulders", "", "upper", "weight", 1.0, "cable lateral"),
    ("Front Raise (Dumbbell)", "lateral_raise", "shoulders", "", "upper", "weight", 1.0, "front raise"),
    ("Upright Row (Cable)", "upright_row", "shoulders", "back", "upper", "weight", 1.0, "upright row"),
    ("Face Pull (Cable)", "rear_delt", "shoulders", "back", "upper", "weight", 1.0, "face pull, facepull"),
    ("Reverse Fly (Cable)", "rear_delt", "shoulders", "back", "upper", "weight", 1.0, "cable reverse fly"),
    ("Reverse Fly (Dumbbell)", "rear_delt", "shoulders", "back", "upper", "weight", 0.5, "reverse fly, rear delt fly"),
    ("Shrug (Dumbbell)", "shrug", "back", "", "upper", "weight", 1.0, "shrug"),
    ("Bicep Curl (Barbell)", "elbow_flex", "biceps", "", "upper", "weight", 1.0, "barbell curl"),
    ("Bicep Curl (Cable)", "elbow_flex", "biceps", "", "upper", "weight", 1.0, "cable curl"),
    ("Bicep Curl (Dumbbell)", "elbow_flex", "biceps", "", "upper", "weight", 0.45, "curl, db curl, bicep curl"),
    ("Hammer Curl (Dumbbell)", "elbow_flex", "biceps", "", "upper", "weight", 0.45, "hammer curl"),
    ("Triceps Extension", "elbow_ext", "triceps", "", "upper", "weight", 1.0, "tricep extension"),
    ("Triceps Extension (Cable)", "elbow_ext", "triceps", "", "upper", "weight", 1.0, "cable tricep extension"),
    ("Triceps Pushdown (Cable - Straight Bar)", "elbow_ext", "triceps", "", "upper", "weight", 1.0, "pushdown, tricep pushdown"),
    ("Overhead Tricep Extension", "elbow_ext", "triceps", "", "upper", "weight", 1.0, "overhead extension"),
    ("Skullcrusher (Dumbbell)", "elbow_ext", "triceps", "", "upper", "weight", 0.5, "skullcrusher"),
    ("Squat (Barbell)", "squat", "quads", "glutes", "lower", "weight", 1.0, "squat, back squat, bb squat"),
    ("Safety Bar Squat", "squat", "quads", "glutes", "lower", "weight", 1.0, "ssb squat, safety squat, ssb"),
    ("Box Squat (Barbell)", "squat", "quads", "glutes", "lower", "weight", 0.95, "box squat"),
    ("Goblet Squat (Kettlebell)", "squat", "quads", "glutes", "lower", "weight", 0.35, "goblet, goblet squat"),
    ("Squat (Bodyweight)", "squat", "quads", "glutes", "lower", "bodyweight", 0.0, "air squat, bodyweight squat, bw squat"),
    ("Squat (Dumbbell)", "squat", "quads", "glutes", "lower", "weight", 0.3, "db squat"),
    ("Leg Press", "squat", "quads", "glutes", "lower", "weight", 2.0, "leg press"),
    ("Seated Leg Press (Machine)", "squat", "quads", "glutes", "lower", "weight", 1.6, "seated leg press"),
    ("Single leg press", "single_leg", "quads", "glutes", "lower", "weight", 0.8, "single leg press"),
    ("Split Squat (Bodyweight)", "single_leg", "quads", "glutes", "lower", "bodyweight", 0.0, "bodyweight split squat, bw split squat"),
    ("Single Leg Box Squat", "single_leg", "quads", "glutes", "lower", "bodyweight", 0.0, "single leg box squat"),
    ("Bulgarian Split Squat", "single_leg", "quads", "glutes", "lower", "weight", 0.25, "bss, split squat, bulgarian"),
    ("Reverse Lunge (Barbell)", "single_leg", "quads", "glutes", "lower", "weight", 0.6, "lunge, reverse lunge, barbell lunge, bb lunge"),
    ("Lunge (Dumbbell)", "single_leg", "quads", "glutes", "lower", "weight", 0.25, "db lunge"),
    ("Walking Lunge", "single_leg", "quads", "glutes", "lower", "weight", 0.25, "walking lunges"),
    ("Leg Extension (Machine)", "knee_ext", "quads", "", "lower", "weight", 1.0, "leg extension, leg ext"),
    ("Reverse Nordic", "knee_ext", "quads", "", "lower", "bodyweight", 0.0, ""),
    ("Romanian Deadlift (Barbell)", "hinge", "hamstrings", "glutes back", "lower", "weight", 1.0, "rdl, romanian deadlift, bb rdl"),
    ("Romanian Deadlift (Dumbbell)", "hinge", "hamstrings", "glutes back", "lower", "weight", 0.4, "db rdl"),
    ("Deadlift (Barbell)", "hinge", "hamstrings", "glutes back", "lower", "weight", 1.3, "deadlift, conventional deadlift"),
    ("Trap Bar Deadlift", "hinge", "hamstrings", "glutes quads", "lower", "weight", 1.3, "trap bar, hex bar"),
    ("Single Leg Rdl", "hinge", "hamstrings", "glutes", "lower", "weight", 0.3, "sl rdl, single leg rdl, single-leg rdl"),
    ("Single Leg Rdl (Bodyweight)", "hinge", "hamstrings", "glutes", "lower", "bodyweight", 0.0, "bodyweight rdl, bw sl rdl"),
    ("Glute Bridge", "hip_ext", "glutes", "hamstrings", "lower", "bodyweight", 0.0, "bridge, glute bridges"),
    ("Hip Thrust (Barbell)", "hip_ext", "glutes", "hamstrings", "lower", "weight", 1.0, "hip thrust"),
    ("Glute Kickback (Machine)", "hip_ext", "glutes", "", "lower", "weight", 0.5, "kickback"),
    ("Hip Abductor (Machine)", "hip_abd", "glutes", "", "lower", "weight", 1.0, "abductor"),
    ("Hip Adductor (Machine)", "hip_add", "quads", "", "lower", "weight", 1.0, "adductor"),
    ("Nordic Curl", "knee_flex", "hamstrings", "", "lower", "bodyweight", 0.0, "nordic, nordics, nordic hamstring curl"),
    ("Lying Leg Curl (Machine)", "knee_flex", "hamstrings", "", "lower", "weight", 1.0, "leg curl, lying leg curl, ham curl, hamstring curl"),
    ("Seated Leg Curl (Machine)", "knee_flex", "hamstrings", "", "lower", "weight", 1.0, "seated leg curl, seated curl"),
    ("Standing Calf Raise (Smith Machine)", "calf", "calves", "", "lower", "weight", 1.0, "smith calf raise, calf raise"),
    ("Standing Calf Raise (Barbell)", "calf", "calves", "", "lower", "weight", 1.0, ""),
    ("Standing Calf Raise (Dumbbell)", "calf", "calves", "", "lower", "weight", 0.4, ""),
    ("Standing Calf Raise (Bodyweight)", "calf", "calves", "", "lower", "bodyweight", 0.0, ""),
    ("Seated Calf Raise (Plate Loaded)", "calf", "calves", "", "lower", "weight", 1.0, "seated calf raise"),
    ("Plank", "core_anti_ext", "core", "", "core", "time", 1.0, ""),
    ("Side Plank", "core_anti_lat", "core", "", "core", "time", 1.0, ""),
    ("Pallof Press", "core_anti_rot", "core", "", "core", "weight", 1.0, "pallof"),
    ("Cable Twist", "core_anti_rot", "core", "", "core", "weight", 1.0, "ab twist"),
    ("Dead Bugs", "core_anti_ext", "core", "", "core", "bodyweight", 0.0, "dead bug, deadbugs, deadbug"),
    ("Bird Dog", "core_anti_ext", "core", "", "core", "bodyweight", 0.0, "bird dogs, tabletop"),
    ("Hanging Leg Raise", "core_flex", "core", "", "core", "bodyweight", 0.0, "leg raise"),
    ("Hanging Knee Raise", "core_flex", "core", "", "core", "bodyweight", 0.0, "knee raise"),
    ("Flat Leg Raise", "core_flex", "core", "", "core", "bodyweight", 0.0, ""),
    ("Bicycle Crunch", "core_flex", "core", "", "core", "bodyweight", 0.0, ""),
    ("V Up", "core_flex", "core", "", "core", "bodyweight", 0.0, ""),
    ("Mountain Climber", "core_flex", "core", "", "core", "bodyweight", 0.0, ""),
    ("Shoulder Taps", "core_anti_rot", "core", "", "core", "bodyweight", 0.0, ""),
    ("Dead Hang", "hang", "back", "", "upper", "time", 1.0, "hang"),
    ("Rowing (Machine)", "cardio", "", "", "cardio", "cardio", 1.0, "rower, erg"),
    ("Bike", "cardio", "", "", "cardio", "cardio", 1.0, "bike, cycle, spin"),
    ("Warmup", "warmup", "", "", "warmup", "warmup", 1.0, "warm up"),
    ("90/90 Hip Switch", "mobility", "", "", "warmup", "warmup", 1.0, "90/90, hip switches"),
    ("Couch Stretch", "mobility", "", "", "warmup", "warmup", 1.0, ""),
    # rehab / physio drills (tracked, not counted as hard sets); add your own
    ("Cat Cow", "physio", "", "", "physio", "physio", 1.0, "cat camel"),
    ("Wall Slide", "physio", "", "", "physio", "physio", 1.0, "wall slides"),
    ("Clamshell", "physio", "", "", "physio", "physio", 1.0, "clamshells, clams"),
]

CATALOGUE = {}
ALIASES = {}


def _key(s):
    return " ".join(s.lower().replace("-", " ").replace("_", " ").split())


for row in _ROWS:
    name, pattern, prim, sec, region, kind, factor, aliases = row
    CATALOGUE[name] = {
        "name": name, "pattern": pattern, "primary": prim.split(), "secondary": sec.split(),
        "region": region, "kind": kind, "factor": factor,
        "dumbbell": any(w in name for w in ("Dumbbell", "Kettlebell")) or name in (
            "Bulgarian Split Squat", "Single Leg Rdl", "Lunge (Dumbbell)", "Walking Lunge"),
    }
    ALIASES[_key(name)] = name
    ALIASES.setdefault(_key(name.split(" (")[0]), name)
    for a in aliases.split(","):
        if a.strip():
            ALIASES[_key(a)] = name

# export oddities (trailing spaces)
ALIASES[_key("Straight Arm Pull-Down ")] = "Straight Arm Pull-Down"
