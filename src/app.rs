use crate::content::{Course, Module};
use crate::markdown;
use crate::progress::{self, ModuleProgress, Progress, PASS_PCT};
use eframe::egui::{self, Align, Color32, Layout, Margin, RichText, Sense};
use std::collections::HashMap;

pub mod palette {
    use eframe::egui::Color32;
    pub const BG: Color32 = Color32::from_rgb(19, 21, 27);
    pub const PANEL: Color32 = Color32::from_rgb(24, 26, 34);
    pub const CARD: Color32 = Color32::from_rgb(30, 33, 43);
    pub const CARD_STROKE: Color32 = Color32::from_rgb(44, 48, 62);
    pub const TEXT: Color32 = Color32::from_rgb(208, 211, 222);
    pub const TEXT_STRONG: Color32 = Color32::from_rgb(240, 242, 250);
    pub const MUTED: Color32 = Color32::from_rgb(140, 146, 165);
    pub const ACCENT: Color32 = Color32::from_rgb(122, 162, 247);
    pub const GREEN: Color32 = Color32::from_rgb(126, 201, 142);
    pub const GREEN_BG: Color32 = Color32::from_rgb(28, 52, 38);
    pub const RED: Color32 = Color32::from_rgb(232, 116, 116);
    pub const RED_BG: Color32 = Color32::from_rgb(60, 30, 34);
    pub const YELLOW: Color32 = Color32::from_rgb(224, 190, 110);
    pub const CODE_BG: Color32 = Color32::from_rgb(14, 15, 20);
    pub const CODE_FG: Color32 = Color32::from_rgb(190, 205, 235);
    pub const QUOTE_BG: Color32 = Color32::from_rgb(34, 38, 52);
}
use palette::*;

const TAGLINE: &str = "Nobody asks for your certificate. They ask \u{201C}what did you ship?\u{201D}";
const CONTENT_MAX_W: f32 = 880.0;

#[derive(Clone, Copy, PartialEq)]
enum View {
    Home,
    Module { track: usize, module: usize },
}

#[derive(Default, Clone)]
struct QuizState {
    answers: Vec<Option<usize>>,
    recorded: bool,
    last_pct: Option<u32>,
}

pub struct CourseApp {
    course: Course,
    progress: Progress,
    view: View,
    quiz: HashMap<String, QuizState>,
    confirm_reset: bool,
    scroll_top: bool,
    status: Option<String>,
}

fn status_badge(p: Option<&ModuleProgress>) -> (String, Color32) {
    match p {
        Some(p) if p.completed => (format!("\u{2714} Complete  {}%", p.best_pct), GREEN),
        Some(p) if p.attempts > 0 => (format!("Best {}% \u{2022} retake", p.best_pct), YELLOW),
        _ => ("Not started".to_string(), MUTED),
    }
}

fn nav_dot(p: Option<&ModuleProgress>) -> (&'static str, Color32) {
    match p {
        Some(p) if p.completed => ("\u{2714}", GREEN),
        Some(p) if p.attempts > 0 => ("\u{2022}", YELLOW),
        _ => ("\u{2022}", MUTED),
    }
}

fn card_frame() -> egui::Frame {
    egui::Frame::default()
        .fill(CARD)
        .stroke(egui::Stroke::new(1.0_f32, CARD_STROKE))
        .corner_radius(6.0)
        .inner_margin(Margin::symmetric(12, 9))
}

fn setup_style(ctx: &egui::Context) {
    // Arrows and a few math symbols only exist in the bundled monospace font (Hack),
    // so add it as the last fallback for proportional text.
    let mut fonts = egui::FontDefinitions::default();
    if let Some(fam) = fonts.families.get_mut(&egui::FontFamily::Proportional) {
        fam.push("Hack".to_owned());
    }
    ctx.set_fonts(fonts);

    let mut v = egui::Visuals::dark();
    v.panel_fill = BG;
    v.window_fill = PANEL;
    v.extreme_bg_color = CODE_BG;
    v.faint_bg_color = CARD;
    v.hyperlink_color = ACCENT;
    v.selection.bg_fill = Color32::from_rgb(44, 60, 98);
    v.widgets.noninteractive.fg_stroke.color = TEXT;
    v.widgets.inactive.bg_fill = Color32::from_rgb(38, 42, 55);
    v.widgets.inactive.weak_bg_fill = Color32::from_rgb(38, 42, 55);
    v.widgets.hovered.weak_bg_fill = Color32::from_rgb(50, 56, 74);
    ctx.set_visuals(v);
    ctx.style_mut(|s| {
        s.spacing.item_spacing = egui::vec2(8.0, 6.0);
        s.spacing.button_padding = egui::vec2(10.0, 5.0);
        s.text_styles
            .insert(egui::TextStyle::Body, egui::FontId::proportional(15.0));
        s.text_styles
            .insert(egui::TextStyle::Button, egui::FontId::proportional(14.5));
        s.text_styles
            .insert(egui::TextStyle::Small, egui::FontId::proportional(12.5));
    });
}

