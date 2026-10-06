#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod app;
mod content;
mod markdown;
mod progress;

use eframe::egui;

fn main() -> eframe::Result<()> {
    // `agent-course --check` validates content and exits (handy after editing JSON).
    if std::env::args().any(|a| a == "--check") {
        let course = content::load();
        let mut modules = 0;
        let mut questions = 0;
        let mut links = 0;
        for t in &course.tracks {
            println!("{} ({} modules)", t.title, t.modules.len());
            modules += t.modules.len();
            for m in &t.modules {
                questions += m.quiz.len();
                links += m.links.len();
            }
        }
        println!("source: {}", course.source);
        println!("total: {modules} modules, {questions} questions, {links} links");
        for w in &course.warnings {
            println!("WARNING: {w}");
        }
        println!("progress file: {}", progress::path().display());
        std::process::exit(if course.warnings.is_empty() { 0 } else { 1 });
    }
    let options = eframe::NativeOptions {
        viewport: egui::ViewportBuilder::default()
            .with_inner_size([1200.0, 820.0])
            .with_min_inner_size([820.0, 560.0])
            .with_title("Agent Course"),
        ..Default::default()
    };
    eframe::run_native(
        "Agent Course",
        options,
        Box::new(|cc| Ok(Box::new(app::CourseApp::new(cc)))),
    )
}
