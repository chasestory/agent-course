"""Helpers for authoring course content in Python and emitting JSON.
The JSON in content/ is the source of truth the app reads; these scripts
are just a convenient way to (re)generate it. Editing the JSON directly is fine too."""
import json, textwrap, random, hashlib

def M(id, title, summary, lesson, links, quiz):
    lines = textwrap.dedent(lesson).strip("\n").split("\n")
    return {
        "id": id,
        "title": title,
        "summary": summary,
        "lesson": lines,
        "links": [{"kind": k, "title": t, "url": u} for (k, t, u) in links],
        "quiz": [{"q": q, "choices": c, "answer": a, "explain": e} for (q, c, a, e) in quiz],
    }

def shuffle_choices(track):
    """Deterministically shuffle answer order (seeded by module id + question
    index) so the correct answer isn't always in the same slot. True/False
    questions keep their natural order."""
    for m in track["modules"]:
        for i, q in enumerate(m["quiz"]):
            if q["choices"] in (["True", "False"], ["False", "True"]):
                continue
            seed = int(hashlib.sha256(f"{m['id']}#{i}".encode()).hexdigest(), 16)
            rng = random.Random(seed)
            order = list(range(len(q["choices"])))
            rng.shuffle(order)
            correct = q["choices"][q["answer"]]
            q["choices"] = [q["choices"][j] for j in order]
            q["answer"] = q["choices"].index(correct)

def write(path, track):
    shuffle_choices(track)
    for m in track["modules"]:
        assert 3 <= len(m["quiz"]) <= 5, (m["id"], len(m["quiz"]))
        assert 1 <= len(m["links"]) <= 3, (m["id"], len(m["links"]))
        for q in m["quiz"]:
            assert 0 <= q["answer"] < len(q["choices"]), (m["id"], q["q"])
    ids = [m["id"] for m in track["modules"]]
    assert len(ids) == len(set(ids)), "duplicate ids"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(track, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"wrote {path}: {len(track['modules'])} modules")