fn open_link(ctx: &egui::Context, url: &str) {
    if open::that_detached(url).is_err() {
        ctx.open_url(egui::OpenUrl::new_tab(url));
    }
}

impl CourseApp {
    pub fn new(cc: &eframe::CreationContext<'_>) -> Self {
        setup_style(&cc.egui_ctx);
        let course = crate::content::load();
        // `--open <module-id>` jumps straight to a module.
        let args: Vec<String> = std::env::args().collect();
        let mut view = View::Home;
        if let Some(i) = args.iter().position(|a| a == "--open") {
            if let Some(id) = args.get(i + 1) {
                for (ti, t) in course.tracks.iter().enumerate() {
                    if let Some(mi) = t.modules.iter().position(|m| &m.id == id) {
                        view = View::Module { track: ti, module: mi };
                    }
                }
            }
        }
        Self {
            course,
            progress: Progress::load(),
            view,
            quiz: HashMap::new(),
            confirm_reset: false,
            scroll_top: true,
            status: None,
        }
    }

    fn total(&self) -> usize {
        self.course.tracks.iter().map(|t| t.modules.len()).sum()
    }

    fn done(&self) -> usize {
        self.course
            .tracks
            .iter()
            .flat_map(|t| t.modules.iter())
            .filter(|m| self.progress.is_complete(&m.id))
            .count()
    }

    fn flat(&self) -> Vec<(usize, usize)> {
        let mut v = vec![];
        for (ti, t) in self.course.tracks.iter().enumerate() {
            for mi in 0..t.modules.len() {
                v.push((ti, mi));
            }
        }
        v
    }

    fn next_up(&self) -> Option<(usize, usize)> {
        self.flat()
            .into_iter()
            .find(|(t, m)| !self.progress.is_complete(&self.course.tracks[*t].modules[*m].id))
    }

    fn code(&self, t: usize, m: usize) -> String {
        format!("{}{}", self.course.tracks[t].id, m + 1)
    }

    fn open_module(&mut self, t: usize, m: usize) {
        self.view = View::Module { track: t, module: m };
        self.scroll_top = true;
        self.progress.last_opened = Some(self.course.tracks[t].modules[m].id.clone());
        self.save();
    }

    fn save(&mut self) {
        if let Err(e) = self.progress.save() {
            self.status = Some(format!("Could not save progress: {e}"));
        }
    }

    fn top_bar(&mut self, ctx: &egui::Context) {
        let (done, total) = (self.done(), self.total());
        let mut go_home = false;
        egui::TopBottomPanel::top("top")
            .frame(egui::Frame::default().fill(PANEL).inner_margin(Margin::symmetric(12, 8)))
            .show(ctx, |ui| {
                ui.horizontal(|ui| {
                    if ui
                        .add(egui::Button::new(RichText::new("Agent Course").strong().color(TEXT_STRONG)).frame(false))
                        .on_hover_text("Home")
                        .clicked()
                    {
                        go_home = true;
                    }
                    if !matches!(self.view, View::Home) && ui.button("\u{25C0} Home").clicked() {
                        go_home = true;
                    }
                    if let Some(s) = &self.status {
                        ui.label(RichText::new(s).color(RED));
                    }
                    ui.with_layout(Layout::right_to_left(Align::Center), |ui| {
                        let frac = if total == 0 { 0.0 } else { done as f32 / total as f32 };
                        ui.add(
                            egui::ProgressBar::new(frac)
                                .desired_width(160.0)
                                .fill(ACCENT)
                                .text(format!("{done}/{total}")),
                        );
                        ui.label(RichText::new("complete").color(MUTED));
                    });
                });
            });
        if go_home {
            self.view = View::Home;
            self.scroll_top = true;
        }
    }

