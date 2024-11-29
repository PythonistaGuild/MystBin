use std::sync::Arc;

use regex::Regex;

use crate::config::ScannerConfig;

use super::Scanner;

pub struct GenericScanner {
    name: Arc<String>,
    pattern: Regex,
    nullify: bool,
}

impl GenericScanner {
    pub fn new(config: &ScannerConfig) -> Self {
        let name = Arc::clone(&config.name);
        let pattern = Regex::new(&config.pattern).expect("invalid scanner pattern");
        let nullify = config.invalidate;

        GenericScanner {
            name,
            pattern,
            nullify,
        }
    }
}

impl Scanner for GenericScanner {
    fn pattern(&self) -> &Regex {
        &self.pattern
    }

    fn service(&self) -> Arc<String> {
        Arc::clone(&self.name)
    }

    fn nullify(&self) -> bool {
        self.nullify
    }
}
