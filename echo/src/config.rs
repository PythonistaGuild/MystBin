use std::sync::Arc;

use serde::{Deserialize, Serialize};

#[derive(Debug, Deserialize, Serialize)]
pub struct ScannerConfig {
    pub name: Arc<String>,
    pub pattern: String,
}

#[derive(Debug, Deserialize, Serialize)]
pub struct Config {
    pub allowed_hosts: Vec<String>,
    pub extra_scanners: Vec<ScannerConfig>,
}