    fn home(&mut self, ctx: &egui::Context) {
        let (done, total) = (self.done(), self.total());
        let next = self.next_up().map(|(t, m)| (t, m, self.code(t, m), self.course.tracks[t].modules[m].title.clone()));
        let mut open: Option<(usize, usize)> = None;
        let mut confirm = self.confirm_reset;
        let mut do_reset = false;
        let scroll_top = std::mem::take(&mut self.scroll_top);
        let course = &self.course;
        let progress = &self.progress;

        egui::CentralPanel::default().show(ctx, |ui| {
            let mut sa = egui::ScrollArea::vertical().auto_shrink(false).id_salt("home_scroll");
            if scroll_top {
                sa = sa.vertical_scroll_offset(0.0);
            }
            sa.show(ui, |ui| {
                let avail = ui.available_width();
                let col_w = (avail - 24.0).min(CONTENT_MAX_W).max(200.0);
                let side = ((avail - col_w) / 2.0).max(4.0);
                ui.horizontal(|ui| {
                    ui.add_space(side);
                    ui.vertical(|ui| {
                        ui.set_width(col_w);
                        ui.add_space(14.0);
                        ui.label(RichText::new("Agent Course").size(32.0).strong().color(TEXT_STRONG));
                        ui.label(RichText::new(TAGLINE).italics().size(17.0).color(ACCENT));
                        ui.add_space(14.0);

                        card_frame().show(ui, |ui| {
                            ui.set_width(ui.available_width());
                            let frac = if total == 0 { 0.0 } else { done as f32 / total as f32 };
                            ui.label(RichText::new(format!("{done}/{total} modules complete")).size(18.0).strong().color(TEXT_STRONG));
                            ui.add(egui::ProgressBar::new(frac).fill(ACCENT).show_percentage());
                            ui.add_space(4.0);
                            match &next {
                                Some((t, m, code, title)) => {
                                    if ui.button(RichText::new(format!("\u{25B6}  Continue: {code} \u{2014} {title}")).color(TEXT_STRONG)).clicked() {
                                        open = Some((*t, *m));
                                    }
                                }
                                None => {
                                    ui.label(RichText::new("All modules complete. Now go ship something and write it up.").color(GREEN));
                                }
                            }
                            ui.label(
                                RichText::new(format!(
                                    "A module is marked complete when one quiz attempt scores \u{2265} {PASS_PCT}%. Your best score is kept; retake any time. All modules are unlocked."
                                ))
                                .small()
                                .color(MUTED),
                            );
                        });

                        for (ti, track) in course.tracks.iter().enumerate() {
                            let tdone = track.modules.iter().filter(|m| progress.is_complete(&m.id)).count();
                            let ttotal = track.modules.len();
                            ui.add_space(22.0);
                            ui.horizontal(|ui| {
                                ui.label(RichText::new(&track.title).size(22.0).strong().color(TEXT_STRONG));
                                ui.with_layout(Layout::right_to_left(Align::Center), |ui| {
                                    ui.label(RichText::new(format!("{tdone}/{ttotal}")).color(if tdone == ttotal && ttotal > 0 { GREEN } else { MUTED }));
                                });
                            });
                            ui.label(RichText::new(&track.subtitle).color(MUTED));
                            let frac = if ttotal == 0 { 0.0 } else { tdone as f32 / ttotal as f32 };
                            ui.add(egui::ProgressBar::new(frac).fill(ACCENT).desired_height(6.0));
                            ui.add_space(8.0);

                            for (mi, m) in track.modules.iter().enumerate() {
                                let code = format!("{}{}", track.id, mi + 1);
                                let resp = module_card(ui, &code, m, progress.get(&m.id));
                                if resp.clicked() {
                                    open = Some((ti, mi));
                                }
                                ui.add_space(2.0);
                            }
                        }

                        ui.add_space(26.0);
                        ui.separator();
                        ui.horizontal(|ui| {
                            if !confirm {
                                if ui.button("Reset all progress\u{2026}").clicked() {
                                    confirm = true;
                                }
                            } else {
                                ui.label(RichText::new("Erase all scores and completions?").color(RED));
                                if ui.button(RichText::new("Yes, reset").color(RED)).clicked() {
                                    do_reset = true;
                                    confirm = false;
                                }
                                if ui.button("Cancel").clicked() {
                                    confirm = false;
                                }
                            }
                        });
                        ui.label(RichText::new(format!("Progress file: {}", progress::path().display())).small().color(MUTED));
                        ui.label(RichText::new(format!("Content: {}", course.source)).small().color(MUTED));
                        for w in &course.warnings {
                            ui.label(RichText::new(format!("Content warning: {w}")).small().color(YELLOW));
                        }
                        ui.add_space(20.0);
                    });
                });
            });
        });

        self.confirm_reset = confirm;
        if do_reset {
            self.progress.reset();
            self.quiz.clear();
            self.save();
        }
        if let Some((t, m)) = open {
            self.open_module(t, m);
        }
    }

