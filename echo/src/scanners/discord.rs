use std::sync::Arc;

use base64::{prelude::BASE64_STANDARD_NO_PAD, Engine as _};
use once_cell::sync::Lazy;
use regex::{Match, Regex};

use super::Scanner;

const NAME: Lazy<Arc<String>> = Lazy::new(|| Arc::new(String::from("Discord")));

pub struct DiscordScanner;

impl Scanner for DiscordScanner {
    fn service(&self) -> Arc<String> {
        Arc::clone(&NAME)
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
