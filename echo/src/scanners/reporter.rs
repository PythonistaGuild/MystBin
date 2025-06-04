use std::collections::{HashMap, VecDeque};

use reqwest::header::HeaderMap;
use serde::Serialize;
use tokio::sync::Mutex;

const DESCRIPTION: &str =
    "Mystb.in secret scanning is invalidating these secrets. Use secret pastes to disable this.";

pub struct SecretReporter {
    client: reqwest::Client,
    queued: Mutex<VecDeque<String>>,
    github_token: String,
}

impl SecretReporter {
    pub fn new(github_token: &str) -> Self {
        let version = env!("CARGO_PKG_VERSION");
        let user_agent = format!("Echo/{} (+https://mystb.in)", version);

        let client = reqwest::Client::builder()
            .https_only(true)
            .user_agent(user_agent)
            .build()
            .unwrap();

        let queued = Mutex::new(VecDeque::new());
        let github_token = format!("Bearer {github_token}");

        SecretReporter {
            client,
            queued,
            github_token,
        }
    }

    pub async fn add(&self, item: &str) {
        let mut queue = self.queued.lock().await;
        queue.push_back(item.to_owned());
    }

    pub async fn run(&self) {
        let queue = self.queued.lock().await;

        if queue.is_empty() {
            return;
        }

        let copy = queue.clone();
        let mut data = CreateGist::new();

        for (idx, secret) in copy.iter().enumerate() {
            data.add_file(idx.to_string() + ".txt", secret);
        }

        drop(queue); // Allow acquiring elsewhere

        if let Err(error) = self.create_gist(data).await {
            eprintln!("Failed to create gist: {}", error.0);
        }
    }

    async fn create_gist<'r>(&self, data: CreateGist<'r>) -> Result<(), GistError> {
        let mut headers = HeaderMap::new();

        headers.append("Authorization", self.github_token.parse().unwrap());
        headers.append("X-GitHub-Api-Version", "2022-11-28".parse().unwrap());
        headers.append("Accept", "application/vnd.github+json".parse().unwrap());

        self.client
            .post("https://api.github.com/gists")
            .headers(headers)
            .json(&data)
            .send()
            .await?
            .error_for_status()?;

        let mut queue = self.queued.lock().await;
        queue.drain(0..data.len());

        Ok(())
    }
}

struct GistError(String);

impl From<reqwest::Error> for GistError {
    fn from(value: reqwest::Error) -> Self {
        GistError(value.to_string())
    }
}

#[derive(Serialize)]
struct CreateGist<'r> {
    public: bool,
    description: &'r str,
    files: HashMap<String, CreateGistFile<'r>>,
}

impl<'r> CreateGist<'r> {
    fn new() -> Self {
        CreateGist {
            public: true,
            files: HashMap::new(),
            description: DESCRIPTION,
        }
    }

    fn len(&self) -> usize {
        self.files.len()
    }

    fn add_file(&mut self, filename: String, content: &'r str) {
        self.files.insert(filename, CreateGistFile { content });
    }
}

#[derive(Serialize)]
struct CreateGistFile<'r> {
    content: &'r str,
}
