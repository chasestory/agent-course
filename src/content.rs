//! Course content model. Content lives in `content/*.json` (one file per track).
//! The JSON is embedded into the binary at build time, but if a `content/`
//! folder exists next to the exe (or in the current directory) it is loaded
//! instead, so you can edit lessons without rebuilding.

use serde::Deserialize;
use std::path::{Path, PathBuf};

/// Lesson text can be a single markdown string or an array of lines
/// (arrays are much easier to edit in JSON).
#[derive(Deserialize, Clone, Debug)]
#[serde(untagged)]
pub enum Text {
    One(String),
    Lines(Vec<String>),
}

impl Text {
    pub fn joined(&self) -> String {
        match self {
            Text::One(s) => s.clone(),
            Text::Lines(v) => v.join("\n"),
        }
    }
}

#[derive(Deserialize, Clone, Debug)]
pub struct Link {
    /// "video" or "doc"
    pub kind: String,
    pub title: String,
    pub url: String,
}

#[derive(Deserialize, Clone, Debug)]
pub struct Question {
    pub q: String,
    pub choices: Vec<String>,
    /// zero-based index into `choices`
    pub answer: usize,
    /// shown after answering (explains the right answer and the trap answers)
    pub explain: String,
}

#[derive(Deserialize, Clone, Debug)]
pub struct Module {
    pub id: String,
    pub title: String,
    pub summary: String,
    pub lesson: Text,
    pub links: Vec<Link>,
    pub quiz: Vec<Question>,
}

#[derive(Deserialize, Clone, Debug)]
pub struct Track {
    /// short code shown before module numbers, e.g. "A" -> A1, A2...
    pub id: String,
    pub title: String,
    pub subtitle: String,
    #[serde(default)]
    pub order: i32,
    pub modules: Vec<Module>,
}

pub struct Course {
    pub tracks: Vec<Track>,
    pub source: String,
    pub warnings: Vec<String>,
}

const EMBEDDED: &[(&str, &str)] = &[
    (
        "track-0-math.json",
        include_str!("../content/track-0-math.json"),
    ),
    (
        "track-a-foundations.json",
        include_str!("../content/track-a-foundations.json"),
    ),
    (
        "track-b-ship-agents.json",
        include_str!("../content/track-b-ship-agents.json"),
    ),
];

fn parse(name: &str, text: &str, warnings: &mut Vec<String>) -> Option<Track> {
    match serde_json::from_str::<Track>(text) {
        Ok(t) => Some(t),
        Err(e) => {
            warnings.push(format!("{name}: {e}"));
            None
        }
    }
}

fn load_dir(dir: &Path, warnings: &mut Vec<String>) -> Vec<Track> {
    let mut files: Vec<PathBuf> = match std::fs::read_dir(dir) {
        Ok(rd) => rd
            .filter_map(|e| e.ok().map(|e| e.path()))
            .filter(|p| p.extension().map(|x| x == "json").unwrap_or(false))
            .collect(),
        Err(_) => return vec![],
    };
    files.sort();
    let mut tracks = vec![];
    for f in files {
        let name = f.file_name().unwrap_or_default().to_string_lossy().to_string();
        match std::fs::read_to_string(&f) {
            Ok(text) => {
                if let Some(t) = parse(&name, &text, warnings) {
                    tracks.push(t);
                }
            }
            Err(e) => warnings.push(format!("{name}: {e}")),
        }
    }
    tracks
}

fn validate(tracks: &mut Vec<Track>, warnings: &mut Vec<String>) {
    for t in tracks.iter_mut() {
        for m in t.modules.iter_mut() {
            m.quiz.retain(|q| {
                let ok = q.answer < q.choices.len() && q.choices.len() >= 2;
                if !ok {
                    warnings.push(format!(
                        "{}: dropped quiz question with bad answer index: {}",
                        m.id, q.q
                    ));
                }
                ok
            });
        }
    }
    tracks.sort_by(|a, b| a.order.cmp(&b.order).then(a.id.cmp(&b.id)));
}

pub fn load() -> Course {
    let mut warnings = vec![];
    let mut candidates: Vec<PathBuf> = vec![];
    if let Ok(dir) = std::env::var("AGENT_COURSE_CONTENT") {
        candidates.push(PathBuf::from(dir));
    }
    if let Ok(exe) = std::env::current_exe() {
        if let Some(d) = exe.parent() {
            candidates.push(d.join("content"));
        }
    }
    if let Ok(cwd) = std::env::current_dir() {
        candidates.push(cwd.join("content"));
    }
    for dir in candidates {
        if dir.is_dir() {
            let mut tracks = load_dir(&dir, &mut warnings);
            if !tracks.is_empty() {
                validate(&mut tracks, &mut warnings);
                return Course {
                    tracks,
                    source: dir.display().to_string(),
                    warnings,
                };
            }
        }
    }
    let mut tracks: Vec<Track> = EMBEDDED
        .iter()
        .filter_map(|(n, t)| parse(n, t, &mut warnings))
        .collect();
    validate(&mut tracks, &mut warnings);
    Course {
        tracks,
        source: "built-in (embedded at compile time)".into(),
        warnings,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashSet;

    #[test]
    fn embedded_content_is_valid() {
        let mut warnings = vec![];
        let mut tracks: Vec<Track> = EMBEDDED
            .iter()
            .filter_map(|(n, t)| parse(n, t, &mut warnings))
            .collect();
        validate(&mut tracks, &mut warnings);
        assert!(warnings.is_empty(), "{warnings:?}");
        assert_eq!(tracks.len(), 3);
        assert_eq!(tracks.iter().map(|t| t.id.as_str()).collect::<Vec<_>>(), ["M", "A", "B"]);
        let total: usize = tracks.iter().map(|t| t.modules.len()).sum();
        assert_eq!(total, 52);
        let mut ids = HashSet::new();
        for t in &tracks {
            for m in &t.modules {
                assert!(ids.insert(m.id.clone()), "duplicate id {}", m.id);
                assert!((3..=5).contains(&m.quiz.len()), "{} quiz len", m.id);
                assert!((1..=3).contains(&m.links.len()), "{} links", m.id);
                assert!(!m.lesson.joined().trim().is_empty());
                for l in &m.links {
                    assert!(l.url.starts_with("https://"), "{}", l.url);
                    assert!(l.kind == "video" || l.kind == "doc");
                }
                for q in &m.quiz {
                    assert!(q.answer < q.choices.len());
                    assert!(!q.explain.is_empty());
                }
            }
        }
    }
}
