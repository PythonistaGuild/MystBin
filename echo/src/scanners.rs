use std::sync::{Arc, OnceLock};

use base64::{prelude::BASE64_STANDARD_NO_PAD, Engine};
use once_cell::sync::Lazy;
use regex::{Match, Regex};
use rocket::{
    fairing::{self, Fairing, Info, Kind},
    Build, Rocket,
};

use crate::{
    config::{Config, ScannerConfig},
    models::pastes::Position,
};

fn find_position(content: &str, position: usize) -> Position {
    let haystack = &content[0..position];
    let (idx, line) = haystack.split('\n').enumerate().last().unwrap();

    Position {
        line: idx as i32,
        char: line.len() as i32,
    }
}

pub struct ScanResult<'r> {
    pub head: Position,
    pub tail: Position,

    pub content: &'r str,
    pub service: Arc<String>,
}

trait Scanner: Send + Sync {
    fn pattern(&self) -> &Regex;
    fn service(&self) -> Arc<String>;

    fn confirm(&self, _item: &Match) -> bool {
        true
    }

    fn execute<'r>(&self, haystack: &'r str) -> Vec<Match<'r>> {
        self.pattern()
            .find_iter(haystack)
            .filter(|x| self.confirm(x))
            .collect()
    }
}

struct DiscordScanner {
    name: Arc<String>,
}

impl DiscordScanner {
    fn new() -> Self {
        DiscordScanner {
            name: Arc::new(String::from("Discord")),
        }
    }
}

impl Scanner for DiscordScanner {
    fn service(&self) -> Arc<String> {
        Arc::clone(&self.name)
    }

    fn pattern(&self) -> &'static Regex {
        static PATTERN: Lazy<Regex> = Lazy::new(|| {
            Regex::new(r"[a-zA-Z0-9_-]{23,28}\.[a-zA-Z0-9_-]{6,7}\.[a-zA-Z0-9_-]{27,}").unwrap()
        });

        &PATTERN
    }

    fn confirm(&self, item: &Match) -> bool {
        let mut parts = item.as_str().split('.');

        let user_id = match parts.next() {
            None => return false,
            Some(value) => value,
        };

        // Discord tokens have 3 parts total
        if parts.count() != 2 {
            return false;
        }

        match BASE64_STANDARD_NO_PAD.decode(user_id) {
            Ok(_) => true,
            Err(_) => false,
        }
    }
}

struct GenericScanner {
    name: Arc<String>,
    pattern: Regex,
}

impl GenericScanner {
    fn new(config: &ScannerConfig) -> Self {
        let name = Arc::clone(&config.name);
        let pattern = Regex::new(&config.pattern).expect("invalid scanner pattern");

        GenericScanner { name, pattern }
    }
}

impl Scanner for GenericScanner {
    fn service(&self) -> Arc<String> {
        Arc::clone(&self.name)
    }

    fn pattern(&self) -> &Regex {
        &self.pattern
    }
}

static SCANNERS: OnceLock<Vec<Box<dyn Scanner>>> = OnceLock::new();

pub struct InitScanners;

#[rocket::async_trait]
impl Fairing for InitScanners {
    fn info(&self) -> Info {
        Info {
            name: "Scanner Initialization",
            kind: Kind::Ignite,
        }
    }

    async fn on_ignite(&self, rocket: Rocket<Build>) -> fairing::Result {
        let config = rocket.state::<Config>().unwrap();
        let mut active: Vec<Box<dyn Scanner>> = Vec::new();

        active.push(Box::new(DiscordScanner::new()));

        for value in &config.extra_scanners {
            active.push(Box::new(GenericScanner::new(value)));
        }

        if let Err(_) = SCANNERS.set(active) {
            panic!("failed to set up scanners!")
        }

        Ok(rocket)
    }
}

pub fn scan_file<'r>(content: &'r str) -> Vec<ScanResult<'r>> {
    let mut results = Vec::new();

    for scanner in SCANNERS.get().unwrap() {
        for result in scanner.execute(content) {
            let result = ScanResult {
                service: scanner.service(),
                content: result.as_str(),
                head: find_position(content, result.start()),
                tail: find_position(content, result.end()),
            };

            results.push(result);
        }
    }

    results
}
