use serde::Serialize;

#[derive(Clone, Copy, Serialize)]
pub struct Version {
    version: &'static str,
}

impl Version {
    const fn new() -> Self {
        Version {
            version: env!("CARGO_PKG_VERSION"),
        }
    }
}

pub static VERSION: Version = Version::new();
