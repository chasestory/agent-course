//! Progress persistence: a small JSON file at %APPDATA%\agent-course\progress.json
//! (override with AGENT_COURSE_PROGRESS=<path>).

use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use std::path::PathBuf;
use std::time::{SystemTime, UNIX_EPOCH};

/// A module counts as complete once a quiz attempt scores at least this percentage.
pub const PASS_PCT: u32 = 70;

#[derive(Serialize, Deserialize, Default, Clone, Debug)]
pub struct ModuleProgress {
    #[serde(default)]
    pub best_pct: u32,
    #[serde(default)]
    pub last_pct: u32,
    #[serde(default)]
    pub attempts: u32,
    #[serde(default)]
    pub completed: bool,
    #[serde(default)]
    pub completed_unix: Option<u64>,
}

#[derive(Serialize, Deserialize, Default, Debug)]
pub struct Progress {
    #[serde(default)]
    pub modules: BTreeMap<String, ModuleProgress>,
    #[serde(default)]
    pub last_opened: Option<String>,
}

pub fn path() -> PathBuf {
    if let Ok(p) = std::env::var("AGENT_COURSE_PROGRESS") {
        return PathBuf::from(p);
    }
    let base = std::env::var("APPDATA")
        .map(PathBuf::from)
        .or_else(|_| std::env::var("HOME").map(|h| PathBuf::from(h).join(".config")))
        .unwrap_or_else(|_| PathBuf::from("."));
    base.join("agent-course").join("progress.json")
}

impl Progress {
    pub fn load() -> Self {
        std::fs::read_to_string(path())
            .ok()
            .and_then(|s| serde_json::from_str(&s).ok())
            .unwrap_or_default()
    }

    pub fn save(&self) -> std::io::Result<()> {
        let p = path();
        if let Some(dir) = p.parent() {
            std::fs::create_dir_all(dir)?;
        }
        let tmp = p.with_extension("json.tmp");
        let json = serde_json::to_string_pretty(self).map_err(std::io::Error::other)?;
        std::fs::write(&tmp, json)?;
        std::fs::rename(&tmp, &p)
    }

    pub fn get(&self, id: &str) -> Option<&ModuleProgress> {
        self.modules.get(id)
    }

    pub fn is_complete(&self, id: &str) -> bool {
        self.get(id).map(|m| m.completed).unwrap_or(false)
    }

    /// Record a finished quiz attempt. Returns the percentage scored.
    pub fn record(&mut self, id: &str, correct: usize, total: usize) -> u32 {
        let pct = if total == 0 {
            100
        } else {
            ((correct as f32 / total as f32) * 100.0).round() as u32
        };
        let e = self.modules.entry(id.to_string()).or_default();
        e.attempts += 1;
        e.last_pct = pct;
        e.best_pct = e.best_pct.max(pct);
        if pct >= PASS_PCT && !e.completed {
            e.completed = true;
            e.completed_unix = SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .ok()
                .map(|d| d.as_secs());
        }
        pct
    }

    pub fn reset(&mut self) {
        self.modules.clear();
        self.last_opened = None;
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn pass_threshold_and_best_score() {
        let mut p = Progress::default();
        assert_eq!(p.record("m", 2, 4), 50);
        assert!(!p.is_complete("m"));
        assert_eq!(p.record("m", 3, 4), 75); // >= 70% completes
        assert!(p.is_complete("m"));
        assert_eq!(p.record("m", 1, 4), 25); // lower retake never un-completes
        let m = p.get("m").unwrap();
        assert!(m.completed);
        assert_eq!(m.best_pct, 75);
        assert_eq!(m.last_pct, 25);
        assert_eq!(m.attempts, 3);
    }

    #[test]
    fn exactly_seventy_percent_passes() {
        let mut p = Progress::default();
        assert_eq!(p.record("x", 7, 10), 70);
        assert!(p.is_complete("x"));
        // 2/3 = 67% does not pass
        assert_eq!(p.record("y", 2, 3), 67);
        assert!(!p.is_complete("y"));
    }

    #[test]
    fn roundtrip_json() {
        let mut p = Progress::default();
        p.record("a", 4, 4);
        let s = serde_json::to_string(&p).unwrap();
        let q: Progress = serde_json::from_str(&s).unwrap();
        assert!(q.is_complete("a"));
        // tolerant of missing fields / older files
        let r: Progress = serde_json::from_str("{}").unwrap();
        assert!(r.modules.is_empty());
    }
}
