//! Tiny markdown renderer for lesson text. Supports:
//! `## h2`, `### h3`, paragraphs, `- bullets`, `1. numbered`, `> quotes`,
//! fenced ``` code blocks, inline `code` and **bold**.

use crate::app::palette::*;
use eframe::egui::{self, text::LayoutJob, FontId, RichText, TextFormat};

const BODY: f32 = 15.0;

pub fn render(ui: &mut egui::Ui, md: &str) {
    let mut para = String::new();
    let mut code = String::new();
    let mut in_code = false;

    for raw in md.lines() {
        let line = raw.trim_end();
        let s = line.trim_start();

        if s.starts_with("```") {
            if in_code {
                code_block(ui, &code);
                code.clear();
                in_code = false;
            } else {
                flush(ui, &mut para);
                in_code = true;
            }
            continue;
        }
        if in_code {
            code.push_str(line);
            code.push('\n');
            continue;
        }
        if s.is_empty() {
            flush(ui, &mut para);
            continue;
        }
        if let Some(h) = s.strip_prefix("### ") {
            flush(ui, &mut para);
            ui.add_space(6.0);
            ui.label(RichText::new(h).size(16.0).strong().color(TEXT_STRONG));
            continue;
        }
        if let Some(h) = s.strip_prefix("## ") {
            flush(ui, &mut para);
            ui.add_space(12.0);
            ui.label(RichText::new(h).size(19.0).strong().color(ACCENT));
            ui.add_space(2.0);
            continue;
        }
        if let Some(b) = s.strip_prefix("- ").or_else(|| s.strip_prefix("* ")) {
            flush(ui, &mut para);
            list_item(ui, "•", b);
            continue;
        }
        if let Some((n, rest)) = numbered(s) {
            flush(ui, &mut para);
            list_item(ui, &format!("{n}."), rest);
            continue;
        }
        if let Some(q) = s.strip_prefix("> ") {
            flush(ui, &mut para);
            quote(ui, q);
            continue;
        }
        if !para.is_empty() {
            para.push(' ');
        }
        para.push_str(s);
    }
    if in_code && !code.is_empty() {
        code_block(ui, &code);
    }
    flush(ui, &mut para);
}

fn numbered(s: &str) -> Option<(&str, &str)> {
    let d = s.find(|c: char| !c.is_ascii_digit())?;
    if d == 0 {
        return None;
    }
    s[d..].strip_prefix(". ").map(|r| (&s[..d], r))
}

fn flush(ui: &mut egui::Ui, para: &mut String) {
    if para.is_empty() {
        return;
    }
    ui.add(egui::Label::new(inline(para, BODY)).wrap());
    ui.add_space(4.0);
    para.clear();
}

fn list_item(ui: &mut egui::Ui, marker: &str, text: &str) {
    ui.horizontal_top(|ui| {
        ui.add_space(10.0);
        ui.label(RichText::new(marker).size(BODY).color(ACCENT));
        ui.add(egui::Label::new(inline(text, BODY)).wrap());
    });
}

fn quote(ui: &mut egui::Ui, text: &str) {
    egui::Frame::default()
        .fill(QUOTE_BG)
        .corner_radius(4.0)
        .inner_margin(egui::Margin::symmetric(10, 6))
        .show(ui, |ui| {
            ui.set_width(ui.available_width());
            ui.add(egui::Label::new(inline(text, BODY)).wrap());
        });
    ui.add_space(4.0);
}

fn code_block(ui: &mut egui::Ui, code: &str) {
    egui::Frame::default()
        .fill(CODE_BG)
        .corner_radius(4.0)
        .inner_margin(egui::Margin::same(10))
        .show(ui, |ui| {
            ui.set_width(ui.available_width());
            ui.add(
                egui::Label::new(
                    RichText::new(code.trim_end())
                        .monospace()
                        .size(13.5)
                        .color(CODE_FG),
                )
                .wrap(),
            );
        });
    ui.add_space(6.0);
}

/// Inline formatting: **bold** and `code`.
pub fn inline(text: &str, size: f32) -> LayoutJob {
    let mut job = LayoutJob::default();
    let normal = TextFormat {
        font_id: FontId::proportional(size),
        color: TEXT,
        ..Default::default()
    };
    let bold = TextFormat {
        color: TEXT_STRONG,
        ..normal.clone()
    };
    let code_fmt = TextFormat {
        font_id: FontId::monospace(size - 1.5),
        color: CODE_FG,
        background: CODE_BG,
        ..Default::default()
    };

    let mut bold_on = false;
    let mut buf = String::new();
    let chars: Vec<char> = text.chars().collect();
    let mut i = 0;
    while i < chars.len() {
        let c = chars[i];
        if c == '`' {
            let fmt = if bold_on { bold.clone() } else { normal.clone() };
            job.append(&std::mem::take(&mut buf), 0.0, fmt);
            let mut j = i + 1;
            let mut code = String::new();
            while j < chars.len() && chars[j] != '`' {
                code.push(chars[j]);
                j += 1;
            }
            job.append(&code, 0.0, code_fmt.clone());
            i = j + 1;
            continue;
        }
        if c == '*' && i + 1 < chars.len() && chars[i + 1] == '*' {
            let fmt = if bold_on { bold.clone() } else { normal.clone() };
            job.append(&std::mem::take(&mut buf), 0.0, fmt);
            bold_on = !bold_on;
            i += 2;
            continue;
        }
        buf.push(c);
        i += 1;
    }
    let fmt = if bold_on { bold } else { normal };
    job.append(&buf, 0.0, fmt);
    job
}
