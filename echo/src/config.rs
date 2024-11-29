use std::sync::Arc;

use serde::{Deserialize, Serialize};

#[derive(Debug, Deserialize, Serialize)]
pub struct ScannerConfig {
    pub name: Arc<String>,
    pub pattern: String,
    pub invalidate: bool,
}

#[derive(Debug, Deserialize, Serialize)]
pub struct Config {
    // CORS
    pub allowed_hosts: Vec<String>,
    // Secret Scanning
    pub github_token: String,
    pub extra_scanners: Vec<ScannerConfig>,
}
