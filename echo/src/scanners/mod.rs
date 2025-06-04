use std::{
    sync::{Arc, OnceLock},
    time::Duration,
};

use discord::DiscordScanner;
use generic::GenericScanner;
use regex::{Match, Regex};
use reporter::SecretReporter;
use rocket::{
    fairing::{self, Fairing, Info, Kind},
    Build, Rocket,
};
use tokio::time;

use crate::{config::Config, models::pastes::Position};

mod discord;
mod generic;
mod reporter;

pub struct ScanResult<'r> {
    pub head: Position,
    pub tail: Position,

    pub content: &'r str,
    pub invalidated: bool,
    pub service: Arc<String>,
}

static REPORTER: OnceLock<SecretReporter> = OnceLock::new();
static SCANNERS: OnceLock<Vec<Box<dyn Scanner>>> = OnceLock::new();

pub async fn scan_file<'r>(content: &'r str, invalidate_secrets: bool) -> Vec<ScanResult<'r>> {
    let mut results = Vec::new();

    for scanner in SCANNERS.get().unwrap() {
        for finding in scanner.execute(content) {
            let do_invalidate = scanner.nullify() && invalidate_secrets;

            let result = ScanResult {
                service: scanner.service(),
                content: finding.as_str(),
                invalidated: do_invalidate,
                head: find_position(content, finding.start()),
                tail: find_position(content, finding.end()),
            };

            results.push(result);

            if do_invalidate {
                REPORTER.get().unwrap().add(finding.as_str()).await;
            }
        }
    }

    results
}

fn find_position(content: &str, position: usize) -> Position {
    let haystack = &content[0..position];
    let (idx, line) = haystack.split('\n').enumerate().last().unwrap();

    Position::new(idx as i32, line.len() as i32)
}

trait Scanner: Send + Sync {
    fn pattern(&self) -> &Regex;
    fn service(&self) -> Arc<String>;

    /// Whether to invalidate found secrets
    fn nullify(&self) -> bool {
        true
    }

    /// Whether a found item might be valid
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

        active.push(Box::new(DiscordScanner));

        for value in &config.extra_scanners {
            active.push(Box::new(GenericScanner::new(value)));
        }

        if let Err(_) = SCANNERS.set(active) {
            panic!("failed to set up scanners")
        }

        let reporter = SecretReporter::new(&config.github_token);

        if let Err(_) = REPORTER.set(reporter) {
            panic!("failed to set up reporter")
        }

        tokio::spawn(async move {
            let reporter = REPORTER.get().unwrap();
            let mut interval = time::interval(Duration::from_secs(10));

            loop {
                reporter.run().await;
                interval.tick().await;
            }
        });

        Ok(rocket)
    }
}