    fn module_view(&mut self, ctx: &egui::Context, t: usize, m: usize) {
        let module: Module = self.course.tracks[t].modules[m].clone();
        let code = self.code(t, m);
        let track_title = self.course.tracks[t].title.clone();
        let flat = self.flat();
        let pos = flat.iter().position(|x| *x == (t, m)).unwrap_or(0);
        let prev = if pos > 0 { Some(flat[pos - 1]) } else { None };
        let next = flat.get(pos + 1).copied();
        let scroll_top = std::mem::take(&mut self.scroll_top);
        let mut nav: Option<(usize, usize)> = None;

        // ---- left navigation
        {
            let course = &self.course;
            let progress = &self.progress;
            egui::SidePanel::left("nav")
                .resizable(true)
                .default_width(290.0)
                .frame(egui::Frame::default().fill(PANEL).inner_margin(Margin::same(8)))
                .show(ctx, |ui| {
                    egui::ScrollArea::vertical().auto_shrink(false).show(ui, |ui| {
                        for (ti, track) in course.tracks.iter().enumerate() {
                            ui.add_space(6.0);
                            ui.label(RichText::new(&track.title).strong().color(ACCENT));
                            for (mi, mm) in track.modules.iter().enumerate() {
                                let (dot, col) = nav_dot(progress.get(&mm.id));
                                let sel = ti == t && mi == m;
                                let mut job = egui::text::LayoutJob::default();
                                job.append(dot, 0.0, egui::TextFormat { font_id: egui::FontId::proportional(13.5), color: col, ..Default::default() });
                                job.append(
                                    &format!("  {}{}  {}", track.id, mi + 1, mm.title),
                                    0.0,
                                    egui::TextFormat { font_id: egui::FontId::proportional(13.5), color: if sel { TEXT_STRONG } else { TEXT }, ..Default::default() },
                                );
                                let r = ui.selectable_label(sel, job);
                                if r.clicked() {
                                    nav = Some((ti, mi));
                                }
                                if sel && scroll_top {
                                    r.scroll_to_me(Some(Align::Center));
                                }
                            }
                        }
                    });
                });
        }

        // ---- main content
        let n = module.quiz.len();
        let best = self.progress.get(&module.id).cloned();
        let mut record: Option<(usize, usize)> = None;
        let mut retake = false;
        {
            let state = self.quiz.entry(module.id.clone()).or_default();
            if state.answers.len() != n {
                *state = QuizState { answers: vec![None; n], recorded: false, last_pct: None };
            }
            egui::CentralPanel::default().show(ctx, |ui| {
                let mut sa = egui::ScrollArea::vertical().auto_shrink(false).id_salt("module_scroll");
                if scroll_top {
                    sa = sa.vertical_scroll_offset(0.0);
                }
                sa.show(ui, |ui| {
                    let avail = ui.available_width();
                    let col_w = (avail - 24.0).min(CONTENT_MAX_W).max(200.0);
                    let side = ((avail - col_w) / 2.0).max(4.0);
                    ui.horizontal(|ui| {
                        ui.add_space(side);
                        ui.vertical(|ui| {
                            ui.set_width(col_w);
                            ui.add_space(10.0);
                            prev_next(ui, prev, next, &mut nav);
                            ui.add_space(6.0);
                            ui.label(RichText::new(format!("{track_title}  \u{2022}  {code}")).color(MUTED));
                            ui.label(RichText::new(&module.title).size(27.0).strong().color(TEXT_STRONG));
                            ui.label(RichText::new(&module.summary).size(16.0).italics().color(TEXT));
                            let (badge, col) = status_badge(best.as_ref());
                            ui.label(RichText::new(badge).color(col));
                            ui.add_space(4.0);
                            ui.separator();

                            // lesson
                            markdown::render(ui, &module.lesson.joined());

                            // links
                            if !module.links.is_empty() {
                                ui.add_space(14.0);
                                ui.label(RichText::new("Watch & read").size(19.0).strong().color(ACCENT));
                                for l in &module.links {
                                    let icon = if l.kind == "video" { "\u{25B6} Video" } else { "\u{1F4C4} Docs" };
                                    card_frame().show(ui, |ui| {
                                        ui.set_width(ui.available_width());
                                        ui.horizontal(|ui| {
                                            ui.label(RichText::new(icon).color(if l.kind == "video" { RED } else { ACCENT }).small());
                                            if ui.link(RichText::new(&l.title).color(TEXT_STRONG)).on_hover_text(&l.url).clicked() {
                                                open_link(ui.ctx(), &l.url);
                                            }
                                        });
                                        ui.label(RichText::new(&l.url).small().color(MUTED));
                                    });
                                }
                            }

                            // quiz
                            ui.add_space(18.0);
                            ui.label(RichText::new("Quiz").size(21.0).strong().color(ACCENT));
                            ui.label(RichText::new(format!(
                                "{n} questions \u{2022} answer to get instant feedback \u{2022} score \u{2265} {PASS_PCT}% to complete the module"
                            )).color(MUTED));
                            ui.add_space(6.0);

                            for (qi, q) in module.quiz.iter().enumerate() {
                                let chosen = state.answers[qi];
                                card_frame().show(ui, |ui| {
                                    ui.set_width(ui.available_width());
                                    ui.add(egui::Label::new(markdown::inline(&format!("**{}.** {}", qi + 1, q.q), 15.5)).wrap());
                                    ui.add_space(4.0);
                                    for (ci, choice) in q.choices.iter().enumerate() {
                                        let letter = (b'A' + ci as u8) as char;
                                        let (fill, stroke, mark) = match chosen {
                                            None => (Color32::from_rgb(38, 42, 55), CARD_STROKE, String::new()),
                                            Some(c) if ci == q.answer => (GREEN_BG, GREEN, if c == ci { "  \u{2714}".into() } else { "  \u{2714} correct answer".into() }),
                                            Some(c) if ci == c => (RED_BG, RED, "  \u{2716}".into()),
                                            Some(_) => (Color32::from_rgb(33, 36, 47), CARD_STROKE, String::new()),
                                        };
                                        let resp = egui::Frame::default()
                                            .fill(fill)
                                            .stroke(egui::Stroke::new(1.0_f32, stroke))
                                            .corner_radius(5.0)
                                            .inner_margin(Margin::symmetric(10, 6))
                                            .show(ui, |ui| {
                                                ui.set_width(ui.available_width());
                                                ui.style_mut().interaction.selectable_labels = false;
                                                ui.add(egui::Label::new(markdown::inline(&format!("**{letter}.**  {choice}{mark}"), 15.0)).wrap());
                                            })
                                            .response;
                                        if chosen.is_none() {
                                            let r = resp.interact(Sense::click());
                                            if r.hovered() {
                                                ui.ctx().set_cursor_icon(egui::CursorIcon::PointingHand);
                                            }
                                            if r.clicked() {
                                                state.answers[qi] = Some(ci);
                                            }
                                        }
                                        ui.add_space(2.0);
                                    }
                                    if let Some(c) = chosen {
                                        ui.add_space(4.0);
                                        let (head, col) = if c == q.answer {
                                            ("\u{2714} Correct. ".to_string(), GREEN)
                                        } else {
                                            (format!("\u{2716} Not quite \u{2014} the answer is {}. ", (b'A' + q.answer as u8) as char), RED)
                                        };
                                        ui.horizontal_wrapped(|ui| {
                                            ui.label(RichText::new(head).strong().color(col));
                                        });
                                        ui.add(egui::Label::new(markdown::inline(&q.explain, 14.5)).wrap());
                                    }
                                });
                                ui.add_space(6.0);
                            }

                            let answered = state.answers.iter().filter(|a| a.is_some()).count();
                            let correct = state.answers.iter().zip(module.quiz.iter()).filter(|(a, q)| **a == Some(q.answer)).count();
                            if n > 0 && answered == n {
                                if !state.recorded {
                                    record = Some((correct, n));
                                    state.recorded = true;
                                }
                                let pct = ((correct as f32 / n as f32) * 100.0).round() as u32;
                                let passed = pct >= PASS_PCT;
                                egui::Frame::default()
                                    .fill(if passed { GREEN_BG } else { RED_BG })
                                    .corner_radius(6.0)
                                    .inner_margin(Margin::same(12))
                                    .show(ui, |ui| {
                                        ui.set_width(ui.available_width());
                                        ui.label(RichText::new(format!("Score: {correct}/{n}  ({pct}%)")).size(20.0).strong().color(TEXT_STRONG));
                                        if passed {
                                            ui.label(RichText::new("\u{2714} Module complete. Nice \u{2014} now apply it to something you ship.").color(GREEN));
                                        } else {
                                            ui.label(RichText::new(format!("You need {PASS_PCT}% to complete this module. Re-read the explanations above and retake.")).color(RED));
                                        }
                                        ui.horizontal(|ui| {
                                            if ui.button("Retake quiz").clicked() {
                                                retake = true;
                                            }
                                            if let Some(nx) = next {
                                                if ui.button("Next module \u{25B6}").clicked() {
                                                    nav = Some(nx);
                                                }
                                            }
                                        });
                                    });
                            } else if n > 0 {
                                ui.label(RichText::new(format!("{answered}/{n} answered")).color(MUTED));
                            }
                            ui.add_space(14.0);
                            prev_next(ui, prev, next, &mut nav);
                            ui.add_space(30.0);
                        });
                    });
                });
            });
        }

        if let Some((c, total)) = record {
            let pct = self.progress.record(&module.id, c, total);
            if let Some(s) = self.quiz.get_mut(&module.id) {
                s.last_pct = Some(pct);
            }
            self.save();
        }
        if retake {
            self.quiz.insert(module.id.clone(), QuizState { answers: vec![None; n], recorded: false, last_pct: None });
        }
        if let Some((t2, m2)) = nav {
            self.open_module(t2, m2);
        }
    }
}

fn prev_next(ui: &mut egui::Ui, prev: Option<(usize, usize)>, next: Option<(usize, usize)>, nav: &mut Option<(usize, usize)>) {
    ui.horizontal(|ui| {
        if ui.add_enabled(prev.is_some(), egui::Button::new("\u{25C0} Previous")).clicked() {
            *nav = prev;
        }
        ui.with_layout(Layout::right_to_left(Align::Center), |ui| {
            if ui.add_enabled(next.is_some(), egui::Button::new("Next \u{25B6}")).clicked() {
                *nav = next;
            }
        });
    });
}

fn module_card(ui: &mut egui::Ui, code: &str, m: &Module, p: Option<&ModuleProgress>) -> egui::Response {
    let (badge, col) = status_badge(p);
    let resp = card_frame()
        .show(ui, |ui| {
            ui.set_width(ui.available_width());
            ui.style_mut().interaction.selectable_labels = false;
            ui.with_layout(Layout::right_to_left(Align::Center), |ui| {
                ui.label(RichText::new(badge).color(col).size(13.5));
                ui.with_layout(Layout::left_to_right(Align::Center), |ui| {
                    ui.add_sized([34.0, 20.0], egui::Label::new(RichText::new(code).monospace().color(MUTED)));
                    ui.vertical(|ui| {
                        ui.add(egui::Label::new(RichText::new(&m.title).strong().size(15.5).color(TEXT_STRONG)).wrap());
                        ui.add(egui::Label::new(RichText::new(&m.summary).size(13.5).color(MUTED)).wrap());
                    });
                });
            });
        })
        .response
        .interact(Sense::click());
    if resp.hovered() {
        ui.ctx().set_cursor_icon(egui::CursorIcon::PointingHand);
        ui.painter().rect_stroke(resp.rect, 6.0, egui::Stroke::new(1.0_f32, ACCENT), egui::StrokeKind::Inside);
    }
    resp
}

impl eframe::App for CourseApp {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        self.top_bar(ctx);
        match self.view {
            View::Home => self.home(ctx),
            View::Module { track, module } => {
                if track < self.course.tracks.len() && module < self.course.tracks[track].modules.len() {
                    self.module_view(ctx, track, module)
                } else {
                    self.view = View::Home;
                }
            }
        }
    }
}
